"""Level 1 hidden suite.

Never copied into a session workspace. These keep running at every later level,
so breaking any of them while adding a feature costs marks.
"""

import unittest

from solution import LockerSystem


class TestLevel1(unittest.TestCase):
    def setUp(self):
        self.system = LockerSystem()

    # --- storing ---

    def test_store_returns_true(self):
        self.assertIs(self.system.store("p1", "A"), True)

    def test_store_into_occupied_locker_returns_false(self):
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p2", "A"), False)

    def test_refused_store_does_not_displace_the_sitting_parcel(self):
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.assertEqual(self.system.locate("p1"), "A")
        self.assertIsNone(self.system.locate("p2"))

    def test_duplicate_parcel_id_is_refused(self):
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p1", "B"), False)

    def test_refused_duplicate_leaves_the_original_alone(self):
        self.system.store("p1", "A")
        self.system.store("p1", "B")
        self.assertEqual(self.system.locate("p1"), "A")

    def test_same_parcel_into_the_same_locker_is_still_a_duplicate(self):
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p1", "A"), False)

    def test_many_lockers(self):
        for index in range(50):
            self.assertTrue(self.system.store("p%d" % index, "L%d" % index))
        self.assertEqual(self.system.locate("p37"), "L37")

    # --- locating ---

    def test_locate_missing_parcel(self):
        self.assertIsNone(self.system.locate("ghost"))

    def test_locate_does_not_remove(self):
        self.system.store("p1", "A")
        self.system.locate("p1")
        self.assertEqual(self.system.locate("p1"), "A")

    # --- retrieving ---

    def test_retrieve_returns_the_locker(self):
        self.system.store("p1", "A")
        self.assertEqual(self.system.retrieve("p1"), "A")

    def test_retrieve_missing_returns_none(self):
        self.assertIsNone(self.system.retrieve("ghost"))

    def test_retrieve_twice_returns_none_the_second_time(self):
        self.system.store("p1", "A")
        self.system.retrieve("p1")
        self.assertIsNone(self.system.retrieve("p1"))

    def test_retrieve_frees_the_locker(self):
        self.system.store("p1", "A")
        self.system.retrieve("p1")
        self.assertIs(self.system.store("p2", "A"), True)

    def test_parcel_id_can_be_reused_after_retrieval(self):
        self.system.store("p1", "A")
        self.system.retrieve("p1")
        self.assertIs(self.system.store("p1", "B"), True)
        self.assertEqual(self.system.locate("p1"), "B")

    def test_retrieving_one_parcel_does_not_disturb_others(self):
        self.system.store("p1", "A")
        self.system.store("p2", "B")
        self.system.retrieve("p1")
        self.assertEqual(self.system.locate("p2"), "B")

    # --- ids ---

    def test_ids_are_case_sensitive(self):
        self.assertTrue(self.system.store("p1", "A"))
        self.assertTrue(self.system.store("P1", "a"))
        self.assertEqual(self.system.locate("p1"), "A")
        self.assertEqual(self.system.locate("P1"), "a")

    def test_two_systems_are_independent(self):
        other = LockerSystem()
        self.system.store("p1", "A")
        self.assertIsNone(other.locate("p1"))
        self.assertTrue(other.store("p1", "A"))


if __name__ == "__main__":
    unittest.main()
