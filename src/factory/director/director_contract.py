"""Phase 2 Director interface only; no model or orchestration implementation."""

from __future__ import annotations

from typing import TypeAlias

Storyboard: TypeAlias = dict[str, object]


class Director:
    """Interface boundary for a future topic-to-storyboard director."""

    def create_storyboard(self, topic: str) -> Storyboard:
        """Create a schema-shaped storyboard for *topic* in a future phase."""
        raise NotImplementedError("director_not_implemented")
