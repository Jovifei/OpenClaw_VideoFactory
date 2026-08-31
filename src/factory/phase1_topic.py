"""Deterministic Phase 1 subject research and script-planning contracts."""

from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import urlparse
from pathlib import Path
from typing import Any, Mapping

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline import validation

SCHEMA_VERSION = "1.0"
OPENMONTAGE_COMMIT = "cd9f3c1f03368be87b140af494914b8ee4e3c7a4"
OPENMONTAGE_VERSION = "0.4.0"
MPT_COMMIT = "eb8c23757e098a07bbcd93b3b50e252fc8d1869a"
MPT_VERSION = "1.3.5"
POLICY_VERSION = "phase1-topic-policy-v1"
_FORBIDDEN = {"path", "frame", "audio", "transcript", "logo", "provider", "render", "publish", "asset_id", "asset_ids", "temperature", "top_p", "model", "endpoint_host"}
_PRIMARY_KINDS = {"official_document", "standard", "research_paper", "primary_source"}
# Conservative, unqualified planning estimate only. The measured SAMI timing
# gate remains authoritative for every real candidate.
CHINESE_TTS_CHARS_PER_SECOND = 4.7
MIN_NARRATION_COVERAGE = 0.8
_SAFE_FRAME_CHARACTERS = set("先再把这条结论写清核对日志记录边界现场逐项观察检查确认复核回到过程结果证据清单问题重点步骤接下来然后最后并且是否对应不提前替它下不补充额外原因方便下一次复查：，。！？；")
_SAFE_PROCESS_FRAMES = (
    ("scope_boundary", "先界定检查范围与边界，只讨论已核验的现象、条件和结果。"),
    ("causal_path", "再沿因果路径核对触发、执行和反馈，记录每一步的观察。"),
    ("measurement_evidence", "把测量证据放到同一时间线，保留采样点、阈值和原始日志。"),
    ("normal_fault_comparison", "将正常与故障路径并列比较，标出分叉位置和不同观察。"),
    ("recovery", "发现异常后按既定恢复步骤处理，再次测量确认恢复结果，不把恢复动作当作原因验证，并保存复测条件和过程记录。"),
    ("source_bound_conclusion", "最后回到来源绑定的结论，只陈述已有证据支持的内容，并标出仍需核验的边界，避免越界推断和重复表述。"),
)


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
    fact_ids = [str(item.get("id", "")) for item in facts]
    if len(set(fact_ids)) != len(fact_ids):
        raise _error("duplicate_fact")
    for url in urls + [str(item.get("url", "")) for item in document["comparables"]]:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            raise _error("url_invalid", url=url)
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


_CONTRADICTION_MARKERS = ("不是", "并非", "无需", "不需要", "错误", "装饰", "只是关键词", "相反")


def _longest_common_contiguous(left: str, right: str) -> int:
    previous = [0] * (len(right) + 1)
    best = 0
    for left_char in left:
        current = [0]
        for index, right_char in enumerate(right, 1):
            value = previous[index - 1] + 1 if left_char == right_char else 0
            current.append(value)
            best = max(best, value)
        previous = current
    return best


def _claim_matches(script: str, claim: str) -> bool:
    # Conservative by design: any contradiction marker makes the prose
    # ineligible for factual binding. Uncertainty must produce no fact_refs.
    if any(marker in script for marker in _CONTRADICTION_MARKERS):
        return False
    left = re.sub(r"[^\w\u4e00-\u9fff]", "", script).casefold()
    right = re.sub(r"[^\w\u4e00-\u9fff]", "", claim).casefold()
    if not right:
        return False
    return right in left or _longest_common_contiguous(left, right) / len(right) >= 0.8


def _grounded_chinese_characters(script: str, research: Mapping[str, Any]) -> int:
    return sum(len(re.findall(r"[\u4e00-\u9fff]", sentence)) for sentence in _sentences(script)
               if any(_claim_matches(sentence, str(fact["claim"])) for fact in research["facts"]))


