"""Level 2 hidden suite.

Never copied into a session workspace.
"""

import unittest

from solution import Ledger


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()

    def open(self, *names):
        for name in names:
            self.ledger.create_account(name)

    # --- volume ---

    def test_volume_starts_at_zero(self):
        self.open("a")
        self.assertEqual(self.ledger.volume("a"), 0)

    def test_volume_of_unknown_account_is_none(self):
        self.assertIsNone(self.ledger.volume("ghost"))

    def test_zero_volume_is_not_none(self):
        self.open("a")
        self.assertIsNotNone(self.ledger.volume("a"))

    def test_deposits_add_to_volume(self):
        self.open("a")
        self.ledger.deposit("a", 100)
        self.ledger.deposit("a", 50)
        self.assertEqual(self.ledger.volume("a"), 150)

    def test_withdrawals_add_to_volume_rather_than_subtracting(self):
        # The common wrong answer here is 60, which is the balance.
        self.open("a")
        self.ledger.deposit("a", 100)
        self.ledger.withdraw("a", 40)
        self.assertEqual(self.ledger.volume("a"), 140)

    def test_volume_is_not_the_balance(self):
        self.open("a")
        self.ledger.deposit("a", 100)
        self.ledger.withdraw("a", 100)
        self.assertEqual(self.ledger.balance("a"), 0)
        self.assertEqual(self.ledger.volume("a"), 200)

    def test_refused_deposit_does_not_count(self):
        self.open("a")
        self.ledger.deposit("a", 100)
        self.ledger.deposit("a", 0)
        self.ledger.deposit("a", -30)
        self.assertEqual(self.ledger.volume("a"), 100)

    def test_refused_withdrawal_does_not_count(self):
        self.open("a")
        self.ledger.deposit("a", 100)
        self.ledger.withdraw("a", 5000)
        self.assertEqual(self.ledger.volume("a"), 100)

    # --- top_accounts ordering ---

    def test_orders_by_volume_descending(self):
        self.open("a", "b", "c")
        self.ledger.deposit("a", 10)
        self.ledger.deposit("b", 300)
        self.ledger.deposit("c", 50)
        self.assertEqual(self.ledger.top_accounts(3), ["b", "c", "a"])

    def test_ties_break_alphabetically(self):
        self.open("zed", "amy")
        self.ledger.deposit("zed", 100)
        self.ledger.deposit("amy", 100)
        self.assertEqual(self.ledger.top_accounts(2), ["amy", "zed"])

    def test_tie_break_does_not_override_volume(self):
        # Catches solutions that sort by id first, or sort ascending.
        self.open("amy", "zed")
        self.ledger.deposit("amy", 1)
        self.ledger.deposit("zed", 999)
        self.assertEqual(self.ledger.top_accounts(2), ["zed", "amy"])

    def test_zero_volume_accounts_are_still_listed(self):
        self.open("a", "b")
        self.ledger.deposit("a", 10)
        self.assertEqual(self.ledger.top_accounts(2), ["a", "b"])

    def test_all_zero_volumes_are_alphabetical(self):
        self.open("c", "a", "b")
        self.assertEqual(self.ledger.top_accounts(3), ["a", "b", "c"])

    # --- top_accounts count handling ---

    def test_count_smaller_than_the_number_of_accounts(self):
        self.open("a", "b", "c")
        self.ledger.deposit("a", 30)
        self.ledger.deposit("b", 20)
        self.ledger.deposit("c", 10)
        self.assertEqual(self.ledger.top_accounts(2), ["a", "b"])

    def test_count_larger_than_the_number_of_accounts(self):
        self.open("a")
        self.assertEqual(self.ledger.top_accounts(50), ["a"])

    def test_count_of_zero(self):
        self.open("a")
        self.assertEqual(self.ledger.top_accounts(0), [])

    def test_negative_count(self):
        # A plain slice would return the whole list minus one here.
        self.open("a", "b", "c")
        self.assertEqual(self.ledger.top_accounts(-1), [])

    def test_no_accounts_at_all(self):
        self.assertEqual(self.ledger.top_accounts(5), [])

    def test_returns_a_list(self):
        self.open("a")
        self.assertIsInstance(self.ledger.top_accounts(1), list)

    def test_returns_ids_not_pairs(self):
        self.open("a")
        self.ledger.deposit("a", 5)
        self.assertEqual(self.ledger.top_accounts(1), ["a"])

    # --- level 1 still works ---

    def test_level_one_behaviour_survives(self):
        self.open("a")
        self.assertEqual(self.ledger.deposit("a", 100), 100)
        self.assertEqual(self.ledger.withdraw("a", 40), 60)
        self.assertIsNone(self.ledger.withdraw("a", 1000))
        self.assertIsNone(self.ledger.balance("ghost"))

    def test_scale(self):
        for index in range(500):
            name = "acct%03d" % index
            self.ledger.create_account(name)
            self.ledger.deposit(name, index + 1)
        self.assertEqual(self.ledger.top_accounts(3), ["acct499", "acct498", "acct497"])
        self.assertEqual(self.ledger.volume("acct499"), 500)


if __name__ == "__main__":
    unittest.main()
