"""Level 4 hidden suite.

Never copied into a session workspace.

Heavy on backward compatibility on purpose. This level makes the internal model
wrong (one parcel per locker becomes many), and the usual way to fail it is to
get multi-parcel lockers working while quietly breaking level 1.
"""

import unittest

from solution import LockerSystem


class TestLevel4(unittest.TestCase):
    def setUp(self):
        self.system = LockerSystem()

    # --- capacity ---

    def test_default_capacity_is_one(self):
        self.assertEqual(self.system.capacity("never-seen"), 1)

    def test_set_capacity_returns_true(self):
        self.assertIs(self.system.set_capacity("A", 5), True)
        self.assertEqual(self.system.capacity("A"), 5)

    def test_capacity_below_one_is_refused(self):
        self.assertIs(self.system.set_capacity("A", 0), False)
        self.assertIs(self.system.set_capacity("A", -3), False)
        self.assertEqual(self.system.capacity("A"), 1)

    def test_capacity_of_exactly_one_is_allowed(self):
        self.assertIs(self.system.set_capacity("A", 1), True)

    def test_shrinking_below_occupancy_is_refused(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.assertIs(self.system.set_capacity("A", 1), False)
        self.assertEqual(self.system.capacity("A"), 3)

    def test_shrinking_to_exactly_occupancy_is_allowed(self):
        self.system.set_capacity("A", 4)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.assertIs(self.system.set_capacity("A", 2), True)
        self.assertIs(self.system.store("p3", "A"), False)

    def test_capacity_can_be_raised_later(self):
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p2", "A"), False)
        self.assertIs(self.system.set_capacity("A", 2), True)
        self.assertIs(self.system.store("p2", "A"), True)

    # --- storing into a bigger locker ---

    def test_fills_to_capacity_then_refuses(self):
        self.system.set_capacity("A", 3)
        for index in range(3):
            self.assertIs(self.system.store("p%d" % index, "A"), True)
        self.assertIs(self.system.store("p9", "A"), False)

    def test_duplicate_id_still_refused_even_with_room(self):
        self.system.set_capacity("A", 5)
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p1", "A"), False)

    def test_duplicate_across_lockers_still_refused(self):
        self.system.set_capacity("A", 5)
        self.system.set_capacity("B", 5)
        self.system.store("p1", "A")
        self.assertIs(self.system.store("p1", "B"), False)

    def test_retrieving_makes_room(self):
        self.system.set_capacity("A", 2)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.system.retrieve("p1")
        self.assertIs(self.system.store("p3", "A"), True)

    def test_retrieve_returns_the_right_locker_with_many_inside(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.assertEqual(self.system.retrieve("p2"), "A")
        self.assertEqual(self.system.locate("p1"), "A")

    # --- contents ---

    def test_contents_is_sorted(self):
        self.system.set_capacity("A", 4)
        for parcel in ("pz", "pa", "pm"):
            self.system.store(parcel, "A")
        self.assertEqual(self.system.contents("A"), ["pa", "pm", "pz"])

    def test_contents_of_an_empty_locker(self):
        self.assertEqual(self.system.contents("nothing"), [])

    def test_contents_after_retrieval(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.system.retrieve("p1")
        self.assertEqual(self.system.contents("A"), ["p2"])

    # --- earlier levels must still hold ---

    def test_level_one_unconfigured_locker_holds_one(self):
        self.assertIs(self.system.store("p1", "B"), True)
        self.assertIs(self.system.store("p2", "B"), False)

    def test_level_two_counts_every_parcel_in_a_big_locker(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.assertEqual(self.system.parcel_count(), 2)

    def test_level_two_in_use_lists_a_big_locker_once(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.assertEqual(self.system.lockers_in_use(), ["A"])

    def test_level_two_in_use_drops_a_big_locker_only_when_empty(self):
        self.system.set_capacity("A", 2)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.system.retrieve("p1")
        self.assertEqual(self.system.lockers_in_use(), ["A"])
        self.system.retrieve("p2")
        self.assertEqual(self.system.lockers_in_use(), [])

    def test_level_two_busiest_counts_each_store_in_a_big_locker(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A")
        self.system.store("p2", "A")
        self.system.store("p3", "B")
        self.assertEqual(self.system.busiest_locker(), "A")

    def test_level_three_purge_inside_a_big_locker(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A", 5)
        self.system.store("p2", "A", 100)
        self.system.store("p3", "A")
        self.assertEqual(self.system.purge(10), 1)
        self.assertEqual(self.system.contents("A"), ["p2", "p3"])

    def test_level_three_purge_frees_capacity(self):
        self.system.set_capacity("A", 2)
        self.system.store("p1", "A", 1)
        self.system.store("p2", "A", 1)
        self.assertIs(self.system.store("p3", "A"), False)
        self.assertEqual(self.system.purge(5), 2)
        self.assertIs(self.system.store("p3", "A"), True)

    def test_level_three_expires_at_with_many_inside(self):
        self.system.set_capacity("A", 3)
        self.system.store("p1", "A", 5)
        self.system.store("p2", "A")
        self.assertEqual(self.system.expires_at("p1"), 5)
        self.assertIsNone(self.system.expires_at("p2"))


if __name__ == "__main__":
    unittest.main()
