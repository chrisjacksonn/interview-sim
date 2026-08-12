"""Level 1 samples. A sanity check, not the grade."""

import unittest

from solution import PaymentSystem


class TestLevel1(unittest.TestCase):
    def test_create_and_status(self):
        system = PaymentSystem()
        intent = system.create_intent("req-1", "acme", 500, "usd")
        self.assertIsNotNone(intent)
        self.assertEqual(system.status(intent), "created")

    def test_same_key_is_the_same_intent(self):
        system = PaymentSystem()
        first = system.create_intent("req-1", "acme", 500, "usd")
        again = system.create_intent("req-1", "acme", 500, "usd")
        self.assertEqual(first, again)

    def test_confirm_moves_it_once(self):
        system = PaymentSystem()
        intent = system.create_intent("req-1", "acme", 500, "usd")
        self.assertTrue(system.confirm(intent))
        self.assertEqual(system.status(intent), "confirming")
        self.assertFalse(system.confirm(intent))

    def test_invalid_amount(self):
        system = PaymentSystem()
        self.assertIsNone(system.create_intent("req-2", "acme", 0, "usd"))

    def test_unknown_intent(self):
        self.assertIsNone(PaymentSystem().status("nope"))


if __name__ == "__main__":
    unittest.main()
