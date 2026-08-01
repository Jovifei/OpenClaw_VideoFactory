"""Fail-closed production entrypoint with an explicit offline candidate branch."""

from __future__ import annotations

import sys
from pathlib import Path

MESSAGE = """
OpenClaw VideoFactory production pipeline is not implemented yet.
Read START_HERE_CODEX.md, complete P0, then implement P1/P2 according to the backlog.
Do not register production Cron while this message is present.
""".strip()
if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "candidate":
        project_root = str(Path(__file__).resolve().parents[1])
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        from src.factory.cli import main

        raise SystemExit(main(sys.argv[2:]))
    print(MESSAGE, file=sys.stderr)
    raise SystemExit(78)
