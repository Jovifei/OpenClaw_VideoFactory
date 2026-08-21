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


_SCHEMA_NAME = "phase1_local_brief"
_SUPPORTED_EXECUTION_MODE = "topic"
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


def _deterministic_script(*, topic: str, topic_digest: str, factual_brief: FactualBrief) -> dict[str, object]:
    facts = factual_brief.document.get("facts", [])
    assert isinstance(facts, list) and facts and isinstance(facts[0], dict)
    fact_id = str(facts[0]["fact_id"])
    claim = str(facts[0]["claim"]).strip()
    beats = [
        {
            "purpose": "hook",
            "narration": f"{topic}到底在解决什么工程问题？先把任务拆成可观察、可验证的几个部分。",
            "subtitle": "先拆成可验证的问题",
            "visual_intent": "用角色提出工程问题并标记边界",
            "pose": "question",
            "required_tags": ["education", "explain"],
            "fact_refs": [],
        },
        {
            "purpose": "explain",
            "narration": "先明确对象、边界和输入输出，再按顺序组织信息，避免把猜测当成结论。",
            "subtitle": "对象、边界、输入输出",
            "visual_intent": "展示信息在受控边界内流动",
            "pose": "thinking",
            "required_tags": ["education", "explain"],
            "fact_refs": [],
        },
        {
            "purpose": "evidence",
            "narration": f"关键事实是：{claim}。它来自已核验资料，而不是临场猜测。",
            "subtitle": "先看已核验事实",
            "visual_intent": "把已核验事实放入知识卡片",
            "pose": "measure",
            "required_tags": ["education", "protocol_frame", "measure"],
            "fact_refs": [fact_id],
        },
        {
            "purpose": "repair",
            "narration": "遇到异常时，按现象、条件和证据逐项排查，保留能够复现的工程记录。",
            "subtitle": "按证据逐项排查",
            "visual_intent": "展示由现象到证据的排错步骤",
            "pose": "repair",
            "required_tags": ["education", "warning", "repair"],
            "fact_refs": [],
        },
        {
            "purpose": "summary",
            "narration": f"回顾一下：从问题到事实再到排错路径，{topic}就能变成可执行的工程说明。",
            "subtitle": "问题、事实、排错路径",
            "visual_intent": "总结可复用的工程说明方法",
            "pose": "success",
            "required_tags": ["education", "summary"],
            "fact_refs": [],
        },
    ]
    script = {
        "schema_version": "1.0",
        "script_id": stable_script_id(topic),
        "topic_digest": topic_digest,
        "title": topic,
        "hook": str(beats[0]["narration"]),
        "narration": "\n".join(str(beat["narration"]) for beat in beats),
        "duration_target_seconds": 40,
        "style": {
            "language": "zh-CN",
            "tone": "technical_calm_dry_humor",
            "content_scope": "evergreen_embedded_mainline",
        },
        "beats": beats,
    }
    validate(script, "director_script")
    return script


def build_local_plan(brief: dict[str, object], repo_root: Path) -> dict[str, object]:
    """Build deterministic Phase 1 planning artifacts for a validated brief.

    Only the direct ``topic`` mode is executable in this initial slice.
    ``local_reference`` and ``authorized_public_research`` remain valid input
    contracts, but deliberately fail closed until their separate analysers are
    implemented and explicitly authorised.
    """

    if not isinstance(brief, dict):
        raise _brief_error("type", field="brief")
    _validate_local_brief_schema(brief)
    if _contains_forbidden_control_field(brief):
        raise _brief_error("forbidden_control_field", field="brief")
    mode = str(brief.get("input_mode", ""))
    if mode != _SUPPORTED_EXECUTION_MODE:
        raise FactoryContractError(
            "phase1_local_input_mode_unsupported",
            "Phase 1 local brief input mode is not implemented.",
            {"input_mode": mode, "reason": "not_implemented"},
        )
    root = Path(repo_root).resolve()
    topic = normalize_topic(brief.get("topic"))
    topic_digest = hashlib.sha256(topic.encode("utf-8")).hexdigest()
    factual_brief = _validated_factual_brief(brief, topic=topic, topic_digest=topic_digest)
    context = load_director_context(root)
    script = _deterministic_script(topic=topic, topic_digest=topic_digest, factual_brief=factual_brief)
    storyboard = StoryboardAssembler(repo_root=root, registry=context.registry).from_script(script)
    selection = AssetSelector(repo_root=root, registry=context.registry).select_assets(storyboard, context.registry)
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
    }


__all__ = ["build_local_plan", "load_local_brief"]
