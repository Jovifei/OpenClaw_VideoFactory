"""Provider-backed DirectorScript generation and deterministic scoring."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import validate

from .context import DirectorContext, build_script_prompt, normalize_topic
from .factual import FactualBrief
from .provider import DirectorProvider


def stable_script_id(topic: str) -> str:
    return f"script_{hashlib.sha256(normalize_topic(topic).encode('utf-8')).hexdigest()[:16]}"


@dataclass(frozen=True, slots=True)
class ScriptResult:
    script: dict[str, object]
    score: dict[str, object]
    attempts: int


def _semantic_validate(script: dict[str, object], *, topic: str, context: DirectorContext, brief: FactualBrief | None) -> None:
    expected_digest = hashlib.sha256(normalize_topic(topic).encode("utf-8")).hexdigest()
    if script.get("topic_digest") != expected_digest:
        raise FactoryContractError("director_script_semantics_invalid", "Director script topic digest is not deterministic.", {"field": "topic_digest", "reason": "mismatch"})
    beats = script.get("beats")
    if not isinstance(beats, list) or not 5 <= len(beats) <= 9:
        raise FactoryContractError("director_script_semantics_invalid", "Director script must contain five to nine beats.", {"field": "beats", "reason": "count"})
    if beats[0].get("purpose") != "hook" or beats[-1].get("purpose") != "summary":
        raise FactoryContractError("director_script_semantics_invalid", "Director script must start with hook and end with summary.", {"field": "beats.purpose", "reason": "bookends"})
    allowed_poses = set(context.allowed_poses)
    fact_ids = {str(item.get("fact_id")) for item in (brief.document.get("facts", []) if brief else [])}
    for index, beat in enumerate(beats):
        if not isinstance(beat, dict):
            raise FactoryContractError("director_script_semantics_invalid", "Director script beat must be an object.", {"path": f"beats.{index}", "reason": "type"})
        if beat.get("pose") not in allowed_poses:
            raise FactoryContractError("director_script_semantics_invalid", "Director script pose is outside the Pink Pig vocabulary.", {"path": f"beats.{index}.pose", "reason": "enum"})
        if brief is not None and any(str(ref) not in fact_ids for ref in beat.get("fact_refs", [])):
            raise FactoryContractError("director_script_semantics_invalid", "Director script references an unknown fact.", {"path": f"beats.{index}.fact_refs", "reason": "unknown_fact"})
    if script.get("script_id") != stable_script_id(topic):
        raise FactoryContractError("director_script_semantics_invalid", "Director script ID is not deterministic.", {"field": "script_id", "reason": "mismatch"})


def score_script(script: dict[str, object], *, factual_brief: FactualBrief | None) -> dict[str, object]:
    beats = script.get("beats", [])
    variety = len({str(item.get("visual_intent", "")) for item in beats if isinstance(item, dict)})
    components = {
        "hook": 15 if str(script.get("hook", "")).strip() else 0,
        "clarity": 15 if all(str(item.get("narration", "")).strip() for item in beats if isinstance(item, dict)) else 0,
        "evidence": 15 if factual_brief is not None and factual_brief.verified else 8,
        "visual_variety": min(15, variety * 3),
        "pacing": 15 if 25 <= float(script.get("duration_target_seconds", 0)) <= 60 else 0,
        "originality": 10 if "今天我们来聊聊" not in str(script.get("narration", "")) else 3,
        "account_fit": 10 if script.get("style", {}).get("content_scope") == "evergreen_embedded_mainline" else 0,
        "production_reliability": 5 if 5 <= len(beats) <= 9 else 0,
    }
    score = int(sum(components.values()))
    return {"schema_version": "1.0", "score": score, "components": components, "status": "pass" if score >= 85 else "retry" if score >= 75 else "fail"}


class ScriptPlanner:
    """Generate a schema-bound script without allowing provider asset control."""

    def __init__(self, provider: DirectorProvider, *, repo_root: Path, context: DirectorContext, max_attempts: int = 3) -> None:
        self.provider = provider
        self.repo_root = Path(repo_root).resolve()
        self.context = context
        self.max_attempts = max(1, min(3, int(max_attempts)))
        self.last_result: ScriptResult | None = None

    def create_script(self, topic: str, *, factual_brief: FactualBrief | None = None) -> dict[str, object]:
        normalized = normalize_topic(topic)
        prompt = build_script_prompt(normalized, self.context, factual_brief=factual_brief)
        schema_path = self.repo_root / "schemas" / "video" / "director_script.schema.json"
        quality_retry_used = False
        last_error: FactoryContractError | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                value = self.provider.generate(prompt=prompt, output_schema=schema_path, timeout_seconds=180)
                if not isinstance(value, dict):
                    raise FactoryContractError("director_script_invalid", "Director provider did not return a JSON object.", {"schema": "director_script", "validator": "type", "attempt": attempt})
                # The provider is allowed to omit deterministic fields.  They
                # are injected here before validation, so the model cannot
                # choose IDs, topic digests, or account style tokens.
                value = dict(value)
                value["script_id"] = stable_script_id(normalized)
                value["topic_digest"] = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
                value["style"] = {"language": "zh-CN", "tone": "technical_calm_dry_humor", "content_scope": "evergreen_embedded_mainline"}
                validate(value, "director_script")
                _semantic_validate(value, topic=normalized, context=self.context, brief=factual_brief)
                score = score_script(value, factual_brief=factual_brief)
                self.last_result = ScriptResult(value, score, attempt)
                if score["status"] == "retry" and not quality_retry_used:
                    quality_retry_used = True
                    continue
                if score["status"] != "pass":
                    raise FactoryContractError("director_script_quality_failed", "Director script quality score is below the acceptance threshold.", {"score": int(score["score"]), "attempt": attempt})
                return value
            except FactoryContractError as exc:
                last_error = exc
                if exc.code in {"director_provider_unavailable", "director_context_invalid", "director_topic_invalid", "director_factual_brief_invalid", "director_script_quality_failed"}:
                    break
            except Exception as exc:
                last_error = FactoryContractError("director_script_invalid", "Director script failed validation.", {"reason": type(exc).__name__, "attempt": attempt})
        if last_error is None:
            last_error = FactoryContractError("director_script_invalid", "Director script generation failed.", {"reason": "unknown"})
        raise last_error


__all__ = ["ScriptPlanner", "ScriptResult", "score_script", "stable_script_id"]
