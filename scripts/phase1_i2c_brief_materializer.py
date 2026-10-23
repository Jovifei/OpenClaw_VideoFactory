"""Materialize an executable I2C local brief from preserved research evidence.

This is an evidence-bound conversion helper.  It never edits the historical
research brief and computes the executable factual digest with the same
normalized-topic rule used by ``build_local_plan``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from src.factory.director.context import normalize_topic
from src.factory.phase1_local import load_local_brief


_PUBLISHERS = {
    "nxp_um10204": "NXP Semiconductors",
    "ti_slva689": "Texas Instruments",
}


def execution_topic_digest(topic: str) -> str:
    normalized = normalize_topic(topic)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _source_kind(value: str) -> str:
    if value == "standard":
        return "standard"
    return "official_document"


def materialize_local_brief(research_path: Path, output_path: Path) -> dict[str, Any]:
    historical = json.loads(research_path.read_text(encoding="utf-8"))
    topic = normalize_topic(str(historical["topic"]))
    digest = execution_topic_digest(topic)
    sources = []
    for source in historical["sources"]:
        source_id = str(source["id"])
        sources.append({
            "source_id": source_id,
            "title": str(source["title"]),
            "publisher": _PUBLISHERS.get(source_id, "Source-bound technical publisher"),
            "url": str(source["url"]),
            "kind": _source_kind(str(source["kind"])),
            "published_date": None,
        })
    facts = [
        {
            "fact_id": str(fact["id"]),
            "claim": str(fact["claim"]),
            "source_ids": [str(source_id) for source_id in fact["source_ids"]],
        }
        for fact in historical["facts"]
    ]
    brief = {
        "schema_version": "1.0",
        "input_mode": "topic",
        "topic": topic,
        "title": topic,
        "mascot_mode": "off",
        "aspect_ratio": "9:16",
        "factual_brief": {
            "schema_version": "1.0",
            "topic_digest": digest,
            "review_status": "verified",
            "facts": facts,
            "sources": sources,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(brief, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    load_local_brief(output_path)
    return {
        "topic": topic,
        "execution_topic_digest": digest,
        "output_path": output_path.as_posix(),
        "fact_ids": [item["fact_id"] for item in facts],
        "source_ids": [item["source_id"] for item in sources],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--research", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(materialize_local_brief(args.research, args.output), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
