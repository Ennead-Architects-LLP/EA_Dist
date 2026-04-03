"""Fire-and-forget error reporter that POSTs to ErrorHub."""

from __future__ import annotations

import traceback
from typing import Any

import httpx

_INGEST_URL = "https://error-dump-ennead-projects.vercel.app/error-dump/api/ingest"
_TIMEOUT = 5.0  # seconds


def report_error(
    error: BaseException | str,
    *,
    extra: dict[str, Any] | None = None,
) -> None:
    """Send an error report to ErrorHub.

    This is intentionally fire-and-forget: it never raises and silently
    swallows any network or serialisation failures so that the MCP server
    can keep running.

    Parameters
    ----------
    error:
        The exception instance or a plain error message string.
    extra:
        Optional dictionary of additional context merged into the payload.
    """
    try:
        if isinstance(error, BaseException):
            message = str(error)
            tb = traceback.format_exception(type(error), error, error.__traceback__)
            stack = "".join(tb)
        else:
            message = error
            stack = ""

        payload: dict[str, Any] = {
            "source_app": "EnneadTab-MCP",
            "environment": "mcp-server",
            "error_message": message,
            "traceback": stack,
        }
        if extra:
            payload.update(extra)

        httpx.post(_INGEST_URL, json=payload, timeout=_TIMEOUT)
    except Exception:  # noqa: BLE001 — intentionally broad
        pass
