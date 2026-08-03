"""Guardrail tests for the usage recap.

Stdlib unittest on purpose -- pytest is not installed in the project venv and
the repo's pytest.ini scopes testpaths elsewhere. Run:

    python -m unittest discover -s Apps/lib/DumpScripts/recap -p "check_*.py"

These are not coverage tests. Each one pins a specific way the recap could
become wrong, misleading, or unsendable.
"""

import datetime
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import recap_catalog
import recap_claims
import recap_email_html
import recap_state
import recap_stats


def _log(entries):
    """entries: [(datetime, title, script_path, duration)] -> raw log dict."""
    out = {}
    for stamp, title, script, duration in entries:
        out[stamp.strftime(recap_stats.LOG_KEY_FORMAT)] = {
            "application": "Revit",
            "function_name": title,
            "arguments": [],
            "result": "None",
            "script_path": script,
            "duration": duration,
        }
    return out


class DurationParsing(unittest.TestCase):
    def test_readable_formats(self):
        self.assertAlmostEqual(recap_stats.parse_duration("1.23s"), 1.23)
        self.assertAlmostEqual(recap_stats.parse_duration("2m"), 120.0)
        self.assertAlmostEqual(recap_stats.parse_duration("1m 3s"), 63.0)
        self.assertAlmostEqual(recap_stats.parse_duration("2h 5m"), 7500.0)

    def test_unparseable_returns_none_not_zero(self):
        # Zero would silently deflate "hours in tools"; None lets coverage
        # tracking see the miss.
        self.assertIsNone(recap_stats.parse_duration("ages"))
        self.assertIsNone(recap_stats.parse_duration(None))


class KeyNormalization(unittest.TestCase):
    def test_collapses_whitespace_and_case(self):
        self.assertEqual(
            recap_stats.normalize_tool_key("Batch  Format\nFamily Name"),
            "batch format family name")

    def test_basename_handles_windows_paths_on_posix(self):
        self.assertEqual(
            recap_stats.script_basename(r"A.tab\B.panel\c.pushbutton\d_script.py"),
            "d_script.py")


class UnparseableKeysAreCounted(unittest.TestCase):
    def test_bad_keys_counted_not_silently_dropped(self):
        raw = {"not-a-timestamp": {"function_name": "X"}}
        raw.update(_log([(datetime.datetime(2026, 7, 1, 9, 0, 0),
                          "Good", "g_script.py", "1s")]))
        metrics = recap_stats.build(raw, datetime.date(2026, 8, 3))
        self.assertEqual(metrics["unparseable_keys"], 1)
        self.assertEqual(metrics["total_runs_ever"], 1)


class StreakSemantics(unittest.TestCase):
    """A calendar-day streak would reset every Saturday and be worthless."""

    def _records(self, days):
        entries = [(datetime.datetime.combine(d, datetime.time(10, 0)),
                    "T", "t_script.py", "1s") for d in days]
        return recap_stats.parse_records(_log(entries))[0]

    def test_weekend_does_not_break_streak(self):
        # Thu 2026-07-30 + Fri 07-31 active; Sat/Sun are not working days.
        days = [datetime.date(2026, 7, 30), datetime.date(2026, 7, 31)]
        self.assertEqual(recap_stats.working_day_streak(self._records(days)), 2)

    def test_holiday_hook_does_not_break_streak(self):
        holiday = datetime.date(2026, 7, 30)
        days = [datetime.date(2026, 7, 29), datetime.date(2026, 7, 31)]
        working = lambda d: d.weekday() < 5 and d != holiday
        self.assertEqual(
            recap_stats.working_day_streak(self._records(days),
                                           is_working_day=working), 2)

    def test_real_working_day_gap_breaks_the_run(self):
        # Mon+Tue active, Wed idle, Thu active -> the run ending at Thu is 1.
        days = [datetime.date(2026, 7, 27), datetime.date(2026, 7, 28),
                datetime.date(2026, 7, 30)]
        self.assertEqual(recap_stats.working_day_streak(self._records(days)), 1)

    def test_idle_is_counted_in_working_days_not_calendar_days(self):
        """Last run Friday, checked Tuesday: 4 calendar days but 2 working
        days. Gating on calendar days would skip everyone over a weekend."""
        records = self._records([datetime.date(2026, 7, 31)])   # a Friday
        tuesday = datetime.date(2026, 8, 4)
        self.assertEqual(recap_stats.days_since_last_run(records, tuesday), 4)
        self.assertEqual(
            recap_stats.working_days_since_last_run(records, tuesday), 2)

    def test_streak_survives_today_being_idle(self):
        records = self._records([datetime.date(2026, 7, 30),
                                 datetime.date(2026, 7, 31)])
        idle = recap_stats.working_days_since_last_run(
            records, datetime.date(2026, 8, 3))
        self.assertEqual(idle, 1)
        self.assertTrue(recap_stats.is_streak_alive(idle))
        self.assertFalse(recap_stats.is_streak_alive(2))


