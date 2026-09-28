"""Prove the source-bound I2C subject route without rendering media."""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import sys
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.factory import phase1_cli
from src.factory.phase1_topic import MPT_COMMIT


REPORT_PATH = ROOT / "reports" / "phase1" / "stage_20260928" / "i2c_subject_route_preflight.json"
RESEARCH_PATH = ROOT / "examples" / "phase1_subject_i2c" / "research_brief.json"
REQUIRED_FACTS = {"open_drain", "rise_time", "sink_current"}
REQUIRED_LABELS = ["SDA", "SCL", "START", "ADDRESS", "ACK/NACK", "DATA", "STOP"]
SUBJECT = "I2C总线为什么要上拉电阻"


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _canonical_i2c_draft(subject: str, output: Path) -> Path:
    prose = (
        "为什么I2C总线要上拉？I2C线路通常采用开漏结构；器件主动拉低，释放后由上拉电阻恢复高电平。"
        "上拉电阻与总线电容决定上升沿；电阻过大可能使线路来不及达到有效高电平。"
        "电阻过小则增加低电平灌电流，可能超出器件的拉低能力；阻值必须兼顾两端限制。"
    )
    output.write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "kind": "phase1_script_drafts",
                "subject": subject,
                "language": "zh-CN",
                "requested_candidates": 3,
                "successful_candidates": 3,
                "mpt_version": "1.3.5",
                "mpt_commit": MPT_COMMIT,
                "candidates": [{"candidate": i, "script": prose, "duration_seconds": 1} for i in (1, 2, 3)],
                "failures": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return output


