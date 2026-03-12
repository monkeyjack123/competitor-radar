import unittest

from competitor_radar import (
    analyze_snapshot,
    calculate_field_coverage,
    calculate_overlap_stats,
    count_competitor_overlap,
    detect_changes,
    detect_presence_changes,
    summarize_changes,
)


class DetectChangesTests(unittest.TestCase):
    def test_detects_field_level_changes(self):
        previous = [
            {
                "competitor": "Acme AI",
                "positioning": "AI drafts product docs",
                "pricing": "$49/mo",
                "feature_highlight": "single-shot PRD",
            }
        ]
        current = [
            {
                "competitor": "Acme AI",
                "positioning": "AI drafts and validates product docs",
                "pricing": "$79/mo",
                "feature_highlight": "single-shot PRD",
            }
        ]

        changes = detect_changes(previous, current)

        self.assertEqual(2, len(changes))
        self.assertEqual("positioning", changes[0].field)
        self.assertEqual("pricing", changes[1].field)

    def test_ignores_missing_competitor_overlap(self):
        previous = [{"competitor": "A", "pricing": "$10"}]
        current = [{"competitor": "B", "pricing": "$12"}]

        self.assertEqual([], detect_changes(previous, current, tracked_fields=["pricing"]))

    def test_matches_competitors_case_insensitively(self):
        previous = [{"competitor": "Acme AI", "pricing": "$10"}]
        current = [{"competitor": "  acme ai  ", "pricing": "$12"}]

        changes = detect_changes(previous, current, tracked_fields=["pricing"])

        self.assertEqual(1, len(changes))
        self.assertEqual("acme ai", changes[0].competitor)

    def test_supports_custom_fields(self):
        previous = [{"competitor": "A", "messaging": "Ship faster"}]
        current = [{"competitor": "A", "messaging": "Ship fast with guardrails"}]

        changes = detect_changes(previous, current, tracked_fields=["messaging"])

        self.assertEqual(1, len(changes))
        self.assertEqual("messaging", changes[0].field)


class PresenceDeltaTests(unittest.TestCase):
    def test_detects_added_and_removed_competitors(self):
        previous = [{"competitor": "Acme"}, {"competitor": "Nova"}]
        current = [{"competitor": "Nova"}, {"competitor": "Orbit"}]

        delta = detect_presence_changes(previous, current)

        self.assertEqual(("Orbit",), delta.added)
        self.assertEqual(("Acme",), delta.removed)

    def test_presence_matching_is_case_insensitive(self):
        previous = [{"competitor": "Acme"}, {"competitor": "Nova"}]
        current = [{"competitor": "acme"}, {"competitor": "ORBIT"}]

        delta = detect_presence_changes(previous, current)

        self.assertEqual(("ORBIT",), delta.added)
        self.assertEqual(("Nova",), delta.removed)


class SnapshotDiagnosticsTests(unittest.TestCase):
    def test_reports_duplicates_and_missing_competitor_rows(self):
        snapshot = [
            {"competitor": "Nova", "pricing": "$10"},
            {"competitor": "  nova ", "pricing": "$12"},
            {"competitor": "", "pricing": "$9"},
            {"pricing": "$7"},
        ]

        diagnostics = analyze_snapshot(snapshot)

        self.assertEqual(("Nova",), diagnostics.duplicate_competitors)
        self.assertEqual(2, diagnostics.missing_competitor_rows)


class OverlapTests(unittest.TestCase):
    def test_counts_overlap_case_insensitively(self):
        previous = [{"competitor": "Acme"}, {"competitor": "Nova"}]
        current = [{"competitor": "  acme "}, {"competitor": "Orbit"}]

        self.assertEqual(1, count_competitor_overlap(previous, current))

    def test_returns_zero_when_no_overlap(self):
        previous = [{"competitor": "Acme"}]
        current = [{"competitor": "Nova"}]

        self.assertEqual(0, count_competitor_overlap(previous, current))

    def test_calculates_overlap_stats(self):
        previous = [{"competitor": "Acme"}, {"competitor": "Nova"}]
        current = [{"competitor": "acme"}, {"competitor": "Orbit"}, {"competitor": "Kite"}]

        stats = calculate_overlap_stats(previous, current)

        self.assertEqual(2, stats.previous_count)
        self.assertEqual(3, stats.current_count)
        self.assertEqual(1, stats.overlap_count)
        self.assertAlmostEqual(0.5, stats.overlap_ratio_previous)
        self.assertAlmostEqual(1 / 3, stats.overlap_ratio_current)


class CoverageTests(unittest.TestCase):
    def test_calculates_field_coverage_for_previous_and_current(self):
        previous = [
            {"competitor": "Acme", "pricing": "$10", "positioning": "PMF"},
            {"competitor": "Nova", "pricing": "", "positioning": ""},
        ]
        current = [
            {"competitor": "Acme", "pricing": "$20", "positioning": "PMF"},
            {"competitor": "Nova", "pricing": "$15", "positioning": ""},
        ]

        coverage = calculate_field_coverage(previous, current, tracked_fields=["pricing", "positioning"])

        self.assertEqual("pricing", coverage[0].field)
        self.assertEqual(1, coverage[0].previous_non_empty)
        self.assertEqual(2, coverage[0].current_non_empty)
        self.assertAlmostEqual(0.5, coverage[0].previous_ratio)
        self.assertAlmostEqual(1.0, coverage[0].current_ratio)

        self.assertEqual("positioning", coverage[1].field)
        self.assertEqual(1, coverage[1].previous_non_empty)
        self.assertEqual(1, coverage[1].current_non_empty)


class SummarizeChangesTests(unittest.TestCase):
    def test_groups_changes_per_competitor(self):
        previous = [
            {"competitor": "A", "pricing": "$10", "positioning": "Old"},
            {"competitor": "B", "pricing": "$20", "positioning": "Same"},
        ]
        current = [
            {"competitor": "A", "pricing": "$15", "positioning": "New"},
            {"competitor": "B", "pricing": "$20", "positioning": "Same"},
        ]

        changes = detect_changes(previous, current, tracked_fields=["pricing", "positioning"])
        summary = summarize_changes(changes)

        self.assertEqual(1, len(summary))
        self.assertEqual("A", summary[0].competitor)
        self.assertEqual(2, summary[0].change_count)
        self.assertEqual(("positioning", "pricing"), summary[0].changed_fields)


if __name__ == "__main__":
    unittest.main()
