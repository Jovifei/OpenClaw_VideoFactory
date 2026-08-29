"""Configure the vendored MoneyPrinterTurbo for the Phase 1 script drafter.

Writes the gitignored ``external/MoneyPrinterTurbo/config.toml`` so the LLM
drafter works against an OpenAI-compatible endpoint. Key material is read only
from the environment, piped stdin, or a key file — never from command-line
arguments — and is never echoed, logged, or written anywhere outside the
gitignored config file.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_MPT_ROOT = REPO_ROOT / "external" / "MoneyPrinterTurbo"

DEFAULT_BASE_URL = "https://token-plan-cn.xiaomimimo.com/v1"
DEFAULT_MODEL = "mimo-v2.5"
KEY_ENV_VARS = ("MPT_LLM_API_KEY", "MIMO_API_KEY")

LLM_SETTINGS = {
    "llm_provider": '"openai"',
    "openai_base_url": None,  # filled at runtime (quoted URL)
    "openai_model_name": None,  # filled at runtime (quoted model)
}


def _config_path(mpt_root: Path) -> Path:
    return mpt_root / "config.toml"


def _ensure_config_exists(mpt_root: Path) -> Path:
    path = _config_path(mpt_root)
    if not path.exists():
        example = mpt_root / "config.example.toml"
        if not example.exists():
            raise FileNotFoundError(f"no config.toml or config.example.toml under {mpt_root}")
        shutil.copyfile(example, path)
    return path


def _read_key(args: argparse.Namespace) -> str:
    if args.stdin:
        key = sys.stdin.read().strip()
        source = "stdin"
    elif args.key_file:
        key = Path(args.key_file).read_text(encoding="utf-8").strip()
        source = f"key file {args.key_file}"
    else:
        for name in KEY_ENV_VARS:
            value = os.environ.get(name, "").strip()
            if value:
                key = value
                source = f"env {name}"
                break
        else:
            raise ValueError(
                "no key found; set MPT_LLM_API_KEY/MIMO_API_KEY, pipe the key via --stdin, "
                "or pass --key-file (never paste keys into chat or command lines)"
            )
    if not key:
        raise ValueError(f"key from {source} is empty")
    print(f"[configure] key source: {source}")
    return key


def _apply_settings(text: str, settings: dict[str, str]) -> str:
    """Replace or insert top-level TOML keys; used by tests without secrets."""
    for name, value in settings.items():
        pattern = rf"^{re.escape(name)}\s*=.*$"
        replacement = f"{name} = {value}"
        if re.search(pattern, text, flags=re.M):
            text = re.sub(pattern, replacement, text, count=1, flags=re.M)
        else:
            text = text.rstrip("\n") + "\n" + replacement + "\n"
    return text


def write_config(
    mpt_root: Path,
    *,
    api_key: str,
    base_url: str = DEFAULT_BASE_URL,
    model_name: str = DEFAULT_MODEL,
) -> Path:
    path = _ensure_config_exists(mpt_root)
    text = path.read_text(encoding="utf-8")
    settings = {
        "llm_provider": '"openai"',
        "openai_api_key": json.dumps(api_key),
        "openai_base_url": json.dumps(base_url),
        "openai_model_name": json.dumps(model_name),
        "model_size": '"small"',
    }
    text = _apply_settings(text, settings)
    path.write_text(text, encoding="utf-8")
    print(f"[configure] wrote {path} (gitignored provider settings)")
    return path


def verify(base_url: str, model_name: str, api_key: str, timeout: float = 30.0) -> bool:
    """Minimal live chat completion probe; prints only status, never the key."""
    url = base_url.rstrip("/") + "/chat/completions"
    body = json.dumps(
        {
            "model": model_name,
            "max_tokens": 64,
            "messages": [{"role": "user", "content": "reply with OK"}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = response.status
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - report any failure as verification failure
        print(f"[configure] VERIFY FAILED: {type(exc).__name__}: {exc}")
        return False
    message = payload.get("choices", [{}])[0].get("message", {})
    # Reasoning models (mimo-v2.5) may spend the whole budget on thinking; a
    # populated reasoning_content with HTTP 200 still proves auth and serving.
    responded = bool(message.get("content") or message.get("reasoning_content"))
    print(f"[configure] VERIFY HTTP {status}, model responded: {responded}")
    return status == 200 and responded


def show_status(mpt_root: Path) -> None:
    path = _config_path(mpt_root)
    if not path.exists():
        print("[configure] status: config.toml does not exist")
        return
    text = path.read_text(encoding="utf-8")
    checks = {
        "llm_provider=openai": 'llm_provider = "openai"' in text,
        "base_url set": bool(re.search(r'^openai_base_url = "https?://.+"$', text, flags=re.M)),
        "model set": bool(re.search(r'^openai_model_name = ".+"$', text, flags=re.M)),
        "api_key set": bool(re.search(r'^openai_api_key = ".+"$', text, flags=re.M)),
        "whisper small": 'model_size = "small"' in text,
    }
    for name, ok in checks.items():
        print(f"[configure] {name}: {'yes' if ok else 'NO'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Configure gitignored MoneyPrinterTurbo settings for the script drafter.")
    parser.add_argument("--stdin", action="store_true", help="read the API key from piped stdin")
    parser.add_argument("--key-file", help="read the API key from a local file outside the repo")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--mpt-root", type=Path, default=DEFAULT_MPT_ROOT)
    parser.add_argument("--verify", action="store_true", help="run a live chat-completion probe after writing")
    parser.add_argument("--status-only", action="store_true", help="show which settings are present, then exit")
    args = parser.parse_args(argv)

    if args.status_only:
        show_status(args.mpt_root)
        return 0

    try:
        key = _read_key(args)
        write_config(args.mpt_root, api_key=key, base_url=args.base_url, model_name=args.model)
    except (FileNotFoundError, ValueError, OSError) as exc:
        print(f"[configure] FAILED: {exc}", file=sys.stderr)
        return 1

    if args.verify:
        ok = verify(args.base_url, args.model, key)
        if not ok:
            return 1
    show_status(args.mpt_root)
    print("[configure] OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
