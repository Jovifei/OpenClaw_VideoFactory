"""Registry-backed Pink Pig quality and asset gates for knowledge videos."""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .composition import validate_composition
from .errors import FactoryContractError


REQUIRED_STYLE_SECTIONS = {
    "brand_identity",
    "character_rules",
    "color_rules",
    "pose_rules",
    "forbidden_rules",
    "quality_checks",
}
DEFAULT_SIGNATURE_ASSET_ID = "pink_pig.signature.v1"


def _fail(code: str, message: str, **context: Any) -> FactoryContractError:
    allowed = {"field", "path", "scene_order", "asset_id", "expected", "actual", "reason", "mode"}
    return FactoryContractError(code, message, {k: v for k, v in context.items() if k in allowed})


def _asset_map(registry: Any) -> Mapping[str, Any]:
    assets = getattr(registry, "assets", None)
    if assets is None and isinstance(registry, Mapping):
        assets = registry.get("assets")
    if not isinstance(assets, Mapping):
        if isinstance(assets, list):
            return {str(item.get("asset_id")): item for item in assets if isinstance(item, Mapping) and item.get("asset_id")}
        raise _fail("asset_registry_invalid", "Pink Pig registry assets are unavailable.", field="assets")
    return assets


def _asset(registry: Any, asset_id: str) -> Any:
    assets = _asset_map(registry)
    try:
        return assets[asset_id]
    except (KeyError, TypeError) as exc:
        raise _fail("pink_pig_asset_unregistered", "Timeline references an unregistered Pink Pig asset.", asset_id=asset_id) from exc


def _asset_value(asset: Any, key: str, default: Any = None) -> Any:
    if isinstance(asset, Mapping):
        return asset.get(key, default)
    return getattr(asset, key, default)


def _registry_value(registry: Any, key: str, default: Any = None) -> Any:
    if isinstance(registry, Mapping):
        if key == "character_id" and key not in registry:
            character = registry.get("character")
            if isinstance(character, Mapping):
                return character.get("character_id", default)
        return registry.get(key, default)
    return getattr(registry, key, default)


def _validate_style_profile(registry: Any) -> tuple[Any, str]:
    profile = _registry_value(registry, "style_profile")
    if profile is None:
        raise _fail("pink_pig_style_missing", "Pink Pig style profile is missing.", field="style_profile")
    if isinstance(profile, Mapping):
        missing = REQUIRED_STYLE_SECTIONS - set(profile)
        character_id = profile.get("brand_identity", {}).get("character_id") if isinstance(profile.get("brand_identity"), Mapping) else None
    else:
        missing = REQUIRED_STYLE_SECTIONS - {name for name in REQUIRED_STYLE_SECTIONS if hasattr(profile, name)}
        brand = getattr(profile, "brand_identity", {})
        character_id = brand.get("character_id") if isinstance(brand, Mapping) else None
    if missing:
        raise _fail("pink_pig_style_missing", "Pink Pig style profile is incomplete.", field=sorted(missing)[0])
    registry_character = str(_registry_value(registry, "character_id", ""))
    if registry_character != "pink_pig" or (character_id is not None and str(character_id) != registry_character):
        raise _fail("pink_pig_character_mismatch", "Pink Pig registry/style profile character mismatch.", field="character_id", expected="pink_pig", actual=registry_character)
    return profile, registry_character


def _safe_asset_path(path: Any, root: Path) -> Path:
    if not isinstance(path, str) or not path or "\\" in path:
        raise _fail("pink_pig_asset_unregistered", "Pink Pig asset path must be a repository-relative POSIX path.", field="asset.path")
    pure = PurePosixPath(path)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts) or Path(path).drive:
        raise _fail("pink_pig_asset_unregistered", "Pink Pig asset path is unsafe.", field="asset.path")
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise _fail("pink_pig_asset_unregistered", "Pink Pig asset path escapes the repository.", field="asset.path") from exc
    return candidate


