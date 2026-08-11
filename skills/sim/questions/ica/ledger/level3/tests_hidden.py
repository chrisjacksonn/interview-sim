"""Level 3 hidden suite.

Never copied into a session workspace.
"""

import unittest

from solution import Ledger


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        for name in ("alice", "bob"):
            self.ledger.create_account(name)
        self.ledger.deposit("alice", 500)

    # --- the money moves ---

    def test_transfer_returns_true(self):
        self.assertIs(self.ledger.transfer("alice", "bob", 200), True)

    def test_source_is_debited(self):
        self.ledger.transfer("alice", "bob", 200)
        self.assertEqual(self.ledger.balance("alice"), 300)

    def test_target_is_credited(self):
        self.ledger.transfer("alice", "bob", 200)
        self.assertEqual(self.ledger.balance("bob"), 200)

    def test_total_money_is_conserved(self):
        before = self.ledger.balance("alice") + self.ledger.balance("bob")
        self.ledger.transfer("alice", "bob", 137)
        after = self.ledger.balance("alice") + self.ledger.balance("bob")
        self.assertEqual(before, after)

    def test_transfer_the_entire_balance(self):
        self.assertIs(self.ledger.transfer("alice", "bob", 500), True)
        self.assertEqual(self.ledger.balance("alice"), 0)

    # --- volume counts for both ---

    def test_volume_rises_for_the_source(self):
        self.ledger.transfer("alice", "bob", 200)
        self.assertEqual(self.ledger.volume("alice"), 700)

    def test_volume_rises_for_the_target(self):
        self.ledger.transfer("alice", "bob", 200)
        self.assertEqual(self.ledger.volume("bob"), 200)

    def test_transfer_affects_top_accounts(self):
        self.ledger.transfer("alice", "bob", 500)
        # alice 1000, bob 500.
        self.assertEqual(self.ledger.top_accounts(2), ["alice", "bob"])

    # --- refusals ---

    def test_insufficient_funds_is_refused(self):
        self.assertIs(self.ledger.transfer("alice", "bob", 501), False)

    def test_refused_transfer_moves_nothing(self):
        self.ledger.transfer("alice", "bob", 9999)
        self.assertEqual(self.ledger.balance("alice"), 500)
        self.assertEqual(self.ledger.balance("bob"), 0)

    def test_refused_transfer_does_not_touch_volume(self):
        # Catches solutions that credit volume before checking the balance.
        self.ledger.transfer("alice", "bob", 9999)
        self.assertEqual(self.ledger.volume("alice"), 500)
        self.assertEqual(self.ledger.volume("bob"), 0)

    def test_same_account_is_refused(self):
        self.assertIs(self.ledger.transfer("alice", "alice", 10), False)

    def test_same_account_transfer_changes_nothing(self):
        # A self transfer that "works" can silently double the volume.
        self.ledger.transfer("alice", "alice", 10)
        self.assertEqual(self.ledger.balance("alice"), 500)
        self.assertEqual(self.ledger.volume("alice"), 500)

    def test_unknown_source_is_refused(self):
        self.assertIs(self.ledger.transfer("ghost", "bob", 10), False)

    def test_unknown_target_is_refused(self):
        self.assertIs(self.ledger.transfer("alice", "ghost", 10), False)

    def test_unknown_target_does_not_debit_the_source(self):
        self.ledger.transfer("alice", "ghost", 10)
        self.assertEqual(self.ledger.balance("alice"), 500)

    def test_unknown_target_is_not_created(self):
        self.ledger.transfer("alice", "ghost", 10)
        self.assertIsNone(self.ledger.balance("ghost"))

    def test_zero_amount_is_refused(self):
        self.assertIs(self.ledger.transfer("alice", "bob", 0), False)

    def test_negative_amount_is_refused(self):
        # Otherwise this is a transfer in the opposite direction with no checks.
        self.assertIs(self.ledger.transfer("alice", "bob", -100), False)
        self.assertEqual(self.ledger.balance("bob"), 0)

    def test_transfer_from_an_empty_account(self):
        self.assertIs(self.ledger.transfer("bob", "alice", 1), False)

    # --- chains ---

    def test_chain_of_transfers(self):
        self.ledger.create_account("carol")
        self.ledger.transfer("alice", "bob", 300)
        self.ledger.transfer("bob", "carol", 100)
        self.assertEqual(self.ledger.balance("alice"), 200)
        self.assertEqual(self.ledger.balance("bob"), 200)
        self.assertEqual(self.ledger.balance("carol"), 100)

    # --- earlier levels ---

    def test_level_one_still_works(self):
        self.assertEqual(self.ledger.withdraw("alice", 100), 400)
        self.assertIsNone(self.ledger.withdraw("alice", 100000))
        self.assertIsNone(self.ledger.balance("ghost"))

    def test_level_two_still_works(self):
        self.assertEqual(self.ledger.volume("alice"), 500)
        self.assertEqual(self.ledger.top_accounts(1), ["alice"])
        self.assertEqual(self.ledger.top_accounts(0), [])


if __name__ == "__main__":
    unittest.main()