def _score(script: str, research: Mapping[str, Any], *, duration_target_seconds: int | None = None) -> dict[str, int]:
    compact = re.sub(r"\s+", "", script)
    factual = min(100, 40 + 30 * sum(_claim_matches(script, str(f["claim"])) for f in research["facts"]))
    grounded_chars = _grounded_chinese_characters(script, research)
    required_grounded_chars = max(12, round((duration_target_seconds or 25) * CHINESE_TTS_CHARS_PER_SECOND * 0.12))
    duration_ok = grounded_chars >= required_grounded_chars if re.search(r"[\u4e00-\u9fff]", script) else 18 <= len(compact) <= 800
    dimensions = {"factual_consistency": factual, "hook": 90 if any(x in script for x in ("故障", "为什么", "？")) else 65, "clarity": 90 if len(compact) >= 18 else 55, "duration": 90 if duration_ok else 55, "visualizability": 90 if any(x in script for x in ("原理", "配置", "验证", "时间")) else 60, "originality": 88 if len(set(compact)) >= 12 else 55, "account_fit": 92 if any(x in script for x in ("看门狗", "工程", "配置", "芯片")) else 60}
    dimensions["total"] = round(sum(dimensions.values()) / 7)
    return dimensions


def select_candidate(candidates: Mapping[str, Any], research: Mapping[str, Any], *, rewrite_attempt: int = 0,
                     duration_target_seconds: int | None = None) -> dict[str, Any]:
    if rewrite_attempt not in (0, 1):
        raise _error("rewrite_attempt_invalid")
    scored = [(int(item["candidate"]), str(item["script"]), _score(str(item["script"]), research, duration_target_seconds=duration_target_seconds)) for item in candidates["candidates"]]
    index, script, scores = sorted(scored, key=lambda item: (-item[2]["total"], item[0]))[0]
    if scores["total"] < 85:
        failed = sorted(name for name, score in scores.items() if name != "total" and score < 85)
        guidance = None
        if "duration" in failed:
            required = max(12, round((duration_target_seconds or 25) * CHINESE_TTS_CHARS_PER_SECOND * 0.12))
            guidance = f"补足至少{required}个已核验 claim 锚点字符；只能围绕已核验 claim 写观察、核对和记录步骤。"
        raise _error("selection_threshold_not_met", rewrite_attempt=rewrite_attempt, best_score=scores["total"], best_candidate=index, failed_dimensions=failed, duration_guidance=guidance)
    document = {"schema_version": SCHEMA_VERSION, "selected_candidate": index, "script": script, "score_breakdown": scores, "rewrite_attempt": rewrite_attempt}
    _validate_new(document, "phase1_selected_script")
    return document


def _sentences(prose: str) -> list[str]:
    return [value.strip() for value in re.split(r"(?<=[。！？!?；;])", prose) if value.strip()]


def estimate_narration_duration_seconds(narration: str) -> float:
    """Deterministically estimate local Chinese TTS duration from Han characters."""
    return len(re.findall(r"[\u4e00-\u9fff]", narration)) / CHINESE_TTS_CHARS_PER_SECOND


def _safe_selected_frame(prose: str, fact: Mapping[str, Any]) -> str:
    claim = str(fact["claim"])
    for sentence in _sentences(prose):
        if not _claim_matches(sentence, claim):
            continue
        frame = sentence.replace(claim, "").strip(" ：，。！？；")
        if frame and len(frame) <= 18 and set(frame).issubset(_SAFE_FRAME_CHARACTERS):
            return f"{frame}："
    return ""


def _normalized_narration_frame(text: str) -> str:
    return re.sub(r"[\s\W_]+", "", text).casefold()


def _new_beat(*, purpose: str, narration: str, fact_refs: list[str]) -> dict[str, Any]:
    return {
        "purpose": purpose,
        "narration": narration,
        "subtitle": narration[:80],
        "visual_intent": f"用{purpose}信息图表达当前知识点",
        "pose": "normal",
        "required_tags": ["technical"],
        "fact_refs": fact_refs,
    }


