"""Measured narration timing and one-pass bounded editorial compression."""

from __future__ import annotations

import copy
from typing import Any


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
    "测量最长时间；超预算记录错误并进入恢复路径。",
    "按手册发起，观察 BUSY，检查错误，给看门狗留窗口。",
)
_FREERTOS_COMPACT_NARRATION = (
    "Mutex 的所有权在任务上下文；ISR 不等待 Mutex。",
    "ISR 只取数、清标志，用 FromISR 原语通知任务。",
    "高优先级任务等待时，持锁任务临时继承优先级并尽快释放 Mutex。",
    "ISR 保持短小；共享资源和状态机修改交给任务。",
    "先判断上下文；ISR 交棒，Mutex 和共享状态留在任务。",
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
