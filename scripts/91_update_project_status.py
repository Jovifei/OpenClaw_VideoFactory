from __future__ import annotations
import argparse, json
from datetime import datetime
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
STATUS = ROOT / "PROJECT_STATUS.yaml"
GATES = ROOT / "reports" / "gates"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--phase", required=True, choices=["P0", "P1", "P2", "P3", "P4", "P5", "PRODUCTION"]
    )
    ap.add_argument("--commit", required=True)
    a = ap.parse_args()
    name = "PRODUCTION_READY.json" if a.phase == "PRODUCTION" else a.phase + "_READY.json"
    m = GATES / name
    if not m.exists():
        print(f"Missing {m}")
        return 2
    payload = json.loads(m.read_text(encoding="utf-8"))
    if payload.get("passed") is not True:
        print("Gate not passed")
        return 2
    s = yaml.safe_load(STATUS.read_text(encoding="utf-8"))
    if a.phase != "PRODUCTION":
        s["phases"][a.phase]["status"] = "passed"
        s["phases"][a.phase]["evidence"] = [str(m.relative_to(ROOT)), a.commit]
        order = ["P0", "P1", "P2", "P3", "P4", "P5"]
        i = order.index(a.phase)
        if i + 1 < len(order):
            s["phases"][order[i + 1]]["status"] = "not_started"
            s["current_phase"] = order[i + 1]
    else:
        s["status"] = "production_ready"
        s["current_phase"] = "PRODUCTION"
    s["last_updated"] = datetime.now().astimezone().isoformat(timespec="seconds")
    STATUS.write_text(yaml.safe_dump(s, allow_unicode=True, sort_keys=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