class CatalogJoin(unittest.TestCase):
    def setUp(self):
        self.catalog = recap_catalog.build_catalog()

    def test_catalog_loads(self):
        self.assertGreater(len(self.catalog["tools"]), 100)

    def test_archive_and_tailor_excluded(self):
        for script_path in self.catalog["tools"]:
            lowered = script_path.lower()
            self.assertNotIn("archive", lowered)
            self.assertNotIn("tailor", lowered)

    def test_multi_alias_script_matches_on_any_alias(self):
        """LOG.log records max(aliases, key=len); the catalog registers all of
        them. Every registered alias must resolve to the same script."""
        catalog = {
            "tools": {"s.py": {"script": "s.py", "app": "Revit",
                               "alias": "Long Name Here", "aliases": ["Short", "Long Name Here"],
                               "doc": "d", "tab": "T", "icon": "", "is_popular": False}},
            "by_alias": {"short": "s.py", "long name here": "s.py"},
            "by_basename": {"s.py": "s.py"},
        }
        for key in ("short", "long name here"):
            joined = recap_catalog.join_usage(catalog, {key: 5})
            self.assertEqual(joined["runs"], {"s.py": 5})
            self.assertEqual(joined["coverage"], 1.0)

    def test_tier2_basename_join_survives_a_retitled_tool(self):
        catalog = {
            "tools": {"A.tab/x.pushbutton/x_script.py": {
                "script": "A.tab/x.pushbutton/x_script.py", "app": "Revit",
                "alias": "New Title", "aliases": ["New Title"], "doc": "d",
                "tab": "T", "icon": "", "is_popular": False}},
            "by_alias": {"new title": "A.tab/x.pushbutton/x_script.py"},
            "by_basename": {"x_script.py": "A.tab/x.pushbutton/x_script.py"},
        }
        joined = recap_catalog.join_usage(
            catalog, {"old title": 4}, {"old title": "x_script.py"})
        self.assertEqual(joined["runs"], {"A.tab/x.pushbutton/x_script.py": 4})

    def test_unmatched_keys_are_bucketed_and_lower_coverage(self):
        joined = recap_catalog.join_usage(self.catalog, {"no such tool": 3})
        self.assertEqual(joined["runs"], {})
        self.assertEqual(joined["unknown"], {"no such tool": 3})
        self.assertEqual(joined["coverage"], 0.0)


class RecommendationCredibility(unittest.TestCase):
    """The assertion that protects the whole feature's credibility."""

    def setUp(self):
        self.catalog = recap_catalog.build_catalog()

    def test_never_recommends_a_tool_the_user_has_used(self):
        used = list(self.catalog["tools"])[:40]
        recs = recap_catalog.recommend(
            self.catalog,
            used_scripts={path: 5 for path in used},
            active_apps={"Revit", "Rhino"},
            state=recap_state._empty_state(),
            recently_used=set(used),
            limit=3,
        )
        self.assertTrue(recs)
        for tool in recs:
            self.assertNotIn(tool["script"], used)

    def test_multi_alias_tool_used_under_one_alias_is_not_recommended(self):
        """The exact case that breaks a naive title-based join."""
        catalog = {
            "tools": {
                "s.py": {"script": "s.py", "app": "Revit", "alias": "Long Name",
                         "aliases": ["Short", "Long Name"], "doc": "d", "tab": "T",
                         "icon": "", "is_popular": True},
                "other.py": {"script": "other.py", "app": "Revit", "alias": "Other",
                             "aliases": ["Other"], "doc": "d", "tab": "T",
                             "icon": "", "is_popular": True},
            },
            "by_alias": {"short": "s.py", "long name": "s.py", "other": "other.py"},
            "by_basename": {"s.py": "s.py", "other.py": "other.py"},
        }
        joined = recap_catalog.join_usage(catalog, {"short": 9})
        recs = recap_catalog.recommend(
            catalog, used_scripts=joined["runs"], active_apps={"Revit"},
            state=recap_state._empty_state(),
            recently_used=set(joined["runs"]), limit=2)
        self.assertNotIn("s.py", [tool["script"] for tool in recs])

    def test_never_recommends_into_an_unused_app(self):
        recs = recap_catalog.recommend(
            self.catalog, used_scripts={}, active_apps={"Revit"},
            state=recap_state._empty_state(), limit=5)
        for tool in recs:
            self.assertEqual(tool["app"], "Revit")

    def test_burned_out_tool_is_dropped_permanently(self):
        state = recap_state._empty_state()
        first = recap_catalog.recommend(
            self.catalog, used_scripts={}, active_apps={"Revit"},
            state=state, limit=1)
        target = first[0]["script"]
        for _ in range(recap_state.RECOMMEND_STRIKE_LIMIT):
            recap_state.record_recommendations(state, [target])
        again = recap_catalog.recommend(
            self.catalog, used_scripts={}, active_apps={"Revit"},
            state=state, limit=5)
        self.assertNotIn(target, [tool["script"] for tool in again])