def validate_pink_pig_quality(
    *,
    storyboard: Mapping[str, Any],
    timeline: Mapping[str, Any],
    registry: Any,
    composition: Mapping[str, Any] | None = None,
    mascot_contract: Mapping[str, Any] | None = None,
    repo_root: Path | None = None,
) -> dict[str, object]:
    """Fail-closed Registry/style/character/asset checks and safe evidence."""

    if not isinstance(storyboard, Mapping) or not isinstance(timeline, Mapping):
        raise _fail("pink_pig_quality_invalid", "Storyboard and timeline must be objects.", field="storyboard/timeline")
    root = Path(repo_root).resolve() if repo_root is not None else Path.cwd().resolve()
    profile, character_id = _validate_style_profile(registry)
    ip = storyboard.get("ip")
    if not isinstance(ip, Mapping) or ip.get("character_id") != character_id:
        raise _fail("pink_pig_character_mismatch", "Storyboard character does not match the Pink Pig registry.", field="storyboard.ip.character_id", expected=character_id, actual=ip.get("character_id") if isinstance(ip, Mapping) else None)
    registry_version = _registry_value(registry, "registry_version")
    if ip.get("registry_version") != registry_version:
        raise _fail("pink_pig_character_mismatch", "Storyboard registry version does not match the Pink Pig registry.", field="storyboard.ip.registry_version", expected=registry_version, actual=ip.get("registry_version"))
    if composition is not None:
        composition = validate_composition(composition)
    if mascot_contract is not None:
        mode = mascot_contract.get("mode")
        if mode == "required" and mascot_contract.get("skill_loaded") is not True:
            raise _fail("pink_pig_style_missing", "Required Pink Pig mascot skill is unavailable.", field="mascot_contract", mode=str(mode))
    scenes = timeline.get("scenes")
    if not isinstance(scenes, list) or not scenes:
        raise _fail("pink_pig_quality_invalid", "Timeline has no scenes to gate.", field="timeline.scenes")
    storyboard_scenes = storyboard.get("scenes", [])
    if not isinstance(storyboard_scenes, list) or len(storyboard_scenes) != len(scenes):
        raise _fail("pink_pig_quality_invalid", "Storyboard and timeline scene counts differ.", field="scenes")
    character_rules = profile.get("character_rules", {}) if isinstance(profile, Mapping) else getattr(profile, "character_rules", {})
    if isinstance(character_rules, Mapping) and character_rules.get("core_action_required") is True:
        for index, scene in enumerate(storyboard_scenes, start=1):
            if not isinstance(scene, Mapping) or not str(scene.get("director_notes", "")).strip():
                raise _fail("pink_pig_character_action_missing", "Pink Pig scene does not declare a core engineering action.", scene_order=index, field="storyboard.scenes.director_notes")
    asset_ids: list[str] = []
    for index, scene in enumerate(scenes, start=1):
        if not isinstance(scene, Mapping) or not isinstance(scene.get("asset_id"), str):
            raise _fail("pink_pig_asset_unregistered", "Timeline scene has no resolved Pink Pig asset.", scene_order=index)
        asset_id = str(scene["asset_id"])
        asset = _asset(registry, asset_id)
        if _asset_value(asset, "render_ready") is not True or not _asset_value(asset, "path"):
            raise _fail("pink_pig_asset_unregistered", "Timeline references a non-renderable Pink Pig asset.", scene_order=index, asset_id=asset_id)
        path = _safe_asset_path(_asset_value(asset, "path"), root)
        if not path.is_file():
            raise _fail("pink_pig_asset_unregistered", "Pink Pig asset file is missing.", scene_order=index, asset_id=asset_id)
        image_path = scene.get("image_path")
        if image_path is not None and str(image_path) != str(_asset_value(asset, "path")):
            raise _fail("pink_pig_asset_unregistered", "Timeline image path does not match the Registry.", scene_order=index, asset_id=asset_id)
        asset_ids.append(asset_id)
    signature_asset_id = DEFAULT_SIGNATURE_ASSET_ID
    if isinstance(composition, Mapping) and isinstance(composition.get("signature"), Mapping):
        signature_asset_id = str(composition["signature"].get("asset_id", signature_asset_id))
    signature_asset = _asset(registry, signature_asset_id)
    if _asset_value(signature_asset, "render_ready") is not True or not _asset_value(signature_asset, "path"):
        raise _fail("pink_pig_style_missing", "Pink Pig signature asset is not renderable.", field="signature.asset_id", asset_id=signature_asset_id)
    _safe_asset_path(_asset_value(signature_asset, "path"), root)
    profile_version = profile.get("schema_version", "unknown") if isinstance(profile, Mapping) else getattr(profile, "schema_version", "unknown")
    return {
        "status": "pass",
        "character_id": character_id,
        "registry_version": str(registry_version),
        "style_profile_version": str(profile_version),
        "signature_asset_id": signature_asset_id,
        "asset_ids": asset_ids,
        "asset_count": len(asset_ids),
        "mascot_mode": mascot_contract.get("mode") if isinstance(mascot_contract, Mapping) else None,
    }


__all__ = ["DEFAULT_SIGNATURE_ASSET_ID", "validate_pink_pig_quality"]
