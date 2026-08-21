"""Provider-neutral AI Director contracts for the local video factory."""

from .director_contract import Director, Storyboard
from .ai_director import AIDirector, compose_storyboard, stable_storyboard_id
from .context import (
    DirectorContext,
    DirectorContextBuilder,
    MAX_TOPIC_LENGTH,
    PROMPT_VERSION,
    build_director_prompt,
    build_script_prompt,
    load_director_context,
    normalize_topic,
)
from .factual import FactualBrief, load_factual_brief
from .provider import CodexCliDirectorProvider, DirectorProvider
from .script_planner import ScriptPlanner, ScriptResult, score_script, stable_script_id
from .storyboard_assembler import StoryboardAssembler
from .asset_selector import AssetSelectionResult, AssetSelector

__all__ = [
    "AIDirector",
    "AssetSelectionResult",
    "AssetSelector",
    "CodexCliDirectorProvider",
    "Director",
    "DirectorContext",
    "DirectorContextBuilder",
    "DirectorProvider",
    "FactualBrief",
    "MAX_TOPIC_LENGTH",
    "PROMPT_VERSION",
    "ScriptPlanner",
    "ScriptResult",
    "Storyboard",
    "StoryboardAssembler",
    "build_director_prompt",
    "build_script_prompt",
    "compose_storyboard",
    "load_director_context",
    "normalize_topic",
    "load_factual_brief",
    "score_script",
    "stable_storyboard_id",
    "stable_script_id",
]
