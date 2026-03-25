"""Run all InfraWatch collectors in sequence.

Single entry point for Task Scheduler. Runs silently — no output,
no popups, no console. Failures reported to ErrorDump only.

Usage:
    python collect_all.py              # One-shot (all collectors)
    python collect_all.py --loop 10    # Every 10 minutes
    python collect_all.py --spec-only  # Just machine spec (run on login)
"""

import sys
import time


def run_all():
    """Run all collectors. Each is independent — one failing doesn't block others."""
    import collect_drive_health
    import collect_machine_spec
    import collect_events

    collect_drive_health.collect_once()
    collect_machine_spec.main()
    collect_events.main()


def run_spec_only():
    """Run just the machine spec collector (lightweight, good for login trigger)."""
    import collect_machine_spec
    collect_machine_spec.main()


def main():
    if "--spec-only" in sys.argv:
        run_spec_only()
        return

    if "--loop" in sys.argv:
        idx = sys.argv.index("--loop")
        interval = int(sys.argv[idx + 1]) if idx + 1 < len(sys.argv) else 10
        while True:
            run_all()
            time.sleep(interval * 60)
    else:
        run_all()


if __name__ == "__main__":
    main()
