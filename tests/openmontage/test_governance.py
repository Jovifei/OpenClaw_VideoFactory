import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_repository_and_vendored_subset_are_agpl_and_hash_bound() -> None:
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU AFFERO GENERAL PUBLIC LICENSE" in license_text
    assert "Version 3, 19 November 2007" in license_text
    notices = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")
    assert "calesthio/OpenMontage" in notices
    assert "cd9f3c1f03368be87b140af494914b8ee4e3c7a4" in notices

    manifest_path = ROOT / "third_party" / "openmontage" / "PROVENANCE.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["license"] == "AGPL-3.0-only"
    assert manifest["upstream_commit"] == "cd9f3c1f03368be87b140af494914b8ee4e3c7a4"
    assert manifest["files"]
    for item in manifest["files"]:
        target = ROOT / item["vendored_path"]
        data = target.read_bytes()
        assert hashlib.sha256(data).hexdigest() == item["vendored_sha256"]
        if target.suffix == ".py":
            head = data.decode("utf-8").splitlines()[:6]
            assert any("Source:" in line for line in head)
            assert any("Modified:" in line for line in head)
def test_hash_bound_vendor_files_pin_checkout_line_endings() -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8")
    assert "third_party/openmontage/** text eol=lf" in attributes