class ClaimGuardrails(unittest.TestCase):
    def setUp(self):
        self.catalog = recap_catalog.build_catalog()

    def _select(self, raw_log, today, recommendations=None, state=None):
        metrics = recap_stats.build(raw_log, today)
        joined = recap_catalog.join_usage(
            self.catalog, metrics["month"]["runs_by_tool"],
            metrics["month"]["basenames_by_tool"])
        return recap_claims.select(
            metrics, self.catalog, joined,
            recommendations if recommendations is not None else [],
            state=state or recap_state._empty_state(), peer_data=None)

    def test_cold_start_produces_no_superlative(self):
        raw = _log([(datetime.datetime(2026, 7, 1, 9, 0, 0),
                     "T", "t_script.py", "1s")])
        recs = [{"alias": "A", "doc_line": "d", "tab": "T", "script": "a.py"}]
        claim, candidates = self._select(raw, datetime.date(2026, 8, 3), recs)
        self.assertIsNotNone(claim)
        self.assertEqual(claim.type, "cold_start")
        self.assertEqual([c.type for c in candidates], ["cold_start"])

    def test_tiny_sample_produces_no_comparative_claim(self):
        """n=3 must never yield a ratio/growth claim. Technically true, reads
        as a lie, and is the fastest way to lose the reader."""
        entries = []
        for day in (6, 7, 8):
            entries.append((datetime.datetime(2026, 7, day, 9, 0, 0),
                            "T", "t_script.py", "1s"))
        for day in (2, 3, 4):
            entries.append((datetime.datetime(2026, 6, day, 9, 0, 0),
                            "T", "t_script.py", "1s"))
        # Pad history so cold-start does not short-circuit the check.
        for i in range(30):
            entries.append((datetime.datetime(2026, 1, 5, 9, i % 60, 0),
                            "Pad", "pad_script.py", "1s"))
        claim, candidates = self._select(_log(entries), datetime.date(2026, 8, 3))
        for candidate in candidates:
            self.assertNotIn(candidate.type, ("self_growth", "breadth",
                                              "ratio_vs_office", "office_rank_1"))

    def test_peer_claims_are_unbuildable_without_peer_data(self):
        """Suppressed entirely, never softened into 'you might be #1'."""
        entries = [(datetime.datetime(2026, 7, (i % 20) + 1, 9, i % 60, 0),
                    "T", "t_script.py", "10s") for i in range(120)]
        _claim, candidates = self._select(_log(entries), datetime.date(2026, 8, 3))
        for candidate in candidates:
            self.assertNotIn(candidate.type, recap_claims.PEER_CLAIM_TYPES)

    def test_time_claim_suppressed_when_duration_coverage_is_poor(self):
        entries = [(datetime.datetime(2026, 7, (i % 20) + 1, 9, i % 60, 0),
                    "T", "t_script.py", "unparseable") for i in range(120)]
        _claim, candidates = self._select(_log(entries), datetime.date(2026, 8, 3))
        self.assertNotIn("time_in_tools", [c.type for c in candidates])

    def test_every_claim_renders_both_registers(self):
        """A surface cannot exist without its resolution. This is the
        structural form of 'the curiosity gap always resolves'."""
        entries = [(datetime.datetime(2026, 7, (i % 20) + 1, 9, i % 60, 0),
                    "T", "t_script.py", "30s") for i in range(120)]
        recs = [{"alias": "A", "doc_line": "d", "tab": "T", "script": "a.py"}]
        _claim, candidates = self._select(_log(entries), datetime.date(2026, 8, 3), recs)
        self.assertTrue(candidates)
        for candidate in candidates:
            surface = candidate.render_surface()
            body = candidate.render_body()
            self.assertTrue(surface.strip())
            self.assertTrue(body.strip())
            self.assertNotEqual(surface, body)

    def _busy_july(self):
        entries = []
        for day in range(1, 32):
            date = datetime.date(2026, 7, day)
            if date.weekday() >= 5:
                continue
            for i in range(6):
                entries.append((datetime.datetime(2026, 7, day, 9 + i, 0, 0),
                                "T", "t_script.py", "30s"))
        return _log(entries)

    def test_loss_aversion_replaces_rather_than_stacks(self):
        """A lapsing user has no great month to celebrate, so the superlative
        frame must not render alongside the loss frame."""
        # Last run Fri 2026-07-31; Mon 2026-08-03 -> 1 idle working day.
        claim, candidates = self._select(self._busy_july(), datetime.date(2026, 8, 3))
        self.assertIsNotNone(claim)
        self.assertEqual(claim.type, "streak_at_risk")
        self.assertEqual(len(candidates), 1)

    def test_no_streak_warning_when_the_user_worked_today(self):
        """idle == 0 means nothing is actually at risk."""
        _claim, candidates = self._select(self._busy_july(), datetime.date(2026, 7, 31))
        self.assertNotIn("streak_at_risk", [c.type for c in candidates])

    def test_streak_lost_reports_the_asset_not_the_absence(self):
        # Thu 2026-08-06 -> 3 idle working days since Fri 07-31.
        claim, _candidates = self._select(self._busy_july(), datetime.date(2026, 8, 6))
        self.assertIsNotNone(claim)
        self.assertEqual(claim.type, "streak_lost")
        surface = claim.render_surface().lower()
        for nag in ("come back", "we miss", "haven't used", "have not used"):
            self.assertNotIn(nag, surface)

    def test_loss_aversion_frequency_cap(self):
        state = recap_state._empty_state()
        today = datetime.date(2026, 8, 4)
        self.assertTrue(recap_state.loss_aversion_allowed(state, today))
        state["last_loss_aversion"] = (today - datetime.timedelta(days=3)).strftime("%Y-%m-%d")
        self.assertFalse(recap_state.loss_aversion_allowed(state, today))
        state["last_loss_aversion"] = (today - datetime.timedelta(days=20)).strftime("%Y-%m-%d")
        self.assertTrue(recap_state.loss_aversion_allowed(state, today))

    def test_claim_rotation_suppresses_a_repeat(self):
        state = recap_state._empty_state()
        recap_state.record_claim(state, "self_growth", "T", "2026-06")
        recap_state.record_claim(state, "self_growth", "T", "2026-07")
        self.assertEqual(recap_state.recent_claim_types(state, 2),
                         ["self_growth", "self_growth"])


