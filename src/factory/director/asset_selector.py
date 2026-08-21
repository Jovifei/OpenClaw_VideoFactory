"""Deterministic Registry-backed asset selection for Director Storyboards."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from src.factory.assets.pink_pig.loader import PinkPigAsset, PinkPigRegistry


@dataclass(frozen=True, slots=True)
class AssetSelectionResult:
    storyboard: dict[str, object]
    report: dict[str, object]


def _score(asset: PinkPigAsset, *, requested_tags: set[str], pose: str, purpose: str, used: set[str]) -> tuple[int, int, int, int, str]:
    tags = set(asset.tags)
    tag_score = len(tags & requested_tags) * 100
    purpose_tag = {"hook": "explain", "summary": "summary", "warning": "warning", "repair": "repair", "measure": "measure"}.get(purpose)
    purpose_score = 30 if purpose_tag and purpose_tag in tags else 0
    pose_score = 20 if asset.pose == pose else 0
    repeat_penalty = -1000 if asset.asset_id in used else 0
    knowledge_score = 15 if "knowledge_illustration" in tags else 0
    return (tag_score + purpose_score + pose_score + repeat_penalty + knowledge_score, purpose_score, pose_score, knowledge_score, asset.asset_id)


class AssetSelector:
    def __init__(self, *, repo_root: Path, registry: PinkPigRegistry) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.registry = registry

    def select_assets(self, storyboard: dict[str, object], registry: PinkPigRegistry | None = None) -> AssetSelectionResult:
        active_registry = registry or self.registry
        resolved = dict(storyboard)
        selections: list[dict[str, object]] = []
        used: set[str] = set()
        scenes = resolved.get("scenes", [])
        if not isinstance(scenes, list):
            raise FactoryContractError("director_asset_selection_invalid", "Storyboard scenes are invalid for asset selection.", {"field": "scenes"})
        candidates = [asset for asset in active_registry.render_ready_assets() if asset.path and "signature" not in asset.tags]
        for index, scene in enumerate(scenes):
            if not isinstance(scene, dict):
                raise FactoryContractError("director_asset_selection_invalid", "Storyboard scene is not an object.", {"path": f"scenes.{index}"})
            if scene.get("asset_id") is not None:
                raise FactoryContractError("director_asset_selection_invalid", "Director asset IDs must be injected by Python.", {"path": f"scenes.{index}.asset_id", "reason": "provider_override"})
            requested_tags = {str(value) for value in scene.get("asset_tags", [])}
            purpose = str(scene.get("director_notes", "")).split(":", 1)[0]
            pose = str(scene.get("pose", "normal"))
            ranked = sorted(candidates, key=lambda asset: _score(asset, requested_tags=requested_tags, pose=pose, purpose=purpose, used=used), reverse=True)
            if not ranked:
                raise FactoryContractError("director_asset_unresolved", "No render-ready Registry asset is available.", {"path": f"scenes.{index}.asset_id"})
            asset = ranked[0]
            if asset.asset_id in used and len(ranked) > 1:
                asset = ranked[1]
            used.add(asset.asset_id)
            scene["asset_id"] = asset.asset_id
            selections.append(self._selection(scene, asset))
        report = {"schema_version": "1.0", "job_id": "pending", "storyboard_id": str(resolved.get("storyboard_id", "")), "selections": selections}
        validate(report, "asset_selection_report")
        return AssetSelectionResult(resolved, report)

    def _selection(self, scene: dict[str, object], asset: PinkPigAsset) -> dict[str, object]:
        try:
            digest = hashlib.sha256((self.repo_root / str(asset.path)).read_bytes()).hexdigest() if asset.path else ""
        except OSError as exc:
            raise FactoryContractError("director_asset_unresolved", "Selected Registry asset cannot be read.", {"scene_order": scene.get("order"), "reason": "read"}) from exc
        return {
            "scene_id": str(scene.get("scene_id", "")),
            "asset_id": asset.asset_id,
            "tags": list(asset.tags),
            "relative_path": str(asset.path),
            "sha256": digest,
            "source_type": "deterministic_diagram" if "knowledge_illustration" in asset.tags else "repository_owned",
            "rights_basis": "repository-owned registry asset",
            "classification": "factual" if "knowledge_illustration" in asset.tags else "decorative",
            "fallback_used": False,
            "crop": "contain",
            "transformation": "fit content region",
        }


__all__ = ["AssetSelectionResult", "AssetSelector"]
