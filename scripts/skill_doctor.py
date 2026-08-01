from __future__ import annotations
from pathlib import Path
import json, shutil, socket, subprocess, urllib.request

ROOT = Path(__file__).resolve().parents[1]


def command(name: str):
    return shutil.which(name)


def port_open(host: str, port: int, timeout=0.4):
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def nvidia():
    try:
        p = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
            capture_output=True,
            text=True,
            timeout=8,
        )
        return p.stdout.strip() if p.returncode == 0 else False
    except Exception:
        return False


def main():
    external = ROOT / "external"
    report = {
        "commands": {
            x: bool(command(x))
            for x in [
                "python",
                "node",
                "npm",
                "ffmpeg",
                "ffprobe",
                "git",
                "openclaw",
                "codex",
                "lark-cli",
            ]
        },
        "gpu": nvidia(),
        "services": {
            "comfyui_8188": port_open("127.0.0.1", 8188),
            "capcut_mate_30000": port_open("127.0.0.1", 30000),
        },
        "external_repositories": {
            x: (external / x).exists()
            for x in [
                "remotion-skills",
                "video-podcast-maker",
                "comfyui-mcp",
                "capcut-mate",
                "jianying-editor-skill",
                "ian-fenzhu-illustrations",
            ]
        },
        "local_skills": sorted(p.parent.name for p in (ROOT / "skills").glob("*/SKILL.md")),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
