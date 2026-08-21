"""Provider-neutral AI Director implementation.

The class turns a bounded provider Draft into the existing Storyboard
contract.  The provider is never allowed to choose registry assets, file
paths, scene IDs, orders, or render parameters; those values are injected and
validated here before the existing compiler is called by the outer pipeline.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.failure_contract import sanitize_error_payload
from video_factory.pipeline.storyboard import StoryboardError, compile_storyboard, validate_storyboard
from video_factory.pipeline.validation import validate as validate_schema

from src.factory.assets.pink_pig.loader import PinkPigRegistry, load_registry

from .context import (
    PROMPT_VERSION,
    DirectorContext,
    build_director_prompt,
    load_director_context,
    normalize_topic,
)
from .director_contract import Director
from .provider import CodexCliDirectorProvider, DirectorProvider
from .script_planner import ScriptPlanner
from .factual import FactualBrief


DEFAULT_GLOBALS: dict[str, object] = {
    "aspect_ratio": "9:16",
    "fps": 30,
    "default_scene_seconds": 2.5,
    "default_transition": "fade",
    "transition_seconds": 0.4,
    "narration_cps": 5.0,
    "min_scene_seconds": 1.2,
    "max_scene_seconds": 8.0,
}
_ALLOWED_TRANSITIONS = {"fade", "zoom", "slide"}
_ALLOWED_DRAFT_FIELDS = {"title", "content_scope", "scenes"}
_ALLOWED_SCENE_FIELDS = {
    "purpose",
    "core_action",
    "narration",
    "caption",
    "mood",
    "pose",
    "transition_out",
}
_REPORT_ERROR_CONTEXT_KEYS = {
    "stage",
    "provider",
    "attempt",
    "exit_code",
    "schema",
    "path",
    "validator",
    "reason",
    "status",
}


def stable_storyboard_id(topic: str) -> str:
    """Return a stable, non-secret Storyboard identifier for a topic."""

    normalized = normalize_topic(topic)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return f"sb_{digest}"


def _json_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _safe_report_error(exc: FactoryContractError, *, attempt: int) -> dict[str, object]:
    detail = sanitize_error_payload(exc)
    raw_context = detail.get("context", {})
    context = {
        str(key): value
        for key, value in raw_context.items()
        if key in _REPORT_ERROR_CONTEXT_KEYS
    }
    context.setdefault("attempt", attempt)
    return {
        "code": str(detail["code"]),
        "message": str(detail["message"])[:240],
        "context": context,
    }


def _schema_path(repo_root: Path) -> Path:
    return repo_root / "schemas" / "video" / "director_draft.schema.json"


def _draft_schema_validate(draft: dict[str, object], schema_path: Path) -> None:
    """Validate a provider Draft with deterministic, safe diagnostics."""

    if not schema_path.is_file():
        raise FactoryContractError(
            "director_context_invalid",
            "Director Draft schema is unavailable.",
            {"field": "director_draft_schema", "reason": "missing"},
        )
    try:
        import jsonschema

        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        errors = sorted(
            validator.iter_errors(draft),
            key=lambda error: (
                tuple(str(part) for part in error.absolute_path),
                str(error.validator),
                str(error.message),
            ),
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise FactoryContractError(
            "director_context_invalid",
            "Director Draft schema could not be loaded.",
            {"field": "director_draft_schema", "reason": "read"},
        ) from exc
    except ImportError as exc:
        raise FactoryContractError(
            "director_context_invalid",
            "Director Draft schema validator is unavailable.",
            {"field": "director_draft_schema", "reason": "validator_missing"},
        ) from exc
    except Exception as exc:
        # jsonschema raises version-specific SchemaError subclasses; expose
        # only the stable contract code and a sanitized reason.
        raise FactoryContractError(
            "director_context_invalid",
            "Director Draft schema is invalid.",
            {"field": "director_draft_schema", "reason": "schema_invalid"},
        ) from exc
    if errors:
        error = errors[0]
        path = ".".join(str(part) for part in error.absolute_path)
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft failed schema validation.",
            {
                "schema": "director_draft",
                "path": path,
                "validator": str(error.validator),
            },
        ) from error


def _validate_draft_semantics(draft: dict[str, object], registry: PinkPigRegistry) -> None:
    """Apply semantic checks not expressible in the minimal JSON Schema."""

    if set(draft) - _ALLOWED_DRAFT_FIELDS:
        extra = sorted(set(draft) - _ALLOWED_DRAFT_FIELDS)[0]
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft contains an unsupported field.",
            {"schema": "director_draft", "path": extra, "validator": "additionalProperties"},
        )
    if draft.get("content_scope") != "evergreen_embedded_mainline":
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft content scope is not permitted.",
            {"schema": "director_draft", "path": "content_scope", "validator": "const"},
        )
    title = draft.get("title")
    if not isinstance(title, str) or not title.strip():
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft title must be non-empty.",
            {"schema": "director_draft", "path": "title", "validator": "minLength"},
        )
    scenes = draft.get("scenes")
    if not isinstance(scenes, list) or not 5 <= len(scenes) <= 9:
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft must contain between five and nine scenes.",
            {"schema": "director_draft", "path": "scenes", "validator": "minItems"},
        )
    allowed_poses = set(registry.style_profile.pose_rules.get("allowed_poses", ()))
    for index, scene in enumerate(scenes):
        path = f"scenes.{index}"
        if not isinstance(scene, dict):
            raise FactoryContractError(
                "director_output_invalid",
                "Director Draft scene must be an object.",
                {"schema": "director_draft", "path": path, "validator": "type"},
            )
        extras = set(scene) - _ALLOWED_SCENE_FIELDS
        if extras:
            field = sorted(extras)[0]
            raise FactoryContractError(
                "director_output_invalid",
                "Director Draft scene contains an unsupported field.",
                {"schema": "director_draft", "path": f"{path}.{field}", "validator": "additionalProperties"},
            )
        for field in ("purpose", "core_action", "narration", "pose"):
            if not isinstance(scene.get(field), str) or not scene[field].strip():
                raise FactoryContractError(
                    "director_output_invalid",
                    "Director Draft scene contains an empty required field.",
                    {"schema": "director_draft", "path": f"{path}.{field}", "validator": "minLength"},
                )
        if scene["pose"] not in allowed_poses:
            raise FactoryContractError(
                "director_output_invalid",
                "Director Draft scene pose is not in the Pink Pig vocabulary.",
                {"schema": "director_draft", "path": f"{path}.pose", "validator": "enum"},
            )
        transition = scene.get("transition_out")
        if transition is not None and transition not in _ALLOWED_TRANSITIONS:
            raise FactoryContractError(
                "director_output_invalid",
                "Director Draft transition is unsupported.",
                {"schema": "director_draft", "path": f"{path}.transition_out", "validator": "enum"},
            )
    if scenes[0].get("purpose") != "hook":
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft first scene must be a hook.",
            {"schema": "director_draft", "path": "scenes.0.purpose", "validator": "const"},
        )
    if scenes[-1].get("purpose") != "summary":
        raise FactoryContractError(
            "director_output_invalid",
            "Director Draft last scene must be a summary.",
            {"schema": "director_draft", "path": f"scenes.{len(scenes)-1}.purpose", "validator": "const"},
        )


def compose_storyboard(
    draft: dict[str, object],
    *,
    topic: str,
    registry: PinkPigRegistry,
) -> dict[str, object]:
    """Inject deterministic factory fields into a validated provider Draft."""

    normalized = normalize_topic(topic)
    scenes_out: list[dict[str, object]] = []
    scenes = draft.get("scenes", [])
    assert isinstance(scenes, list)
    for index, scene in enumerate(scenes, start=1):
        assert isinstance(scene, dict)
        transition = scene.get("transition_out")
        if index == len(scenes):
            transition = None
        notes = f"{str(scene['purpose']).strip()}: {str(scene['core_action']).strip()}"
        scenes_out.append(
            {
                "scene_id": f"s{index:02d}",
                "order": index,
                "narration": str(scene["narration"]).strip(),
                "caption": (str(scene["caption"]).strip() if scene.get("caption") is not None else None),
                "mood": (str(scene["mood"]).strip() if scene.get("mood") is not None else None),
                "pose": str(scene["pose"]).strip(),
                "asset_id": None,
                "duration_intent": {"mode": "narration"},
                "transition_out": transition,
                "director_notes": notes,
            }
        )
    return {
        "schema_version": "1.0",
        "storyboard_id": stable_storyboard_id(normalized),
        "title": str(draft["title"]).strip(),
        "ip": {
            "character_id": registry.character_id,
            "registry_version": registry.registry_version,
        },
        "globals": dict(DEFAULT_GLOBALS),
        "scenes": scenes_out,
    }


class AIDirector(Director):
    """Turn a topic into a validated Storyboard through a bounded provider."""

    def __init__(
        self,
        provider: DirectorProvider | None = None,
        *,
        repo_root: Path | None = None,
        context: DirectorContext | None = None,
        max_attempts: int = 3,
        workflow: str = "auto",
    ) -> None:
        if max_attempts < 1 or max_attempts > 3:
            raise ValueError("director_attempts_invalid")
        # ai_director.py lives at <repo>/src/factory/director/ai_director.py.
        self.repo_root = Path(repo_root).resolve() if repo_root is not None else Path(__file__).resolve().parents[3]
        self.provider = provider or CodexCliDirectorProvider()
        self.context = context
        self.max_attempts = max_attempts
        if workflow not in {"auto", "legacy", "phase2"}:
            raise ValueError("director_workflow_invalid")
        self.workflow = workflow
        self.last_report: dict[str, object] | None = None
        self.last_script: dict[str, object] | None = None
        self.last_score: dict[str, object] | None = None
        self.last_asset_selection: dict[str, object] | None = None
        self.factual_brief: FactualBrief | None = None

    def _context(self) -> DirectorContext:
        if self.context is None:
            self.context = load_director_context(self.repo_root)
        return self.context

    def _provider_name(self) -> str:
        return str(getattr(self.provider, "provider_name", type(self.provider).__name__))

    def _provider_version(self) -> str:
        value = getattr(self.provider, "provider_version", "unknown")
        return str(value).replace("\r", "").replace("\n", "")[:128] or "unknown"

    def _report_base(self, topic: str, attempts: int) -> dict[str, object]:
        factual_required = not (self.factual_brief is not None and self.factual_brief.verified)
        return {
            "schema_version": "1.0",
            "provider": self._provider_name(),
            "provider_version": self._provider_version(),
            "prompt_version": PROMPT_VERSION,
            "topic_digest": hashlib.sha256(topic.encode("utf-8")).hexdigest(),
            "attempts": attempts,
            "draft_validation": {"status": "fail", "error_count": 1, "validator": "jsonschema"},
            "storyboard_validation": {"status": "fail", "error_count": 1, "validator": "jsonschema"},
            "semantic_validation": {"status": "fail", "error_count": 1, "validator": "director_semantics"},
            "storyboard_id": stable_storyboard_id(topic),
            "storyboard_sha256": _json_sha256({}),
            "compiled_duration_seconds": 0.0,
            "factual_review_required": factual_required,
            "error": None,
        }

    def _reset_run_state(self) -> None:
        """Drop artifacts from a prior invocation before starting a run."""

        self.last_report = None
        self.last_script = None
        self.last_score = None
        self.last_asset_selection = None

    def create_script(self, topic: str, *, factual_brief: FactualBrief | None = None) -> dict[str, object]:
        """Generate a deterministic DirectorScript for the Phase 2 path."""

        self._reset_run_state()
        if factual_brief is not None:
            self.factual_brief = factual_brief
        context = self._context()
        planner = ScriptPlanner(
            self.provider,
            repo_root=self.repo_root,
            context=context,
            max_attempts=self.max_attempts,
        )
        script = planner.create_script(topic, factual_brief=factual_brief)
        self.last_script = script
        self.last_score = planner.last_result.score if planner.last_result else None
        return script

    def _create_phase2_storyboard(self, topic: str, *, factual_brief: FactualBrief | None = None) -> dict[str, object]:
        normalized = normalize_topic(topic)
        context = self._context()
        factual_brief = factual_brief if factual_brief is not None else self.factual_brief
        script = self.create_script(normalized, factual_brief=factual_brief)
        from .storyboard_assembler import StoryboardAssembler
        from .asset_selector import AssetSelector

        assembler = StoryboardAssembler(repo_root=self.repo_root, registry=context.registry)
        storyboard = assembler.from_script(script)
        selection = AssetSelector(repo_root=self.repo_root, registry=context.registry).select_assets(
            storyboard, context.registry
        )
        storyboard = selection.storyboard
        validate_schema(storyboard, "storyboard")
        validate_storyboard(storyboard)
        timeline = compile_storyboard(storyboard, context.registry, repo_root=self.repo_root)
        total = float(timeline.get("total_duration_seconds", 0.0))
        if not 25.0 <= total <= 60.0:
            raise FactoryContractError(
                "director_storyboard_invalid",
                "Director storyboard duration is outside the approved range.",
                {"path": "timeline.total_duration_seconds", "reason": "duration_range"},
            )
        self.last_asset_selection = selection.report
        self.last_report = {
            **self._report_base(normalized, 1),
            "draft_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
            "storyboard_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
            "semantic_validation": {"status": "pass", "error_count": 0, "validator": "director_semantics"},
            "storyboard_id": storyboard["storyboard_id"],
            "storyboard_sha256": _json_sha256(storyboard),
            "compiled_duration_seconds": round(total, 3),
        }
        validate_schema(self.last_report, "director_run_report")
        return storyboard

    def create_storyboard(self, topic: str) -> dict[str, object]:
        self._reset_run_state()
        if self.workflow == "phase2" or (
            self.workflow == "auto" and isinstance(self.provider, CodexCliDirectorProvider)
        ):
            return self._create_phase2_storyboard(topic)
        normalized = normalize_topic(topic)
        context = self._context()
        prompt = build_director_prompt(normalized, context)
        schema_path = _schema_path(self.repo_root)
        attempts = 0
        last_error: FactoryContractError | None = None
        for attempt in range(1, self.max_attempts + 1):
            attempts = attempt
            try:
                draft = self.provider.generate(
                    prompt=prompt,
                    output_schema=schema_path,
                    timeout_seconds=180,
                )
                if not isinstance(draft, dict):
                    raise FactoryContractError(
                        "director_output_invalid",
                        "Director provider output must be a JSON object.",
                        {"schema": "director_draft", "validator": "type"},
                    )
                _draft_schema_validate(draft, schema_path)
                _validate_draft_semantics(draft, context.registry)
                storyboard = compose_storyboard(draft, topic=normalized, registry=context.registry)
                validate_schema(storyboard, "storyboard")
                validate_storyboard(storyboard)
                timeline = compile_storyboard(storyboard, context.registry, repo_root=self.repo_root)
                total = float(timeline.get("total_duration_seconds", 0.0))
                if not 25.0 <= total <= 60.0:
                    raise FactoryContractError(
                        "director_storyboard_invalid",
                        "Director storyboard duration is outside the approved range.",
                        {"path": "timeline.total_duration_seconds", "reason": "duration_range"},
                    )
                self.last_report = {
                    **self._report_base(normalized, attempts),
                    "draft_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
                    "storyboard_validation": {"status": "pass", "error_count": 0, "validator": "jsonschema"},
                    "semantic_validation": {"status": "pass", "error_count": 0, "validator": "director_semantics"},
                    "storyboard_id": storyboard["storyboard_id"],
                    "storyboard_sha256": _json_sha256(storyboard),
                    "compiled_duration_seconds": round(total, 3),
                }
                validate_schema(self.last_report, "director_run_report")
                return storyboard
            except FactoryContractError as exc:
                last_error = exc
                # Missing local prerequisites and an unavailable provider are
                # deterministic blockers; repeating them cannot improve the
                # result and would create misleading provider activity.
                if exc.code in {
                    "director_provider_unavailable",
                    "director_context_invalid",
                    "director_topic_invalid",
                }:
                    break
            except StoryboardError as exc:
                last_error = FactoryContractError(
                    "director_storyboard_invalid",
                    "Director storyboard failed semantic validation.",
                    {"reason": str(exc).split(":", 1)[0]},
                )
            except Exception as exc:
                last_error = FactoryContractError(
                    "director_storyboard_invalid",
                    "Director storyboard could not be validated.",
                    {"reason": type(exc).__name__},
                )
        assert last_error is not None
        self.last_report = self._report_base(normalized, attempts)
        self.last_report["error"] = _safe_report_error(last_error, attempt=attempts)
        validate_schema(self.last_report, "director_run_report")
        raise last_error


__all__ = [
    "AIDirector",
    "DEFAULT_GLOBALS",
    "compose_storyboard",
    "stable_storyboard_id",
]
