"""Secret-safe OpenClaw RPC credential providers.

Providers return a token only to the RPC client.  This module never serializes,
logs, hashes, or places a credential on a command line.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping, Sequence

TokenProvider = Callable[[], str | None]
TOKEN_ENVIRONMENT_VARIABLE = "OPENCLAW_GATEWAY_TOKEN"


def environment_token_provider(
    environ: Mapping[str, str] | None = None,
    *,
    variable: str = TOKEN_ENVIRONMENT_VARIABLE,
) -> TokenProvider:
    """Return a lazy provider backed by an inherited process environment."""
    source = os.environ if environ is None else environ

    def provide() -> str | None:
        value = source.get(variable)
        if not isinstance(value, str):
            return None
        value = value.strip()
        return value or None

    return provide


def chained_token_provider(providers: Sequence[TokenProvider]) -> TokenProvider:
    """Use the first non-empty provider without exposing which token was read."""
    provider_list = tuple(providers)

    def provide() -> str | None:
        for provider in provider_list:
            value = provider()
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None

    return provide
