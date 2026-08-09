"""Registry adapter layer: bridges ``PinkPigRegistry`` into the pipeline.

This module isolates the ``src.factory`` dependency so that the rest of
``video_factory/pipeline/`` only deals with plain dicts (the same shape as
``build_asset_manifest`` output).

Public API (§3.7):
  - :func:`load_pink_pig_registry` — convenience loader
  - :func:`registry_to_manifest` — convert registry → pipeline-internal manifest
"""

from __future__ import annotations

from pathlib import Path


def load_pink_pig_registry(repo_root: Path | None = None):
    """Load the Pink Pig registry from its canonical location.

    Parameters
    ----------
    repo_root : Path | None
        Repository root path. Passed through to ``verify()`` if needed.

    Returns
    -------
    PinkPigRegistry
        The loaded and validated registry.
    """
    from src.factory.assets.pink_pig.loader import load_registry

    reg = load_registry(repo_root=repo_root)
    # Run verification (non-hash, just existence + dimensions)
    if repo_root is not None:
        errors = reg.verify(repo_root=repo_root, check_hash=False)
        if errors:
            raise ValueError(f"registry_verify_failed:{';'.join(errors[:5])}")
    return reg


def registry_to_manifest(registry, *, repo_root: Path) -> dict:
    """Convert a ``PinkPigRegistry`` into a pipeline-compatible asset manifest.

    The returned dict has the same top-level keys as
    ``asset_loader.build_asset_manifest()`` output (``schema_version``,
    ``assets[]`` with ``order/path/width/height``), making it a drop-in
    replacement for directory-scanned manifests.
    """
    assets_list = []
    for idx, asset in enumerate(registry.render_ready_assets(), start=1):
        assets_list.append(
            {
                "order": idx,
                "path": asset.path or "",
                "width": asset.width,
                "height": asset.height,
                "asset_id": asset.asset_id,
                "pose": asset.pose,
            }
        )
    return {
        "schema_version": "1.0",
        "asset_directory": "pink_pig_registry",
        "source": "registry",
        "assets": assets_list,
    }
