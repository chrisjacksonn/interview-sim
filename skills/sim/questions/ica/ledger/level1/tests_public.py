"""Level 1 samples. A sanity check, not the grade."""

import unittest

from solution import Ledger


class TestLevel1(unittest.TestCase):
    def test_open_and_deposit(self):
        ledger = Ledger()
        self.assertTrue(ledger.create_account("alice"))
        self.assertEqual(ledger.deposit("alice", 500), 500)
        self.assertEqual(ledger.balance("alice"), 500)

    def test_duplicate_account(self):
        ledger = Ledger()
        ledger.create_account("alice")
        self.assertFalse(ledger.create_account("alice"))

    def test_withdraw(self):
        ledger = Ledger()
        ledger.create_account("alice")
        ledger.deposit("alice", 500)
        self.assertEqual(ledger.withdraw("alice", 200), 300)

    def test_overdraw_is_refused(self):
        ledger = Ledger()
        ledger.create_account("alice")
        ledger.deposit("alice", 100)
        self.assertIsNone(ledger.withdraw("alice", 1000))
        self.assertEqual(ledger.balance("alice"), 100)

    def test_unknown_account(self):
        ledger = Ledger()
        self.assertIsNone(ledger.deposit("bob", 100))
        self.assertIsNone(ledger.balance("bob"))


if __name__ == "__main__":
    unittest.main()
