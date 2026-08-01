"""Generate V2.8 data-contract JSON Schemas under schemas/video_workflow/.

Zero-dependency (stdlib json). Each schema has: $id, version, required, enum
where relevant, timestamp/source/confidence/provenance/status, and a
backward_compatibility note. timeline_manifest is the single timeline source.

Run: python scripts/generate_v28_schemas.py
"""

import json
from pathlib import Path

OUT = Path(r"E:\project\OpenClaw_VideoFactory\schemas\video_workflow")
OUT.mkdir(parents=True, exist_ok=True)
SCHEMA_BASE = "https://openclaw-videofactory.local/schemas/video_workflow"


def common(meta_fields=None):
    """Common provenance fields appended to every schema."""
    base = {
        "schema_version": {"type": "string", "const": "1.0"},
        "source": {
            "type": "object",
            "required": ["kind", "id"],
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": [
                        "openclaw_skill",
                        "provider_adapter",
                        "human",
                        "platform",
                        "synthetic_fixture",
                    ],
                },
                "id": {"type": "string"},
                "version": {"type": "string"},
            },
        },
        "provenance": {
            "type": "object",
            "properties": {
                "created_at": {"type": "string", "format": "date-time"},
                "created_by": {"type": "string"},
                "tool": {"type": "string"},
            },
        },
        "status": {
            "type": "string",
            "enum": ["draft", "active", "rejected", "superseded", "deprecated"],
        },
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "validation_errors": {"type": "array", "items": {"type": "string"}, "default": []},
    }
    if meta_fields:
        base.update(meta_fields)
    return base


def write(name, schema):
    p = OUT / f"{name}.schema.json"
    p.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