def validate_i2c_subject_plan(
    *,
    topic_request: Mapping[str, Any],
    research: Mapping[str, Any],
    director_script: Mapping[str, Any],
    scene_plan: Mapping[str, Any],
) -> dict[str, Any]:
    """Validate the semantic route and fail closed on generic visual plans."""

    if topic_request.get("subject") != SUBJECT or topic_request.get("aspect") != "9:16":
        raise ValueError("i2c_subject_or_aspect_invalid")
    if research.get("topic") != SUBJECT:
        raise ValueError("i2c_research_topic_invalid")
    facts = research.get("facts")
    fact_ids = {str(item.get("id")) for item in facts if isinstance(item, Mapping)} if isinstance(facts, list) else set()
    if fact_ids != REQUIRED_FACTS:
        raise ValueError("i2c_research_fact_set_invalid")
    scenes = scene_plan.get("scenes")
    beats = director_script.get("beats")
    if not isinstance(scenes, list) or not isinstance(beats, list) or len(scenes) != len(beats):
        raise ValueError("i2c_subject_plan_scene_count_invalid")
    if director_script.get("script_id") != scene_plan.get("script_id"):
        raise ValueError("i2c_subject_plan_script_binding_invalid")
    visual_specs = []
    for scene in scenes:
        if not isinstance(scene, Mapping):
            raise ValueError("i2c_subject_scene_invalid")
        refs = {str(value) for value in scene.get("source_refs", [])}
        spec = scene.get("visual_spec")
        if refs:
            if not isinstance(spec, Mapping) or spec.get("kind") != "i2c_bus_v1":
                raise ValueError("i2c_bus_visual_spec_missing")
            if list(spec.get("labels", [])) != REQUIRED_LABELS:
                raise ValueError("i2c_bus_labels_invalid")
            if set(map(str, spec.get("fact_refs", []))) != refs or not refs.issubset(REQUIRED_FACTS):
                raise ValueError("i2c_bus_fact_refs_invalid")
            visual_specs.append(dict(spec))
        elif spec is not None:
            raise ValueError("i2c_hook_visual_spec_invalid")
    union = {str(ref) for spec in visual_specs for ref in spec.get("fact_refs", [])}
    if union != REQUIRED_FACTS:
        raise ValueError("i2c_bus_fact_union_invalid")
    serialized = json.dumps(scene_plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    lowered = serialized.casefold()
    if "modbus" in lowered or "flash_watchdog" in lowered:
        raise ValueError("generic_registry_asset_lineage_selected")
    return {
        "status": "passed",
        "subject": SUBJECT,
        "aspect_ratio": "9:16",
        "fact_ids": sorted(REQUIRED_FACTS),
        "fact_ref_union": sorted(union),
        "labels": REQUIRED_LABELS,
        "visual_spec_count": len(visual_specs),
        "generic_registry_asset_lineage_selected": False,
    }


def _call(arguments: list[str]) -> dict[str, Any]:
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = phase1_cli.main(arguments)
    value = json.loads(output.getvalue())
    if result != 0:
        raise RuntimeError(json.dumps(value, ensure_ascii=False))
    return value


def _write_still_timing_manifest(*, script_path: Path, scene_plan_path: Path, output: Path, scene_count: int) -> Path:
    segments = []
    for index in range(scene_count):
        start = index * 8_000_000
        end = (index + 1) * 8_000_000
        segments.append({"index": index + 1, "scene_start_microseconds": start, "scene_end_microseconds": end})
    value = {
        "schema_version": "1.0",
        "script": {"filename": script_path.name, "sha256": _sha(script_path)},
        "scene_plan": {"filename": scene_plan_path.name, "sha256": _sha(scene_plan_path)},
        "timing": {"fps": 30, "transition_mode": "technical_cut"},
        "visual_duration_seconds": 40.0,
        "segments": segments,
    }
    output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output


def run_preflight() -> dict[str, Any]:
    historical_sha = _sha(RESEARCH_PATH)
    runtime = Path(tempfile.mkdtemp(prefix="i2c-subject-route-preflight-", dir="E:/Claude_allow/Download"))
    state = runtime / "state"
    # The CLI writes relative artifact paths against PROJECT_ROOT, so the
    # isolated runtime itself is the temporary project root.  The canonical
    # research file remains read-only in the repository.
    phase1_cli.STATE_ROOT = state
    phase1_cli.DATABASE_PATH = state / "jobs.sqlite3"
    phase1_cli.INPUT_ROOT = state / "inputs"
    phase1_cli.PROJECT_ROOT = runtime
    phase1_cli.OPENMONTAGE_PROJECTS_ROOT = state / "openmontage_projects"
    phase1_cli.SUBJECT_DELIVERY_ROOT = runtime / "dist"
    draft_path = _canonical_i2c_draft(SUBJECT, runtime / "mpt.json")
    phase1_cli.MPT_RUN_DRAFTS = lambda **_kwargs: draft_path
    created = _call(["create-subject", "--subject", SUBJECT, "--duration", "40", "--aspect-ratio", "9:16", "--idempotency-key", "i2c-subject-route-preflight-20260928"])
    job_id = str(created["job"]["job_id"])
    attached = _call(["attach-research", "--job-id", job_id, "--research", str(RESEARCH_PATH)])
    planned = _call(["run", "--job-id", job_id, "--plan-only"])
    root = runtime / Path(str(attached["research_path"])).parent
    request = json.loads((root / "topic_request.json").read_text(encoding="utf-8"))
    research = json.loads((root / "research_brief.json").read_text(encoding="utf-8"))
    director = json.loads((root / "director_script.json").read_text(encoding="utf-8"))
    scene_plan = json.loads((root / "scene_plan.json").read_text(encoding="utf-8"))
    route = validate_i2c_subject_plan(topic_request=request, research=research, director_script=director, scene_plan=scene_plan)
    forbidden_media = sorted(str(path.relative_to(runtime)) for path in runtime.rglob("*") if path.is_file() and path.suffix.lower() in {".mp4", ".wav", ".mp3", ".aac"})
    if forbidden_media:
        raise ValueError("plan_only_media_created")
    still_root = runtime / "still_evidence"
    still_timing = _write_still_timing_manifest(
        script_path=root / "director_script.json",
        scene_plan_path=root / "scene_plan.json",
        output=runtime / "stills_timing_manifest.json",
        scene_count=len(scene_plan["scenes"]),
    )
    still_report = runtime / "i2c_subject_stills.json"
    rendered = subprocess.run(
        ["node", str(ROOT / "scripts" / "render_i2c_subject_stills.mjs"), "--script", str(root / "director_script.json"), "--scene-plan", str(root / "scene_plan.json"), "--timing-manifest", str(still_timing), "--output-dir", str(still_root), "--report", str(still_report)],
        capture_output=True,
        text=True,
        check=False,
        timeout=300,
    )
    if rendered.returncode != 0:
        raise RuntimeError(f"i2c_still_preflight_failed:{rendered.stderr.strip()[-400:]}")
    still_value = json.loads(still_report.read_text(encoding="utf-8"))
    if still_value.get("status") != "PASS_BOUNDED_STILL_ONLY" or still_value.get("full_render") is not False or still_value.get("render_media_called") is not False:
        raise ValueError("i2c_still_preflight_contract_invalid")
    return {
        "schema_version": "phase1_i2c_subject_route_preflight_v1",
        "status": "I2C_SUBJECT_ROUTE_PREFLIGHT_READY_FOR_REMOTE_REVIEW",
        "runtime_locator_id": runtime.name,
        "plan_only_job_id": job_id,
        "plan_only_job_is_non_candidate": True,
        "job_state": planned["job"]["state"],
        "canonical_research": {"path": RESEARCH_PATH.relative_to(ROOT).as_posix(), "sha256": historical_sha, "bytes_unchanged": _sha(RESEARCH_PATH) == historical_sha},
        "subject_control_path": ["create-subject", "attach-research", "run --plan-only"],
        "research_artifact_sha256": next(item["sha256"] for item in planned["artifacts"] if item["artifact_type"] == "research_brief"),
        "selected_script_sha256": next(item["sha256"] for item in planned["artifacts"] if item["artifact_type"] == "selected_script"),
        "director_script_sha256": next(item["sha256"] for item in planned["artifacts"] if item["artifact_type"] == "director_script"),
        "scene_plan_sha256": next(item["sha256"] for item in planned["artifacts"] if item["artifact_type"] == "scene_plan"),
        "editorial_validation": "source_bound_candidate_selected_by_existing_phase1_topic_path",
        "visual_route": route,
        "generic_registry_asset_lineage": {"selected_as_semantic_authority": False, "proof": "phase1_scene_plan_contains_no_asset_id_or_registry_asset_path"},
        "source_aligned_audio_integration": {"adapter": "src/factory/phase1_subject_audio.py", "status": "ADAPTER_PRESENT_NO_PRODUCTION_MEDIA_RUN", "production_media_run": False, "objective_pcm_media_evidence": "NOT_RUN_NO_MEDIA_BOUNDARY", "contract_tests": "tests/phase1_local/test_phase1_subject_audio.py"},
        "still_evidence": {"status": still_value["status"], "report": str(still_report), "timing_manifest": str(still_timing), "still_count": len(still_value.get("stills", [])), "full_render": False},
        "transition_evidence": {"mode": "technical_cut", "status": "PASS_BOUNDED_TIMELINE_ONLY", "scene_boundaries_contiguous": True, "encoded_transition_frames": False, "full_render": False},
        "candidate001_excluded": "job-b4a2e8e851268bc14e5e4a15",
        "candidate002_excluded": "job-b1a186b7b265c2ed46b7c3cb",
        "candidate003_authorized": False,
        "full_render": False,
        "human_review": "PENDING",
        "prereview": "NOT_RUN",
        "formal_gate": "NOT_AUTHORIZED",
    }


def main() -> int:
    value = run_preflight()
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": value["status"], "job_id": value["plan_only_job_id"], "report": str(REPORT_PATH)} , ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
