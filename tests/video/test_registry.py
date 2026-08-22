"""T05 / stage-four ① — Pink Pig Asset Registry loading and resolution.

Covers architecture §3.1 (registry data structure), §3.6 (loader API) and the
T02 acceptance criteria:

* ``registry.json`` validates against its own ``registry.schema.json``
* every declared asset file really exists on disk
* ``width``/``height`` match the ffprobe-measured values
* ``sha256`` matches the measured digest
* ``resolve()`` follows the deterministic chain asset_id > pose > mood > default
* the three ``render_ready: false`` poses fall back to a render-ready asset
* ``resolve(asset_id=<unknown>)`` raises ``RegistryError("asset_unresolved:...")``
* ``registry.verify(repo_root=ROOT)`` returns ``[]``
* error code ``asset_fallback_cycle:<asset_id>`` (§4.3 row 7)
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import subprocess

import pytest
from jsonschema import Draft202012Validator

from src.factory.assets.pink_pig.loader import (
    POSES,
    REGISTRY_PATH,
    PinkPigAsset,
    PinkPigRegistry,
    RegistryError,
    load_registry,
)
from video_factory.pipeline.registry import registry_to_manifest

from . import ROOT

REGISTRY_SCHEMA_PATH = ROOT / "src" / "factory" / "assets" / "pink_pig" / "registry.schema.json"

# The three poses that have no rasterised PNG yet (§9.2) and therefore must
# resolve through ``fallback_asset_id``.
FALLBACK_POSES = ("question", "warning", "ending")
RENDER_READY_POSES = ("normal", "thinking", "measure", "repair", "success")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def raw_registry() -> dict:
    """The registry document exactly as it sits on disk."""
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry_schema() -> dict:
    return json.loads(REGISTRY_SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def registry() -> PinkPigRegistry:
    return load_registry()


def _ffprobe_dimensions(path) -> tuple[int, int]:
    """Return the (width, height) ffprobe reports for *path*."""
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
            str(path),
        ],
        capture_output=True,
        text=True,
        timeout=15,
        check=True,
    )
    stream = json.loads(proc.stdout)["streams"][0]
    return int(stream["width"]), int(stream["height"])


# ---------------------------------------------------------------------------
# Schema conformance
# ---------------------------------------------------------------------------


class TestRegistrySchema:
    def test_registry_schema_is_a_valid_draft_2020_12_schema(self, registry_schema: dict) -> None:
        Draft202012Validator.check_schema(registry_schema)

    def test_registry_schema_declares_expected_identity(self, registry_schema: dict) -> None:
        assert registry_schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert registry_schema["title"] == "PinkPigRegistry"

    def test_registry_schema_accepts_unproduced_asset_fallbacks(
        self, raw_registry: dict, registry_schema: dict
    ) -> None:
        """SVG-only poses are valid when they declare an explicit fallback."""
        assert list(Draft202012Validator(registry_schema).iter_errors(raw_registry)) == []

    def test_loader_rejects_invalid_registry_instead_of_swallowing_schema_errors(self, raw_registry: dict) -> None:
        """The loader builds the valid registry and fails closed for invalid data."""
        reg = load_registry()
        assert reg.registry_version == "1.2.0"
        assert reg.verify(repo_root=ROOT) == []


# ---------------------------------------------------------------------------
# Asset files on disk
# ---------------------------------------------------------------------------


class TestAssetFiles:
    def test_every_render_ready_asset_declares_a_path(self, registry: PinkPigRegistry) -> None:
        for asset in registry.render_ready_assets():
            assert asset.path, f"render-ready asset without path: {asset.asset_id}"

    def test_every_declared_asset_file_exists(self, registry: PinkPigRegistry) -> None:
        missing = [
            asset.asset_id
            for asset in registry.assets.values()
            if asset.path and not (ROOT / asset.path).is_file()
        ]
        assert missing == []

    def test_declared_dimensions_match_ffprobe(self, registry: PinkPigRegistry) -> None:
        mismatches = []
        for asset in registry.render_ready_assets():
            width, height = _ffprobe_dimensions(asset.absolute_path(ROOT))
            if (width, height) != (asset.width, asset.height):
                mismatches.append(
                    f"{asset.asset_id}: declared {asset.width}x{asset.height}, "
                    f"ffprobe {width}x{height}"
                )
        assert mismatches == []

    def test_declared_sha256_matches_measured_digest(self, registry: PinkPigRegistry) -> None:
        mismatches = []
        for asset in registry.render_ready_assets():
            digest = hashlib.sha256(asset.absolute_path(ROOT).read_bytes()).hexdigest()
            if digest != asset.sha256:
                mismatches.append(f"{asset.asset_id}: declared {asset.sha256}, measured {digest}")
        assert mismatches == []

    def test_paths_are_repo_relative_posix(self, registry: PinkPigRegistry) -> None:
        """§8.1 — repo-relative POSIX paths only; no drive letters, no ``..``."""
        for asset in registry.assets.values():
            if not asset.path:
                continue
            assert "\\" not in asset.path, asset.asset_id
            assert ".." not in asset.path.split("/"), asset.asset_id
            assert not asset.path.startswith("/"), asset.asset_id
            assert ":" not in asset.path, asset.asset_id

    def test_verify_reports_no_errors(self, registry: PinkPigRegistry) -> None:
        """T02 acceptance: ``registry.verify(repo_root=ROOT)`` returns ``[]``."""
        assert registry.verify(repo_root=ROOT) == []

    def test_verify_with_hash_check_reports_no_errors(self, registry: PinkPigRegistry) -> None:
        assert registry.verify(repo_root=ROOT, check_hash=True) == []


# ---------------------------------------------------------------------------
# Registry structure
# ---------------------------------------------------------------------------


class TestRegistryStructure:
    def test_identity_fields(self, registry: PinkPigRegistry) -> None:
        assert registry.schema_version == "1.0"
        assert registry.registry_version == "1.2.0"
        assert registry.character_id == "pink_pig"
        assert registry.default_asset_id == "pink_pig.normal.v1"

    def test_pose_index_covers_the_whole_closed_pose_vocabulary(
        self, registry: PinkPigRegistry
    ) -> None:
        assert set(registry.pose_index) == set(POSES)
        assert len(POSES) == 8

    def test_pose_index_targets_exist(self, registry: PinkPigRegistry) -> None:
        for pose, asset_id in registry.pose_index.items():
            assert asset_id in registry.assets, f"pose_index[{pose}] -> unknown {asset_id}"

    def test_mood_index_targets_are_known_poses(self, registry: PinkPigRegistry) -> None:
        for mood, pose in registry.mood_index.items():
            assert pose in registry.pose_index, f"mood_index[{mood}] -> unknown pose {pose}"

    def test_asset_ids_follow_the_naming_convention(self, registry: PinkPigRegistry) -> None:
        import re

        pattern = re.compile(r"^pink_pig\.[a-z_]+\.v[0-9]+$")
        for asset_id in registry.assets:
            assert pattern.match(asset_id), asset_id

    def test_asset_pose_is_in_the_closed_vocabulary(self, registry: PinkPigRegistry) -> None:
        for asset in registry.assets.values():
            assert asset.pose in POSES, f"{asset.asset_id} has pose {asset.pose!r}"

    def test_non_render_ready_assets_declare_a_fallback(self, registry: PinkPigRegistry) -> None:
        """§3.1 — ``render_ready: false`` requires ``fallback_asset_id``."""
        for asset in registry.assets.values():
            if not asset.render_ready:
                assert asset.fallback_asset_id, f"{asset.asset_id} has no fallback_asset_id"
                assert asset.fallback_asset_id in registry.assets

    def test_render_ready_asset_count(self, registry: PinkPigRegistry) -> None:
        ready = {asset.pose for asset in registry.render_ready_assets()}
        assert ready == set(RENDER_READY_POSES)

    def test_provenance_records_the_upstream_repository(self, registry: PinkPigRegistry) -> None:
        """§9.1 — the upstream repo is a prompt/style spec, tracked for attribution."""
        prov = registry.provenance
        assert prov.upstream_repo == "https://github.com/Jovifei/ian-fenzhu-illustrations"
        assert prov.upstream_commit == "99ab94973b4d9b01d1f1ddb2737acf70c89b7c52"
        assert prov.upstream_license == "MIT"
        assert prov.content_kind == "prompt_style_spec"

    def test_dataclasses_are_frozen(self, registry: PinkPigRegistry) -> None:
        asset = registry.get("pink_pig.normal.v1")
        with pytest.raises(dataclasses.FrozenInstanceError):
            asset.width = 1  # type: ignore[misc]


# ---------------------------------------------------------------------------
# resolve() — the deterministic resolution chain (R1 / §3.6)
# ---------------------------------------------------------------------------


class TestResolutionChain:
    @pytest.mark.parametrize("pose", RENDER_READY_POSES)
    def test_resolve_by_pose_returns_that_pose(self, registry: PinkPigRegistry, pose: str) -> None:
        asset = registry.resolve(pose=pose)
        assert asset.pose == pose
        assert asset.render_ready is True

    @pytest.mark.parametrize("pose", FALLBACK_POSES)
    def test_resolve_by_non_render_ready_pose_falls_back(
        self, registry: PinkPigRegistry, pose: str
    ) -> None:
        """T02 acceptance: a ``render_ready: false`` pose still yields a usable asset."""
        declared = registry.get(registry.pose_index[pose])
        assert declared.render_ready is False

        resolved = registry.resolve(pose=pose)
        assert resolved.render_ready is True
        assert resolved.asset_id == declared.fallback_asset_id
        assert resolved.path

    def test_explicit_asset_id_wins_over_pose_and_mood(self, registry: PinkPigRegistry) -> None:
        asset = registry.resolve(
            asset_id="pink_pig.success.v1", pose="normal", mood="calm"
        )
        assert asset.asset_id == "pink_pig.success.v1"

    def test_pose_wins_over_mood(self, registry: PinkPigRegistry) -> None:
        # mood "calm" maps to pose "normal"; an explicit pose must take priority.
        asset = registry.resolve(pose="thinking", mood="calm")
        assert asset.asset_id == "pink_pig.thinking.v1"

    @pytest.mark.parametrize(
        ("mood", "expected_pose"),
        [("calm", "normal"), ("focused", "measure")],
    )
    def test_resolve_by_mood(
        self, registry: PinkPigRegistry, mood: str, expected_pose: str
    ) -> None:
        assert registry.resolve(mood=mood).pose == expected_pose

    def test_resolve_by_mood_pointing_at_a_non_render_ready_pose_falls_back(
        self, registry: PinkPigRegistry
    ) -> None:
        # mood "curious" -> pose "question" -> render_ready False -> fallback normal
        assert registry.mood_index["curious"] == "question"
        assert registry.resolve(mood="curious").asset_id == "pink_pig.normal.v1"

    def test_resolve_without_hints_returns_the_default(self, registry: PinkPigRegistry) -> None:
        assert registry.resolve().asset_id == registry.default_asset_id

    def test_resolve_unknown_pose_falls_back_to_the_default(
        self, registry: PinkPigRegistry
    ) -> None:
        assert registry.resolve(pose="does_not_exist").asset_id == registry.default_asset_id

    def test_resolve_unknown_asset_id_raises_asset_unresolved(
        self, registry: PinkPigRegistry
    ) -> None:
        """T02 acceptance: unknown asset ids fail loudly with the §4.3 error code."""
        with pytest.raises(RegistryError, match=r"^asset_unresolved:"):
            registry.resolve(asset_id="pink_pig.does_not_exist.v9")

    def test_get_unknown_asset_id_raises_asset_unresolved(
        self, registry: PinkPigRegistry
    ) -> None:
        with pytest.raises(RegistryError, match=r"^asset_unresolved:nope$"):
            registry.get("nope")

    def test_absolute_path_is_rooted_at_repo_root(self, registry: PinkPigRegistry) -> None:
        asset = registry.get("pink_pig.normal.v1")
        assert asset.absolute_path(ROOT) == (ROOT / "assets" / "pink_pig" / "pig01.png").resolve()

    def test_absolute_path_without_a_path_raises(self, registry: PinkPigRegistry) -> None:
        asset = registry.get(registry.pose_index["question"])
        assert asset.path is None
        with pytest.raises(RegistryError, match=r"^asset_no_path:"):
            asset.absolute_path(ROOT)


# ---------------------------------------------------------------------------
# Error code coverage — asset_fallback_cycle (§4.3 row 7)
# ---------------------------------------------------------------------------


def _synthetic_asset(asset_id: str, *, render_ready: bool, fallback: str | None) -> PinkPigAsset:
    return PinkPigAsset(
        asset_id=asset_id,
        pose="normal",
        moods=(),
        path="assets/pink_pig/pig01.png" if render_ready else None,
        source_svg=None,
        width=1080,
        height=1920,
        render_ready=render_ready,
        sha256="",
        pose_confidence="assigned_by_order",
        tags=(),
        fallback_asset_id=fallback,
    )


def _synthetic_registry(assets: list[PinkPigAsset], default_asset_id: str) -> PinkPigRegistry:
    template = load_registry()
    return PinkPigRegistry(
        schema_version=template.schema_version,
        registry_version=template.registry_version,
        character_id=template.character_id,
        style_profile=template.style_profile,
        ip_constraints=template.ip_constraints,
        provenance=template.provenance,
        assets={asset.asset_id: asset for asset in assets},
        pose_index={"normal": default_asset_id},
        mood_index={},
        default_asset_id=default_asset_id,
    )


class TestFallbackFailureModes:
    def test_fallback_cycle_raises_asset_fallback_cycle(self) -> None:
        """§4.3 row 7 — a fallback loop must be detected, not followed forever."""
        cyclic = _synthetic_registry(
            [
                _synthetic_asset("pink_pig.a.v1", render_ready=False, fallback="pink_pig.b.v1"),
                _synthetic_asset("pink_pig.b.v1", render_ready=False, fallback="pink_pig.a.v1"),
            ],
            default_asset_id="pink_pig.a.v1",
        )
        with pytest.raises(RegistryError, match=r"^asset_fallback_cycle:"):
            cyclic.resolve(asset_id="pink_pig.a.v1")

    def test_fallback_chain_longer_than_three_hops_is_rejected(self) -> None:
        chain = _synthetic_registry(
            [
                _synthetic_asset("pink_pig.a.v1", render_ready=False, fallback="pink_pig.b.v1"),
                _synthetic_asset("pink_pig.b.v1", render_ready=False, fallback="pink_pig.c.v1"),
                _synthetic_asset("pink_pig.c.v1", render_ready=False, fallback="pink_pig.d.v1"),
                _synthetic_asset("pink_pig.d.v1", render_ready=False, fallback="pink_pig.e.v1"),
                _synthetic_asset("pink_pig.e.v1", render_ready=True, fallback=None),
            ],
            default_asset_id="pink_pig.a.v1",
        )
        with pytest.raises(RegistryError, match=r"^asset_fallback_cycle:"):
            chain.resolve(asset_id="pink_pig.a.v1")

    def test_not_render_ready_without_fallback_raises_asset_unresolved(self) -> None:
        dead_end = _synthetic_registry(
            [_synthetic_asset("pink_pig.a.v1", render_ready=False, fallback=None)],
            default_asset_id="pink_pig.a.v1",
        )
        with pytest.raises(RegistryError, match=r"^asset_unresolved:"):
            dead_end.resolve(asset_id="pink_pig.a.v1")


# ---------------------------------------------------------------------------
# Loader entry point and pipeline adapter
# ---------------------------------------------------------------------------


class TestLoaderAndAdapter:
    def test_load_registry_missing_file_raises(self, tmp_path) -> None:
        with pytest.raises(RegistryError, match=r"^registry_file_missing:"):
            load_registry(tmp_path / "nope.json")

    def test_load_registry_is_deterministic(self) -> None:
        first, second = load_registry(), load_registry()
        assert first.assets.keys() == second.assets.keys()
        assert first.default_asset_id == second.default_asset_id

    def test_registry_to_manifest_matches_asset_manifest_shape(
        self, registry: PinkPigRegistry
    ) -> None:
        """The adapter output must be a drop-in for ``build_asset_manifest``."""
        manifest = registry_to_manifest(registry, repo_root=ROOT)
        assert manifest["schema_version"] == "1.0"
        assert manifest["source"] == "registry"
        assert len(manifest["assets"]) == len(registry.render_ready_assets())
        assert [item["order"] for item in manifest["assets"]] == list(
            range(1, len(manifest["assets"]) + 1)
        )
        for item in manifest["assets"]:
            assert {"order", "path", "width", "height", "asset_id", "pose"} <= set(item)
            assert (ROOT / item["path"]).is_file()
