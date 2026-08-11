"""Level 1 hidden suite.

Never copied into a session workspace. These keep running at every later level.
"""

import unittest

from solution import Ledger


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()

    # --- opening accounts ---

    def test_create_returns_true(self):
        self.assertIs(self.ledger.create_account("a"), True)

    def test_new_account_starts_at_zero(self):
        self.ledger.create_account("a")
        self.assertEqual(self.ledger.balance("a"), 0)

    def test_duplicate_create_returns_false(self):
        self.ledger.create_account("a")
        self.assertIs(self.ledger.create_account("a"), False)

    def test_duplicate_create_does_not_reset_the_balance(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 700)
        self.ledger.create_account("a")
        self.assertEqual(self.ledger.balance("a"), 700)

    def test_ids_are_case_sensitive(self):
        self.assertTrue(self.ledger.create_account("a"))
        self.assertTrue(self.ledger.create_account("A"))
        self.ledger.deposit("a", 10)
        self.assertEqual(self.ledger.balance("A"), 0)

    # --- deposits ---

    def test_deposit_returns_the_new_balance(self):
        self.ledger.create_account("a")
        self.assertEqual(self.ledger.deposit("a", 500), 500)
        self.assertEqual(self.ledger.deposit("a", 250), 750)

    def test_deposit_to_unknown_account(self):
        self.assertIsNone(self.ledger.deposit("ghost", 100))

    def test_deposit_of_zero_is_refused(self):
        self.ledger.create_account("a")
        self.assertIsNone(self.ledger.deposit("a", 0))
        self.assertEqual(self.ledger.balance("a"), 0)

    def test_deposit_of_a_negative_is_refused(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 100)
        self.assertIsNone(self.ledger.deposit("a", -50))
        self.assertEqual(self.ledger.balance("a"), 100)

    # --- withdrawals ---

    def test_withdraw_returns_the_new_balance(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 500)
        self.assertEqual(self.ledger.withdraw("a", 200), 300)

    def test_withdraw_the_exact_balance_is_allowed(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 500)
        self.assertEqual(self.ledger.withdraw("a", 500), 0)

    def test_withdraw_one_more_than_the_balance_is_refused(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 500)
        self.assertIsNone(self.ledger.withdraw("a", 501))
        self.assertEqual(self.ledger.balance("a"), 500)

    def test_refused_withdrawal_leaves_the_balance_alone(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 100)
        self.ledger.withdraw("a", 1000)
        self.assertEqual(self.ledger.balance("a"), 100)

    def test_withdraw_from_an_empty_account(self):
        self.ledger.create_account("a")
        self.assertIsNone(self.ledger.withdraw("a", 1))

    def test_withdraw_from_unknown_account(self):
        self.assertIsNone(self.ledger.withdraw("ghost", 100))

    def test_withdraw_of_zero_is_refused(self):
        self.ledger.create_account("a")
        self.ledger.deposit("a", 100)
        self.assertIsNone(self.ledger.withdraw("a", 0))

    def test_withdraw_of_a_negative_is_refused(self):
        # Otherwise a negative withdrawal is a deposit with no checks.
        self.ledger.create_account("a")
        self.ledger.deposit("a", 100)
        self.assertIsNone(self.ledger.withdraw("a", -500))
        self.assertEqual(self.ledger.balance("a"), 100)

    # --- balances ---

    def test_balance_of_unknown_account_is_none(self):
        self.assertIsNone(self.ledger.balance("ghost"))

    def test_balance_of_a_new_account_is_zero_not_none(self):
        # Zero and "no such account" are different answers.
        self.ledger.create_account("a")
        self.assertEqual(self.ledger.balance("a"), 0)
        self.assertIsNotNone(self.ledger.balance("a"))

    def test_accounts_are_independent(self):
        self.ledger.create_account("a")
        self.ledger.create_account("b")
        self.ledger.deposit("a", 100)
        self.assertEqual(self.ledger.balance("b"), 0)

    def test_two_ledgers_are_independent(self):
        other = Ledger()
        self.ledger.create_account("a")
        self.assertIsNone(other.balance("a"))

    def test_many_accounts(self):
        for index in range(200):
            self.ledger.create_account("acct%03d" % index)
            self.ledger.deposit("acct%03d" % index, index + 1)
        self.assertEqual(self.ledger.balance("acct150"), 151)


if __name__ == "__main__":
    unittest.main()
