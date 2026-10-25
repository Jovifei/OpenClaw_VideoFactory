from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import subprocess
import sys
import threading
from pathlib import Path

import pytest

import generate_video
from src.factory import phase1_cli
from src.factory.db import CandidateStore
from video_factory.pipeline.errors import FactoryContractError


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def local_store(tmp_path, monkeypatch):
    monkeypatch.setattr(phase1_cli, 'PROJECT_ROOT', tmp_path)
    monkeypatch.setattr(phase1_cli, 'INPUT_ROOT', tmp_path / 'inputs')
    monkeypatch.setattr(phase1_cli, 'DATABASE_PATH', tmp_path / 'jobs.sqlite3')
    store = phase1_cli._store()
    brief = tmp_path / 'input.json'
    brief.write_text('{}', encoding='utf-8')
    job = store.create_job('local_topic', 'test:review', 'video_factory_local_brief', 'test',
                           requested_duration_seconds=30, metadata={'brief_path': 'input.json'})
    return tmp_path, store, job['job_id']


def _run(job_id):
    return phase1_cli._run_job(argparse.Namespace(job_id=job_id, plan_only=False))


def _fake_outputs(root):
    # Control-plane unit fixtures only; not evidence of a real MP4 or review.
    output, review = root / 'fake-output.mp4', root / 'fake-review.json'
    output.write_bytes(b'UNIT FIXTURE ONLY')
    review.write_text('{}', encoding='utf-8')
    return {'output': str(output), 'review_package': str(review)}


@pytest.mark.parametrize('reference', [False, True], ids=['topic', 'reference'])
def test_quality_checkpoint_retry_never_becomes_ready_before_publication(local_store, monkeypatch, reference):
    root, store, job_id = local_store
    if reference:
        job_id = store.create_job('local_reference', 'test:reference-recovery', 'video_factory_local_reference',
                                  'reference', requested_duration_seconds=30,
                                  metadata={'brief_path': 'input.json', 'input_mode': 'local_reference',
                                            'runtime_root': 'runtime', 'source_sha256': 'a' * 64})['job_id']
        monkeypatch.setattr(phase1_cli, 'load_reference_bundle', lambda *a, **k: {})
    phase1_cli._advance_to_rendering(store, job_id)
    store.advance(job_id, 'QUALITY_CHECK', 'checkpoint_before_worker_exit')
    store.cancel(job_id, 'recover_interrupted_worker')
    assert store.retry(job_id, 'explicit_retry')['state'] == 'QUALITY_CHECK'
    seen = []

    def render(*args, **kwargs):
        seen.append(kwargs['render_identity'])
        assert store.status(job_id)['state'] != 'PENDING_REVIEW'
        assert store.artifacts(job_id) == []
        return _fake_outputs(root)

    monkeypatch.setattr(generate_video, 'run_local_brief', render)
    result = _run(job_id)
    assert result['status'] == 'pending_review'
    assert seen == [f'{job_id}:attempt:1']
    assert {row['artifact_type'] for row in store.artifacts(job_id)} == {'final_master', 'review_package'}
    pending = [event for event in store.events(job_id) if event['to_state'] == 'PENDING_REVIEW']
    assert len(pending) == 1 and len(pending[0]['payload']['artifacts']) == 2


def test_quality_checkpoint_retry_missing_media_fails_without_review(local_store, monkeypatch):
    root, store, job_id = local_store
    phase1_cli._advance_to_rendering(store, job_id)
    store.advance(job_id, 'QUALITY_CHECK', 'interrupted_publication')
    store.cancel(job_id, 'recover_worker')
    store.retry(job_id, 'explicit_retry')
    result = _fake_outputs(root)
    Path(result['output']).unlink()
    monkeypatch.setattr(generate_video, 'run_local_brief', lambda *a, **k: result)
    with pytest.raises(FactoryContractError, match='phase1_review_artifact_invalid'):
        _run(job_id)
    assert store.status(job_id)['state'] == 'FAILED' and store.artifacts(job_id) == []
    assert store.retry(job_id, 'repair_input')['state'] == 'RENDERING'
    assert not [event for event in store.events(job_id) if event['to_state'] == 'PENDING_REVIEW']


@pytest.mark.parametrize('missing', ['output', 'review_package'])
def test_missing_artifact_never_publishes_terminal_or_partial_rows(local_store, monkeypatch, missing):
    root, store, job_id = local_store
    result = _fake_outputs(root)
    Path(result[missing]).unlink()
    monkeypatch.setattr(generate_video, 'run_local_brief', lambda *a, **k: result)
    with pytest.raises((OSError, ValueError, FactoryContractError)):
        _run(job_id)
    assert store.status(job_id)['state'] == 'FAILED'
    assert store.artifacts(job_id) == []
    assert store.retry(job_id, 'repair_input')['state'] == 'RENDERING'


