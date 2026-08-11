"""Level 3 samples. A sanity check, not the grade."""

import unittest

from solution import Ledger


class TestLevel3(unittest.TestCase):
    def build(self):
        ledger = Ledger()
        ledger.create_account("alice")
        ledger.create_account("bob")
        ledger.deposit("alice", 500)
        return ledger

    def test_transfer_moves_money(self):
        ledger = self.build()
        self.assertTrue(ledger.transfer("alice", "bob", 200))
        self.assertEqual(ledger.balance("alice"), 300)
        self.assertEqual(ledger.balance("bob"), 200)

    def test_transfer_counts_for_both_volumes(self):
        ledger = self.build()
        ledger.transfer("alice", "bob", 200)
        self.assertEqual(ledger.volume("alice"), 700)
        self.assertEqual(ledger.volume("bob"), 200)

    def test_insufficient_funds(self):
        ledger = self.build()
        self.assertFalse(ledger.transfer("alice", "bob", 9999))

    def test_same_account(self):
        self.assertFalse(self.build().transfer("alice", "alice", 10))

    def test_unknown_account(self):
        self.assertFalse(self.build().transfer("alice", "ghost", 10))


if __name__ == "__main__":
    unittest.main()
