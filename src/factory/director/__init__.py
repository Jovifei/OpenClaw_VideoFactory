"""Provider-neutral AI Director contracts for the local video factory."""

from .director_contract import Director, Storyboard
from .ai_director import AIDirector, compose_storyboard, stable_storyboard_id
from .context import (
    DirectorContext,
    DirectorContextBuilder,
    MAX_TOPIC_LENGTH,
    PROMPT_VERSION,
    build_director_prompt,
    load_director_context,
    normalize_topic,
)
from .provider import CodexCliDirectorProvider, DirectorProvider

__all__ = [
    "AIDirector",
    "CodexCliDirectorProvider",
    "Director",
    "DirectorContext",
    "DirectorContextBuilder",
    "DirectorProvider",
    "MAX_TOPIC_LENGTH",
    "PROMPT_VERSION",
    "Storyboard",
    "build_director_prompt",
    "compose_storyboard",
    "load_director_context",
    "normalize_topic",
    "stable_storyboard_id",
]
