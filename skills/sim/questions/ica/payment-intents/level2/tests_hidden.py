"""Level 2 hidden suite. Never copied into a session workspace."""

import unittest

from solution import PaymentSystem


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.system = PaymentSystem()

    def test_empty_system_has_no_statuses(self):
        self.assertEqual(self.system.count_by_status(), {})

    def test_one_created_intent(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(self.system.count_by_status(), {"created": 1})

    def test_counts_move_with_status(self):
        first = self.system.create_intent("k1", "acme", 500, "usd")
        self.system.create_intent("k2", "acme", 300, "usd")
        self.system.confirm(first)
        self.assertEqual(self.system.count_by_status(), {"confirming": 1, "created": 1})

    def test_statuses_with_no_intents_are_absent(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.assertNotIn("confirming", self.system.count_by_status())

    def test_a_replayed_key_is_counted_once(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(self.system.count_by_status(), {"created": 1})

    def test_refused_creates_are_not_counted(self):
        self.system.create_intent("k1", "acme", 0, "usd")
        self.system.create_intent("", "acme", 100, "usd")
        self.assertEqual(self.system.count_by_status(), {})

    def test_counts_across_merchants(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.system.create_intent("k2", "globex", 500, "usd")
        self.assertEqual(self.system.count_by_status(), {"created": 2})

    def test_returns_a_dict(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.assertIsInstance(self.system.count_by_status(), dict)

    def test_captured_total_starts_at_zero(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(self.system.captured_total("acme"), 0)

    def test_captured_total_is_not_the_intent_amount(self):
        """Creating an intent is not capturing money."""
        self.system.create_intent("k1", "acme", 5000, "usd")
        self.assertEqual(self.system.captured_total("acme"), 0)

    def test_captured_total_of_unknown_merchant(self):
        self.assertEqual(self.system.captured_total("nobody"), 0)

    def test_captured_total_is_per_merchant(self):
        self.system.create_intent("k1", "acme", 500, "usd")
        self.system.create_intent("k2", "globex", 700, "usd")
        self.assertEqual(self.system.captured_total("globex"), 0)

    def test_merchant_names_are_case_sensitive(self):
        self.system.create_intent("k1", "Acme", 500, "usd")
        self.assertEqual(self.system.captured_total("acme"), 0)

    def test_confirming_does_not_capture(self):
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.system.confirm(intent)
        self.assertEqual(self.system.captured_total("acme"), 0)

    def test_level_one_still_works(self):
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(self.system.status(intent), "created")
        self.assertIs(self.system.confirm(intent), True)
        self.assertIs(self.system.confirm(intent), False)
        self.assertIsNone(self.system.create_intent("k2", "acme", -1, "usd"))

    def test_scale(self):
        for index in range(300):
            self.system.create_intent("k%d" % index, "acme", 10, "usd")
        self.assertEqual(self.system.count_by_status(), {"created": 300})
