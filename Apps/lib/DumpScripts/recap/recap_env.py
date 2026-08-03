"""Environment bootstrap for the usage recap producer.

The producer runs under CPython 3 (Task Scheduler / dev shell), NOT inside
Revit or Rhino. This is the only module that touches ENVIRONMENT / USER, so
the rest of the package can stay pure functions over plain dicts.

Why the split matters: everything else in this package is unit-testable
without a Windows box, an L: drive, or an EnneadTab install.
"""

import os
import sys


_BOOTSTRAPPED = [False]


def bootstrap():
    """Put Apps/lib on sys.path so `from EnneadTab import ...` resolves.

    Mirrors Apps/_rhino/startup.py: walk up to the Apps folder, append its
    `lib` child. Idempotent.
    """
    if _BOOTSTRAPPED[0]:
        return
    here = os.path.dirname(os.path.abspath(__file__))
    # .../Apps/lib/DumpScripts/recap -> .../Apps/lib
    lib_path = os.path.dirname(os.path.dirname(here))
    if lib_path not in sys.path:
        sys.path.append(lib_path)
    _BOOTSTRAPPED[0] = True


def kill_switch_active():
    """True if a `.recap_kill` sentinel sits at the EA_Dist / EnneadTab-OS root.

    One-file commit disables the feature fleet-wide without every machine
    needing to re-enroll. Copied deliberately from
    collect_all.py::_kill_switch_active so the two behave identically.
    """
    cur = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        if os.path.basename(cur) in ("EA_Dist", "EnneadTab-OS"):
            return os.path.exists(os.path.join(cur, ".recap_kill"))
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return False


def get_user_name():
    bootstrap()
    from EnneadTab import USER
    return USER.USER_NAME


def is_developer():
    bootstrap()
    from EnneadTab import USER
    return bool(USER.IS_DEVELOPER)


def get_email_address(user_name=None):
    bootstrap()
    from EnneadTab import USER
    if user_name:
        return USER.get_company_email_address(user_name)
    return USER.get_company_email_address()


def dump_file(file_name):
    """Absolute path to a file in the local dump folder."""
    bootstrap()
    from EnneadTab import FOLDER
    return FOLDER.get_local_dump_folder_file(file_name)


def is_shared_root_available():
    """Whether the shared root is genuinely reachable.

    ENVIRONMENT.SHARED_DUMP_FOLDER silently falls back to the LOCAL dump when
    the shared root is gone, so `set_data(..., is_local=False)` can quietly
    write to a private folder and a later read would treat one machine's own
    file as the office aggregate. Never trust a shared read without this.

    Phase 1 writes nothing shared; this exists so the peer path (phase 4)
    cannot be added without confronting the trap.
    """
    bootstrap()
    from EnneadTab import ENVIRONMENT
    try:
        if not ENVIRONMENT.is_shared_root_available():
            return False
    except Exception:
        return False
    # Belt two: even if the flag says reachable, refuse if the resolved shared
    # folder actually points inside the local dump.
    try:
        shared = os.path.normcase(os.path.abspath(ENVIRONMENT.SHARED_DUMP_FOLDER))
        local = os.path.normcase(os.path.abspath(ENVIRONMENT.DUMP_FOLDER))
        if shared == local or shared.startswith(local + os.sep):
            return False
    except Exception:
        return False
    return True


def is_email_enabled():
    """Monthly recap opt-in. Same key the Revit settings dialog writes.

    Defaults True so a user who has never opened the dialog still gets the
    recap; the footer tells them how to turn it off.
    """
    bootstrap()
    from EnneadTab import CONFIG
    try:
        return bool(CONFIG.get_setting("checkbox_recap_email_monthly", True))
    except Exception:
        return True


def is_digest_enabled():
    bootstrap()
    from EnneadTab import CONFIG
    try:
        return bool(CONFIG.get_setting("checkbox_recap_digest_weekly", True))
    except Exception:
        return True


def read_log(user_name=None):
    """Raw log dict for a user. Returns {} when the file is missing."""
    bootstrap()
    from EnneadTab import DATA_FILE
    name = "log_{}".format(user_name or get_user_name())
    try:
        return DATA_FILE.get_data(name) or {}
    except Exception:
        return {}
