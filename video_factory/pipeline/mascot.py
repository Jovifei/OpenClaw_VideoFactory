"""Runtime Pink Pig skill/profile gate with an explicit mode switch."""

from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import FactoryContractError

ALLOWED_MASCOT_MODES = {"required", "optional", "off"}
DEFAULT_SKILL_REF = "skills/pink-pig-mascot-director/SKILL.md"
DEFAULT_STYLE_PROFILE_REF = "src/factory/assets/pink_pig/style_profile.json"


def _safe_repo_path(repo_root: Path, reference: str, field: str) -> Path:
    if not isinstance(reference, str) or not reference or "\\" in reference:
        raise FactoryContractError("mascot_config_invalid", "Mascot reference must be a relative POSIX path.", {"field": field})
    pure = PurePosixPath(reference)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise FactoryContractError("mascot_config_invalid", "Mascot reference contains an unsafe path.", {"field": field})
    candidate = (repo_root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise FactoryContractError("mascot_config_invalid", "Mascot reference escapes the repository.", {"field": field}) from exc
    return candidate


def load_mascot_contract(repo_root: Path, config: dict[str, Any] | None = None) -> dict[str, object]:
    """Load the Pink Pig skill when mode is required/optional.

    ``off`` is an explicit escape hatch for non-IP videos. Knowledge videos
    set ``required`` and fail closed if the skill or style profile is missing.
    """

    if config is not None and not isinstance(config, dict):
        raise FactoryContractError("mascot_config_invalid", "Mascot configuration must be an object.", {"field": "mascot"})
    values = dict(config or {})
    mode = str(values.get("mode", "off"))
    if mode not in ALLOWED_MASCOT_MODES:
        raise FactoryContractError("mascot_config_invalid", "Mascot mode is unsupported.", {"field": "mode"})
    if mode == "off":
        return {"mode": "off", "skill_loaded": False}
    skill_ref = str(values.get("skill_ref", DEFAULT_SKILL_REF))
    profile_ref = str(values.get("style_profile_ref", DEFAULT_STYLE_PROFILE_REF))
    try:
        skill_path = _safe_repo_path(repo_root, skill_ref, "skill_ref")
        profile_path = _safe_repo_path(repo_root, profile_ref, "style_profile_ref")
        skill_text = skill_path.read_text(encoding="utf-8")
        profile = json.loads(profile_path.read_text(encoding="utf-8"))
        if not skill_text.strip() or not isinstance(profile, dict):
            raise ValueError("empty_or_invalid")
        required_sections = {"brand_identity", "character_rules", "color_rules", "pose_rules", "forbidden_rules", "quality_checks"}
        if not required_sections.issubset(profile):
            raise ValueError("style_profile_sections_missing")
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        if mode == "optional":
            return {"mode": "optional", "skill_loaded": False, "fallback": "skill_unavailable"}
        raise FactoryContractError(
            "mascot_skill_unavailable",
            "Pink Pig mascot skill or style profile is unavailable.",
            {"field": "skill_ref", "reason": "load"},
        ) from exc
    return {
        "mode": mode,
        "skill_loaded": True,
        "skill_ref": skill_ref,
        "style_profile_ref": profile_ref,
        "style_profile_version": str(profile.get("schema_version", "unknown")),
    }


__all__ = ["ALLOWED_MASCOT_MODES", "load_mascot_contract"]
