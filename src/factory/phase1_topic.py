"""Deterministic Phase 1 subject research and script-planning contracts."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline import validation

SCHEMA_VERSION = "1.0"
OPENMONTAGE_COMMIT = "cd9b905d41c2e1ddfbb730323e57481e9a36bfe6"
OPENMONTAGE_VERSION = "0.4.0"
MPT_COMMIT = "eb8c23757e098a07bbcd93b3b50e252fc8d1869a"
MPT_VERSION = "1.3.5"
POLICY_VERSION = "phase1-topic-policy-v1"
_FORBIDDEN = {"path", "frame", "audio", "transcript", "logo", "provider", "render", "publish", "asset_id", "asset_ids", "temperature", "top_p", "model", "endpoint_host"}
_PRIMARY_KINDS = {"official_document", "standard", "research_paper", "primary_source"}


def _error(reason: str, **context: Any) -> FactoryContractError:
    return FactoryContractError("phase1_topic_contract_invalid", f"Phase 1 topic planning contract is invalid: {reason}.", {"reason": reason, **context})


def _normalized(value: str) -> str:
    result = " ".join(str(value).split())
    if not result:
        raise _error("empty_text")
    return result


def _reject_controls(value: Any, path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            token = str(key).lower()
            if token in _FORBIDDEN or token.endswith("_path") or token.endswith("_id") and token.startswith("asset"):
                raise _error("forbidden_control", path=f"{path}.{key}")
            _reject_controls(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_controls(child, f"{path}[{index}]")


def _validate_new(document: dict[str, Any], schema_name: str) -> None:
    if not validation.is_available():
        raise _error("schema_validation_unavailable", schema=schema_name)
    validation.validate(document, schema_name)


def build_topic_request(*, subject: str, duration: int = 40, aspect: str = "16:9", language: str = "zh-CN", mascot: str = "off") -> dict[str, Any]:
    document = {"schema_version": SCHEMA_VERSION, "subject": _normalized(subject), "duration": duration, "aspect": aspect, "language": language, "mascot": mascot}
    try:
        _validate_new(document, "phase1_topic_request")
    except FactoryContractError:
        raise
    except Exception as exc:
        raise _error("request_schema") from exc
    return document


def stable_subject_key(request: Mapping[str, Any]) -> str:
    canonical = {"topic": _normalized(str(request["subject"])).casefold(), "duration": int(request["duration"]), "aspect": str(request["aspect"]), "mascot": str(request["mascot"]), "policy_version": POLICY_VERSION, "openmontage_commit": OPENMONTAGE_COMMIT, "mpt_commit": MPT_COMMIT}
    digest = hashlib.sha256(json.dumps(canonical, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    return f"phase1-subject:{OPENMONTAGE_COMMIT}:{MPT_COMMIT}:{digest}"


def build_research_brief(*, topic: str, sources: list[dict[str, Any]], facts: list[dict[str, Any]], comparables: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    document = {"schema_version": SCHEMA_VERSION, "topic": _normalized(topic), "topic_digest": hashlib.sha256(_normalized(topic).casefold().encode("utf-8")).hexdigest(), "sources": sources, "facts": facts, "comparables": comparables or []}
    _reject_controls(document.get("comparables", []))
    ids = [str(item.get("id", "")) for item in sources]
    urls = [str(item.get("url", "")) for item in sources]
    if len(set(ids)) != len(ids) or len(set(urls)) != len(urls):
        raise _error("duplicate_source")
    if not any(item.get("kind") in _PRIMARY_KINDS for item in sources):
        raise _error("primary_source_required")
    known = set(ids)
    if any(not set(map(str, fact.get("source_ids", []))) or not set(map(str, fact.get("source_ids", []))).issubset(known) for fact in facts):
        raise _error("fact_source_invalid")
    try:
        _validate_new(document, "phase1_research_brief")
    except FactoryContractError:
        raise
    except Exception as exc:
        raise _error("research_schema") from exc
    return document


def _load(value: Path | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(value, Path):
        loaded = json.loads(value.read_text(encoding="utf-8"))
    else:
        loaded = dict(value)
    if not isinstance(loaded, dict):
        raise _error("object_required")
    return loaded


def ingest_mpt_candidates(value: Path | Mapping[str, Any]) -> dict[str, Any]:
    source = _load(value)
    _reject_controls(source)
    # Adapter metadata is accepted at ingress, then deliberately omitted from
    # the canonical candidates contract so downstream stages cannot inherit
    # provider/runtime controls.
    allowed = {"schema_version", "kind", "review_status", "subject", "language", "paragraphs", "requested_candidates", "successful_candidates", "mpt_version", "mpt_commit", "generated_at", "candidates", "failures"}
    if set(source) - allowed:
        raise _error("raw_provider_controls", fields=sorted(set(source) - allowed))
    if source.get("mpt_commit") != MPT_COMMIT or source.get("mpt_version") != MPT_VERSION:
        raise _error("mpt_pin_mismatch")
    candidates = source.get("candidates")
    if source.get("successful_candidates") != 3 or not isinstance(candidates, list) or len(candidates) != 3 or source.get("failures"):
        raise _error("exactly_three_successes_required")
    if {int(item.get("candidate", -1)) for item in candidates} != {1, 2, 3}:
        raise _error("candidate_ids_invalid")
    document = {"schema_version": SCHEMA_VERSION, "mpt_version": MPT_VERSION, "mpt_commit": MPT_COMMIT, "candidates": [{"candidate": int(item["candidate"]), "script": _normalized(str(item["script"]))} for item in candidates]}
    _reject_controls(document)
    try:
        _validate_new(document, "phase1_script_candidates")
    except FactoryContractError:
        raise
    except Exception as exc:
        raise _error("candidate_schema") from exc
    return document


def _score(script: str, research: Mapping[str, Any]) -> dict[str, int]:
    compact = re.sub(r"\s+", "", script)
    claims = [str(f["id"]) for f in research["facts"]]
    factual = min(100, 70 + 15 * sum(ref in script for ref in claims))
    dimensions = {"factual_consistency": factual, "hook": 90 if any(x in script for x in ("故障", "为什么", "？")) else 65, "clarity": 90 if len(compact) >= 18 else 55, "duration": 90 if 18 <= len(compact) <= 800 else 55, "visualizability": 90 if any(x in script for x in ("原理", "配置", "验证", "时间")) else 60, "originality": 88 if len(set(compact)) >= 12 else 55, "account_fit": 92 if any(x in script for x in ("看门狗", "工程", "配置", "芯片")) else 60}
    dimensions["total"] = round(sum(dimensions.values()) / 7)
    return dimensions


def select_candidate(candidates: Mapping[str, Any], research: Mapping[str, Any], *, rewrite_attempt: int = 0) -> dict[str, Any]:
    if rewrite_attempt not in (0, 1):
        raise _error("rewrite_attempt_invalid")
    scored = [(int(item["candidate"]), str(item["script"]), _score(str(item["script"]), research)) for item in candidates["candidates"]]
    index, script, scores = sorted(scored, key=lambda item: (-item[2]["total"], item[0]))[0]
    if scores["total"] < 85:
        failed = sorted(name for name, score in scores.items() if name != "total" and score < 85)
        raise _error("selection_threshold_not_met", rewrite_attempt=rewrite_attempt, best_score=scores["total"], best_candidate=index, failed_dimensions=failed)
    document = {"schema_version": SCHEMA_VERSION, "selected_candidate": index, "script": script, "score_breakdown": scores, "rewrite_attempt": rewrite_attempt}
    _validate_new(document, "phase1_selected_script")
    return document


def build_director_script(request: Mapping[str, Any], research: Mapping[str, Any], selected: Mapping[str, Any]) -> dict[str, Any]:
    refs = [str(f["id"]) for f in research["facts"]]
    purposes = ["hook", "problem", "principle", "verification", "summary"]
    narrations = [f"{request['subject']}出故障时，第一步不是重启，而是确认失去响应的证据。", f"先界定故障现象与触发边界：{research['facts'][0]['claim']}", f"再拆解工作原理：{research['facts'][min(1, len(refs)-1)]['claim']}", "配置后用时间轴和故障注入验证超时、恢复与边界条件。", "最后把现象、原理、配置和验证闭环，留下可复查的工程结论。"]
    beats = [{"purpose": purpose, "narration": text, "subtitle": text[:80], "visual_intent": f"用{purpose}信息图表达当前知识点", "pose": "normal", "required_tags": ["technical"], "fact_refs": refs} for purpose, text in zip(purposes, narrations)]
    digest = str(research["topic_digest"])
    script = {"schema_version": SCHEMA_VERSION, "script_id": f"script_{hashlib.sha256((selected['script']+digest).encode('utf-8')).hexdigest()[:16]}", "topic_digest": digest, "title": str(request["subject"]), "hook": narrations[0], "narration": "".join(narrations), "duration_target_seconds": int(request["duration"]), "style": {"language": "zh-CN", "tone": "technical_calm_dry_humor", "content_scope": "evergreen_embedded_mainline"}, "beats": beats}
    validation.validate(script, "director_script")
    return script


def build_scene_plan(script: Mapping[str, Any], research: Mapping[str, Any]) -> dict[str, Any]:
    visual_types = ["kinetic_typography", "system_diagram", "timeline", "comparison_card", "checklist"]
    scenes = []
    for index, beat in enumerate(script["beats"], 1):
        visual = visual_types[(index - 1) % len(visual_types)]
        scenes.append({"scene_index": index, "scene_type": str(beat["purpose"]), "narration": str(beat["narration"]), "on_screen_knowledge": str(beat["subtitle"]), "information_role": "explain_verified_fact", "narrative_role": str(beat["purpose"]), "shot_intent": str(beat["visual_intent"]), "visual_type": visual, "motion": "progressive_reveal", "transition": "cut", "fallback_visual": "accessible_text_card", "source_refs": list(beat["fact_refs"])})
    plan = {"schema_version": SCHEMA_VERSION, "script_id": script["script_id"], "scenes": scenes}
    _validate_new(plan, "phase1_scene_plan")
    return plan


__all__ = ["MPT_COMMIT", "MPT_VERSION", "OPENMONTAGE_COMMIT", "OPENMONTAGE_VERSION", "build_director_script", "build_research_brief", "build_scene_plan", "build_topic_request", "ingest_mpt_candidates", "select_candidate", "stable_subject_key"]
