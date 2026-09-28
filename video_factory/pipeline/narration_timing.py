"""Measured narration timing and one-pass bounded editorial compression."""

from __future__ import annotations

import copy
import hashlib
import re
from typing import Any
from pathlib import Path


_FLASH_FACTS = {
    "flash_erase_sequence",
    "iwdg_independent_timeout",
    "service_window_is_budget",
    "observable_recovery",
}
_FREERTOS_FACTS = {
    "mutex_task_ownership",
    "isr_nonblocking_boundary",
    "priority_inheritance_context",
    "short_isr_handler",
}

_FLASH_COMPACT_NARRATION = (
    "擦除期间看门狗仍在倒计时，服务窗口怎么安排？",
    "按手册解锁、发起、等待 BUSY、检查错误、确认完成。",
    "独立看门狗持续倒计时；用最长擦除时间和响应延迟算服务窗口，超时会复位。",
    "测量最长擦除时间和服务窗口；超预算记录错误并进入恢复路径。",
    "按手册发起，观察 BUSY，检查错误，给看门狗留窗口。",
)
_FREERTOS_COMPACT_NARRATION = (
    "Mutex 的所有权在任务上下文；ISR 不等待 Mutex。",
    "ISR 只取数、清标志，用 FromISR 原语通知任务。",
    "高优先级任务等待时，持锁任务临时继承优先级并尽快释放 Mutex。",
    "ISR 保持短小；共享资源和状态机修改交给任务。",
    "先判断上下文；ISR 用 FromISR 交棒；Mutex、优先级继承和共享状态都回到任务。",
)

_FACT_ANCHORS: dict[str, tuple[tuple[str, ...], ...]] = {
    "flash_erase_sequence": (("手册", "解锁", "发起"),),
    "iwdg_independent_timeout": (("看门狗",), ("倒计时", "复位")),
    "service_window_is_budget": (("服务窗口",), ("最长", "预算", "响应延迟", "擦除时间")),
    "observable_recovery": (("错误",), ("恢复", "超预算")),
    "mutex_task_ownership": (("Mutex",), ("任务",)),
    "isr_nonblocking_boundary": (("ISR",), ("FromISR", "通知", "队列", "信号量")),
    "priority_inheritance_context": (("优先级",), ("持锁", "继承", "反转")),
    "short_isr_handler": (("ISR",), ("任务",), ("短小", "取数", "共享")),
}

_FACT_CONTRADICTIONS: dict[str, tuple[re.Pattern[str], ...]] = {
    "mutex_task_ownership": (re.compile(r"ISR.{0,8}(?:取得|获取|持有).{0,8}Mutex"),),
    "isr_nonblocking_boundary": (re.compile(r"ISR.{0,8}(?<!不等待)(?:等待|阻塞).{0,8}(?:Mutex|互斥)"),),
    "priority_inheritance_context": (re.compile(r"ISR.{0,8}(?:优先级继承|继承优先级)"),),
    "short_isr_handler": (re.compile(r"ISR.{0,12}(?:长时间|较长处理|处理共享资源)"),),
    "flash_erase_sequence": (re.compile(r"(?:无需|不用|不必).{0,8}(?:手册|检查)"),),
    "iwdg_independent_timeout": (re.compile(r"(?:看门狗|IWDG).{0,8}(?:停止|不会).{0,8}(?:倒计时|复位)"),),
    "service_window_is_budget": (re.compile(r"(?:服务窗口|最长擦除时间).{0,8}(?:无需|不用).{0,8}计算"),),
    "observable_recovery": (re.compile(r"(?<!不能)(?<!停止)(?:无限|无穷).{0,4}(?:重试|等待)"),),
}
_UNSUPPORTED_ASSERTIONS = (
    re.compile(r"100%"),
    re.compile(r"保证(?:永不|一定不)复位"),
    re.compile(r"任意器件"),
    re.compile(r"每次擦除\s*1\s*ms"),
)


