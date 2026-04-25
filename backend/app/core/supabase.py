"""Supabase client singleton.

Always uses the service role key (server-side only). Writes bypass RLS.
Returns ``None`` when Supabase is not configured so callers can gracefully
skip persistence during local development.
"""

from __future__ import annotations

import threading
from typing import Optional

from . import config

try:
    from supabase import Client, create_client
except ImportError:  # pragma: no cover — dep may be absent in unit tests
    Client = None  # type: ignore[assignment,misc]

    def create_client(*_args, **_kwargs):  # type: ignore[no-redef]
        raise RuntimeError("supabase package not installed")


_client: Optional["Client"] = None
_lock = threading.Lock()


def get_client() -> Optional["Client"]:
    """Return a cached Supabase client, or ``None`` if not configured."""
    global _client
    if not config.supabase_configured():
        return None
    if _client is not None:
        return _client
    with _lock:
        if _client is None:
            _client = create_client(
                config.SUPABASE_URL,
                config.SUPABASE_SERVICE_ROLE_KEY,
            )
    return _client


def reset_client() -> None:
    """Testing hook — clear the cached client."""
    global _client
    with _lock:
        _client = None