def test_pending_review_reuse_rejects_changed_bytes(local_store, monkeypatch):
    root, store, job_id = local_store
    result = _fake_outputs(root)
    monkeypatch.setattr(generate_video, 'run_local_brief', lambda *a, **k: result)
    assert _run(job_id)['status'] == 'pending_review'
    Path(result['output']).write_bytes(b'CHANGED AFTER REVIEW')
    with pytest.raises((OSError, ValueError, FactoryContractError)):
        _run(job_id)
    assert store.status(job_id)['state'] == 'FAILED'


def test_cancel_retry_fences_returning_worker(local_store, monkeypatch):
    root, store, job_id = local_store
    result = _fake_outputs(root)
    def old_worker(*args, **kwargs):
        controller = CandidateStore(store.path)
        controller.cancel(job_id, 'test_cancel')
        controller.retry(job_id, 'test_retry')
        return result
    monkeypatch.setattr(generate_video, 'run_local_brief', old_worker)
    with pytest.raises((OSError, ValueError, FactoryContractError)):
        _run(job_id)
    assert store.status(job_id)['state'] == 'RENDERING'
    assert store.status(job_id)['attempt'] == 1
    assert store.artifacts(job_id) == []


def test_same_job_has_one_executing_worker(local_store, monkeypatch):
    root, store, job_id = local_store
    result = _fake_outputs(root)
    entered, release, second_done = threading.Event(), threading.Event(), threading.Event()
    calls, errors = [], []
    def render(*args, **kwargs):
        calls.append(1)
        entered.set()
        if not release.wait(10):
            raise RuntimeError('test_release_timeout')
        return result
    def worker(done=None):
        try:
            _run(job_id)
        except Exception as exc:
            errors.append(exc)
        finally:
            if done is not None:
                done.set()
    monkeypatch.setattr(generate_video, 'run_local_brief', render)
    first = threading.Thread(target=worker)
    second = threading.Thread(target=worker, args=(second_done,))
    first.start()
    try:
        assert entered.wait(5)
        second.start()
        assert second_done.wait(3), 'second worker must report busy instead of entering render'
        assert len(calls) == 1
    finally:
        release.set()
        first.join(5)
        if second.ident is not None:
            second.join(5)
    assert store.status(job_id)['state'] == 'PENDING_REVIEW'
    assert len(errors) == 1


def _request(root, *, aspect='9:16', key=None):
    brief = json.loads((ROOT / 'examples/phase1_local_modbus/brief.json').read_text(encoding='utf-8'))
    brief['aspect_ratio'] = aspect
    path = root / f'request-{aspect.replace(":", "_")}.json'
    path.write_text(json.dumps(brief, ensure_ascii=False), encoding='utf-8')
    return phase1_cli._create_topic(argparse.Namespace(brief=path, idempotency_key=key))


def test_aspect_variants_do_not_replace_queued_input(local_store):
    root, store, _ = local_store
    first = _request(root)
    persisted = root / first['job']['metadata']['brief_path']
    before = hashlib.sha256(persisted.read_bytes()).hexdigest()
    second = _request(root, aspect='16:9')
    assert first['job']['job_id'] != second['job']['job_id']
    assert hashlib.sha256(persisted.read_bytes()).hexdigest() == before
    assert _request(root)['job']['job_id'] == first['job']['job_id']


def test_explicit_key_conflict_does_not_change_input(local_store):
    root, store, _ = local_store
    first = _request(root, key='same-explicit-key')
    persisted = root / first['job']['metadata']['brief_path']
    before = persisted.read_bytes()
    with pytest.raises(FactoryContractError, match='idempotency'):
        _request(root, aspect='16:9', key='same-explicit-key')
    assert persisted.read_bytes() == before


def test_explicit_key_from_other_fixture_is_a_conflict(local_store):
    root, store, _ = local_store
    store.create_job('local_subject', 'mixed:key', 'phase1_subject_plan', 'test',
                     requested_duration_seconds=30, metadata={'topic_request_path': 'subject.json'})
    with pytest.raises(FactoryContractError, match='idempotency'):
        _request(root, key='mixed:key')


def test_legacy_key_conflict_does_not_read_outside_project(local_store, monkeypatch):
    root, store, _ = local_store
    foreign = root.parent / 'foreign-unit-input.json'
    foreign.write_text('{}', encoding='utf-8')
    store.create_job('local_topic', 'legacy:foreign', 'video_factory_local_brief', 'test',
                     requested_duration_seconds=30, metadata={'brief_path': '../foreign-unit-input.json'})
    read = Path.read_text
    def contained_read(path, *args, **kwargs):
        if path.resolve() == foreign.resolve():
            raise AssertionError('Legacy collision must not read foreign input.')
        return read(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'read_text', contained_read)
    with pytest.raises(FactoryContractError, match='idempotency'):
        _request(root, key='legacy:foreign')


