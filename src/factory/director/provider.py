"""Provider adapters for the local AI Director.

The Codex CLI adapter is intentionally a narrow read-only subprocess boundary.
It never receives repository write access, model/profile selection, credentials,
or arbitrary shell text.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Protocol, Sequence, runtime_checkable

from video_factory.pipeline.errors import FactoryContractError


@runtime_checkable
class DirectorProvider(Protocol):
    """Provider-neutral structured Draft generation contract."""

    def generate(
        self,
        *,
        prompt: str,
        output_schema: Path,
        timeout_seconds: int = 180,
    ) -> dict[str, object]:
        ...


def _safe_provider_error(code: str, message: str, **context: Any) -> FactoryContractError:
    safe_context = {
        key: value
        for key, value in context.items()
        if key in {"provider", "attempt", "exit_code", "reason", "limit", "schema", "validator"}
    }
    return FactoryContractError(code, message, safe_context)


class CodexCliDirectorProvider:
    """Generate one structured Draft through ``codex exec`` in read-only mode."""

    provider_name = "codex-cli"
    # The adapter does not run a version probe because the probe would add an
    # unbounded external command to the generation contract.  Callers may
    # inject the observed CLI version when they construct a provider.
    provider_version = "unknown"

    def __init__(
        self,
        *,
        executable: str | Sequence[str] = "codex",
        working_dir: Path | None = None,
        max_output_bytes: int = 256 * 1024,
    ) -> None:
        self.executable = executable
        self.working_dir = Path(working_dir).resolve() if working_dir is not None else None
        self.max_output_bytes = int(max_output_bytes)
        if self.max_output_bytes <= 0:
            raise ValueError("director_provider_limit_invalid")

    def _command_prefix(self) -> list[str]:
        if isinstance(self.executable, str):
            resolved = shutil.which(self.executable)
            if not resolved:
                raise _safe_provider_error(
                    "director_provider_unavailable",
                    "Codex CLI provider is unavailable.",
                    provider=self.provider_name,
                    reason="executable_missing",
                )
            return [resolved]
        values = [str(item) for item in self.executable]
        if not values:
            raise _safe_provider_error(
                "director_provider_unavailable",
                "Director provider command is empty.",
                provider=self.provider_name,
                reason="command_empty",
            )
        return values

    def _detect_version(self, command_prefix: list[str]) -> str:
        try:
            completed = subprocess.run(
                command_prefix + ["--version"],
                capture_output=True,
                text=True,
                shell=False,
                timeout=10,
                check=False,
            )
            if completed.returncode == 0:
                value = (getattr(completed, "stdout", "") or "").strip().splitlines()[0]
                if value:
                    return value[:128]
        except (OSError, subprocess.SubprocessError, IndexError):
            pass
        return "unknown"

    def generate(
        self,
        *,
        prompt: str,
        output_schema: Path,
        timeout_seconds: int = 180,
    ) -> dict[str, object]:
        if not isinstance(prompt, str) or not prompt:
            raise _safe_provider_error(
                "director_provider_failed",
                "Director provider prompt is empty.",
                provider=self.provider_name,
                reason="prompt_empty",
            )
        schema = Path(output_schema)
        if not schema.is_file():
            raise _safe_provider_error(
                "director_provider_unavailable",
                "Director Draft schema is unavailable.",
                provider=self.provider_name,
                reason="schema_missing",
            )
        if int(timeout_seconds) <= 0:
            raise _safe_provider_error(
                "director_provider_failed",
                "Director provider timeout must be positive.",
                provider=self.provider_name,
                reason="timeout_invalid",
            )

        sandbox = self.working_dir
        temporary_sandbox: tempfile.TemporaryDirectory[str] | None = None
        output_path: Path | None = None
        try:
            if sandbox is None:
                temporary_sandbox = tempfile.TemporaryDirectory(prefix="pink_pig_director_")
                sandbox = Path(temporary_sandbox.name).resolve()
            elif not sandbox.is_dir():
                raise _safe_provider_error(
                    "director_provider_unavailable",
                    "Director provider working directory is unavailable.",
                    provider=self.provider_name,
                    reason="working_dir_missing",
                )
            output_path = sandbox / "director_draft.json"
            if output_path.exists():
                raise _safe_provider_error(
                    "director_provider_unavailable",
                    "Director provider working directory is not empty.",
                    provider=self.provider_name,
                    reason="output_exists",
                )
            command_prefix = self._command_prefix()
            self.provider_version = self._detect_version(command_prefix)
            command = command_prefix + [
                "exec",
                "--ephemeral",
                "--sandbox",
                "read-only",
                "--skip-git-repo-check",
                "--ignore-user-config",
                "--color",
                "never",
                "--output-schema",
                str(schema),
                "--output-last-message",
                str(output_path),
                "-C",
                str(sandbox),
                "-",
            ]
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    capture_output=True,
                    text=True,
                    shell=False,
                    cwd=os.fspath(sandbox),
                    timeout=int(timeout_seconds),
                    check=False,
                )
            except FileNotFoundError as exc:
                raise _safe_provider_error(
                    "director_provider_unavailable",
                    "Codex CLI provider is unavailable.",
                    provider=self.provider_name,
                    reason="executable_missing",
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise _safe_provider_error(
                    "director_provider_timeout",
                    "Codex CLI Director provider timed out.",
                    provider=self.provider_name,
                    reason="timeout",
                ) from exc
            except OSError as exc:
                raise _safe_provider_error(
                    "director_provider_failed",
                    "Codex CLI provider process could not be started.",
                    provider=self.provider_name,
                    reason="process_start",
                ) from exc

            if completed.returncode != 0:
                raise _safe_provider_error(
                    "director_provider_failed",
                    "Codex CLI Director provider failed.",
                    provider=self.provider_name,
                    reason="nonzero_exit",
                    exit_code=int(completed.returncode),
                )
            try:
                if output_path.is_file():
                    raw = output_path.read_bytes()
                else:
                    raw = (completed.stdout or "").encode("utf-8", errors="replace")
            except OSError as exc:
                raise _safe_provider_error(
                    "director_output_invalid",
                    "Codex CLI Director output could not be read.",
                    provider=self.provider_name,
                    reason="output_read",
                ) from exc
            if len(raw) > self.max_output_bytes:
                raise _safe_provider_error(
                    "director_provider_failed",
                    "Codex CLI Director provider output exceeded the limit.",
                    provider=self.provider_name,
                    reason="output_too_large",
                    limit=self.max_output_bytes,
                )
            try:
                value = json.loads(raw.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise _safe_provider_error(
                    "director_output_invalid",
                    "Codex CLI Director output is not valid JSON.",
                    provider=self.provider_name,
                    reason="json_parse",
                ) from exc
            if not isinstance(value, dict):
                raise _safe_provider_error(
                    "director_output_invalid",
                    "Codex CLI Director output must be a JSON object.",
                    provider=self.provider_name,
                    reason="json_type",
                )
            return dict(value)
        finally:
            if output_path is not None:
                try:
                    output_path.unlink(missing_ok=True)
                except OSError:
                    # The temporary directory cleanup below remains the safety
                    # boundary; a caller-owned job directory is never removed.
                    pass
            if temporary_sandbox is not None:
                temporary_sandbox.cleanup()


__all__ = ["CodexCliDirectorProvider", "DirectorProvider"]