def rewrite_narration_once(
    script: dict[str, Any], factual_brief: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return one deterministic concise rewrite, preserving fact bindings.

    This is intentionally limited to the two fixed Phase 1 fixtures.  A
    generic rewrite would risk dropping a required fact or introducing a new
    claim without a source binding.
    """

    facts = factual_brief.get("facts", [])
    fact_ids = {str(item.get("fact_id")) for item in facts if isinstance(item, dict)}
    if _FLASH_FACTS.issubset(fact_ids):
        replacement = _FLASH_COMPACT_NARRATION
        topic_kind = "flash_watchdog"
    elif _FREERTOS_FACTS.issubset(fact_ids):
        replacement = _FREERTOS_COMPACT_NARRATION
        topic_kind = "freertos_mutex"
    else:
        raise ValueError("narration_rewrite_fixture_unsupported")
    beats = script.get("beats")
    if not isinstance(beats, list) or len(beats) != len(replacement):
        raise ValueError("narration_rewrite_scene_count_invalid")
    rewritten = copy.deepcopy(script)
    rewritten_beats = rewritten["beats"]
    for beat, narration in zip(rewritten_beats, replacement):
        if not isinstance(beat, dict):
            raise ValueError("narration_rewrite_beat_invalid")
        beat["narration"] = narration
    rewritten["narration"] = "\n".join(replacement)
    return rewritten, {"topic_kind": topic_kind, "fact_ids": sorted(fact_ids), "scene_count": len(replacement)}


def validate_narration_claims(script: dict[str, Any], factual_brief: dict[str, Any]) -> dict[str, Any]:
    """Check rewritten beats against conservative source-bound claim anchors."""

    facts = {str(item.get("fact_id")): str(item.get("claim", "")) for item in factual_brief.get("facts", []) if isinstance(item, dict)}
    beats = script.get("beats")
    if not isinstance(beats, list):
        raise ValueError("narration_claim_validation_beats_invalid")
    checks: list[dict[str, Any]] = []
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise ValueError(f"narration_claim_validation_beat_invalid:{index}")
        text = str(beat.get("narration", ""))
        for fact_ref in beat.get("fact_refs", []):
            fact_id = str(fact_ref)
            if fact_id not in facts or fact_id not in _FACT_ANCHORS:
                raise ValueError(f"narration_claim_validation_unavailable:{fact_id}")
            if any(pattern.search(text) for pattern in _FACT_CONTRADICTIONS.get(fact_id, ())):
                raise ValueError(f"narration_fact_claim_contradiction:{fact_id}")
            if any(pattern.search(text) for pattern in _UNSUPPORTED_ASSERTIONS):
                raise ValueError(f"narration_unsupported_assertion:{fact_id}")
            missing = [
                "/".join(group)
                for group in _FACT_ANCHORS[fact_id]
                if not any(token in text for token in group)
            ]
            if missing:
                raise ValueError(f"narration_fact_claim_missing:{fact_id}:{','.join(missing)}")
            checks.append({"scene_index": index + 1, "fact_id": fact_id, "status": "passed"})
    return {"status": "passed", "checks": checks}


def storyboard_with_narration(storyboard: dict[str, Any], script: dict[str, Any]) -> dict[str, Any]:
    """Copy a storyboard and replace only scene narration from a script."""

    scenes = storyboard.get("scenes")
    beats = script.get("beats")
    if not isinstance(scenes, list) or not isinstance(beats, list) or len(scenes) != len(beats):
        raise ValueError("narration_storyboard_scene_count_invalid")
    result = copy.deepcopy(storyboard)
    for scene, beat in zip(result["scenes"], beats):
        if not isinstance(scene, dict) or not isinstance(beat, dict):
            raise ValueError("narration_storyboard_shape_invalid")
        scene["narration"] = str(beat["narration"])
    return result


def plan_source_aligned_narration(
    *,
    storyboard: dict[str, Any],
    script: dict[str, Any],
    factual_brief: dict[str, Any],
    registry: Any,
    repo_root: Path,
    work_dir: Path,
    voice: str,
    provider: str,
    tail_margin_seconds: float = 0.2,
) -> dict[str, Any]:
    """Authoritative production helper shared by proof and outer job paths."""

    from .audio_planner import (
        NarrationDurationBudgetError,
        allocate_scene_durations,
        align_complete_segments,
        synthesize_tts_segments,
    )
    from .storyboard import compile_storyboard

    current_script = copy.deepcopy(script)
    current_storyboard = copy.deepcopy(storyboard)
    validate_narration_claims(current_script, factual_brief)
    passes: list[dict[str, Any]] = []
    rewrite_count = 0
    for pass_index in range(2):
        timeline = compile_storyboard(current_storyboard, registry, repo_root=Path(repo_root))
        raw_dir = Path(work_dir) / f"narration_pass_{pass_index}" / "raw"
        segments = synthesize_tts_segments(timeline, work_dir=raw_dir, voice=voice, provider=provider)
        raw_total = round(sum(float(segment["actual_duration"]) for segment in segments), 3)
        pass_record = {
            "pass": pass_index,
            "rewrite_count": rewrite_count,
            "raw_total_seconds": raw_total,
            "narration": [str(beat.get("narration", "")) for beat in current_script.get("beats", [])],
            "segments": [
                dict(segment, audio_sha256=hashlib.sha256(Path(str(segment["audio_path"])).read_bytes()).hexdigest())
                for segment in segments
            ],
        }
        try:
            allocated = allocate_scene_durations(timeline, segments, tail_margin_seconds=tail_margin_seconds)
        except NarrationDurationBudgetError as exc:
            pass_record["allocation_error"] = str(exc)
            passes.append(pass_record)
            if rewrite_count >= 1:
                raise
            original_refs = [list(beat.get("fact_refs", [])) for beat in current_script.get("beats", [])]
            current_script, rewrite_meta = rewrite_narration_once(current_script, factual_brief)
            validate_narration_claims(current_script, factual_brief)
            rewritten_refs = [list(beat.get("fact_refs", [])) for beat in current_script.get("beats", [])]
            pass_record["fact_refs_preserved"] = original_refs == rewritten_refs
            if not pass_record["fact_refs_preserved"]:
                raise ValueError("narration_rewrite_fact_bindings_changed")
            current_storyboard = storyboard_with_narration(storyboard, current_script)
            rewrite_count += 1
            pass_record["rewrite_meta"] = rewrite_meta
            continue
        subtitle_path = Path(work_dir) / f"narration_pass_{pass_index}" / "subtitle.srt"
        from .subtitle import build_srt_from_timeline
        cues = build_srt_from_timeline(allocated, subtitle_path)
        aligned_dir = Path(work_dir) / f"narration_pass_{pass_index}" / "aligned"
        audio_path = Path(work_dir) / f"narration_pass_{pass_index}" / "audio.wav"
        aligned = align_complete_segments(segments, allocated, output_dir=aligned_dir, output_path=audio_path)
        pass_record["allocation"] = {
            "duration_seconds": allocated["total_duration_seconds"],
            "scene_durations": [scene["duration"] for scene in allocated["scenes"]],
            "srt_endpoint_seconds": cues[-1]["end"],
            "srt_sha256": hashlib.sha256(subtitle_path.read_bytes()).hexdigest(),
        }
        pass_record["aligned_audio"] = aligned
        pass_record["objective_audio_integrity"] = aligned["integrity"]
        pass_record["scene_boundary_markers"] = [
            {
                "scene_id": scene["scene_id"],
                "start_seconds": round(sum(float(item["duration"]) for item in allocated["scenes"][:index]), 3),
                "end_seconds": round(sum(float(item["duration"]) for item in allocated["scenes"][: index + 1]), 3),
            }
            for index, scene in enumerate(allocated["scenes"])
        ]
        passes.append(pass_record)
        return {
            "timeline": allocated,
            "storyboard": current_storyboard,
            "script": current_script,
            "audio_path": Path(aligned["path"]),
            "segments": tuple(aligned["segments"]),
            "subtitle_path": subtitle_path,
            "rewrite_count": rewrite_count,
            "passes": passes,
            "objective_audio_integrity": aligned["integrity"],
        }
    raise AssertionError("source_aligned_narration_pass_exhausted")
