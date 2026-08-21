from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from src.factory import reference_video
from video_factory.pipeline.errors import FactoryContractError


def _make_mp4(path: Path, *, audio: bool = False) -> None:
    command = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=blue:s=320x180:r=30"]
    if audio:
        command.extend(["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000"])
    command.extend(["-t", "1.2", "-c:v", "libx264", "-pix_fmt", "yuv420p"])
    if audio:
        command.extend(["-c:a", "aac", "-shortest"])
    else:
        command.append("-an")
    command.append(str(path))
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    assert completed.returncode == 0, completed.stderr


def _rights(path: Path) -> Path:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    rights_path = path.with_name("rights.json")
    rights_path.write_text(json.dumps({
        "schema_version": "1.0",
        "rights_basis": "owned",
        "source_owner": "Jovi",
        "license_reference": "local-test",
        "source_sha256": digest,
        "processing_timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
    }), encoding="utf-8")
    return rights_path


def test_ingest_copies_hash_bound_read_only_reference(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    _make_mp4(source)
    storage = tmp_path / "storage"
    runtime = tmp_path / "runtime"
    monkeypatch.setattr(reference_video, "REFERENCE_STORAGE_ROOT", storage)
    monkeypatch.setattr(reference_video, "REFERENCE_RUNTIME_ROOT", runtime)
    monkeypatch.setattr(reference_video, "PROJECT_ROOT", tmp_path)
    bundle = reference_video.ingest_reference(source, _rights(source))
    stored = Path(bundle["stored_path"])
    assert stored.read_bytes() == source.read_bytes()
    assert (stored.stat().st_mode & 0o222) == 0
    assert bundle["receipt"]["source_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()


def test_ingest_rejects_fake_or_wrong_extension(tmp_path: Path) -> None:
    fake = tmp_path / "not-video.mp4"
    fake.write_bytes(b"not an mp4")
    rights = tmp_path / "rights.json"
    rights.write_text(json.dumps({}), encoding="utf-8")
    with pytest.raises(FactoryContractError) as caught:
        reference_video.ingest_reference(fake, rights)
    assert caught.value.code in {"reference_video_invalid", "reference_rights_invalid", "reference_contract_invalid"}

    wrong = tmp_path / "source.mov"
    wrong.write_bytes(b"x")
    with pytest.raises(FactoryContractError) as caught:
        reference_video.ingest_reference(wrong, rights)
    assert caught.value.code == "reference_video_extension_invalid"


def test_ingest_rejects_source_sha_mismatch(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    _make_mp4(source)
    rights = _rights(source)
    value = json.loads(rights.read_text(encoding="utf-8"))
    value["source_sha256"] = "0" * 64
    rights.write_text(json.dumps(value), encoding="utf-8")
    with pytest.raises(FactoryContractError) as caught:
        reference_video.ingest_reference(source, rights)
    assert caught.value.code == "reference_rights_sha_mismatch"


def test_ingest_rejects_source_changed_during_ffprobe(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    _make_mp4(source)
    rights = _rights(source)

    def mutate_then_probe(path: Path) -> dict[str, object]:
        path.write_bytes(path.read_bytes() + b"changed")
        return {"duration_seconds": 1.2, "width": 320, "height": 180, "has_audio": False, "fps": 30.0}

    monkeypatch.setattr(reference_video, "_run_ffprobe", mutate_then_probe)
    with pytest.raises(FactoryContractError) as caught:
        reference_video.ingest_reference(source, rights)
    assert caught.value.code == "reference_source_changed"


def test_ingest_rejects_symlink_source(tmp_path: Path) -> None:
    source = tmp_path / "source.mp4"
    _make_mp4(source)
    link = tmp_path / "link.mp4"
    try:
        link.symlink_to(source)
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable in this Windows test environment")
    with pytest.raises(FactoryContractError) as caught:
        reference_video.ingest_reference(link, _rights(source))
    assert caught.value.code == "reference_video_reparse_rejected"
