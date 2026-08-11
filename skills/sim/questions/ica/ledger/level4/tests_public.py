"""Level 4 samples. A sanity check, not the grade."""

import unittest

from solution import Ledger


class TestLevel4(unittest.TestCase):
    def build(self):
        ledger = Ledger()
        ledger.create_account("old")
        ledger.create_account("new")
        ledger.deposit("old", 300)
        ledger.deposit("new", 100)
        return ledger

    def test_merge_sums_balance_and_volume(self):
        ledger = self.build()
        self.assertTrue(ledger.merge_accounts("old", "new"))
        self.assertEqual(ledger.balance("new"), 400)
        self.assertEqual(ledger.volume("new"), 400)

    def test_source_is_gone(self):
        ledger = self.build()
        ledger.merge_accounts("old", "new")
        self.assertIsNone(ledger.balance("old"))
        self.assertIsNone(ledger.deposit("old", 50))

    def test_the_id_becomes_available_again(self):
        ledger = self.build()
        ledger.merge_accounts("old", "new")
        self.assertTrue(ledger.create_account("old"))
        self.assertEqual(ledger.balance("old"), 0)

    def test_refusals(self):
        ledger = self.build()
        self.assertFalse(ledger.merge_accounts("old", "old"))
        self.assertFalse(ledger.merge_accounts("old", "ghost"))


if __name__ == "__main__":
    unittest.main()
