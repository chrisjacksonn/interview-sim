"""Level 4 samples. A sanity check, not the grade."""

import unittest

from solution import PaymentSystem


class TestLevel4(unittest.TestCase):
    def build(self):
        system = PaymentSystem()
        intent = system.create_intent("k1", "acme", 500, "usd")
        system.confirm(intent)
        return system, intent

    def test_capture(self):
        system, intent = self.build()
        self.assertTrue(system.processor_callback("cb-1", intent, "captured"))
        self.assertEqual(system.status(intent), "captured")
        self.assertEqual(system.captured_total("acme"), 500)

    def test_duplicate_callback_does_nothing(self):
        system, intent = self.build()
        system.processor_callback("cb-1", intent, "captured")
        self.assertFalse(system.processor_callback("cb-1", intent, "captured"))
        self.assertEqual(system.captured_total("acme"), 500)

    def test_capture_is_final(self):
        system, intent = self.build()
        system.processor_callback("cb-1", intent, "captured")
        self.assertFalse(system.processor_callback("cb-2", intent, "declined"))
        self.assertEqual(system.status(intent), "captured")

    def test_refund_is_idempotent(self):
        system, intent = self.build()
        system.processor_callback("cb-1", intent, "captured")
        self.assertEqual(system.refund("r1", intent, 200), 200)
        self.assertEqual(system.refund("r1", intent, 200), 200)
        self.assertEqual(system.refunded_total(intent), 200)

    def test_refund_cannot_exceed_capture(self):
        system, intent = self.build()
        system.processor_callback("cb-1", intent, "captured")
        system.refund("r1", intent, 200)
        self.assertIsNone(system.refund("r2", intent, 400))


if __name__ == "__main__":
    unittest.main()
