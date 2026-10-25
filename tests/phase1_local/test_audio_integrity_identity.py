from __future__ import annotations

import hashlib
import shutil
import struct
import wave

import pytest

from scripts.phase1_audio_integrity import _audit_fixture


@pytest.fixture
def audio_fixture(tmp_path):
    # Real tiny PCM WAVs for the audit contract, not production speech or human approval.
    raw, aligned, combined = tmp_path / 'raw.wav', tmp_path / 'aligned' / 'one.wav', tmp_path / 'audio.wav'
    aligned.parent.mkdir()
    pcm = struct.pack('<h', 1200) * 480
    for path, data in [(raw, pcm), (aligned, pcm + b'\0\0' * 480)]:
        with wave.open(str(path), 'wb') as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(48000)
            handle.writeframes(data)
    shutil.copy2(aligned, combined)
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    return {'topic': 'UNIT AUDIO AUDIT', 'passes': [{'rewrite_count': 1,
        'allocation': {'duration_seconds': 0.02}, 'aligned_audio': {
            'path': str(combined), 'sha256': sha(combined), 'duration_seconds': 0.02,
            'segments': [{'scene_id': 'unit', 'audio_path': str(raw), 'aligned_audio_file': 'one.wav',
                          'raw_audio_sha256': sha(raw), 'aligned_audio_sha256': sha(aligned)}]}}]}


def test_audio_audit_keeps_distinct_source_and_aligned_identities(audio_fixture):
    result = _audit_fixture(audio_fixture)
    assert result['audio_sha256_matches_report'] is True
    assert result['segments'][0]['raw_audio_sha256'] != result['segments'][0]['aligned_audio_sha256']
    assert result['actual_endpoint_seconds'] == pytest.approx(0.02)


@pytest.mark.parametrize('target', ['combined', 'raw'])
def test_audio_audit_rejects_declared_identity_mismatch(audio_fixture, target):
    aligned = audio_fixture['passes'][0]['aligned_audio']
    if target == 'combined':
        aligned['sha256'] = 'a' * 64
    else:
        aligned['segments'][0]['raw_audio_sha256'] = 'a' * 64
    with pytest.raises(ValueError, match='audio_identity_mismatch'):
        _audit_fixture(audio_fixture)


def test_audio_audit_measures_duration_instead_of_trusting_matching_declarations(audio_fixture):
    audio_fixture['passes'][0]['allocation']['duration_seconds'] = 1.0
    audio_fixture['passes'][0]['aligned_audio']['duration_seconds'] = 1.0
    with pytest.raises(ValueError, match='audio_endpoint_mismatch'):
        _audit_fixture(audio_fixture)
