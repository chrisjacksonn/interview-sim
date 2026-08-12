"""Level 4 hidden suite.

Never copied into a session workspace.

Weighted toward the earlier levels and toward money, because that is where the
damage is. Every previous level treated status as something a call sets. It is
now decided by callbacks that may arrive twice, late, or in the wrong order, and
the usual way to fail is to get captures working while a duplicate quietly
charges twice or a stale decline undoes one.
"""

import unittest

from solution import PaymentSystem


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.system = PaymentSystem()
        self.intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.system.confirm(self.intent)

    # --- capturing ---

    def test_capture_returns_true(self):
        self.assertIs(self.system.processor_callback("cb1", self.intent, "captured"), True)

    def test_capture_sets_the_status(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertEqual(self.system.status(self.intent), "captured")

    def test_capture_defaults_to_the_full_amount(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertEqual(self.system.captured_total("acme"), 500)

    def test_a_partial_capture_is_what_counts(self):
        self.system.processor_callback("cb1", self.intent, "captured", 300)
        self.assertEqual(self.system.captured_total("acme"), 300)

    def test_decline_sets_the_status(self):
        self.system.processor_callback("cb1", self.intent, "declined")
        self.assertEqual(self.system.status(self.intent), "declined")

    def test_decline_captures_nothing(self):
        self.system.processor_callback("cb1", self.intent, "declined")
        self.assertEqual(self.system.captured_total("acme"), 0)

    # --- at least once means duplicates ---

    def test_duplicate_callback_returns_false(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertIs(self.system.processor_callback("cb1", self.intent, "captured"), False)

    def test_duplicate_capture_does_not_charge_twice(self):
        """The one that costs real money."""
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertEqual(self.system.captured_total("acme"), 500)

    def test_a_replayed_id_is_ignored_even_with_different_contents(self):
        self.system.processor_callback("cb1", self.intent, "captured", 500)
        self.system.processor_callback("cb1", self.intent, "captured", 9999)
        self.assertEqual(self.system.captured_total("acme"), 500)

    def test_duplicate_decline_is_also_ignored(self):
        self.system.processor_callback("cb1", self.intent, "declined")
        self.assertIs(self.system.processor_callback("cb1", self.intent, "declined"), False)

    def test_callback_ids_are_global_not_per_intent(self):
        other = self.system.create_intent("k2", "acme", 700, "usd")
        self.system.confirm(other)
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertIs(self.system.processor_callback("cb1", other, "captured"), False)

    # --- capture is final ---

    def test_a_later_decline_cannot_undo_a_capture(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertIs(self.system.processor_callback("cb2", self.intent, "declined"), False)
        self.assertEqual(self.system.status(self.intent), "captured")

    def test_a_later_decline_does_not_take_the_money_back(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.processor_callback("cb2", self.intent, "declined")
        self.assertEqual(self.system.captured_total("acme"), 500)

    def test_a_second_distinct_capture_does_not_charge_again(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.processor_callback("cb2", self.intent, "captured")
        self.assertEqual(self.system.captured_total("acme"), 500)

    def test_a_decline_can_be_followed_by_a_capture(self):
        # Only capture is final. A decline is not the end of the story.
        self.system.processor_callback("cb1", self.intent, "declined")
        self.assertIs(self.system.processor_callback("cb2", self.intent, "captured"), True)
        self.assertEqual(self.system.status(self.intent), "captured")

    # --- bad callbacks ---

    def test_empty_callback_id_is_refused(self):
        self.assertIs(self.system.processor_callback("", self.intent, "captured"), False)
        self.assertEqual(self.system.status(self.intent), "confirming")

    def test_unknown_intent_is_refused(self):
        self.assertIs(self.system.processor_callback("cb1", "nope", "captured"), False)

    def test_unrecognised_outcome_is_refused(self):
        self.assertIs(self.system.processor_callback("cb1", self.intent, "maybe"), False)
        self.assertEqual(self.system.status(self.intent), "confirming")

    def test_a_refused_callback_does_not_burn_its_id(self):
        self.system.processor_callback("cb1", "nope", "captured")
        self.assertIs(self.system.processor_callback("cb1", self.intent, "captured"), True)

    # --- refunds, now that there is something to refund ---

    def test_refund_after_capture(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertEqual(self.system.refund("r1", self.intent, 200), 200)
        self.assertEqual(self.system.refunded_total(self.intent), 200)

    def test_refund_is_idempotent(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertEqual(self.system.refund("r1", self.intent, 200), 200)
        self.assertEqual(self.system.refund("r1", self.intent, 200), 200)
        self.assertEqual(self.system.refunded_total(self.intent), 200)

    def test_refunds_accumulate(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.refund("r1", self.intent, 200)
        self.system.refund("r2", self.intent, 100)
        self.assertEqual(self.system.refunded_total(self.intent), 300)

    def test_refund_up_to_the_full_capture(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertEqual(self.system.refund("r1", self.intent, 500), 500)

    def test_refund_beyond_the_capture_is_refused(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertIsNone(self.system.refund("r1", self.intent, 501))

    def test_refunds_cannot_exceed_the_capture_in_aggregate(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.refund("r1", self.intent, 400)
        self.assertIsNone(self.system.refund("r2", self.intent, 200))
        self.assertEqual(self.system.refunded_total(self.intent), 400)

    def test_the_ceiling_is_the_capture_not_the_intent_amount(self):
        """A processor may capture less than was asked for."""
        self.system.processor_callback("cb1", self.intent, "captured", 300)
        self.assertIsNone(self.system.refund("r1", self.intent, 400))
        self.assertEqual(self.system.refund("r2", self.intent, 300), 300)

    def test_refund_on_a_declined_intent_is_refused(self):
        self.system.processor_callback("cb1", self.intent, "declined")
        self.assertIsNone(self.system.refund("r1", self.intent, 100))

    def test_a_replayed_refund_does_not_double_count_against_the_ceiling(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.refund("r1", self.intent, 500)
        self.system.refund("r1", self.intent, 500)
        self.assertEqual(self.system.refunded_total(self.intent), 500)

    # --- earlier levels under the new model ---

    def test_level_one_survives(self):
        again = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(again, self.intent)
        self.assertIs(self.system.confirm(self.intent), False)
        self.assertIsNone(self.system.status("nope"))

    def test_level_two_counts_the_new_statuses(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        other = self.system.create_intent("k2", "acme", 100, "usd")
        self.system.confirm(other)
        self.system.processor_callback("cb2", other, "declined")
        self.assertEqual(self.system.count_by_status(), {"captured": 1, "declined": 1})

    def test_level_two_totals_are_per_merchant(self):
        other = self.system.create_intent("k2", "globex", 700, "usd")
        self.system.confirm(other)
        self.system.processor_callback("cb1", self.intent, "captured")
        self.system.processor_callback("cb2", other, "captured")
        self.assertEqual(self.system.captured_total("acme"), 500)
        self.assertEqual(self.system.captured_total("globex"), 700)

    def test_level_three_rules_still_apply(self):
        self.system.processor_callback("cb1", self.intent, "captured")
        self.assertIsNone(self.system.refund("", self.intent, 100))
        self.assertIsNone(self.system.refund("r1", self.intent, 0))
        self.assertIsNone(self.system.refund("r1", "nope", 100))

    def test_scale(self):
        for index in range(200):
            intent = self.system.create_intent("m%d" % index, "big", 100, "usd")
            self.system.confirm(intent)
            self.system.processor_callback("c%d" % index, intent, "captured")
            self.system.processor_callback("c%d" % index, intent, "captured")
        self.assertEqual(self.system.captured_total("big"), 20000)


if __name__ == "__main__":
    unittest.main()
