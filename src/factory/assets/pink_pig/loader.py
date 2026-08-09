"""Pink Pig IP asset registry loader and resolver.

This module provides:
- :func:`load_registry` — load + validate a ``registry.json`` into a
  :class:`PinkPigRegistry` dataclass.
- :class:`PinkPigRegistry` — frozen dataclass with ``resolve()`` for
  deterministic asset resolution (asset_id → pose → mood → default).
- :class:`RegistryError` — domain-specific exception.

Pose vocabulary (closed set, aligned with ``src/factory/assets/mascot/*.svg``):
  normal, thinking, question, measure, repair, success, warning, ending
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from video_factory.pipeline.errors import FactoryContractError
from video_factory.pipeline.validation import is_available, validate as _validate

# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------
REGISTRY_PATH = Path(__file__).resolve().parent / "registry.json"

POSES: frozenset[str] = frozenset(
    ["normal", "thinking", "question", "measure", "repair", "success", "warning", "ending"]
)


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------
class RegistryError(ValueError):
    """Raised when an asset cannot be resolved from the registry."""


# ---------------------------------------------------------------------------
# Supporting dataclasses (frozen, slots)
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class StyleProfile:
    schema_version: str
    brand_identity: dict[str, Any]
    character_rules: dict[str, Any]
    color_rules: dict[str, Any]
    pose_rules: dict[str, Any]
    forbidden_rules: tuple[str, ...]
    quality_checks: tuple[dict[str, Any], ...]


@dataclass(frozen=True, slots=True)
class IpConstraints:
    must_have: tuple[str, ...]
    character_must_perform_core_action: bool
    min_whitespace_ratio: float
    max_subject_ratio: float
    no_repeated_composition: bool


@dataclass(frozen=True, slots=True)
class Provenance:
    upstream_repo: str
    upstream_commit: str
    upstream_license: str
    local_path: str
    content_kind: str


@dataclass(frozen=True, slots=True)
class PinkPigAsset:
    """A single IP asset entry in the registry."""

    asset_id: str
    pose: str
    moods: tuple[str, ...]
    path: str | None
    source_svg: str | None
    width: int
    height: int
    render_ready: bool
    sha256: str
    pose_confidence: str
    tags: tuple[str, ...]
    fallback_asset_id: str | None = field(default=None, compare=False)

    def absolute_path(self, repo_root: Path) -> Path:
        """Resolve *path* (repo-relative POSIX) to an absolute ``Path``."""
        if self.path is None:
            raise RegistryError(f"asset_no_path:{self.asset_id}")
        return (repo_root / self.path).resolve()


@dataclass(frozen=True, slots=True)
class PinkPigRegistry:
    """The complete Pink Pig asset registry — single source of truth for IP."""

    schema_version: str
    registry_version: str
    character_id: str
    style_profile: StyleProfile
    ip_constraints: IpConstraints
    provenance: Provenance
    assets: Mapping[str, PinkPigAsset]
    pose_index: Mapping[str, str]
    mood_index: Mapping[str, str]
    default_asset_id: str

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, asset_id: str) -> PinkPigAsset:
        """Look up an asset by its ``asset_id``."""
        try:
            return self.assets[asset_id]
        except KeyError as exc:
            raise RegistryError(f"asset_unresolved:{asset_id}") from exc

    def resolve(
        self,
        *,
        asset_id: str | None = None,
        pose: str | None = None,
        mood: str | None = None,
    ) -> PinkPigAsset:
        """Deterministic resolution chain (R1).

        Resolution order:
          1. Explicit ``asset_id``
          2. ``pose`` → ``pose_index[pose]``
          3. ``mood`` → ``mood_index[mood]`` → ``pose_index[pose]``
          4. ``default_asset_id``
          5. Failure → raise ``RegistryError``

        If the resolved asset has ``render_ready == False``, follow
        ``fallback_asset_id`` (max 3 hops to prevent cycles).
        """
        resolved_id: str | None = None

        # Step 1 — explicit asset_id
        if asset_id is not None:
            resolved_id = asset_id
        # Step 2 — pose lookup
        elif pose is not None:
            resolved_id = self.pose_index.get(pose)
        # Step 3 — mood → pose lookup
        elif mood is not None:
            resolved_pose = self.mood_index.get(mood)
            if resolved_pose is not None:
                resolved_id = self.pose_index.get(resolved_pose)

        # Step 4 — default
        if resolved_id is None:
            resolved_id = self.default_asset_id

        # Resolve through fallback chain (max 3 hops)
        visited: list[str] = []
        current_id = resolved_id
        for _ in range(4):  # initial + up to 3 fallbacks
            if current_id in visited:
                raise RegistryError(f"asset_fallback_cycle:{current_id}")
            visited.append(current_id)
            asset = self.get(current_id)
            if asset.render_ready:
                return asset
            if asset.fallback_asset_id is None:
                raise RegistryError(f"asset_unresolved:{current_id} (no fallback)")
            current_id = asset.fallback_asset_id

        raise RegistryError(f"asset_fallback_cycle:{resolved_id}")

    def render_ready_assets(self) -> tuple[PinkPigAsset, ...]:
        """Return all assets with ``render_ready == True``."""
        return tuple(a for a in self.assets.values() if a.render_ready)

    def verify(self, *, repo_root: Path, check_hash: bool = False) -> list[str]:
        """Verify every render-ready asset against the filesystem.

        Checks performed:
          - File exists at ``repo_root / asset.path``
          - ffprobe-reported dimensions match ``width`` × ``height``
          - (optional) SHA-256 hash matches ``sha256`` field

        Returns a list of error strings; empty means clean.
        """
        errors: list[str] = []
        for asset in self.render_ready_assets():
            abs_path = asset.absolute_path(repo_root)
            if not abs_path.is_file():
                errors.append(f"asset_missing:{asset.asset_id}:{asset.path}")
                continue
            # Dimension check via ffprobe
            try:
                proc = subprocess.run(
                    [
                        "ffprobe",
                        "-v",
                        "error",
                        "-select_streams",
                        "v:0",
                        "-show_entries",
                        "stream=width,height",
                        "-of",
                        "json",
                        str(abs_path),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                stream = json.loads(proc.stdout)["streams"][0]
                w, h = int(stream["width"]), int(stream["height"])
                if w != asset.width or h != asset.height:
                    errors.append(
                        f"dimension_mismatch:{asset.asset_id}:"
                        f"expected {asset.width}x{asset.height}, got {w}x{h}"
                    )
            except Exception as exc:
                errors.append(f"ffprobe_error:{asset.asset_id}:{exc}")
            # Hash check (optional, slow on large files)
            if check_hash and asset.sha256:
                try:
                    actual = hashlib.sha256(abs_path.read_bytes()).hexdigest()
                    if actual != asset.sha256:
                        errors.append(f"hash_mismatch:{asset.asset_id}")
                except Exception as exc:
                    errors.append(f"hash_error:{asset.asset_id}:{exc}")
        return errors


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_STYLE_PROPS = (
    "schema_version",
    "brand_identity",
    "character_rules",
    "color_rules",
    "pose_rules",
    "forbidden_rules",
    "quality_checks",
)
_IP_PROPS = (
    "must_have",
    "character_must_perform_core_action",
    "min_whitespace_ratio",
    "max_subject_ratio",
    "no_repeated_composition",
)
_PROV_PROPS = (
    "upstream_repo",
    "upstream_commit",
    "upstream_license",
    "local_path",
    "content_kind",
)


def _make_style_profile(d: dict) -> StyleProfile:
    sd = {k: d[k] for k in _STYLE_PROPS}
    sd["brand_identity"] = dict(sd["brand_identity"])
    sd["character_rules"] = dict(sd["character_rules"])
    sd["color_rules"] = dict(sd["color_rules"])
    sd["pose_rules"] = dict(sd["pose_rules"])
    sd["forbidden_rules"] = tuple(sd["forbidden_rules"])
    sd["quality_checks"] = tuple(dict(item) for item in sd["quality_checks"])
    return StyleProfile(**sd)


_STYLE_REQUIRED = frozenset(_STYLE_PROPS)


def _invalid_registry(message: str, context: dict[str, Any]) -> FactoryContractError:
    return FactoryContractError("asset_registry_invalid", message, context)


def _resolve_repo_relative(repo_root: Path, reference: str, *, field: str) -> Path:
    """Resolve a registry reference without allowing traversal or reparse escape."""
    if not isinstance(reference, str) or not reference:
        raise _invalid_registry("Registry reference must be a non-empty relative path.", {"field": field})
    if "\\" in reference or reference.startswith("/") or Path(reference).drive:
        raise _invalid_registry("Registry reference must use a relative POSIX path.", {"field": field})
    pure = PurePosixPath(reference)
    if any(part in ("", ".", "..") for part in pure.parts):
        raise _invalid_registry("Registry reference contains an unsafe path segment.", {"field": field})
    root = Path(repo_root).resolve()
    candidate = (root / Path(*pure.parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise _invalid_registry("Registry reference escapes the repository root.", {"field": field}) from exc
    return candidate


def _load_style_profile(path: Path) -> StyleProfile:
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _invalid_registry("Pink Pig style profile could not be read.", {"field": "style_profile_ref"}) from exc
    if not isinstance(profile, dict):
        raise _invalid_registry("Pink Pig style profile must be an object.", {"field": "style_profile"})
    missing = sorted(_STYLE_REQUIRED - set(profile))
    if missing:
        raise _invalid_registry("Pink Pig style profile is missing required sections.", {"field": missing[0]})
    if not isinstance(profile["forbidden_rules"], list) or not all(
        isinstance(item, str) and item for item in profile["forbidden_rules"]
    ):
        raise _invalid_registry("Pink Pig forbidden rules must be non-empty strings.", {"field": "forbidden_rules"})
    if not isinstance(profile["quality_checks"], list):
        raise _invalid_registry("Pink Pig quality checks must be an array.", {"field": "quality_checks"})
    for index, check in enumerate(profile["quality_checks"]):
        if not isinstance(check, dict) or not {"check_id", "required", "mode", "description"}.issubset(check):
            raise _invalid_registry("Pink Pig quality check has an invalid shape.", {"field": f"quality_checks.{index}"})
    return _make_style_profile(profile)


def _make_ip_constraints(d: dict) -> IpConstraints:
    id_ = {k: d[k] for k in _IP_PROPS}
    id_["must_have"] = tuple(id_["must_have"])
    return IpConstraints(**id_)


def _make_provenance(d: dict) -> Provenance:
    pd = {k: d[k] for k in _PROV_PROPS}
    return Provenance(**pd)


def _make_asset(d: dict) -> PinkPigAsset:
    ad = {
        "asset_id": d["asset_id"],
        "pose": d["pose"],
        "moods": tuple(d.get("moods", [])),
        "path": d.get("path"),
        "source_svg": d.get("source_svg"),
        "width": d["width"],
        "height": d["height"],
        "render_ready": d["render_ready"],
        "sha256": d.get("sha256", ""),
        "pose_confidence": d.get("pose_confidence", "assigned_by_order"),
        "tags": tuple(d.get("tags", [])),
        "fallback_asset_id": d.get("fallback_asset_id"),
    }
    return PinkPigAsset(**ad)


# ---------------------------------------------------------------------------
# Public factory function
# ---------------------------------------------------------------------------

def load_registry(path: Path | None = None, *, repo_root: Path | None = None) -> PinkPigRegistry:
    """Load, validate, and return a :class:`PinkPigRegistry`.

    Parameters
    ----------
    path : Path | None
        Path to ``registry.json``. Defaults to the module's co-located file.
    repo_root : Path | None
        Repository root (used only for documentation; verification requires
        explicit ``verify()`` call with this value).

    Returns
    -------
    PinkPigRegistry
    """
    if path is None:
        path = REGISTRY_PATH
    path = Path(path)
    if not path.is_file():
        raise RegistryError(f"registry_file_missing:{path}")

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise _invalid_registry("Pink Pig asset registry could not be read.", {"field": "registry"}) from exc

    if repo_root is None:
        repo_root = REGISTRY_PATH.parents[4]
    repo_root = Path(repo_root).resolve()

    # Validate against schema when available. Schema errors are contract failures;
    # they must not be swallowed because the registry is an IP safety boundary.
    if is_available():
        _validate(raw, "pink_pig_registry")

    style_path = _resolve_repo_relative(repo_root, raw["style_profile_ref"], field="style_profile_ref")
    if not style_path.is_file():
        raise _invalid_registry("Pink Pig style profile reference does not exist.", {"field": "style_profile_ref"})
    style_profile = _load_style_profile(style_path)

    # Build sub-objects
    char = raw["character"]
    prov = _make_provenance(raw["provenance"])
    sp = style_profile
    ic = _make_ip_constraints(raw["ip_constraints"])

    assets_map: dict[str, PinkPigAsset] = {}
    for ad in raw.get("assets", []):
        asset = _make_asset(ad)
        assets_map[asset.asset_id] = asset

    registry = PinkPigRegistry(
        schema_version=raw.get("schema_version", "1.0"),
        registry_version=raw.get("registry_version", "1.0.0"),
        character_id=char["character_id"],
        style_profile=sp,
        ip_constraints=ic,
        provenance=prov,
        assets=assets_map,
        pose_index=dict(raw.get("pose_index", {})),
        mood_index=dict(raw.get("mood_index", {})),
        default_asset_id=raw.get("default_asset_id", ""),
    )
    return registry
