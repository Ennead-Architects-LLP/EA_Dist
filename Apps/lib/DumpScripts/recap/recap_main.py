"""EnneadTab usage recap -- producer entry point.

Runs under CPython 3 from Task Scheduler (via run_recap.bat) or by hand.
Computes the recap, picks the headline claim, renders the HTML, and writes the
pending-digest handoff that Revit/Rhino read at startup.

    python recap_main.py                    # dry run: build + open, send nothing
    python recap_main.py --run              # cadence-gated real run
    python recap_main.py --selftest         # imports only; prove deployment
    python recap_main.py --fake-user NAME   # another user's log, forced dry-run
    python recap_main.py --log-json PATH    # synthetic log (testing, no EnneadTab)

PHASE 1 SCOPE: no email is sent, nothing is written to the shared drive, and no
APPS entry exists yet. The point of this phase is to validate the CONTENT --
the subjective, risky part -- before any infrastructure is committed to.
"""

import argparse
import datetime
import json
import os
import sys
import webbrowser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import recap_catalog
import recap_claims
import recap_email_html
import recap_env
import recap_state
import recap_stats


PENDING_FILE = "recap_pending_digest"
PENDING_SCHEMA = 1
DIGEST_TTL_DAYS = 10


# ------------------------------------------------------------------- plumbing

def _is_standalone(args):
    """True when the run must not touch EnneadTab at all.

    ENVIRONMENT reads os.environ["USERPROFILE"] at import time and creates
    folders, so importing it off Windows raises. --log-json / --out-dir exist
    precisely so claim quality can be reviewed on any machine, which means
    they must bypass the library rather than degrade through it.
    """
    return bool(args.log_json or args.out_dir)


def _load_log(args):
    if args.log_json:
        with open(args.log_json, "r", encoding="utf-8") as handle:
            return json.load(handle)
    return recap_env.read_log(args.fake_user)


def _resolve_user(args):
    if args.fake_user:
        return args.fake_user
    if not _is_standalone(args):
        try:
            return recap_env.get_user_name()
        except Exception:
            pass
    return os.environ.get("USERNAME") or os.environ.get("USER") or "unknown"


def _out_path(args, file_name):
    if args.out_dir:
        if not os.path.isdir(args.out_dir):
            os.makedirs(args.out_dir)
        return os.path.join(args.out_dir, file_name)
    return recap_env.dump_file(file_name)


# --------------------------------------------------------------------- recap

def build_recap(raw_log, today, state, user_name):
    """Everything the surfaces need, computed once. No I/O."""
    metrics = recap_stats.build(raw_log, today)
    catalog = recap_catalog.build_catalog()

    month = metrics["month"]
    joined = recap_catalog.join_usage(
        catalog, month.get("runs_by_tool"), month.get("basenames_by_tool"))

    # Display names for the chart, resolved through the join so a reworded
    # title still renders as the tool's real name.
    display_names = {}
    for key in month.get("runs_by_tool", {}):
        script_path = catalog["by_alias"].get(key)
        if script_path is None:
            basename = (month.get("basenames_by_tool") or {}).get(key)
            script_path = catalog["by_basename"].get(basename) if basename else None
        if script_path and script_path in catalog["tools"]:
            display_names[key] = catalog["tools"][script_path]["alias"]
    metrics["display_names"] = display_names

    # Apps the user actually touches -- never recommend into an unused one.
    active_apps = set()
    for app, count in (month.get("runs_by_application") or {}).items():
        if count > 0 and app in (recap_catalog.REVIT, recap_catalog.RHINO):
            active_apps.add(app)
    if not active_apps:
        for app, count in (metrics["week"].get("runs_by_application") or {}).items():
            if app in (recap_catalog.REVIT, recap_catalog.RHINO):
                active_apps.add(app)

    # "Used" spans all history, not just this month: recommending something
    # they used last quarter is the credibility failure this guards against.
    ever_used = set()
    for key in metrics.get("first_use_dates", {}):
        script_path = catalog["by_alias"].get(key)
        if script_path:
            ever_used.add(script_path)

    recommendations = recap_catalog.recommend(
        catalog,
        used_scripts=joined["runs"],
        active_apps=active_apps,
        state=state,
        team_adoption=None,          # phase 4
        recently_used=ever_used,
    )
    for tool in recommendations:
        tool["doc_line"] = recap_catalog.first_line_of_doc(tool.get("doc"))

    allow_loss = recap_state.loss_aversion_allowed(state, today)
    claim, candidates = recap_claims.select(
        metrics, catalog, joined, recommendations,
        state=state,
        peer_data=None,              # phase 4; peer claims cannot be built
        allow_loss_aversion=allow_loss,
        previous_streak=int((state.get("streak") or {}).get("longest", 0)),
    )

    return {
        "metrics": metrics,
        "catalog": catalog,
        "joined": joined,
        "recommendations": recommendations,
        "claim": claim,
        "candidates": candidates,
        "user_name": user_name,
    }


