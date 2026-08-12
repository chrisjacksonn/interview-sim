"""Level 1 hidden suite. Never copied into a session workspace."""

import unittest

from solution import PaymentSystem


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.system = PaymentSystem()

    def test_create_returns_an_id(self):
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertIsInstance(intent, str)
        self.assertTrue(intent)

    def test_new_intent_is_created(self):
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(self.system.status(intent), "created")

    def test_same_key_returns_the_same_id(self):
        first = self.system.create_intent("k1", "acme", 500, "usd")
        again = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(first, again)

    def test_same_key_does_not_create_a_second_intent(self):
        """One intent, not two, so it can only be confirmed once."""
        first = self.system.create_intent("k1", "acme", 500, "usd")
        again = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertIs(self.system.confirm(first), True)
        self.assertIs(self.system.confirm(again), False)

    def test_replay_after_confirm_does_not_reset_status(self):
        first = self.system.create_intent("k1", "acme", 500, "usd")
        self.system.confirm(first)
        again = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(again, first)
        self.assertEqual(self.system.status(first), "confirming")

    def test_different_keys_are_different_intents(self):
        first = self.system.create_intent("k1", "acme", 500, "usd")
        second = self.system.create_intent("k2", "acme", 500, "usd")
        self.assertNotEqual(first, second)

    def test_same_key_wins_even_with_different_details(self):
        first = self.system.create_intent("k1", "acme", 500, "usd")
        again = self.system.create_intent("k1", "other", 999, "eur")
        self.assertEqual(again, first)

    def test_empty_key_is_refused(self):
        self.assertIsNone(self.system.create_intent("", "acme", 500, "usd"))

    def test_empty_merchant_is_refused(self):
        self.assertIsNone(self.system.create_intent("k1", "", 500, "usd"))

    def test_empty_currency_is_refused(self):
        self.assertIsNone(self.system.create_intent("k1", "acme", 500, ""))

    def test_zero_amount_is_refused(self):
        self.assertIsNone(self.system.create_intent("k1", "acme", 0, "usd"))

    def test_negative_amount_is_refused(self):
        self.assertIsNone(self.system.create_intent("k1", "acme", -5, "usd"))

    def test_a_refused_create_does_not_burn_the_key(self):
        self.assertIsNone(self.system.create_intent("k1", "acme", 0, "usd"))
        self.assertIsNotNone(self.system.create_intent("k1", "acme", 500, "usd"))

    def test_confirm_returns_true_once(self):
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertIs(self.system.confirm(intent), True)

    def test_confirm_twice_is_refused(self):
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.system.confirm(intent)
        self.assertIs(self.system.confirm(intent), False)

    def test_confirm_unknown_intent(self):
        self.assertIs(self.system.confirm("nope"), False)

    def test_status_of_unknown_intent(self):
        self.assertIsNone(self.system.status("nope"))

    def test_intents_are_independent(self):
        first = self.system.create_intent("k1", "acme", 500, "usd")
        second = self.system.create_intent("k2", "acme", 500, "usd")
        self.system.confirm(first)
        self.assertEqual(self.system.status(second), "created")

    def test_two_systems_are_independent(self):
        other = PaymentSystem()
        intent = self.system.create_intent("k1", "acme", 500, "usd")
        self.assertIsNone(other.status(intent))

    def test_many_intents(self):
        ids = [self.system.create_intent("k%d" % i, "acme", 100, "usd") for i in range(200)]
        self.assertEqual(len(set(ids)), 200)
