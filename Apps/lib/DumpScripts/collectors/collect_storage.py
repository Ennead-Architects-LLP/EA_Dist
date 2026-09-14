"""Collect storage folder snapshots and POST to InfraWatch.

Stdlib-only — no pip dependencies.
Designed to run weekly on designated reporter machines (3-reporter pool).
Walks storage_watchlist.json, collects folder sizes/latencies, and posts
partial results (reporting any unavailable shares in shares_failed[]).

Usage:
    python collect_storage.py              # Live run (gated on reporter pool)
    python collect_storage.py --dry-run    # Preview snapshot without POSTing
    python collect_storage.py --force-run  # Run even if not in reporter pool
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from infrawatch_common import (
    get_machine_name,
    post_to_infrawatch_detailed,
    report_error,
)

CONFIG_FILENAME = "storage_watchlist.json"


def load_config(config_path=None):
    if config_path is None:
        here = os.path.dirname(os.path.abspath(__file__))
        config_path = os.path.join(here, CONFIG_FILENAME)
    if not os.path.exists(config_path):
        return {"reporters": [], "folders": []}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        report_error("collect_storage.load_config", str(e))
        return {"reporters": [], "folders": []}


def is_designated_reporter(config):
    reporters = config.get("reporters", [])
    if not reporters or "*" in reporters:
        return True
    current = get_machine_name().upper()
    return current in [r.upper() for r in reporters]


def measure_folder(folder_path, max_depth=5, timeout_sec=60):
    """Measure folder size, file count, and listing latency.
    Returns (ok, result_dict_or_error_str).
    """
    start_time = time.perf_counter()
    try:
        # Check initial accessibility
        if not os.path.exists(folder_path):
            return False, "path does not exist or network path unavailable"
        if not os.path.isdir(folder_path):
            return False, "path is not a directory"

        # Latency check: time to list top-level
        list_start = time.perf_counter()
        top_entries = os.listdir(folder_path)
        latency_ms = round((time.perf_counter() - list_start) * 1000, 1)

        total_bytes = 0
        file_count = 0
        dir_count = 0
        deadline = start_time + timeout_sec
        timed_out = False

        base_depth = folder_path.rstrip(r"\/").count(os.sep)

        for root, dirs, files in os.walk(folder_path):
            if time.perf_counter() > deadline:
                timed_out = True
                break

            current_depth = root.count(os.sep) - base_depth
            if current_depth >= max_depth:
                dirs.clear()  # Do not recurse deeper than max_depth

            dir_count += len(dirs)
            for f in files:
                file_count += 1
                fp = os.path.join(root, f)
                try:
                    total_bytes += os.path.getsize(fp)
                except (OSError, IOError):
                    pass

        total_gb = round(total_bytes / (1024 ** 3), 2)
        total_time_ms = round((time.perf_counter() - start_time) * 1000, 1)

        data = {
            "total_bytes": total_bytes,
            "total_gb": total_gb,
            "file_count": file_count,
            "dir_count": dir_count,
            "latency_ms": latency_ms,
            "walk_time_ms": total_time_ms,
            "timed_out": timed_out,
        }
        return True, data
    except Exception as e:
        return False, str(e)


def collect_snapshots(config, verbose=False):
    folders = config.get("folders", [])
    snapshots = []
    shares_failed = []

    for item in folders:
        path = item.get("folder_path")
        key = item.get("canonical_key", path)
        if not path:
            continue

        if verbose:
            print(f"[collect_storage] Probing {key}: {path}...", file=sys.stderr)

        ok, result = measure_folder(path)
        if ok:
            record = {
                "canonical_key": key,
                "folder_path": path,
                "status": "online",
                **result,
            }
            snapshots.append(record)
            if verbose:
                print(f"[collect_storage]   -> {result["total_gb"]} GB, {result["file_count"]} files", file=sys.stderr)
        else:
            fail_record = {
                "canonical_key": key,
                "folder_path": path,
                "status": "unavailable",
                "error": result,
            }
            shares_failed.append(fail_record)
            if verbose:
                print(f"[collect_storage]   -> FAILED: {result}", file=sys.stderr)

    return snapshots, shares_failed


def build_payload(snapshots, shares_failed):
    return {
        "machine_name": get_machine_name(),
        "measured_at": datetime.now(timezone.utc).isoformat(),
        "collector_version": "1.0.0",
        "snapshots": snapshots,
        "shares_failed": shares_failed,
        "total_shares_monitored": len(snapshots) + len(shares_failed),
        "successful_shares": len(snapshots),
        "failed_shares": len(shares_failed),
    }


def main():
    parser = argparse.ArgumentParser(description="InfraWatch Storage Snapshot Collector")
    parser.add_argument("--dry-run", action="store_true", help="Print payload and do not POST")
    parser.add_argument("--force-run", action="store_true", help="Bypass reporter pool check")
    parser.add_argument("--verbose", action="store_true", help="Verbose progress output")
    parser.add_argument("--config", type=str, default=None, help="Path to custom watchlist config")
    args, _ = parser.parse_known_args()

    config = load_config(args.config)

    if not args.force_run and not is_designated_reporter(config):
        if args.verbose:
            print(f"[collect_storage] Machine \"{get_machine_name()}\" is not in designated reporter pool. Skipping.", file=sys.stderr)
        return 0

    try:
        snapshots, shares_failed = collect_snapshots(config, verbose=args.verbose)
        payload = build_payload(snapshots, shares_failed)

        if args.dry_run:
            print(json.dumps(payload, indent=2))
            return 0

        ok, detail = post_to_infrawatch_detailed("storage/snapshot", payload)
        if not ok:
            print(f"[collect_storage] POST failed: {detail}", file=sys.stderr)
            report_error("collect_storage.post", detail)
            return 1

        if args.verbose:
            print(f"[collect_storage] Successfully posted {len(snapshots)} snapshots ({len(shares_failed)} failed shares).", file=sys.stderr)
        return 0
    except Exception as e:
        report_error("collect_storage.main", str(e))
        print(f"[collect_storage] Unhandled error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
