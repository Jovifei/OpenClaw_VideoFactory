"""Paths and fixed policy for the offline candidate only."""

from __future__ import annotations

import os
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def state_root() -> Path:
    return Path(os.environ.get("P1_CANDIDATE_STATE_ROOT", PROJECT_ROOT / "state" / "p1_candidate"))


def jobs_root() -> Path:
    return Path(os.environ.get("P1_CANDIDATE_JOBS_ROOT", PROJECT_ROOT / "jobs" / "p1_candidate"))


def database_path() -> Path:
    return state_root() / "factory_candidate.sqlite3"
