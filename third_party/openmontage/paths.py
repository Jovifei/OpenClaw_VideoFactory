# Source: derived from https://github.com/calesthio/OpenMontage/tree/cd9f3c1f03368be87b140af494914b8ee4e3c7a4/lib/paths.py
# Modified: minimal bounded paths for the vendored subset; no environment or global workspace discovery.
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PACKAGE_ROOT.parents[1]
PROJECTS_DIR = REPO_ROOT / "dist" / "openmontage_projection"
