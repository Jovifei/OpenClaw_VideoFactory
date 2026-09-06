from __future__ import annotations

import json
from pathlib import Path

from src.factory import phase1_cli
from src.factory.db import CandidateStore
from src.factory.phase1_topic import MPT_COMMIT, build_research_brief


def _configure(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(phase1_cli, "STATE_ROOT", tmp_path / "state")
    monkeypatch.setattr(phase1_cli, "DATABASE_PATH", tmp_path / "state" / "jobs.sqlite3")
    monkeypatch.setattr(phase1_cli, "INPUT_ROOT", tmp_path / "state" / "inputs")
    monkeypatch.setattr(phase1_cli, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(phase1_cli, "OPENMONTAGE_PROJECTS_ROOT", tmp_path / "state" / "openmontage_projects")
    monkeypatch.setattr(phase1_cli, "SUBJECT_DELIVERY_ROOT", tmp_path / "dist" / "phase1_local")


def _output(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def _projected_sqlite_state(job_id: str) -> str:
    project = phase1_cli.OPENMONTAGE_PROJECTS_ROOT / job_id
    pointer = json.loads((project / "current.json").read_text(encoding="utf-8"))
    generation = project / pointer["generation"]
    checkpoint = next(generation.glob("checkpoint_*.json"))
    return json.loads(checkpoint.read_text(encoding="utf-8"))["metadata"]["sqlite_state"]


def _research() -> dict:
    return build_research_brief(topic="看门狗", sources=[{"id":"s1","url":"https://x/a","title":"a","kind":"official_document"},{"id":"s2","url":"https://x/b","title":"b","kind":"research_paper"}], facts=[{"id":"f1","claim":"看门狗检测失去响应","source_ids":["s1"]},{"id":"f2","claim":"超时需验证","source_ids":["s2"]}])


def test_create_subject_is_stably_idempotent_and_parameter_sensitive(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    args = ["create-subject", "--subject", "看门狗"]
    assert phase1_cli.main(args) == 0
    first = _output(capsys)
    assert _projected_sqlite_state(first["job"]["job_id"]) == "NEW"
    assert first["job"]["fixture_id"] == "local_subject"
    assert first["job"]["metadata"]["pipeline_type"] == "phase1-local-topic"
    assert phase1_cli.main(args) == 0
    second = _output(capsys)
    assert second["status"] == "existing"
    assert second["job"]["job_id"] == first["job"]["job_id"]
    assert phase1_cli.main(args + ["--duration", "41"]) == 0
    assert _output(capsys)["job"]["job_id"] != first["job"]["job_id"]


def test_requested_idempotency_key_is_audit_only(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject","--subject","看门狗","--idempotency-key","user-a"]) == 0
    first = _output(capsys)["job"]
    assert phase1_cli.main(["create-subject","--subject","看门狗","--idempotency-key","user-b"]) == 0
    same = _output(capsys)["job"]
    assert same["job_id"] == first["job_id"]
    assert first["metadata"]["requested_idempotency_key"] == "user-a"
    assert phase1_cli.main(["create-subject","--subject","串口 DMA","--idempotency-key","user-a"]) == 0
    assert _output(capsys)["job"]["job_id"] != first["job_id"]


def test_attach_research_contains_copy_and_subject_run_stops_before_render(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    created = _output(capsys)
    job_id = created["job"]["job_id"]
    outside = tmp_path / "outside.json"
    outside.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(outside)]) == 0
    attached = _output(capsys)
    copied = tmp_path / attached["research_path"]
    assert copied.is_file() and copied != outside

    def fake_run_drafts(**kwargs):
        output = tmp_path / "mpt.json"
        output.write_text(json.dumps({"schema_version":"1.0","kind":"phase1_script_drafts","subject":"看门狗","language":"zh-CN","requested_candidates":3,"successful_candidates":3,"mpt_version":"1.3.5","mpt_commit":MPT_COMMIT,"candidates":[{"candidate":i,"script":"看门狗发生故障：看门狗检测失去响应，超时需验证。再解释原理、配置和恢复边界。","duration_seconds":1} for i in range(1,4)],"failures":[]}, ensure_ascii=False), encoding="utf-8")
        return output

    monkeypatch.setattr(phase1_cli, "MPT_RUN_DRAFTS", fake_run_drafts)
    assert phase1_cli.main(["run", "--job-id", job_id, "--plan-only"]) == 0
    result = _output(capsys)
    assert result["status"] == "subject_plan_ready"
    assert result["job"]["state"] == "ASSETS"
    assert {a["artifact_type"] for a in result["artifacts"]} == {"research_brief", "script_candidates", "selected_script", "director_script", "scene_plan"}
    store = CandidateStore(phase1_cli.DATABASE_PATH)
    assert store.status(job_id)["state"] == "ASSETS"


def test_attach_research_rejects_unrelated_topic(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    unrelated = _research()
    unrelated["topic"] = "串口 DMA"
    unrelated["topic_digest"] = "0" * 64
    path = tmp_path / "unrelated.json"
    path.write_text(json.dumps(unrelated, ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(path)]) == 2
    assert _output(capsys)["error"]["code"] == "phase1_research_topic_mismatch"


def test_subject_failure_is_persisted_and_retry_reenters_planning(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    research_path = tmp_path / "research.json"
    research_path.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(research_path)]) == 0
    _output(capsys)
    monkeypatch.setattr(phase1_cli, "MPT_RUN_DRAFTS", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("mpt failed")))
    assert phase1_cli.main(["run", "--job-id", job_id]) == 2
    _output(capsys)
    store = CandidateStore(phase1_cli.DATABASE_PATH)
    assert store.status(job_id)["state"] == "FAILED"
    assert _projected_sqlite_state(job_id) == "FAILED"
    assert phase1_cli.main(["retry", "--job-id", job_id]) == 0
    retried = _output(capsys)
    assert retried["job"]["state"] == "SCRIPTING"
    assert _projected_sqlite_state(job_id) == "SCRIPTING"


def test_subject_cancel_is_projected(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    assert phase1_cli.main(["cancel", "--job-id", job_id]) == 0
    _output(capsys)
    assert _projected_sqlite_state(job_id) == "CANCELLED"


def test_subject_second_attempt_receives_score_informed_guidance(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    research_path = tmp_path / "research.json"
    research_path.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(research_path)]) == 0
    _output(capsys)
    calls = []
    def fake_run_drafts(**kwargs):
        calls.append(kwargs)
        strong = len(calls) == 2
        script = "看门狗发生故障：看门狗检测失去响应，超时需验证。再解释原理、配置和恢复边界。" if strong else "短"
        output = tmp_path / f"mpt-{len(calls)}.json"
        output.write_text(json.dumps({"schema_version":"1.0","kind":"phase1_script_drafts","subject":"看门狗","language":"zh-CN","requested_candidates":3,"successful_candidates":3,"mpt_version":"1.3.5","mpt_commit":MPT_COMMIT,"candidates":[{"candidate":i,"script":script,"duration_seconds":1} for i in range(1,4)],"failures":[]}, ensure_ascii=False), encoding="utf-8")
        return output
    monkeypatch.setattr(phase1_cli, "MPT_RUN_DRAFTS", fake_run_drafts)
    assert phase1_cli.main(["run", "--job-id", job_id, "--plan-only"]) == 0
    result = _output(capsys)
    assert calls[0]["rewrite_guidance"] is None
    assert "改进维度" in calls[1]["rewrite_guidance"]
    assert "完整已核验 claim" in calls[1]["rewrite_guidance"]
    selected_path = tmp_path / next(a["relative_path"] for a in result["artifacts"] if a["artifact_type"] == "selected_script")
    assert json.loads(selected_path.read_text(encoding="utf-8"))["rewrite_attempt"] == 1
    assert "看门狗检测失去响应" in calls[0]["research_guidance"]
    assert "s1" in calls[0]["research_guidance"]


def test_subject_default_run_delivers_once_and_registers_preview_aliases(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "看门狗"]) == 0
    job_id = _output(capsys)["job"]["job_id"]
    research_path = tmp_path / "research.json"; research_path.write_text(json.dumps(_research(), ensure_ascii=False), encoding="utf-8")
    assert phase1_cli.main(["attach-research", "--job-id", job_id, "--research", str(research_path)]) == 0; _output(capsys)
    monkeypatch.setattr(phase1_cli, "MPT_RUN_DRAFTS", lambda **_: _drafts(tmp_path))
    calls: list[object] = []
    def media(request, **_):
        calls.append(request)
        root = request.workdir; root.mkdir(parents=True)
        preview = root / "audible_preview.mp4"; preview.write_bytes(b"synthetic-preview")
        receipt = root / "subject_media_result.json"; receipt.write_text("{}", encoding="utf-8")
        return {"paths": {"preview": str(preview)}, "output": str(preview), "receipt": str(receipt)}
    def package(request, **_):
        root = request.package_root / f"attempt_{request.attempt}" / "review_package"; root.mkdir(parents=True)
        review = root / "review_package.json"; review.write_text("{}", encoding="utf-8")
        quality = root / "subject_quality_report.json"; quality.write_text("{}", encoding="utf-8")
        return {"package_path": str(root), "review_package": str(review), "quality_report": str(quality), "media_receipt": str(request.media_root / "subject_media_result.json"), "preview": str(request.media_root / "audible_preview.mp4")}
    monkeypatch.setattr(phase1_cli, "run_subject_media", media)
    monkeypatch.setattr(phase1_cli, "build_subject_review_package", package)
    monkeypatch.setattr(phase1_cli, "validate_subject_media_receipt", lambda _: {})
    assert phase1_cli.main(["run", "--job-id", job_id]) == 0
    result = _output(capsys)
    assert result["status"] == "pending_review" and result["job"]["state"] == "PENDING_REVIEW" and len(calls) == 1
    artifacts = {item["artifact_type"]: item for item in result["artifacts"]}
    assert {"final_master", "review_package", "media_receipt"}.issubset(artifacts)
    assert artifacts["final_master"]["relative_path"].endswith("audible_preview.mp4")
    assert phase1_cli.main(["run", "--job-id", job_id]) == 0
    assert _output(capsys)["idempotent"] is True and len(calls) == 1


def test_subject_media_failure_returns_review_blocked_and_retry_resumes_rendering(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "串口 DMA"]) == 0
    job = _output(capsys)["job"]
    store = CandidateStore(phase1_cli.DATABASE_PATH)
    for target in ("RESEARCHING", "SCRIPTING", "VOICE", "CAPTIONS", "ASSETS"):
        store.advance(job["job_id"], target)
    monkeypatch.setattr(phase1_cli, "run_subject_media", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("synthetic media failed")))
    assert phase1_cli.main(["run", "--job-id", job["job_id"]]) == 0
    assert _output(capsys)["status"] == "review_blocked"
    assert store.status(job["job_id"])["state"] == "FAILED"
    assert phase1_cli.main(["retry", "--job-id", job["job_id"]]) == 0
    assert _output(capsys)["job"]["state"] == "RENDERING"