# 1. topic_candidate
write(
    "topic_candidate",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/topic_candidate.schema.json",
        "title": "Topic Candidate",
        "type": "object",
        "required": [
            "topic_id",
            "title",
            "summary",
            "source",
            "provenance",
            "status",
            "freshness",
            "schema_version",
        ],
        "properties": {
            "topic_id": {"type": "string"},
            "title": {"type": "string", "minLength": 4, "maxLength": 120},
            "summary": {"type": "string", "maxLength": 500},
            "category": {"type": "string"},
            "signals": {"type": "array", "items": {"type": "string"}},
            "freshness": {
                "type": "object",
                "required": ["observed_at", "expires_at"],
                "properties": {
                    "observed_at": {"type": "string", "format": "date-time"},
                    "expires_at": {"type": "string", "format": "date-time"},
                    "decay": {"type": "string", "enum": ["fast", "medium", "slow"]},
                },
            },
            "dedup_key": {"type": "string"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 2. topic_evidence
write(
    "topic_evidence",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/topic_evidence.schema.json",
        "title": "Topic Evidence",
        "type": "object",
        "required": [
            "evidence_id",
            "topic_id",
            "claim",
            "sources",
            "confidence",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "evidence_id": {"type": "string"},
            "topic_id": {"type": "string"},
            "claim": {"type": "string"},
            "sources": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["url", "retrieved_at"],
                    "properties": {
                        "url": {"type": "string"},
                        "retrieved_at": {"type": "string", "format": "date-time"},
                        "publisher": {"type": "string"},
                        "license": {"type": "string"},
                    },
                },
            },
            "conflict_with": {"type": "array", "items": {"type": "string"}},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 3. comment_signal
write(
    "comment_signal",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/comment_signal.schema.json",
        "title": "Comment Signal",
        "type": "object",
        "required": [
            "signal_id",
            "platform",
            "cluster_label",
            "representative_text",
            "count",
            "sentiment",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "signal_id": {"type": "string"},
            "platform": {
                "type": "string",
                "enum": ["douyin", "xiaohongshu", "kuaishou", "bilibili", "weibo", "synthetic"],
            },
            "cluster_label": {"type": "string"},
            "representative_text": {"type": "string", "maxLength": 280},
            "count": {"type": "integer", "minimum": 1},
            "sentiment": {
                "type": "string",
                "enum": ["positive", "neutral", "negative", "mixed", "hostile"],
            },
            "is_hostile": {"type": "boolean", "default": False},
            "prompt_injection_safe": {
                "type": "boolean",
                "default": True,
                "description": "hostile comments must never become model instructions",
            },
            **common(),
        },
        "additionalProperties": False,
    },
)

# 4. topic_scorecard
write(
    "topic_scorecard",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/topic_scorecard.schema.json",
        "title": "Topic Scorecard (explainable)",
        "type": "object",
        "required": [
            "topic_id",
            "dimensions",
            "decision",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "topic_id": {"type": "string"},
            "dimensions": {
                "type": "object",
                "required": [
                    "audience_pain",
                    "novelty",
                    "evidence_strength",
                    "account_fit",
                    "visual_potential",
                    "production_cost",
                    "competition",
                    "comment_potential",
                    "copyright_risk",
                    "platform_risk",
                    "freshness",
                    "confidence",
                ],
                "properties": {
                    d: {
                        "type": "object",
                        "required": ["score", "weight", "reason"],
                        "properties": {
                            "score": {"type": "number", "minimum": 0, "maximum": 10},
                            "weight": {"type": "number", "minimum": 0, "maximum": 1},
                            "reason": {"type": "string"},
                            "uncertainty": {"type": "number", "minimum": 0, "maximum": 1},
                            "data_time": {"type": "string", "format": "date-time"},
                        },
                    }
                    for d in [
                        "audience_pain",
                        "novelty",
                        "evidence_strength",
                        "account_fit",
                        "visual_potential",
                        "production_cost",
                        "competition",
                        "comment_potential",
                        "copyright_risk",
                        "platform_risk",
                        "freshness",
                        "confidence",
                    ]
                },
            },
            "decision": {
                "type": "string",
                "enum": ["auto_shortlist", "manual_review", "hard_reject"],
            },
            "reject_reason": {"type": "string"},
            "duplicate_of": {"type": "string"},
            "source_conflict": {"type": "boolean"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 5. research_brief
write(
    "research_brief",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/research_brief.schema.json",
        "title": "Research Brief",
        "type": "object",
        "required": [
            "brief_id",
            "topic_id",
            "evidence_ids",
            "angle",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "brief_id": {"type": "string"},
            "topic_id": {"type": "string"},
            "evidence_ids": {"type": "array", "minItems": 2, "items": {"type": "string"}},
            "angle": {"type": "string"},
            "key_facts": {"type": "array", "items": {"type": "string"}},
            "target_audience": {"type": "string"},
            "style_profile_version": {"type": "string"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 6. hook_candidates
write(
    "hook_candidates",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/hook_candidates.schema.json",
        "title": "Hook Candidates",
        "type": "object",
        "required": ["brief_id", "candidates", "source", "provenance", "status", "schema_version"],
        "properties": {
            "brief_id": {"type": "string"},
            "candidates": {
                "type": "array",
                "minItems": 3,
                "items": {
                    "type": "object",
                    "required": ["hook_id", "text", "type"],
                    "properties": {
                        "hook_id": {"type": "string"},
                        "text": {"type": "string", "maxLength": 60},
                        "type": {
                            "type": "string",
                            "enum": ["question", "stat", "story", "contrarian", "promise", "scene"],
                        },
                        "review_pass": {"type": "boolean"},
                        "review_reason": {"type": "string"},
                    },
                },
            },
            "style_profile_version": {"type": "string"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 7. script_package
write(
    "script_package",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/script_package.schema.json",
        "title": "Script Package",
        "type": "object",
        "required": [
            "script_id",
            "brief_id",
            "hook_id",
            "title",
            "body",
            "structure_ratios",
            "stages",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "script_id": {"type": "string"},
            "brief_id": {"type": "string"},
            "hook_id": {"type": "string"},
            "title": {"type": "string"},
            "body": {"type": "string"},
            "structure_ratios": {
                "type": "object",
                "properties": {
                    "hook": {"type": "number"},
                    "develop": {"type": "number"},
                    "tech": {"type": "number"},
                    "cta": {"type": "number"},
                },
            },
            "fact_refs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "each fact points to evidence_id",
            },
            "stages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["stage", "status", "diff"],
                    "properties": {
                        "stage": {
                            "type": "string",
                            "enum": [
                                "hook_gen",
                                "hook_review",
                                "script_write",
                                "fact_review",
                                "humanize",
                                "risk_review",
                                "platform_adapt",
                                "final_approve",
                            ],
                        },
                        "status": {"type": "string", "enum": ["pending", "passed", "rejected"]},
                        "diff": {"type": "string"},
                        "reviewer": {"type": "string"},
                    },
                },
            },
            "human_approved": {"type": "boolean"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 8. risk_review
write(
    "risk_review",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/risk_review.schema.json",
        "title": "Risk Review",
        "type": "object",
        "required": [
            "review_id",
            "script_id",
            "copyright_risk",
            "platform_risk",
            "safety_risk",
            "decision",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "review_id": {"type": "string"},
            "script_id": {"type": "string"},
            "copyright_risk": {"type": "string", "enum": ["none", "low", "medium", "high"]},
            "platform_risk": {"type": "string", "enum": ["none", "low", "medium", "high"]},
            "safety_risk": {"type": "string", "enum": ["none", "low", "medium", "high"]},
            "silent_deletion": {
                "type": "boolean",
                "default": False,
                "description": "risk review must NOT silently delete core viewpoints",
            },
            "decision": {"type": "string", "enum": ["pass", "reject", "revise"]},
            "reason": {"type": "string"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 9. timeline_manifest (THE single timeline source)
write(
    "timeline_manifest",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/timeline_manifest.schema.json",
        "title": "Timeline Manifest (single timeline source)",
        "type": "object",
        "required": [
            "timeline_id",
            "script_id",
            "duration_seconds",
            "fps",
            "tracks",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "timeline_id": {"type": "string"},
            "script_id": {"type": "string"},
            "duration_seconds": {"type": "number", "minimum": 0},
            "fps": {"type": "number", "minimum": 1},
            "tracks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["track_id", "kind", "segments"],
                    "properties": {
                        "track_id": {"type": "string"},
                        "kind": {
                            "type": "string",
                            "enum": [
                                "audio",
                                "subtitle",
                                "visual",
                                "animation",
                                "transition",
                                "bgm",
                                "sfx",
                                "character_action",
                            ],
                        },
                        "segments": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["start", "end"],
                                "properties": {
                                    "start": {"type": "number", "minimum": 0},
                                    "end": {"type": "number", "minimum": 0},
                                    "label": {"type": "string"},
                                    "asset_ref": {"type": "string"},
                                    "text": {"type": "string"},
                                },
                            },
                        },
                    },
                },
            },
            "renderer": {"type": "string", "enum": ["remotion", "hyperframes", "ffmpeg"]},
            "overlap_allowed": {"type": "boolean", "default": False},
            **common(),
        },
        "additionalProperties": False,
        "description": "Single source of truth for audio/subtitle/visual/animation/transition/BGM/SFX/character-action timing. Consumed by Remotion/HyperFrames/FFmpeg. Subtitles are derived (last), not driving.",
    },
)

# 10. asset_manifest
write(
    "asset_manifest",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/asset_manifest.schema.json",
        "title": "Asset Manifest",
        "type": "object",
        "required": [
            "manifest_id",
            "timeline_id",
            "assets",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "manifest_id": {"type": "string"},
            "timeline_id": {"type": "string"},
            "assets": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["asset_id", "kind", "path", "sha256"],
                    "properties": {
                        "asset_id": {"type": "string"},
                        "kind": {
                            "type": "string",
                            "enum": [
                                "image",
                                "clip",
                                "mascot_frame",
                                "audio",
                                "bgm",
                                "sfx",
                                "font",
                            ],
                        },
                        "path": {"type": "string"},
                        "sha256": {"type": "string"},
                        "license": {"type": "string"},
                        "referenced_by_track": {"type": "string"},
                    },
                },
            },
            "unreferenced_rejected": {"type": "boolean", "default": True},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 11. edit_decision_list
write(
    "edit_decision_list",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/edit_decision_list.schema.json",
        "title": "Edit Decision List (rough cut)",
        "type": "object",
        "required": [
            "edl_id",
            "timeline_id",
            "cuts",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "edl_id": {"type": "string"},
            "timeline_id": {"type": "string"},
            "cuts": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["kind", "start", "end", "reason"],
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": ["filler", "pause", "retake", "silence", "noise"],
                        },
                        "start": {"type": "number"},
                        "end": {"type": "number"},
                        "reason": {"type": "string"},
                        "confidence": {"type": "number"},
                    },
                },
            },
            "pause_threshold_seconds": {"type": "number", "default": 0.5},
            "packed_transcript_path": {"type": "string"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 12. style_profile
write(
    "style_profile",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/style_profile.schema.json",
        "title": "Style Profile",
        "type": "object",
        "required": [
            "profile_id",
            "version",
            "brand",
            "narrative",
            "motion",
            "caption",
            "audio",
            "character",
            "platform_profiles",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "profile_id": {"type": "string"},
            "version": {"type": "string", "description": "versioned; changes record reason"},
            "change_reason": {"type": "string"},
            "brand": {"type": "object"},
            "narrative": {"type": "object"},
            "motion": {"type": "object"},
            "caption": {"type": "object"},
            "audio": {"type": "object"},
            "character": {"type": "object"},
            "platform_profiles": {"type": "object"},
            "anti_homogenization": {
                "type": "object",
                "properties": {"variants": {"type": "array", "items": {"type": "string"}}},
            },
            **common(),
        },
        "additionalProperties": False,
    },
)

# 13. quality_report
write(
    "quality_report",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/quality_report.schema.json",
        "title": "Quality Report",
        "type": "object",
        "required": [
            "report_id",
            "job_id",
            "checks",
            "decision",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "report_id": {"type": "string"},
            "job_id": {"type": "string"},
            "checks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["name", "passed"],
                    "properties": {
                        "name": {
                            "type": "string",
                            "enum": [
                                "resolution",
                                "fps",
                                "audio_level",
                                "subtitle_sync",
                                "copyright",
                                "brand_compliance",
                                "structure_ratio",
                                "hook_first_2s",
                            ],
                        },
                        "passed": {"type": "boolean"},
                        "detail": {"type": "string"},
                    },
                },
            },
            "decision": {"type": "string", "enum": ["pass", "fail", "human_review"]},
            "self_review_pass": {"type": "integer", "minimum": 0, "maximum": 3},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 14. publish_result
write(
    "publish_result",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/publish_result.schema.json",
        "title": "Publish Result",
        "type": "object",
        "required": [
            "publish_id",
            "job_id",
            "platform",
            "published_at",
            "human_approved",
            "metrics",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "publish_id": {"type": "string"},
            "job_id": {"type": "string"},
            "platform": {"type": "string"},
            "published_at": {"type": "string", "format": "date-time"},
            "human_approved": {"type": "boolean", "description": "HUMAN ONLY; no auto-publish"},
            "metrics": {
                "type": "object",
                "properties": {
                    "plays": {"type": "integer"},
                    "completion_rate": {"type": "number"},
                    "avg_watch_seconds": {"type": "number"},
                    "likes": {"type": "integer"},
                    "favorites": {"type": "integer"},
                    "comments": {"type": "integer"},
                    "shares": {"type": "integer"},
                    "follows": {"type": "integer"},
                    "negative_feedback": {"type": "integer"},
                },
            },
            "production_cost_usd": {"type": "number"},
            "human_edit_minutes": {"type": "number"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 15. postmortem
write(
    "postmortem",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/postmortem.schema.json",
        "title": "Postmortem (immutable)",
        "type": "object",
        "required": [
            "postmortem_id",
            "publish_id",
            "successful_patterns",
            "failed_patterns",
            "failure_class",
            "new_topic_signals",
            "style_adjustments",
            "skill_update_candidates",
            "sample_size",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "postmortem_id": {"type": "string"},
            "publish_id": {"type": "string"},
            "successful_patterns": {"type": "array", "items": {"type": "string"}},
            "failed_patterns": {"type": "array", "items": {"type": "string"}},
            "failure_class": {
                "type": "string",
                "enum": ["hook", "title", "ai_flavor", "pacing", "copyright", "other"],
            },
            "new_topic_signals": {"type": "array", "items": {"type": "string"}},
            "style_adjustments": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "dimension": {"type": "string"},
                        "change": {"type": "string"},
                        "evidence_count": {"type": "integer"},
                    },
                },
            },
            "skill_update_candidates": {"type": "array", "items": {"type": "string"}},
            "sample_size": {
                "type": "integer",
                "description": "low sample => no global rule change (anti-overfitting)",
            },
            "immutable": {"type": "boolean", "const": True},
            **common(),
        },
        "additionalProperties": False,
    },
)

# 16. skill_distillation
write(
    "skill_distillation",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/skill_distillation.schema.json",
        "title": "Skill Distillation (NOT a summary)",
        "type": "object",
        "required": [
            "skill_id",
            "name",
            "problem",
            "applicability",
            "non_applicability",
            "inputs",
            "procedure",
            "decision_rules",
            "common_failures",
            "examples",
            "counterexamples",
            "safety",
            "version",
            "evidence",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "skill_id": {"type": "string"},
            "name": {"type": "string"},
            "problem": {"type": "string"},
            "applicability": {"type": "array", "items": {"type": "string"}},
            "non_applicability": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "applicability boundaries required",
            },
            "inputs": {"type": "array", "items": {"type": "string"}},
            "procedure": {"type": "array", "items": {"type": "string"}},
            "decision_rules": {"type": "array", "items": {"type": "string"}},
            "common_failures": {"type": "array", "items": {"type": "string"}},
            "examples": {"type": "array", "items": {"type": "string"}},
            "counterexamples": {"type": "array", "items": {"type": "string"}},
            "safety": {"type": "string"},
            "version": {"type": "string"},
            "evidence": {"type": "array", "items": {"type": "string"}},
            "deprecated_by": {"type": "string"},
            "is_summary_only": {
                "type": "boolean",
                "const": False,
                "description": "a video summary is NOT a skill; this must be false",
            },
            **common(),
        },
        "additionalProperties": False,
    },
)

# 17. provider_adapter
write(
    "provider_adapter",
    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"{SCHEMA_BASE}/provider_adapter.schema.json",
        "title": "Provider Adapter (research candidate)",
        "type": "object",
        "required": [
            "adapter_id",
            "name",
            "category",
            "install_status",
            "approval_status",
            "research_status",
            "interface",
            "source",
            "provenance",
            "status",
            "schema_version",
        ],
        "properties": {
            "adapter_id": {"type": "string"},
            "name": {"type": "string"},
            "category": {
                "type": "string",
                "enum": [
                    "broad_research",
                    "vertical_platform",
                    "comment",
                    "copywriting",
                    "humanizer",
                    "subtitle_tts",
                    "rough_cut",
                    "motion",
                    "publish",
                    "reference_analysis",
                ],
            },
            "install_status": {"type": "string", "const": "not_installed"},
            "approval_status": {"type": "string", "const": "not_approved"},
            "research_status": {"type": "string", "const": "research_candidate"},
            "interface": {
                "type": "object",
                "required": [
                    "capabilities",
                    "inputs",
                    "outputs",
                    "auth",
                    "cost",
                    "privacy",
                    "license",
                    "reliability",
                    "fallback",
                    "health",
                    "audit_status",
                ],
                "properties": {
                    "capabilities": {"type": "array", "items": {"type": "string"}},
                    "inputs": {"type": "string"},
                    "outputs": {"type": "string"},
                    "auth": {"type": "string"},
                    "cost": {"type": "string"},
                    "privacy": {"type": "string"},
                    "license": {"type": "string"},
                    "reliability": {"type": "string"},
                    "fallback": {"type": "string"},
                    "health": {"type": "string"},
                    "audit_status": {"type": "string"},
                },
            },
            "article_ref": {"type": "string"},
            **common(),
        },
        "additionalProperties": False,
    },
)

# Summary
schemas = sorted(OUT.glob("*.schema.json"))
print(f"Generated {len(schemas)} schemas in {OUT}")
for s in schemas:
    print(f"  {s.name}")