def build_director_script(request: Mapping[str, Any], research: Mapping[str, Any], selected: Mapping[str, Any]) -> dict[str, Any]:
    prose = _normalized(str(selected["script"]))
    facts = list(research["facts"])
    if not facts:
        raise _error("facts_required")
    target_seconds = int(request["duration"])
    minimum_chars = round(target_seconds * CHINESE_TTS_CHARS_PER_SECOND * MIN_NARRATION_COVERAGE)
    hook_fact = next((fact for sentence in _sentences(prose) for fact in facts
                      if _claim_matches(sentence, str(fact["claim"]))), None)
    selected_frame = _safe_selected_frame(prose, hook_fact) if hook_fact is not None else ""
    hook = f"{request['subject']}排查时，{selected_frame}先把问题范围、证据边界和检查顺序放在同一张图上。"
    beats = [_new_beat(purpose="hook", narration=hook, fact_refs=[])]
    for fact in facts:
        beats.append(_new_beat(purpose="explain_verified_fact", narration=str(fact["claim"]), fact_refs=[str(fact["id"])]))
    if len(beats) > 9:
        raise _error("narration_beat_limit_exceeded", beat_count=len(beats))
    used_frames = {_normalized_narration_frame(beat["narration"]) for beat in beats}
    if len(used_frames) != len(beats):
        raise _error("narration_frame_duplicate", purpose="verified_claim")
    for purpose, frame in _SAFE_PROCESS_FRAMES:
        narration = "".join(str(beat["narration"]) for beat in beats)
        if len(beats) >= 5 and len(re.findall(r"[\u4e00-\u9fff]", narration)) >= minimum_chars:
            break
        normalized = _normalized_narration_frame(frame)
        if not normalized or normalized in used_frames:
            raise _error("narration_frame_duplicate", purpose=purpose)
        if len(beats) >= 9:
            break
        beats.append(_new_beat(purpose=purpose, narration=frame, fact_refs=[]))
        used_frames.add(normalized)
    narration = "".join(str(beat["narration"]) for beat in beats)
    estimate = estimate_narration_duration_seconds(narration)
    if not target_seconds * MIN_NARRATION_COVERAGE <= estimate <= target_seconds:
        raise _error("narration_budget_unreachable", estimated_seconds=estimate, target_seconds=target_seconds,
                     available_process_frames=len(_SAFE_PROCESS_FRAMES))
    digest = str(research["topic_digest"])
    script = {"schema_version": SCHEMA_VERSION, "script_id": f"script_{hashlib.sha256((prose+digest).encode('utf-8')).hexdigest()[:16]}", "topic_digest": digest, "title": str(request["subject"]), "hook": hook, "narration": narration, "duration_target_seconds": int(request["duration"]), "style": {"language": "zh-CN", "tone": "technical_calm_dry_humor", "content_scope": "evergreen_embedded_mainline"}, "beats": beats}
    validation.validate(script, "director_script")
    return script


def build_scene_plan(script: Mapping[str, Any], research: Mapping[str, Any]) -> dict[str, Any]:
    visual_types = ["kinetic_typography", "system_diagram", "timeline", "comparison_card", "checklist"]
    scenes = []
    for index, beat in enumerate(script["beats"], 1):
        visual = visual_types[(index - 1) % len(visual_types)]
        information_role = ("hook_question" if beat["purpose"] == "hook" else
                            "explain_verified_fact" if beat["fact_refs"] else "engineering_process_frame")
        scenes.append({"scene_index": index, "scene_type": str(beat["purpose"]), "narration": str(beat["narration"]), "on_screen_knowledge": str(beat["subtitle"]), "information_role": information_role, "narrative_role": str(beat["purpose"]), "shot_intent": str(beat["visual_intent"]), "visual_type": visual, "motion": "progressive_reveal", "transition": "cut", "fallback_visual": "accessible_text_card", "source_refs": list(beat["fact_refs"])})
    plan = {"schema_version": SCHEMA_VERSION, "script_id": script["script_id"], "scenes": scenes}
    _validate_new(plan, "phase1_scene_plan")
    return plan


__all__ = ["MPT_COMMIT", "MPT_VERSION", "OPENMONTAGE_COMMIT", "OPENMONTAGE_VERSION", "build_director_script", "build_research_brief", "build_scene_plan", "build_topic_request", "ingest_mpt_candidates", "select_candidate", "stable_subject_key"]
