"""Level 3 hidden suite.

Never copied into a session workspace.
"""

import unittest

from solution import LockerSystem


class TestLevel3(unittest.TestCase):
    def setUp(self):
        self.system = LockerSystem()

    # --- backward compatibility, the point of the optional argument ---

    def test_two_argument_store_still_works(self):
        self.assertIs(self.system.store("p1", "A"), True)

    def test_two_argument_store_still_refuses_an_occupied_locker(self):
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p2", "A"), False)

    def test_undated_parcel_survives_any_purge(self):
        self.system.store("p1", "A")
        self.assertEqual(self.system.purge(10 ** 9), 0)
        self.assertEqual(self.system.locate("p1"), "A")

    # --- the boundary ---

    def test_expiry_is_inclusive(self):
        self.system.store("p1", "A", 10)
        self.assertEqual(self.system.purge(10), 1)

    def test_one_before_the_deadline_survives(self):
        self.system.store("p1", "A", 10)
        self.assertEqual(self.system.purge(9), 0)
        self.assertEqual(self.system.locate("p1"), "A")

    def test_well_past_the_deadline(self):
        self.system.store("p1", "A", 10)
        self.assertEqual(self.system.purge(11), 1)

    def test_zero_and_negative_times(self):
        self.system.store("p1", "A", 0)
        self.system.store("p2", "B", -5)
        self.assertEqual(self.system.purge(0), 2)

    # --- purge behaviour ---

    def test_purge_returns_the_number_removed(self):
        self.system.store("p1", "A", 1)
        self.system.store("p2", "B", 1)
        self.system.store("p3", "C", 100)
        self.assertEqual(self.system.purge(50), 2)

    def test_purge_of_nothing_returns_zero(self):
        self.assertEqual(self.system.purge(5), 0)

    def test_purge_twice_does_not_double_count(self):
        self.system.store("p1", "A", 1)
        self.assertEqual(self.system.purge(5), 1)
        self.assertEqual(self.system.purge(5), 0)

    def test_purged_locker_becomes_free(self):
        self.system.store("p1", "A", 1)
        self.system.purge(5)
        self.assertIs(self.system.store("p2", "A"), True)

    def test_purged_parcel_id_is_reusable(self):
        self.system.store("p1", "A", 1)
        self.system.purge(5)
        self.assertIs(self.system.store("p1", "B"), True)

    def test_purge_updates_the_level_two_reports(self):
        self.system.store("p1", "A", 1)
        self.system.store("p2", "B")
        self.system.purge(5)
        self.assertEqual(self.system.parcel_count(), 1)
        self.assertEqual(self.system.lockers_in_use(), ["B"])

    def test_purge_does_not_change_lifetime_store_counts(self):
        # A took two parcels historically; purging must not erase that.
        self.system.store("p1", "A", 1)
        self.system.purge(5)
        self.system.store("p2", "A", 1)
        self.system.purge(5)
        self.system.store("p3", "B")
        self.assertEqual(self.system.busiest_locker(), "A")

    def test_purge_leaves_unexpired_parcels_alone(self):
        self.system.store("p1", "A", 100)
        self.system.store("p2", "B", 1)
        self.system.purge(50)
        self.assertEqual(self.system.locate("p1"), "A")
        self.assertIsNone(self.system.locate("p2"))

    def test_purge_many(self):
        for index in range(100):
            self.system.store("p%d" % index, "L%d" % index, index)
        self.assertEqual(self.system.purge(49), 50)
        self.assertEqual(self.system.parcel_count(), 50)

    # --- expires_at ---

    def test_expires_at_returns_the_deadline(self):
        self.system.store("p1", "A", 77)
        self.assertEqual(self.system.expires_at("p1"), 77)

    def test_expires_at_of_an_undated_parcel_is_none(self):
        self.system.store("p1", "A")
        self.assertIsNone(self.system.expires_at("p1"))

    def test_expires_at_of_a_missing_parcel_is_none(self):
        self.assertIsNone(self.system.expires_at("ghost"))

    def test_expires_at_after_retrieval_is_none(self):
        self.system.store("p1", "A", 5)
        self.system.retrieve("p1")
        self.assertIsNone(self.system.expires_at("p1"))

    def test_retrieve_still_works_on_a_dated_parcel(self):
        self.system.store("p1", "A", 5)
        self.assertEqual(self.system.retrieve("p1"), "A")


if __name__ == "__main__":
    unittest.main()
