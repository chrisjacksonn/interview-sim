"""Level 4 hidden suite.

Never copied into a session workspace.

Weighted toward the earlier levels. A file used to have one size and now has a
history, and the usual way to fail is to make versioning work while total_size,
largest, or find start reporting history instead of the live size.
"""

import unittest

from solution import FileStore


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.store = FileStore()
        self.store.add("a.txt", 100)

    # --- update ---

    def test_update_returns_true(self):
        self.assertIs(self.store.update("a.txt", 250), True)

    def test_update_changes_the_live_size(self):
        self.store.update("a.txt", 250)
        self.assertEqual(self.store.get("a.txt"), 250)

    def test_update_unknown_file_is_refused(self):
        self.assertIs(self.store.update("ghost", 5), False)

    def test_update_with_a_negative_size_is_refused(self):
        self.assertIs(self.store.update("a.txt", -1), False)
        self.assertEqual(self.store.get("a.txt"), 100)

    def test_update_to_zero_is_allowed(self):
        self.assertIs(self.store.update("a.txt", 0), True)
        self.assertEqual(self.store.get("a.txt"), 0)

    def test_add_still_refuses_an_existing_name(self):
        # update is how a file changes; add must not become an alias for it.
        self.assertIs(self.store.add("a.txt", 500), False)
        self.assertEqual(self.store.get("a.txt"), 100)

    # --- version_count ---

    def test_new_file_has_one_version(self):
        self.assertEqual(self.store.version_count("a.txt"), 1)

    def test_version_count_rises_with_updates(self):
        self.store.update("a.txt", 1)
        self.store.update("a.txt", 2)
        self.assertEqual(self.store.version_count("a.txt"), 3)

    def test_version_count_of_unknown_file(self):
        self.assertIsNone(self.store.version_count("ghost"))

    def test_refused_update_does_not_add_a_version(self):
        self.store.update("a.txt", -5)
        self.assertEqual(self.store.version_count("a.txt"), 1)

    # --- revert ---

    def test_revert_restores_the_previous_size(self):
        self.store.update("a.txt", 250)
        self.assertIs(self.store.revert("a.txt"), True)
        self.assertEqual(self.store.get("a.txt"), 100)

    def test_revert_lowers_the_version_count(self):
        self.store.update("a.txt", 250)
        self.store.revert("a.txt")
        self.assertEqual(self.store.version_count("a.txt"), 1)

    def test_cannot_revert_the_only_version(self):
        self.assertIs(self.store.revert("a.txt"), False)
        self.assertEqual(self.store.get("a.txt"), 100)

    def test_revert_unknown_file(self):
        self.assertIs(self.store.revert("ghost"), False)

    def test_revert_down_a_long_history(self):
        for size in (10, 20, 30):
            self.store.update("a.txt", size)
        self.store.revert("a.txt")
        self.store.revert("a.txt")
        self.assertEqual(self.store.get("a.txt"), 10)
        self.assertEqual(self.store.version_count("a.txt"), 2)

    def test_update_after_revert_starts_a_new_branch(self):
        self.store.update("a.txt", 250)
        self.store.revert("a.txt")
        self.store.update("a.txt", 400)
        self.assertEqual(self.store.get("a.txt"), 400)
        self.assertEqual(self.store.version_count("a.txt"), 2)

    # --- history must not leak into the reports ---

    def test_total_size_uses_the_live_version_only(self):
        # The failure here reports 350, the sum of the whole history.
        self.store.update("a.txt", 250)
        self.assertEqual(self.store.total_size(), 250)

    def test_total_size_after_revert(self):
        self.store.update("a.txt", 250)
        self.store.revert("a.txt")
        self.assertEqual(self.store.total_size(), 100)

    def test_largest_uses_the_live_version(self):
        self.store.add("b.txt", 200)
        self.store.update("a.txt", 1)
        self.assertEqual(self.store.largest(2), ["b.txt", "a.txt"])

    def test_largest_reflects_an_update_upwards(self):
        self.store.add("b.txt", 200)
        self.store.update("a.txt", 999)
        self.assertEqual(self.store.largest(1), ["a.txt"])

    def test_prefix_total_uses_the_live_version(self):
        self.store.add("docs/x", 10)
        self.store.update("docs/x", 70)
        self.assertEqual(self.store.total_size_with_prefix("docs/"), 70)

    def test_find_lists_a_versioned_file_once(self):
        self.store.update("a.txt", 250)
        self.store.update("a.txt", 260)
        self.assertEqual(self.store.find("a"), ["a.txt"])

    def test_get_returns_the_newest(self):
        self.store.update("a.txt", 250)
        self.store.update("a.txt", 260)
        self.assertEqual(self.store.get("a.txt"), 260)

    # --- delete removes the whole history ---

    def test_delete_returns_the_live_size(self):
        self.store.update("a.txt", 250)
        self.assertEqual(self.store.delete("a.txt"), 250)

    def test_delete_removes_every_version(self):
        self.store.update("a.txt", 250)
        self.store.delete("a.txt")
        self.assertIsNone(self.store.version_count("a.txt"))

    def test_readding_after_delete_starts_at_one_version(self):
        self.store.update("a.txt", 250)
        self.store.delete("a.txt")
        self.store.add("a.txt", 7)
        self.assertEqual(self.store.version_count("a.txt"), 1)
        self.assertEqual(self.store.get("a.txt"), 7)

    def test_cannot_revert_after_readding(self):
        self.store.update("a.txt", 250)
        self.store.delete("a.txt")
        self.store.add("a.txt", 7)
        self.assertIs(self.store.revert("a.txt"), False)

    # --- earlier levels under the new model ---

    def test_level_one_survives(self):
        self.assertIsNone(self.store.get("ghost"))
        self.assertIsNone(self.store.delete("ghost"))
        self.assertIs(self.store.add("", 5), False)
        self.assertIs(self.store.add("b.txt", -1), False)

    def test_level_two_survives(self):
        self.store.add("b.txt", 0)
        self.assertEqual(self.store.largest(2), ["a.txt", "b.txt"])
        self.assertEqual(self.store.total_size(), 100)

    def test_level_three_survives(self):
        self.store.add("docs/z", 5)
        self.assertEqual(self.store.find("docs/"), ["docs/z"])
        self.assertEqual(self.store.total_size_with_prefix(""), 105)
