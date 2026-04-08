"""Shared utilities for InfraWatch collectors.

All collectors are stdlib-only — no pip dependencies required.
Runs on any machine with Python 3.x.
"""

import json
import os
import socket
import sys
import urllib.request

INFRAWATCH_BASE = "https://infrawatch-one.vercel.app/infra/api/ingest"
# 2026-04-08: skipTrailingSlashRedirect fixed on ErrorDump, but keep
# trailing slash for backwards compat with older deployments
ERRORDUMP_URL = "https://error-dump-ennead-projects.vercel.app/error-dump/api/ingest/"

# Local failure counter — survives within a single collect_all run.
# If ErrorDump itself is down, at least stderr shows something.
_error_dump_failures = 0


def post_to_infrawatch(endpoint, payload):
    """POST JSON to an InfraWatch ingest endpoint. Returns True on success."""
    url = "{}/{}".format(INFRAWATCH_BASE, endpoint)
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status == 200
    except Exception:
        return False


def report_error(func_name, error_msg):
    """Report failure to ErrorDump. Never raises, but logs to stderr on failure."""
    global _error_dump_failures
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
        _error_dump_failures = 0  # reset on success
    except Exception as e:
        _error_dump_failures += 1
        # 2026-04-08: bare except:pass hid months of ErrorDump failures.
        # Log to stderr so at least scheduled-task logs capture it.
        print("[infrawatch] ErrorDump report failed ({}x): {}".format(
            _error_dump_failures, e), file=sys.stderr)


def get_machine_name():
    return socket.gethostname()


def get_username():
    return os.environ.get("USERNAME", "Unknown")
