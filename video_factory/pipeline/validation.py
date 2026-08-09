"""Thin jsonschema wrapper: unified schema loading, validation, and graceful degradation.

When ``jsonschema`` is not installed (e.g. minimal environments), ``is_available()``
returns ``False`` and ``validate()`` becomes a no-op with a warning — the pipeline
does **not** crash on import.
"""

from __future__ import annotations

import logging
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
    "director_run_report": "schemas/video/director_run_report.schema.json",
    "composition": "schemas/video/composition.schema.json",
    "pink_pig_registry": "src/factory/assets/pink_pig/registry.schema.json",
}

_SCHEMA_ERROR_CODES: dict[str, str] = {
    "pink_pig_registry": "asset_registry_invalid",
    "storyboard": "storyboard_schema_invalid",
    "timeline": "timeline_schema_invalid",
    "video_job": "video_job_invalid",
    "video_job_state": "video_job_state_invalid",
    "director_draft": "director_draft_invalid",
    "director_run_report": "director_run_report_invalid",
    "composition": "composition_schema_invalid",
}

_SCHEMA_ERROR_MESSAGES: dict[str, str] = {
    "pink_pig_registry": "Pink Pig asset registry failed schema validation.",
    "storyboard": "Storyboard failed schema validation.",
    "timeline": "Timeline failed schema validation.",
    "video_job": "Video render job failed schema validation.",
    "video_job_state": "Video job state failed schema validation.",
    "director_draft": "Director draft failed schema validation.",
    "director_run_report": "Director run report failed schema validation.",
    "composition": "Composition failed schema validation.",
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
    validator = jsonschema.Draft202012Validator(schema)
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