def test_database_publication_error_rolls_back_all_artifacts_and_state(local_store):
    root, store, job_id = local_store
    from src.factory.state import STAGES
    for stage in STAGES[1:-1]:
        store.advance(job_id, stage)
    connection = store._connect()
    connection.execute("CREATE TRIGGER fail_review BEFORE INSERT ON artifacts "
                       "WHEN NEW.artifact_type='review_package' BEGIN SELECT RAISE(ABORT,'injected_store_failure'); END")
    connection.commit()
    connection.close()
    records = phase1_cli._publication_artifacts({
        'final_master': _fake_outputs(root)['output'], 'review_package': root / 'fake-review.json'})
    with pytest.raises(sqlite3.IntegrityError, match='injected_store_failure'):
        store.publish_review_artifacts(job_id, records, reason='test')
    assert store.status(job_id)['state'] == 'QUALITY_CHECK'
    assert store.artifacts(job_id) == []


def test_old_locks_schema_migration_preserves_existing_rows(local_store):
    root, store, job_id = local_store
    connection = store._connect()
    connection.execute('DROP TABLE locks')
    connection.execute('CREATE TABLE locks(lock_name TEXT PRIMARY KEY,job_id TEXT NOT NULL REFERENCES jobs(job_id),acquired_at TEXT NOT NULL)')
    connection.execute('INSERT INTO locks VALUES(?,?,?)', ('other-resource', job_id, '2000-01-01T00:00:00Z'))
    connection.commit()
    connection.close()
    store.initialize()
    connection = store._connect()
    try:
        row = dict(connection.execute('SELECT * FROM locks WHERE lock_name=?', ('other-resource',)).fetchone())
    finally:
        connection.close()
    assert row['job_id'] == job_id and row['owner_token'] == '' and row['attempt'] == 0
    with store.execution_claim(job_id):
        assert store.status(job_id)['state'] == 'NEW'


def test_report_pruning_retention_dry_run_never_deletes_data(local_store):
    root, store, job_id = local_store
    from src.factory.inventory import build_retention_plan
    connection = store._connect()
    connection.execute('UPDATE jobs SET created_at=? WHERE job_id=?', ('2000-01-01T00:00:00Z', job_id))
    connection.commit()
    connection.close()
    media = root / 'retained.mp4'
    media.write_bytes(b'UNIT RETENTION FIXTURE')
    before_job = store.status(job_id)
    before_media = media.read_bytes()
    reports = root / 'reports'
    reports.mkdir()
    report = reports / 'historical.md'
    report.write_text(job_id, encoding='utf-8')
    before = build_retention_plan(store, reports)
    report.unlink()
    after = build_retention_plan(store, reports)
    assert before['entries'][0]['action'] == 'retain'
    assert after['entries'][0]['action'] == 'manual_review_only'
    for plan in [before, after]:
        assert plan['destructive_actions'] is False and plan['deletion_performed'] is False
    assert media.read_bytes() == before_media and store.status(job_id) == before_job


def test_killed_claim_owner_requires_explicit_cancel_retry(local_store):
    root, store, job_id = local_store
    code = """from pathlib import Path
import sys
from src.factory.db import CandidateStore
s=CandidateStore(Path(sys.argv[1]));s.initialize()
with s.execution_claim(sys.argv[2]):
 print('CLAIM_READY',flush=True)
 sys.stdin.read()
"""
    child = subprocess.Popen([sys.executable, '-c', code, str(store.path), job_id],
                             cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert child.stdout.readline().strip() == b'CLAIM_READY'
        child.terminate()
        child.wait(timeout=5)
        assert child.poll() is not None
        controller = CandidateStore(store.path)
        with pytest.raises(ValueError, match='job_execution_in_progress'):
            with controller.execution_claim(job_id):
                pytest.fail('A dead owner must not be silently taken over.')
        controller.cancel(job_id, 'verified_test_owner_dead')
        retried = controller.retry(job_id, 'explicit_recovery')
        assert retried['attempt'] == 1
        with controller.execution_claim(job_id):
            assert controller.status(job_id)['state'] == 'NEW'
    finally:
        if child.poll() is None:
            child.terminate()
            child.wait(timeout=5)
        for stream in [child.stdin, child.stdout, child.stderr]:
            if stream is not None:
                stream.close()
