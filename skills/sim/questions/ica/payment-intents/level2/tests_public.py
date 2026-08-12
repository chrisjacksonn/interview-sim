"""Level 2 samples. A sanity check, not the grade."""

import unittest

from solution import PaymentSystem


class TestLevel2(unittest.TestCase):
    def build(self):
        system = PaymentSystem()
        self.a = system.create_intent("k1", "acme", 500, "usd")
        system.create_intent("k2", "acme", 300, "usd")
        system.create_intent("k3", "globex", 100, "usd")
        return system

    def test_counts_by_status(self):
        system = self.build()
        system.confirm(self.a)
        self.assertEqual(system.count_by_status(), {"confirming": 1, "created": 2})

    def test_nothing_captured_yet(self):
        self.assertEqual(self.build().captured_total("acme"), 0)

    def test_unknown_merchant(self):
        self.assertEqual(self.build().captured_total("nobody"), 0)

    def test_empty_system(self):
        self.assertEqual(PaymentSystem().count_by_status(), {})


if __name__ == "__main__":
    unittest.main()
