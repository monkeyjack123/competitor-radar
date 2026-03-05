import unittest

from competitor_radar import detect_changes, detect_presence_changes, summarize_changes


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
