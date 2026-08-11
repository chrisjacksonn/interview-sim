"""Level 4 hidden suite.

Never copied into a session workspace.

Weighted toward the earlier levels on purpose. This level makes account ids
impermanent, which every previous level assumed, and the usual way to fail is to
get merging working while leaving a ghost account behind that still shows up in
balances, volumes, or top_accounts.
"""

import unittest

from solution import Ledger


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.ledger = Ledger()
        self.ledger.create_account("old")
        self.ledger.create_account("new")
        self.ledger.deposit("old", 300)
        self.ledger.deposit("new", 100)

    # --- the merge itself ---

    def test_merge_returns_true(self):
        self.assertIs(self.ledger.merge_accounts("old", "new"), True)

    def test_balances_are_summed(self):
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.balance("new"), 400)

    def test_volumes_are_summed(self):
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.volume("new"), 400)

    def test_merging_is_not_itself_movement(self):
        # Volume must be 400, not 700. Catches solutions that route the merge
        # through deposit or transfer and pick up the volume twice.
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.volume("new"), 400)

    def test_merging_an_empty_account(self):
        self.ledger.create_account("empty")
        self.assertIs(self.ledger.merge_accounts("empty", "new"), True)
        self.assertEqual(self.ledger.balance("new"), 100)
        self.assertEqual(self.ledger.volume("new"), 100)

    def test_merge_into_an_empty_account(self):
        self.ledger.create_account("empty")
        self.ledger.merge_accounts("old", "empty")
        self.assertEqual(self.ledger.balance("empty"), 300)
        self.assertEqual(self.ledger.volume("empty"), 300)

    # --- the source is really gone ---

    def test_source_balance_is_none(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIsNone(self.ledger.balance("old"))

    def test_source_volume_is_none(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIsNone(self.ledger.volume("old"))

    def test_source_cannot_be_deposited_into(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIsNone(self.ledger.deposit("old", 50))

    def test_source_cannot_be_withdrawn_from(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIsNone(self.ledger.withdraw("old", 1))

    def test_source_disappears_from_top_accounts(self):
        # The ghost-account failure: a merged id still being ranked.
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.top_accounts(10), ["new"])

    def test_source_cannot_transfer(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIs(self.ledger.transfer("old", "new", 10), False)

    def test_cannot_transfer_into_the_source(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIs(self.ledger.transfer("new", "old", 10), False)

    def test_source_cannot_be_merged_again(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIs(self.ledger.merge_accounts("old", "new"), False)

    # --- the id is reusable ---

    def test_the_id_can_be_recreated(self):
        self.ledger.merge_accounts("old", "new")
        self.assertIs(self.ledger.create_account("old"), True)

    def test_the_recreated_account_is_empty(self):
        self.ledger.merge_accounts("old", "new")
        self.ledger.create_account("old")
        self.assertEqual(self.ledger.balance("old"), 0)
        self.assertEqual(self.ledger.volume("old"), 0)

    def test_recreating_does_not_disturb_the_target(self):
        self.ledger.merge_accounts("old", "new")
        self.ledger.create_account("old")
        self.assertEqual(self.ledger.balance("new"), 400)

    # --- refusals ---

    def test_merging_an_account_into_itself_is_refused(self):
        # If allowed, an account would double its own balance.
        self.assertIs(self.ledger.merge_accounts("old", "old"), False)
        self.assertEqual(self.ledger.balance("old"), 300)

    def test_unknown_source_is_refused(self):
        self.assertIs(self.ledger.merge_accounts("ghost", "new"), False)
        self.assertEqual(self.ledger.balance("new"), 100)

    def test_unknown_target_is_refused(self):
        self.assertIs(self.ledger.merge_accounts("old", "ghost"), False)
        self.assertEqual(self.ledger.balance("old"), 300)

    def test_refused_merge_does_not_delete_the_source(self):
        self.ledger.merge_accounts("old", "ghost")
        self.assertEqual(self.ledger.balance("old"), 300)

    # --- chains of merges ---

    def test_three_way_merge(self):
        self.ledger.create_account("third")
        self.ledger.deposit("third", 50)
        self.ledger.merge_accounts("old", "new")
        self.ledger.merge_accounts("third", "new")
        self.assertEqual(self.ledger.balance("new"), 450)
        self.assertEqual(self.ledger.volume("new"), 450)
        self.assertEqual(self.ledger.top_accounts(5), ["new"])

    def test_merged_target_can_itself_be_merged(self):
        self.ledger.create_account("final")
        self.ledger.merge_accounts("old", "new")
        self.ledger.merge_accounts("new", "final")
        self.assertEqual(self.ledger.balance("final"), 400)
        self.assertIsNone(self.ledger.balance("new"))

    # --- earlier levels under the new model ---

    def test_level_one_after_a_merge(self):
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.deposit("new", 100), 500)
        self.assertEqual(self.ledger.withdraw("new", 200), 300)
        self.assertIsNone(self.ledger.withdraw("new", 99999))

    def test_level_two_after_a_merge(self):
        self.ledger.create_account("other")
        self.ledger.deposit("other", 1000)
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.top_accounts(2), ["other", "new"])
        self.assertEqual(self.ledger.volume("new"), 400)

    def test_level_three_after_a_merge(self):
        self.ledger.merge_accounts("old", "new")
        self.ledger.create_account("dest")
        self.assertIs(self.ledger.transfer("new", "dest", 400), True)
        self.assertEqual(self.ledger.balance("new"), 0)
        self.assertEqual(self.ledger.balance("dest"), 400)

    def test_merged_balance_is_spendable(self):
        # The merged money has to be real, not just reported.
        self.ledger.merge_accounts("old", "new")
        self.assertEqual(self.ledger.withdraw("new", 400), 0)


if __name__ == "__main__":
    unittest.main()
