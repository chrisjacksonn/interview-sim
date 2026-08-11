"""Level 2 samples. A sanity check, not the grade."""

import unittest

from solution import LockerSystem


class TestLevel2(unittest.TestCase):
    def test_counts_and_usage(self):
        system = LockerSystem()
        system.store("p1", "B")
        system.store("p2", "A")
        self.assertEqual(system.parcel_count(), 2)
        self.assertEqual(system.lockers_in_use(), ["A", "B"])

    def test_emptied_locker_is_not_in_use(self):
        system = LockerSystem()
        system.store("p1", "B")
        system.store("p2", "A")
        system.retrieve("p1")
        self.assertEqual(system.parcel_count(), 1)
        self.assertEqual(system.lockers_in_use(), ["A"])

    def test_busiest_counts_history(self):
        system = LockerSystem()
        system.store("p1", "B")
        system.retrieve("p1")
        system.store("p2", "B")
        system.store("p3", "A")
        self.assertEqual(system.busiest_locker(), "B")

    def test_busiest_of_nothing(self):
        self.assertIsNone(LockerSystem().busiest_locker())


if __name__ == "__main__":
    unittest.main()
