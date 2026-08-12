"""Level 3 samples. A sanity check, not the grade."""

import unittest

from solution import PaymentSystem


class TestLevel3(unittest.TestCase):
    def test_refund_needs_a_capture(self):
        system = PaymentSystem()
        intent = system.create_intent("k1", "acme", 500, "usd")
        self.assertIsNone(system.refund("r1", intent, 100))

    def test_refunded_total_starts_at_zero(self):
        system = PaymentSystem()
        intent = system.create_intent("k1", "acme", 500, "usd")
        self.assertEqual(system.refunded_total(intent), 0)

    def test_unknown_intent(self):
        self.assertIsNone(PaymentSystem().refunded_total("nope"))

    def test_invalid_amount(self):
        system = PaymentSystem()
        intent = system.create_intent("k1", "acme", 500, "usd")
        self.assertIsNone(system.refund("r1", intent, 0))


if __name__ == "__main__":
    unittest.main()
