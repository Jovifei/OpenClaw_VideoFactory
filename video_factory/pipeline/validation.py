"""Thin jsonschema wrapper: unified schema loading, validation, and graceful degradation.

When ``jsonschema`` is not installed (e.g. minimal environments), ``is_available()``
returns ``False`` and ``validate()`` becomes a no-op with a warning — the pipeline
does **not** crash on import.
"""

from __future__ import annotations

import logging
import json
import warnings
from pathlib import Path

from .errors import FactoryContractError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema catalogue: name → relative path under schemas/video/
# ---------------------------------------------------------------------------
_SCHEMA_MAP: dict[str, str] = {
    "storyboard": "schemas/video/storyboard.schema.json",
    "timeline": "schemas/video/timeline.schema.json",
    "video_job": "schemas/video/video_job.schema.json",
    "video_job_state": "schemas/video/video_job_state.schema.json",
    "director_draft": "schemas/video/director_draft.schema.json",
    "director_script": "schemas/video/director_script.schema.json",
    "director_factual_brief": "schemas/video/director_factual_brief.schema.json",
    "director_run_report": "schemas/video/director_run_report.schema.json",
    "asset_selection_report": "schemas/video/asset_selection_report.schema.json",
    "director_quality_report": "schemas/video/director_quality_report.schema.json",
    "phase1_quality_report": "schemas/video/phase1_quality_report.schema.json",
    "phase1_review_package": "schemas/video/phase1_review_package.schema.json",
    "reference_receipt": "schemas/video/reference_receipt.schema.json",
    "reference_rights": "schemas/video/reference_rights.schema.json",
    "reference_report": "schemas/video/reference_report.schema.json",
    "original_brief": "schemas/video/original_brief.schema.json",
    "difference_report": "schemas/video/difference_report.schema.json",
    "composition": "schemas/video/composition.schema.json",
    "phase1_topic_request": "schemas/video/phase1_topic_request.schema.json",
    "phase1_research_brief": "schemas/video/phase1_research_brief.schema.json",
    "phase1_script_candidates": "schemas/video/phase1_script_candidates.schema.json",
    "phase1_selected_script": "schemas/video/phase1_selected_script.schema.json",
    "phase1_scene_plan": "schemas/video/phase1_scene_plan.schema.json",
    "phase1_subject_media_result": "schemas/video/phase1_subject_media_result.schema.json",
    "pink_pig_registry": "src/factory/assets/pink_pig/registry.schema.json",
}

_SCHEMA_ERROR_CODES: dict[str, str] = {
    "pink_pig_registry": "asset_registry_invalid",
    "storyboard": "storyboard_schema_invalid",
    "timeline": "timeline_schema_invalid",
    "video_job": "video_job_invalid",
    "video_job_state": "video_job_state_invalid",
    "director_draft": "director_draft_invalid",
    "director_script": "director_script_schema_invalid",
    "director_factual_brief": "director_factual_brief_invalid",
    "director_run_report": "director_run_report_invalid",
    "asset_selection_report": "asset_selection_report_invalid",
    "director_quality_report": "director_quality_report_invalid",
    "phase1_quality_report": "phase1_quality_report_invalid",
    "phase1_review_package": "phase1_review_package_invalid",
    "reference_receipt": "reference_receipt_invalid",
    "reference_rights": "reference_rights_invalid",
    "reference_report": "reference_report_invalid",
    "original_brief": "original_brief_invalid",
    "difference_report": "difference_report_invalid",
    "composition": "composition_schema_invalid",
    "phase1_topic_request": "phase1_topic_request_invalid",
    "phase1_research_brief": "phase1_research_brief_invalid",
    "phase1_script_candidates": "phase1_script_candidates_invalid",
    "phase1_selected_script": "phase1_selected_script_invalid",
    "phase1_scene_plan": "phase1_scene_plan_invalid",
    "phase1_subject_media_result": "phase1_subject_media_result_invalid",
}

_SCHEMA_ERROR_MESSAGES: dict[str, str] = {
    "pink_pig_registry": "Pink Pig asset registry failed schema validation.",
    "storyboard": "Storyboard failed schema validation.",
    "timeline": "Timeline failed schema validation.",
    "video_job": "Video render job failed schema validation.",
    "video_job_state": "Video job state failed schema validation.",
    "director_draft": "Director draft failed schema validation.",
    "director_script": "Director script failed schema validation.",
    "director_factual_brief": "Director factual brief failed schema validation.",
    "director_run_report": "Director run report failed schema validation.",
    "asset_selection_report": "Asset selection report failed schema validation.",
    "director_quality_report": "Director quality report failed schema validation.",
    "phase1_quality_report": "Phase 1 quality report failed schema validation.",
    "phase1_review_package": "Phase 1 review package failed schema validation.",
    "reference_receipt": "Reference receipt failed schema validation.",
    "reference_rights": "Reference rights failed schema validation.",
    "reference_report": "Reference report failed schema validation.",
    "original_brief": "Original brief failed schema validation.",
    "difference_report": "Difference report failed schema validation.",
    "composition": "Composition failed schema validation.",
    "phase1_topic_request": "Phase 1 topic request failed schema validation.",
    "phase1_research_brief": "Phase 1 research brief failed schema validation.",
    "phase1_script_candidates": "Phase 1 script candidates failed schema validation.",
    "phase1_selected_script": "Phase 1 selected script failed schema validation.",
    "phase1_scene_plan": "Phase 1 scene plan failed schema validation.",
    "phase1_subject_media_result": "Phase 1 subject media result failed schema validation.",
}

