"""Fail-closed automation entrypoint with explicit local Phase 1 controls."""

from __future__ import annotations

import sys
from pathlib import Path

MESSAGE = """
Phase 1 local video controls are available through: scripts/factory.py phase1.
Phase 2 OpenClaw/Feishu automation is not implemented or authorized.
Do not register production Cron while this message is present.
""".strip()
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "phase1":
        project_root = str(Path(__file__).resolve().parents[1])
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from src.factory.phase1_cli import main

        raise SystemExit(main(sys.argv[2:]))
    if len(sys.argv) > 1 and sys.argv[1] == "candidate":
        project_root = str(Path(__file__).resolve().parents[1])
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from src.factory.cli import main

        raise SystemExit(main(sys.argv[2:]))
    print(MESSAGE, file=sys.stderr)
    raise SystemExit(78)
