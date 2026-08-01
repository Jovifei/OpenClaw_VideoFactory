from __future__ import annotations
from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
errors: list[str] = []
warnings: list[str] = []

try:
    import yaml
except Exception:
    yaml = None
    errors.append("PyYAML is required to validate YAML and SKILL frontmatter.")


def check_json(path: Path) -> None:
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid JSON {path}: {exc}")


def check_yaml(path: Path) -> None:
    if yaml is None:
        return
    try:
        yaml.safe_load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        errors.append(f"Invalid YAML {path}: {exc}")


for path in ROOT.rglob("*.json"):
    if "reports" not in path.parts:
        check_json(path)

for path in ROOT.rglob("*.yaml"):
    check_yaml(path)

for path in ROOT.glob("skills/*/SKILL.md"):
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        errors.append(f"Missing frontmatter: {path}")
        continue
    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append(f"Broken frontmatter: {path}")
        continue
    if yaml:
        try:
            meta = yaml.safe_load(parts[1])
            for key in ("name", "description"):
                if not meta or not meta.get(key):
                    errors.append(f"Missing {key} in {path}")
            oc = ((meta or {}).get("metadata") or {}).get("openclaw") or {}
            if "envVars" in oc:
                warnings.append(
                    f"Unsupported metadata.openclaw.envVars in {path}; use requires.env/config."
                )
        except Exception as exc:
            errors.append(f"Invalid frontmatter {path}: {exc}")

secret_patterns = [
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
    re.compile(r"\b\d{9,}:[A-Za-z0-9_-]{20,}\b"),
]
for path in ROOT.rglob("*"):
    if not path.is_file() or path.suffix.lower() in {
        ".png",
        ".jpg",
        ".jpeg",
        ".mp4",
        ".wav",
        ".zip",
    }:
        continue
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        continue
    for pat in secret_patterns:
        if pat.search(text):
            errors.append(f"Possible secret pattern in {path}")

factory = ROOT / "scripts" / "factory.py"
if factory.exists():
    text = factory.read_text(encoding="utf-8")
    if "Placeholder candidate set" in text:
        warnings.append("scripts/factory.py still contains placeholder candidate topics.")
    if "Scaffold ready" in text:
        warnings.append("scripts/factory.py run command is still a scaffold, not a real pipeline.")

print("Handoff validation")
print("==================")
for w in warnings:
    print("WARNING:", w)
for e in errors:
    print("ERROR:", e)
print(f"Warnings: {len(warnings)}")
print(f"Errors: {len(errors)}")
sys.exit(1 if errors else 0)
