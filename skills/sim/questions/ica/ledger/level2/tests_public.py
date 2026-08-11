"""Level 2 samples. A sanity check, not the grade."""

import unittest

from solution import Ledger


class TestLevel2(unittest.TestCase):
    def build(self):
        ledger = Ledger()
        for name in ("alice", "bob", "carol"):
            ledger.create_account(name)
        ledger.deposit("alice", 100)
        ledger.withdraw("alice", 40)
        ledger.deposit("bob", 500)
        return ledger

    def test_volume_counts_both_directions(self):
        self.assertEqual(self.build().volume("alice"), 140)

    def test_untouched_account_has_zero_volume(self):
        self.assertEqual(self.build().volume("carol"), 0)

    def test_top_accounts(self):
        self.assertEqual(self.build().top_accounts(2), ["bob", "alice"])

    def test_top_accounts_beyond_the_end(self):
        self.assertEqual(self.build().top_accounts(10), ["bob", "alice", "carol"])

    def test_top_accounts_of_zero(self):
        self.assertEqual(self.build().top_accounts(0), [])


if __name__ == "__main__":
    unittest.main()