class EmailBodyGuardrails(unittest.TestCase):
    def test_rejects_newlines(self):
        with self.assertRaises(ValueError):
            recap_email_html.assert_sendable("<div>a\nb</div>")

    def test_rejects_border_left(self):
        with self.assertRaises(ValueError):
            recap_email_html.assert_sendable(
                '<div style="border-left:1px solid red">x</div>')

    def test_rejects_style_block(self):
        with self.assertRaises(ValueError):
            recap_email_html.assert_sendable("<style>a{}</style>")

    def test_bar_chart_is_clean(self):
        html = recap_email_html.bar_chart(
            [{"label": "A", "value": 10}, {"label": "B", "value": 2}], highlight=0)
        recap_email_html.assert_sendable(html)
        self.assertIn("bgcolor", html)

    def test_escapes_markup_in_tool_names(self):
        html = recap_email_html.bar_chart(
            [{"label": "<script>x</script>", "value": 1}])
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)

    def test_zero_values_do_not_divide_by_zero(self):
        html = recap_email_html.bar_chart([{"label": "A", "value": 0}])
        recap_email_html.assert_sendable(html)


class CadenceGates(unittest.TestCase):
    def test_monthly_waits_until_the_month_is_complete(self):
        state = recap_state._empty_state()
        self.assertFalse(recap_state.monthly_due(state, datetime.date(2026, 8, 1)))
        self.assertTrue(recap_state.monthly_due(state, datetime.date(2026, 8, 2)))

    def test_monthly_not_repeated_within_a_month(self):
        state = recap_state._empty_state()
        state["last_monthly_sent_month"] = "2026-08"
        self.assertFalse(recap_state.monthly_due(state, datetime.date(2026, 8, 20)))

    def test_weekly_keys_on_iso_week(self):
        state = recap_state._empty_state()
        today = datetime.date(2026, 8, 3)
        self.assertTrue(recap_state.weekly_due(state, today))
        state["last_weekly_week_id"] = recap_state.iso_week_id(today)
        self.assertFalse(recap_state.weekly_due(state, today))
        self.assertTrue(recap_state.weekly_due(
            state, today + datetime.timedelta(days=7)))


class FirstSeenIndex(unittest.TestCase):
    def test_keeps_earliest_date_across_merges(self):
        state = recap_state._empty_state()
        recap_state.update_first_seen(state, {"a": "2026-05-02"})
        recap_state.update_first_seen(state, {"a": "2026-03-01"})
        recap_state.update_first_seen(state, {"a": "2026-09-09"})
        self.assertEqual(state["first_seen"]["a"], "2026-03-01")


if __name__ == "__main__":
    unittest.main(verbosity=2)
