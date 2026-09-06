from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_phase1_pipeline_has_exact_stages_and_only_final_human_gate() -> None:
    path = ROOT / "third_party" / "openmontage" / "pipelines" / "phase1-local-topic.yaml"
    manifest = yaml.safe_load(path.read_text(encoding="utf-8"))
    stages = manifest["stages"]
    assert [stage["name"] for stage in stages] == [
        "research", "proposal", "script", "scene_plan", "assets", "edit", "compose", "review"
    ]
    assert [stage["name"] for stage in stages if stage["human_approval_default"]] == ["review"]
    assert manifest["metadata"]["state_authority"] == "factory_sqlite"
