"""Level 2 hidden suite.

Never copied into a session workspace.
"""

import unittest

from solution import LockerSystem


class TestLevel2(unittest.TestCase):
    def setUp(self):
        self.system = LockerSystem()

    # --- parcel_count ---

    def test_count_starts_at_zero(self):
        self.assertEqual(self.system.parcel_count(), 0)

    def test_count_rises_and_falls(self):
        self.system.store("p1", "A")
        self.system.store("p2", "B")
        self.assertEqual(self.system.parcel_count(), 2)
        self.system.retrieve("p1")
        self.assertEqual(self.system.parcel_count(), 1)

    def test_refused_store_does_not_change_the_count(self):
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.system.store("p1", "B")
        self.assertEqual(self.system.parcel_count(), 1)

    def test_failed_retrieve_does_not_change_the_count(self):
        self.system.store("p1", "A")
        self.system.retrieve("ghost")
        self.assertEqual(self.system.parcel_count(), 1)

    # --- lockers_in_use ---

    def test_in_use_is_empty_initially(self):
        self.assertEqual(self.system.lockers_in_use(), [])

    def test_in_use_is_sorted(self):
        for locker in ("D", "b", "A", "c"):
            self.system.store("p" + locker, locker)
        self.assertEqual(self.system.lockers_in_use(), sorted(["D", "b", "A", "c"]))

    def test_emptied_locker_drops_out(self):
        self.system.store("p1", "A")
        self.system.store("p2", "B")
        self.system.retrieve("p1")
        self.assertEqual(self.system.lockers_in_use(), ["B"])

    def test_all_emptied_gives_an_empty_list(self):
        self.system.store("p1", "A")
        self.system.retrieve("p1")
        self.assertEqual(self.system.lockers_in_use(), [])

    def test_reused_locker_appears_once(self):
        self.system.store("p1", "A")
        self.system.retrieve("p1")
        self.system.store("p2", "A")
        self.assertEqual(self.system.lockers_in_use(), ["A"])

    def test_returns_a_list_not_a_set(self):
        self.system.store("p1", "A")
        self.assertIsInstance(self.system.lockers_in_use(), list)

    # --- busiest_locker ---

    def test_busiest_of_an_empty_system_is_none(self):
        self.assertIsNone(self.system.busiest_locker())

    def test_busiest_counts_retrieved_parcels_too(self):
        # The whole point of "over the lifetime": B is empty but has taken two.
        self.system.store("p1", "B")
        self.system.retrieve("p1")
        self.system.store("p2", "B")
        self.system.retrieve("p2")
        self.system.store("p3", "A")
        self.assertEqual(self.system.busiest_locker(), "B")

    def test_busiest_after_everything_is_emptied(self):
        self.system.store("p1", "Z")
        self.system.retrieve("p1")
        self.assertEqual(self.system.busiest_locker(), "Z")

    def test_ties_break_by_smallest_id(self):
        self.system.store("p1", "B")
        self.system.store("p2", "A")
        self.assertEqual(self.system.busiest_locker(), "A")

    def test_three_way_tie(self):
        self.system.store("p1", "C")
        self.system.store("p2", "B")
        self.system.store("p3", "A")
        self.assertEqual(self.system.busiest_locker(), "A")

    def test_refused_stores_do_not_count_toward_busiest(self):
        # A gets one real store then two refusals; B gets two real ones.
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.system.store("p3", "A")
        self.system.store("p4", "B")
        self.system.retrieve("p4")
        self.system.store("p5", "B")
        self.assertEqual(self.system.busiest_locker(), "B")

    def test_clear_winner_not_alphabetical(self):
        # Catches anything that just returns the smallest id in use.
        self.system.store("p1", "A")
        for index in range(5):
            self.system.store("q%d" % index, "Z")
            self.system.retrieve("q%d" % index)
        self.assertEqual(self.system.busiest_locker(), "Z")

    # --- level 1 still works ---

    def test_level_one_behaviour_survives(self):
        self.assertTrue(self.system.store("p1", "A"))
        self.assertFalse(self.system.store("p2", "A"))
        self.assertEqual(self.system.locate("p1"), "A")
        self.assertEqual(self.system.retrieve("p1"), "A")


if __name__ == "__main__":
    unittest.main()
