"""T05 test package for the Pink Pig Video Factory Phase 1 productization.

Covers the five test targets of ``handoff_prepared/03_CODEX_EXECUTION_PROMPT.txt``
stage four (asset loading / storyboard / timeline / render / MP4 metadata) and the
six requirements of ``docs/PINK_PIG_PHASE1_ARCHITECTURE.md`` §6 T05.

Run with::

    <envs/default python> -m pytest tests/video -v

The suite must be executed with the repository root as the current working
directory: ``video_factory/pipeline/validation.py`` resolves ``schemas/video/*``
through CWD-relative paths (see the delivery report, deviation D5).
"""

from __future__ import annotations

import sys
from pathlib import Path

# tests/video/__init__.py -> tests/video -> tests -> <repo root>
ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

__all__ = ["ROOT"]
