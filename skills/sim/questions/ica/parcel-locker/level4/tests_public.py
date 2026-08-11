"""Level 4 samples. A sanity check, not the grade."""

import unittest

from solution import LockerSystem


class TestLevel4(unittest.TestCase):
    def test_bigger_locker_takes_more(self):
        system = LockerSystem()
        self.assertTrue(system.set_capacity("A", 3))
        self.assertTrue(system.store("p1", "A"))
        self.assertTrue(system.store("p2", "A"))
        self.assertTrue(system.store("p3", "A"))
        self.assertFalse(system.store("p4", "A"))
        self.assertEqual(system.contents("A"), ["p1", "p2", "p3"])

    def test_default_capacity_is_one(self):
        system = LockerSystem()
        self.assertEqual(system.capacity("B"), 1)
        system.store("p1", "B")
        self.assertFalse(system.store("p2", "B"))

    def test_shrinking_below_occupancy_is_refused(self):
        system = LockerSystem()
        system.set_capacity("A", 3)
        system.store("p1", "A")
        system.store("p2", "A")
        self.assertFalse(system.set_capacity("A", 1))
        self.assertFalse(system.set_capacity("A", 0))

    def test_retrieving_makes_room(self):
        system = LockerSystem()
        system.set_capacity("A", 2)
        system.store("p1", "A")
        system.store("p2", "A")
        system.retrieve("p1")
        self.assertTrue(system.store("p3", "A"))


if __name__ == "__main__":
    unittest.main()
