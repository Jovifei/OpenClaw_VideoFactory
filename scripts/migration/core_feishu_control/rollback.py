"""Document-only rollback guard for the 033 maintenance window.

Production stop/restore is deliberately not implemented here. The script
checks that the approved rollback plan exists and refuses ``--execute``.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback-plan", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.execute:
        print(json.dumps({"status": "BLOCKED", "reason": "PRODUCTION_EXECUTION_DISABLED_033"}))
        return 2
    result = {
        "status": "PASS" if args.rollback_plan.is_file() else "FAIL",
        "execution": "NOT_APPLIED",
        "rollback_plan_present": args.rollback_plan.is_file(),
        "actions": [
            "stop_project_gateway",
            "restore_core_feishu_binding",
            "verify_text_attachment_session",
        ],
    }
    print(json.dumps(result, ensure_ascii=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
