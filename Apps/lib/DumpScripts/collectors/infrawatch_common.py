"""Shared utilities for InfraWatch collectors.

All collectors are stdlib-only — no pip dependencies required.
Runs on any machine with Python 3.x.
"""

import json
import os
import socket
import urllib.request

INFRAWATCH_BASE = "https://infrawatch-one.vercel.app/infra/api/ingest"
ERRORDUMP_URL = "https://error-dump-ennead-projects.vercel.app/error-dump/api/ingest"
# Write-only key for InfraWatch metrics — no sensitive data access.
# Hardcoded because EA_Dist machines can't read env vars from network.
API_KEY = "03f95bfdca109614860d330bbf67394af808381e81efb1da"


def post_to_infrawatch(endpoint, payload):
    """POST JSON to an InfraWatch ingest endpoint. Returns True on success."""
    url = "{}/{}".format(INFRAWATCH_BASE, endpoint)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": API_KEY,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception:
        return False


def report_error(func_name, error_msg):
    """Silently report failure to ErrorDump. Never raises."""
    try:
        data = json.dumps({
            "source_app": "EnneadTab-OS",
            "environment": "terminal",
            "error_message": str(error_msg)[:5000],
            "function_name": func_name,
            "user_name": os.environ.get("USERNAME", "Unknown"),
            "machine_name": socket.gethostname(),
            "context": {"is_silent": True, "collector": "infrawatch"},
        }).encode("utf-8")
        req = urllib.request.Request(
            ERRORDUMP_URL,
            data=data,
            headers={"Content-Type": "application/json"},
        )
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # Truly silent — if ErrorDump fails, nothing happens


def get_machine_name():
    return socket.gethostname()


def get_username():
    return os.environ.get("USERNAME", "Unknown")
