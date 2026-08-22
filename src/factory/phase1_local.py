"""Pure local-brief planning for the first Phase 1 video-factory slice.

This module deliberately does not invoke a provider, a process, or a network
client.  It turns a schema-bound user brief into the existing DirectorScript,
Storyboard, and registry-backed asset-selection contracts.  Rendering remains
the responsibility of the later, explicitly authorised entrypoint.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from src.factory.director.asset_selector import AssetSelector
from src.factory.director.context import load_director_context, normalize_topic
from src.factory.director.factual import FactualBrief
from src.factory.director.script_planner import stable_script_id
from src.factory.director.storyboard_assembler import StoryboardAssembler
from src.factory.reference_video import POLICY_VERSION, brief_digest, stable_reference_job_key


_SCHEMA_NAME = "phase1_local_brief"
_SUPPORTED_EXECUTION_MODES = frozenset({"topic", "local_reference"})
_FORBIDDEN_CONTROL_FIELDS = frozenset({"asset_id", "path", "render", "provider_prompt"})


def _repo_root_from_module() -> Path:
    # phase1_local.py lives at <repo>/src/factory/phase1_local.py.
    return Path(__file__).resolve().parents[2]


def _schema_path() -> Path:
    return _repo_root_from_module() / "schemas" / "video" / f"{_SCHEMA_NAME}.schema.json"


def _brief_error(reason: str, *, field: str = "brief") -> FactoryContractError:
    return FactoryContractError(
        "phase1_local_brief_invalid",
        "Phase 1 local brief is invalid.",
        {"field": field, "reason": reason},
    )


def _load_schema_validator() -> Any:
    """Load the local schema with its factual-brief reference resolved offline."""

    try:
        import jsonschema
        from referencing import Registry, Resource

        schema_file = _schema_path()
        factual_file = schema_file.with_name("director_factual_brief.schema.json")
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        factual_schema = json.loads(factual_file.read_text(encoding="utf-8"))
        registry = Registry()
        factual_resource = Resource.from_contents(factual_schema)
        registry = registry.with_resource(factual_file.resolve().as_uri(), factual_resource)
        registry = registry.with_resource(str(factual_schema["$id"]), factual_resource)
        return jsonschema.Draft202012Validator(schema, registry=registry)
    except (ImportError, OSError, UnicodeError, ValueError, KeyError) as exc:
        raise _brief_error("schema_unavailable", field="schema") from exc


def _validate_local_brief_schema(brief: dict[str, object]) -> None:
    validator = _load_schema_validator()
    errors = sorted(
        validator.iter_errors(brief),
        key=lambda error: (tuple(str(part) for part in error.absolute_path), str(error.validator)),
    )
    if errors:
        error = errors[0]
        field = str(next(iter(error.absolute_path), "brief"))
        raise _brief_error("schema", field=field) from error


def _contains_forbidden_control_field(value: object) -> bool:
    if isinstance(value, dict):
        return any(str(key) in _FORBIDDEN_CONTROL_FIELDS or _contains_forbidden_control_field(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_control_field(item) for item in value)
    return False


def load_local_brief(path: Path) -> dict[str, object]:
    """Read and validate one Phase 1 local brief from a JSON file.

    The supplied path is an explicit local user input.  No reference inside
    the file is dereferenced, so the function cannot expand into filesystem,
    network, provider, or process activity.
    """

    if not isinstance(path, Path):
        raise _brief_error("path_type", field="path")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise _brief_error("read", field="brief") from exc
    if not isinstance(value, dict):
        raise _brief_error("type", field="brief")
    brief: dict[str, object] = dict(value)
    _validate_local_brief_schema(brief)
    if _contains_forbidden_control_field(brief):
        raise _brief_error("forbidden_control_field", field="brief")
    return brief


def _validated_factual_brief(brief: dict[str, object], *, topic: str, topic_digest: str) -> FactualBrief:
    value = brief.get("factual_brief")
    if not isinstance(value, dict):
        raise _brief_error("type", field="factual_brief")
    factual = dict(value)
    # Reuse the canonical factual schema and enforce the same source-link
    # invariants as the Provider path, while keeping the local brief inline.
    validate(factual, "director_factual_brief")
    if factual.get("topic_digest") != topic_digest:
        raise _brief_error("topic_digest_mismatch", field="factual_brief.topic_digest")
    if factual.get("review_status") != "verified":
        raise _brief_error("factual_brief_not_verified", field="factual_brief.review_status")
    sources = factual.get("sources")
    facts = factual.get("facts")
    if not isinstance(sources, list) or not isinstance(facts, list):
        raise _brief_error("type", field="factual_brief")
    source_ids = {str(item.get("source_id")) for item in sources if isinstance(item, dict)}
    if len(source_ids) < 2:
        raise _brief_error("minimum_sources", field="factual_brief.sources")
    for fact in facts:
        if not isinstance(fact, dict) or any(str(source_id) not in source_ids for source_id in fact.get("source_ids", [])):
            raise _brief_error("source_unresolved", field="factual_brief.facts")
    return FactualBrief(document=factual, relative_path="inline")


def _deterministic_script(*, topic: str, topic_digest: str, factual_brief: FactualBrief, duration_target_seconds: int = 40) -> dict[str, object]:
    facts = factual_brief.document.get("facts", [])
    assert isinstance(facts, list) and facts and isinstance(facts[0], dict)
    fact_ids = {str(fact.get("fact_id")) for fact in facts if isinstance(fact, dict)}
    clean_topic = topic.rstrip("。！？；， ")
    clean_claim = str(facts[0]["claim"]).strip().rstrip("。！？；， ")
    flash_watchdog_ids = {
        "flash_erase_sequence",
        "iwdg_independent_timeout",
        "service_window_is_budget",
        "observable_recovery",
    }
    if flash_watchdog_ids.issubset(fact_ids):
        # This fixture is deliberately concrete: its narration must teach the
        # reviewed engineering point instead of falling back to a generic
        # "object/boundary/input-output" template.
        beat_specs = [
            {
                "purpose": "hook",
                "narration": "闪存擦除不是“点一下等结果”：看门狗还在倒计时，服务窗口怎么安排？",
                "subtitle": "擦除时看门狗怎么办？",
                "visual_intent": "用角色提出擦除与看门狗服务窗口的工程问题",
                "pose": "question",
                "required_tags": ["flash_watchdog", "flash_window", "education", "explain"],
                "fact_refs": [],
            },
            {
                "purpose": "explain",
                "narration": "先按芯片手册拆成四拍：解锁并发起、等待忙状态、检查错误、确认完成。每一拍都要有可观察状态。",
                "subtitle": "发起、等待、检查、确认",
                "visual_intent": "展示闪存操作从发起到完成的四个可观察阶段",
                "pose": "thinking",
                "required_tags": ["flash_watchdog", "erase_sequence", "education", "explain", "protocol_frame"],
                "fact_refs": ["flash_erase_sequence"],
            },
            {
                "purpose": "evidence",
                "narration": "独立看门狗用独立低速时钟持续倒计时；擦除时间和服务窗口算错，就可能在操作中触发复位。",
                "subtitle": "服务窗口要算出来",
                "visual_intent": "把独立时钟、倒计时和复位风险放入知识卡片",
                "pose": "measure",
                "required_tags": ["flash_watchdog", "watchdog_budget", "education", "measure"],
                "fact_refs": ["iwdg_independent_timeout", "service_window_is_budget"],
            },
            {
                "purpose": "repair",
                "narration": "工程上先测最长擦除时间，再安排服务窗口；超过预算就记录错误、进入恢复路径，不能无限重试。",
                "subtitle": "超预算就走恢复路径",
                "visual_intent": "展示测量预算、记录错误和明确恢复动作",
                "pose": "repair",
                "required_tags": ["flash_watchdog", "recovery_path", "education", "warning", "repair"],
                "fact_refs": ["observable_recovery", "service_window_is_budget"],
            },
            {
                "purpose": "summary",
                "narration": "记住四件事：按手册发起，观察忙状态，检查错误，给看门狗留出可计算的窗口。",
                "subtitle": "按手册，留窗口，有恢复",
                "visual_intent": "总结闪存操作与看门狗服务窗口的可复用检查表",
                "pose": "success",
                "required_tags": ["flash_watchdog", "checklist", "education", "summary"],
                "fact_refs": [],
            },
        ]
    else:
        fact_id = str(facts[0]["fact_id"])
        beat_specs = [
            {
                "purpose": "hook",
                "narration": f"{clean_topic}最容易误判的地方是什么？先给出一个可观察的问题。",
                "subtitle": "先找出可观察的问题",
                "visual_intent": "用角色提出工程问题并标记边界",
                "pose": "question",
                "required_tags": ["education", "explain"],
                "fact_refs": [],
            },
            {
                "purpose": "explain",
                "narration": "把流程拆成发起、执行、校验和收尾四步，先看状态，再下结论。",
                "subtitle": "发起、执行、校验、收尾",
                "visual_intent": "展示信息在受控边界内流动",
                "pose": "thinking",
                "required_tags": ["education", "explain"],
                "fact_refs": [],
            },
            {
                "purpose": "evidence",
                "narration": f"已核验事实是：{clean_claim}。",
                "subtitle": "先看已核验事实",
                "visual_intent": "把已核验事实放入知识卡片",
                "pose": "measure",
                "required_tags": ["education", "protocol_frame", "measure"],
                "fact_refs": [fact_id],
            },
            {
                "purpose": "repair",
                "narration": "出现异常时，记录触发条件、状态和恢复动作；超出预算就停止重试。",
                "subtitle": "记录条件、状态和恢复",
                "visual_intent": "展示由现象到证据的排错步骤",
                "pose": "repair",
                "required_tags": ["education", "warning", "repair"],
                "fact_refs": [],
            },
            {
                "purpose": "summary",
                "narration": f"记住：按顺序执行，留下可观察证据，才能把{clean_topic}变成可复现的工程步骤。",
                "subtitle": "按顺序，留证据，可复现",
                "visual_intent": "总结可复用的工程说明方法",
                "pose": "success",
                "required_tags": ["education", "summary"],
                "fact_refs": [],
            },
        ]
    beats = [dict(spec) for spec in beat_specs]
    script = {
        "schema_version": "1.0",
        "script_id": stable_script_id(topic),
        "topic_digest": topic_digest,
        "title": topic,
        "hook": str(beats[0]["narration"]),
        "narration": "\n".join(str(beat["narration"]) for beat in beats),
        "duration_target_seconds": duration_target_seconds,
        "style": {
            "language": "zh-CN",
            "tone": "technical_calm_dry_humor",
            "content_scope": "evergreen_embedded_mainline",
        },
        "beats": beats,
    }
    validate(script, "director_script")
    return script


def build_local_plan(
    brief: dict[str, object],
    repo_root: Path,
    *,
    reference_context: dict[str, object] | None = None,
) -> dict[str, object]:
    """Build deterministic Phase 1 planning artifacts for a validated brief.

    ``local_reference`` is executable only when the caller supplies a
    sanitized, analyzer-produced context.  The context contains no path or
    media bytes; the CLI obtains it from the receipt/report bundle and the
    renderer never trusts a user brief alone.
    """

    if not isinstance(brief, dict):
        raise _brief_error("type", field="brief")
    _validate_local_brief_schema(brief)
    if _contains_forbidden_control_field(brief):
        raise _brief_error("forbidden_control_field", field="brief")
    mode = str(brief.get("input_mode", ""))
    if mode not in _SUPPORTED_EXECUTION_MODES:
        raise FactoryContractError(
            "phase1_local_input_mode_unsupported",
            "Phase 1 local brief input mode is not implemented.",
            {"input_mode": mode, "reason": "not_implemented"},
        )
    root = Path(repo_root).resolve()
    topic = normalize_topic(brief.get("topic"))
    topic_digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    if mode == "local_reference":
        if not isinstance(reference_context, dict):
            raise FactoryContractError(
                "phase1_reference_context_required",
                "A verified reference-analysis context is required for local_reference mode.",
                {"reason": "missing"},
            )
        expected_context = {
            "source_sha256": str(brief.get("reference_sha256", "")),
            "policy_version": POLICY_VERSION,
            "analysis_verified": True,
        }
        if any(reference_context.get(key) != value for key, value in expected_context.items()):
            raise FactoryContractError(
                "phase1_reference_context_invalid",
                "Reference-analysis context does not match the original brief.",
                {"reason": "digest_or_policy_mismatch"},
            )
    factual_brief = _validated_factual_brief(brief, topic=topic, topic_digest=topic_digest)
    context = load_director_context(root)
    abstraction = brief.get("reference_abstraction") if mode == "local_reference" else None
    duration_target = int(abstraction.get("duration_target_seconds", 40)) if isinstance(abstraction, dict) else 40
    script = _deterministic_script(
        topic=topic,
        topic_digest=topic_digest,
        factual_brief=factual_brief,
        duration_target_seconds=duration_target,
    )
    storyboard = StoryboardAssembler(repo_root=root, registry=context.registry).from_script(script)
    selection = AssetSelector(repo_root=root, registry=context.registry).select_assets(storyboard, context.registry)
    if mode == "local_reference":
        stable_key = stable_reference_job_key(str(brief["reference_sha256"]), brief)
        job_id = f"phase1_ref_{hashlib.sha256(stable_key.encode('utf-8')).hexdigest()[:24]}"
    else:
        job_id = f"phase1_{topic_digest[:16]}"
    asset_selection = {**selection.report, "job_id": job_id}
    validate(asset_selection, "asset_selection_report")
    return {
        "job_id": job_id,
        "topic": topic,
        "topic_digest": topic_digest,
        "script": script,
        "storyboard": selection.storyboard,
        "asset_selection": asset_selection,
        "factual_brief": factual_brief.document,
        "input_mode": mode,
        "reference_digest": brief_digest(brief) if mode == "local_reference" else None,
    }


__all__ = ["build_local_plan", "load_local_brief"]
