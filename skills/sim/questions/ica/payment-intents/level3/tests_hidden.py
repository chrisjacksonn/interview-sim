"""Level 3 hidden suite. Never copied into a session workspace."""

import unittest

from solution import PaymentSystem


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.system = PaymentSystem()
        self.intent = self.system.create_intent("k1", "acme", 500, "usd")

    def test_refunded_total_starts_at_zero(self):
        self.assertEqual(self.system.refunded_total(self.intent), 0)

    def test_refunded_total_of_unknown_intent_is_none(self):
        self.assertIsNone(self.system.refunded_total("nope"))

    def test_zero_is_not_none(self):
        self.assertIsNotNone(self.system.refunded_total(self.intent))

    def test_refund_without_capture_is_refused(self):
        self.assertIsNone(self.system.refund("r1", self.intent, 100))

    def test_refund_without_capture_changes_nothing(self):
        self.system.refund("r1", self.intent, 100)
        self.assertEqual(self.system.refunded_total(self.intent), 0)

    def test_refund_of_unknown_intent(self):
        self.assertIsNone(self.system.refund("r1", "nope", 100))

    def test_empty_key_is_refused(self):
        self.assertIsNone(self.system.refund("", self.intent, 100))

    def test_zero_amount_is_refused(self):
        self.assertIsNone(self.system.refund("r1", self.intent, 0))

    def test_negative_amount_is_refused(self):
        self.assertIsNone(self.system.refund("r1", self.intent, -50))

    def test_a_refused_refund_does_not_burn_the_key(self):
        """Otherwise a retry of a rejected request is silently swallowed."""
        self.assertIsNone(self.system.refund("r1", self.intent, 0))
        self.assertIsNone(self.system.refund("r1", self.intent, 100))
        self.assertEqual(self.system.refunded_total(self.intent), 0)

    def test_refund_on_a_confirming_intent_is_refused(self):
        self.system.confirm(self.intent)
        self.assertIsNone(self.system.refund("r1", self.intent, 100))

    def test_refunds_are_per_intent(self):
        other = self.system.create_intent("k2", "acme", 500, "usd")
        self.system.refund("r1", other, 100)
        self.assertEqual(self.system.refunded_total(self.intent), 0)

    def test_level_one_survives(self):
        self.assertEqual(self.system.status(self.intent), "created")
        self.assertIs(self.system.confirm(self.intent), True)
        self.assertIsNone(self.system.create_intent("", "acme", 100, "usd"))

    def test_level_two_survives(self):
        self.assertEqual(self.system.count_by_status(), {"created": 1})
        self.assertEqual(self.system.captured_total("acme"), 0)

    def test_replayed_create_key_still_returns_the_same_intent(self):
        again = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(again, self.intent)

    def test_many_intents_and_refused_refunds(self):
        for index in range(100):
            intent = self.system.create_intent("m%d" % index, "acme", 100, "usd")
            self.assertIsNone(self.system.refund("r%d" % index, intent, 10))
        self.assertEqual(self.system.captured_total("acme"), 0)