def write_pending_digest(args, recap, today):
    """Handoff file the Revit/Rhino startup hook consumes.

    `expires_at` is what stops a stale digest being shown as current -- the
    common failure (task never enrolled, machine off), not the rare one.
    """
    claim = recap["claim"]
    if claim is None:
        return None

    html_path = _out_path(args, "recap_digest_{}.html".format(recap["user_name"]))
    expires = today + datetime.timedelta(days=DIGEST_TTL_DAYS)
    payload = {
        "schema": PENDING_SCHEMA,
        "generated_at": today.strftime("%Y-%m-%d"),
        "expires_at": expires.strftime("%Y-%m-%d"),
        "consumed": False,
        "week_id": recap_state.iso_week_id(today),
        "surface_text": claim.render_surface(),
        "body_text": claim.render_body(),
        "claim_type": claim.type,
        "html_path": html_path,
        "chart": _toast_chart(recap),
    }

    if args.dry_run:
        path = _out_path(args, "recap_pending_digest_dryrun.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)
        return path

    recap_env.bootstrap()
    from EnneadTab import DATA_FILE
    DATA_FILE.set_data(payload, PENDING_FILE)
    return PENDING_FILE


def _toast_chart(recap):
    """Declarative chart payload -- NotificationHost renders it.

    The producer never rasterizes anything: it ships raw data plus a type, so
    the Revit/Rhino side only builds a dict and stays IronPython-2.7 safe.
    `mask_labels` hides the winning bar's identity, which is the visual half of
    the curiosity gap.
    """
    month = recap["metrics"]["month"]
    top = month.get("top_tools") or []
    if not top:
        return None
    names = recap["metrics"].get("display_names") or {}
    series = []
    for key, count in top[:5]:
        series.append({"label": names.get(key, key), "value": count})
    return {
        "type": "bar",
        "series": series,
        "highlight": 0,
        "mask_labels": True,
        "caption": recap["metrics"]["month_label"],
    }


# ------------------------------------------------------------------ reporting

def print_dry_run_report(recap, args):
    metrics = recap["metrics"]
    month = metrics["month"]
    joined = recap["joined"]

    print("=" * 68)
    print("EnneadTab recap dry run -- {} -- {}".format(
        recap["user_name"], metrics["month_id"]))
    print("=" * 68)
    print("runs ever          : {}".format(metrics["total_runs_ever"]))
    print("runs in month      : {}".format(month["total_runs"]))
    print("active days        : {}".format(month["active_days"]))
    print("distinct tools     : {}".format(month["distinct_tools"]))
    print("streak (work days) : {} (alive={})".format(
        metrics["streak"], metrics["streak_alive"]))
    print("idle working days  : {}  [calendar: {}]".format(
        metrics["working_days_idle"], metrics["days_since_last_run"]))
    print("duration coverage  : {:.2f}".format(month["duration_parse_coverage"]))
    print("unparseable keys   : {}".format(metrics["unparseable_keys"]))
    print("catalog join       : {:.3f} coverage, {} unknown keys".format(
        joined["coverage"], len(joined["unknown"])))
    if joined["unknown"]:
        worst = sorted(joined["unknown"].items(), key=lambda kv: -kv[1])[:5]
        for key, count in worst:
            print("    unmatched: {!r} x{}".format(key, count))
    if joined["coverage"] < 0.9:
        print("  !! join coverage below 0.9 -- knowledge file may lag the log;")
        print("     comparative claims should be treated as unreliable.")

    print("-" * 68)
    print("CLAIM CANDIDATES (scored, best first)")
    if not recap["candidates"]:
        print("    none qualified")
    for claim in recap["candidates"]:
        marker = "->" if claim is recap["claim"] else "  "
        print("{} {:<16} score={:.3f}".format(marker, claim.type, claim.score))
        print("       surface: {}".format(claim.render_surface()))
        print("       body   : {}".format(claim.render_body()))

    print("-" * 68)
    print("RECOMMENDATIONS")
    for index, tool in enumerate(recap["recommendations"], start=1):
        print("  {}. {} [{} / {}] score={}".format(
            index, tool["alias"], tool["app"], tool["tab"], tool["score"]))
        print("     {}".format(tool["doc_line"]))
    print("=" * 68)


# ----------------------------------------------------------------------- main

def selftest():
    """Prove the deployment before trusting a scheduled run.

    The real risk is import surface: EMAIL pulls in EXE/IMAGE/SPEAK, IMAGE
    probes System.Drawing via clr, and ENVIRONMENT creates folders and probes
    the shared root at import time. Nothing in DumpScripts/collectors imports
    EnneadTab at all, so this path is genuinely unproven per machine.
    """
    ok = True
    for label, thunk in (
        ("recap_stats", lambda: recap_stats.build({}, datetime.date.today())),
        ("recap_catalog", lambda: recap_catalog.build_catalog()),
        ("recap_email_html", lambda: recap_email_html.bar_chart(
            [{"label": "a", "value": 1}])),
        ("EnneadTab bootstrap", lambda: recap_env.bootstrap()),
        ("EnneadTab.USER", lambda: recap_env.get_user_name()),
        ("EnneadTab.DATA_FILE", lambda: recap_env.read_log()),
        ("shared root probe", lambda: recap_env.is_shared_root_available()),
    ):
        try:
            thunk()
            print("  ok    {}".format(label))
        except Exception as error:
            ok = False
            print("  FAIL  {}: {}: {}".format(label, type(error).__name__, error))
    print("selftest {}".format("passed" if ok else "FAILED"))
    return 0 if ok else 1


def parse_args(argv):
    parser = argparse.ArgumentParser(description="EnneadTab usage recap producer")
    parser.add_argument("--run", action="store_true",
                        help="Real run (cadence-gated). Default is a dry run.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Build and open the preview; send and persist nothing.")
    parser.add_argument("--selftest", action="store_true",
                        help="Import probe only. Prints what resolved.")
    parser.add_argument("--fake-user", metavar="NAME",
                        help="Compute against another user's log. Forces dry run.")
    parser.add_argument("--log-json", metavar="PATH",
                        help="Read a synthetic log from a JSON file (testing).")
    parser.add_argument("--out-dir", metavar="PATH",
                        help="Write outputs here instead of the dump folder.")
    parser.add_argument("--today", metavar="YYYY-MM-DD",
                        help="Override today's date (testing).")
    parser.add_argument("--no-open", action="store_true",
                        help="Do not open the preview in a browser.")
    args = parser.parse_args(argv)

    # Dry run is the default, and --fake-user can never be anything else:
    # computing against someone else's log must not be able to mail them.
    if args.fake_user or not args.run:
        args.dry_run = True
    return args


def main(argv=None):
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if args.selftest:
        return selftest()

    if recap_env.kill_switch_active():
        return 0

    if args.today:
        today = datetime.datetime.strptime(args.today, "%Y-%m-%d").date()
    else:
        today = datetime.date.today()

    user_name = _resolve_user(args)

    try:
        raw_log = _load_log(args)
    except Exception as error:
        print("Could not read the usage log: {}".format(error))
        return 1

    if _is_standalone(args):
        state = recap_state._empty_state()   # standalone/testing: no persistence
    else:
        state = recap_state.load(user_name)

    recap = build_recap(raw_log, today, state, user_name)

    if recap["claim"] is None:
        print("No claim qualified -- nothing worth sending. "
              "(This is a correct outcome for a quiet month, not an error.)")
        if not args.dry_run:
            return 0

    body = ""
    if recap["claim"] is not None:
        body = recap_email_html.build(
            recap["claim"], recap["metrics"], recap["recommendations"], user_name)

    if args.dry_run:
        print_dry_run_report(recap, args)
        if body:
            html_path = _out_path(args, "recap_preview.html")
            with open(html_path, "w", encoding="utf-8") as handle:
                handle.write(body)
            print("preview written: {}".format(html_path))
            if not args.no_open:
                try:
                    webbrowser.open("file:///" + html_path.replace("\\", "/"))
                except Exception:
                    pass
        pending = write_pending_digest(args, recap, today)
        if pending:
            print("pending digest : {}".format(pending))
        state_path = _out_path(args, "recap_state_{}_dryrun.json".format(user_name))
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump(state, handle, indent=2, default=str)
        print("state (not saved): {}".format(state_path))
        return 0

    # ---- real run (phase 1: still no email, no shared writes) ----
    # Respect the opt-out. A user who turned the digest off must not get a
    # pending file written for them at all -- not merely a suppressed toast.
    if not recap_env.is_digest_enabled():
        return 0

    if recap_state.weekly_due(state, today) and recap["claim"] is not None:
        write_pending_digest(args, recap, today)
        state["last_weekly_week_id"] = recap_state.iso_week_id(today)
        if recap["claim"].is_loss_aversion():
            state["last_loss_aversion"] = today.strftime("%Y-%m-%d")
        recap_state.record_claim(
            state, recap["claim"].type, recap["claim"].tool,
            recap["metrics"]["month_id"])
        recap_state.record_recommendations(
            state, [tool["script"] for tool in recap["recommendations"]])

    recap_state.update_first_seen(state, recap["metrics"].get("first_use_dates", {}))
    streak = state.get("streak") or {}
    streak["current"] = recap["metrics"]["streak"]
    streak["longest"] = max(int(streak.get("longest", 0)), recap["metrics"]["streak"])
    state["streak"] = streak
    recap_state.save(state, user_name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