def test_subject_cancelled_during_media_never_reaches_pending_review(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "中断测试"]) == 0
    job = _output(capsys)["job"]
    store = CandidateStore(phase1_cli.DATABASE_PATH)
    for target in ("RESEARCHING", "SCRIPTING", "VOICE", "CAPTIONS", "ASSETS"):
        store.advance(job["job_id"], target)
    def cancel_after_start(*_args, **_kwargs):
        store.cancel(job["job_id"], "synthetic_cancel")
        return {}
    monkeypatch.setattr(phase1_cli, "run_subject_media", cancel_after_start)
    assert phase1_cli.main(["run", "--job-id", job["job_id"]]) == 0
    result = _output(capsys)
    assert result["status"] == "cancelled" and result["job"]["state"] == "CANCELLED"
    assert "final_master" not in {item["artifact_type"] for item in result["artifacts"]}


def test_subject_missing_request_at_assets_is_review_blocked_and_projected(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    store = CandidateStore(phase1_cli.DATABASE_PATH); store.initialize()
    job = store.create_job("local_subject", "missing-request", "phase1_subject_plan", "看门狗", metadata={"input_mode": "local_subject"})
    for target in ("RESEARCHING", "SCRIPTING", "VOICE", "CAPTIONS", "ASSETS"):
        store.advance(job["job_id"], target)
    assert phase1_cli.main(["run", "--job-id", job["job_id"]]) == 0
    assert _output(capsys)["status"] == "review_blocked"
    assert store.status(job["job_id"])["state"] == "FAILED" and _projected_sqlite_state(job["job_id"]) == "FAILED"


def test_subject_cancel_after_builder_withdraws_ready_manifest_before_publication(tmp_path, monkeypatch, capsys) -> None:
    _configure(tmp_path, monkeypatch)
    assert phase1_cli.main(["create-subject", "--subject", "撤回测试"]) == 0
    job = _output(capsys)["job"]
    store = CandidateStore(phase1_cli.DATABASE_PATH)
    for target in ("RESEARCHING", "SCRIPTING", "VOICE", "CAPTIONS", "ASSETS"):
        store.advance(job["job_id"], target)
    monkeypatch.setattr(phase1_cli, "validate_subject_media_receipt", lambda _: {})
    monkeypatch.setattr(phase1_cli, "run_subject_media", lambda *_args, **_kwargs: {})
    def package(request, **_):
        root = request.package_root / f"attempt_{request.attempt}" / "review_package"; root.mkdir(parents=True)
        request.media_root.mkdir(parents=True, exist_ok=True)
        review = root / "review_package.json"; review.write_text(json.dumps({"status": "ready_for_human_review"}), encoding="utf-8")
        preview = request.media_root / "audible_preview.mp4"; preview.write_bytes(b"synthetic-preview")
        receipt = request.media_root / "subject_media_result.json"; receipt.write_text("{}", encoding="utf-8")
        store.cancel(job["job_id"], "synthetic_after_builder")
        return {"review_package": str(review), "quality_report": str(root / "subject_quality_report.json"), "media_receipt": str(receipt), "preview": str(preview)}
    monkeypatch.setattr(phase1_cli, "build_subject_review_package", package)
    assert phase1_cli.main(["run", "--job-id", job["job_id"]]) == 0
    result = _output(capsys)
    manifest_root = phase1_cli.SUBJECT_DELIVERY_ROOT / f"phase1_subject_{job['job_id'].split('-')[-1]}" / "attempt_1" / "review_package"
    assert result["status"] == "cancelled" and not (manifest_root / "review_package.json").exists()
    assert (manifest_root / "review_package.cancelled.json").is_file()
    assert not {"final_master", "review_package", "media_receipt"}.intersection({item["artifact_type"] for item in result["artifacts"]})


def _drafts(tmp_path: Path) -> Path:
    output = tmp_path / "mpt-default.json"
    output.write_text(json.dumps({"schema_version":"1.0","kind":"phase1_script_drafts","subject":"看门狗","language":"zh-CN","requested_candidates":3,"successful_candidates":3,"mpt_version":"1.3.5","mpt_commit":MPT_COMMIT,"candidates":[{"candidate":i,"script":"看门狗发生故障：看门狗检测失去响应，超时需验证。再解释原理、配置和恢复边界。","duration_seconds":1} for i in range(1,4)],"failures":[]}, ensure_ascii=False), encoding="utf-8")
    return output