# Lazy-loaded cache
_schemas: dict[str, dict] = {}
_available: bool | None = None


class SchemaValidationError(FactoryContractError):
    """Raised when a document fails JSON Schema validation."""

    def __init__(self, code: str, message: str, context: dict | None = None) -> None:
        super().__init__(code, message, context)


def _try_import_jsonschema() -> bool:
    """Return True if jsonschema is importable."""
    try:
        import jsonschema  # noqa: F401

        return True
    except ImportError:
        return False


def is_available() -> bool:
    """Check whether jsonschema validation is functional."""
    global _available  # noqa: PLW0603
    if _available is None:
        _available = _try_import_jsonschema()
        if not _available:
            warnings.warn(
                "jsonschema not installed; schema validation will be skipped. "
                "Install with: pip install 'jsonschema>=4.0'",
                UserWarning,
                stacklevel=2,
            )
    return _available


def load(name: str) -> dict:
    """Load and return a parsed JSON Schema by name.

    Parameters
    ----------
    name : str
        One of: ``"storyboard"``, ``"timeline"``, ``"video_job"``,
        ``"pink_pig_registry"``.

    Returns
    -------
    dict
        The parsed schema object.

    Raises
    ------
    ValueError
        If *name* is not in the catalogue.
    """
    global _schemas  # noqa: PLW0603
    if name not in _schemas:
        path_str = _SCHEMA_MAP.get(name)
        if path_str is None:
            raise FactoryContractError(
                "schema_catalog_invalid",
                "The requested schema is not catalogued.",
                {"schema": name},
            )
        path = Path(path_str)
        if not path.is_file():
            raise FactoryContractError(
                "schema_catalog_invalid",
                "The catalogued schema file is missing.",
                {"schema": name},
            )
        import json

        _schemas[name] = json.loads(path.read_text(encoding="utf-8"))
    return _schemas[name]


def validate(document: dict, schema_name: str) -> None:
    """Validate *document* against the named schema.

    When jsonschema is unavailable this is a silent no-op (with one warning
    logged at module level via ``is_available()``).

    Parameters
    ----------
    document : dict
        The JSON-compatible document to validate.
    schema_name : str
        Schema name recognised by :func:`load`.

    Raises
    ------
    SchemaValidationError
        If validation fails.
    ValueError
        If *schema_name* is unknown or its file is missing.
    """
    if not is_available():
        logger.debug("jsonschema unavailable; skipping validation of %s", schema_name)
        return
    import jsonschema

    schema = load(schema_name)
    path_str = _SCHEMA_MAP[schema_name]
    schema_path = Path(path_str).resolve()
    # Resolve all repository-local schema references from the checked-out
    # catalog.  This prevents jsonschema from treating the documentation-only
    # openclaw.local $id as a network endpoint during offline validation.
    store: dict[str, dict] = {}
    for candidate in schema_path.parent.glob("*.schema.json"):
        try:
            loaded = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, ValueError):
            continue
        if isinstance(loaded, dict):
            store[candidate.resolve().as_uri()] = loaded
            if isinstance(loaded.get("$id"), str):
                store[str(loaded["$id"])] = loaded
    # Use the modern ``referencing`` registry so each external schema keeps
    # its own ``$id`` scope.  The legacy RefResolver mutates the active scope
    # after resolving ``composition.schema.json`` and can then incorrectly
    # resolve Storyboard's local ``#/$defs/scene`` against Composition.
    try:
        from referencing import Registry, Resource

        registry = Registry()
        for uri, loaded in store.items():
            # A schema may be registered under both its repository file URI
            # and documentation-only canonical $id.  Registering the same
            # resource under both keeps validation offline and deterministic.
            registry = registry.with_resource(uri, Resource.from_contents(loaded))
        validator = jsonschema.Draft202012Validator(schema, registry=registry)
    except ImportError:  # pragma: no cover - jsonschema installs referencing
        resolver = jsonschema.RefResolver.from_schema(schema, store=store)
        validator = jsonschema.Draft202012Validator(schema, resolver=resolver)
    errors = sorted(
        validator.iter_errors(document),
        key=lambda err: (
            tuple(str(part) for part in err.absolute_path),
            str(err.validator),
            str(err.message),
        ),
    )
    if errors:
        exc = errors[0]
        path_parts = [str(part) for part in exc.absolute_path]
        context = {
            "schema": schema_name,
            "path": ".".join(path_parts),
            "validator": str(exc.validator),
        }
        code = _SCHEMA_ERROR_CODES.get(schema_name, "schema_catalog_invalid")
        message = _SCHEMA_ERROR_MESSAGES.get(
            schema_name, "Document failed schema validation."
        )
        raise SchemaValidationError(code, message, context) from exc
