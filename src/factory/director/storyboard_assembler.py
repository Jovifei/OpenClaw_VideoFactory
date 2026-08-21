"""Deterministic DirectorScript to Storyboard assembly."""

from __future__ import annotations

from pathlib import Path

from video_factory.pipeline.composition import load_composition
from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.storyboard import validate_storyboard
from video_factory.pipeline.validation import validate

from src.factory.assets.pink_pig.loader import PinkPigRegistry

from .ai_director import DEFAULT_GLOBALS


class StoryboardAssembler:
    def __init__(self, *, repo_root: Path, registry: PinkPigRegistry) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.registry = registry
        self.composition = load_composition("knowledge_illustration", repo_root=self.repo_root)

    def from_script(self, script: dict[str, object]) -> dict[str, object]:
        validate(script, "director_script")
        beats = script.get("beats")
        if not isinstance(beats, list) or len(beats) < 5:
            raise FactoryContractError("director_script_semantics_invalid", "Director script has too few beats.", {"field": "beats"})
        scenes: list[dict[str, object]] = []
        content_region = self.composition.get("regions", {}).get("content_area")
        for index, beat in enumerate(beats, start=1):
            if not isinstance(beat, dict):
                raise FactoryContractError("director_storyboard_invalid", "Director beat is not an object.", {"path": f"beats.{index - 1}"})
            scenes.append({
                "scene_id": f"s{index:02d}",
                "order": index,
                "narration": str(beat["narration"]).strip(),
                "caption": beat.get("subtitle"),
                "mood": None,
                "pose": str(beat["pose"]),
                "asset_id": None,
                "asset_tags": list(beat.get("required_tags", [])),
                "layout_mode": "knowledge_illustration",
                "subtitle_layout": "knowledge_illustration",
                "character_position": "bottom_right",
                "content_region": content_region,
                "duration_intent": {"mode": "narration"},
                "transition_out": None if index == len(beats) else "fade",
                "director_notes": f"{beat['purpose']}: {beat['visual_intent']}",
            })
        storyboard = {
            "schema_version": "1.0",
            "storyboard_id": f"sb_{str(script['topic_digest'])[:16]}",
            "title": str(script["title"]).strip(),
            "ip": {"character_id": self.registry.character_id, "registry_version": self.registry.registry_version},
            "globals": dict(DEFAULT_GLOBALS),
            "composition": self.composition,
            "scenes": scenes,
        }
        validate(storyboard, "storyboard")
        validate_storyboard(storyboard)
        return storyboard


__all__ = ["StoryboardAssembler"]
