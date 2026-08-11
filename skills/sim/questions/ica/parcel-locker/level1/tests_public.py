"""Level 1 samples. A sanity check, not the grade."""

import unittest

from solution import LockerSystem


class TestLevel1(unittest.TestCase):
    def test_store_and_locate(self):
        system = LockerSystem()
        self.assertTrue(system.store("p1", "A"))
        self.assertEqual(system.locate("p1"), "A")

    def test_occupied_locker_is_refused(self):
        system = LockerSystem()
        system.store("p1", "A")
        self.assertFalse(system.store("p2", "A"))

    def test_duplicate_parcel_is_refused(self):
        system = LockerSystem()
        system.store("p1", "A")
        self.assertFalse(system.store("p1", "B"))

    def test_retrieve_frees_the_locker(self):
        system = LockerSystem()
        system.store("p1", "A")
        self.assertEqual(system.retrieve("p1"), "A")
        self.assertIsNone(system.locate("p1"))
        self.assertTrue(system.store("p2", "A"))

    def test_retrieve_missing_parcel(self):
        self.assertIsNone(LockerSystem().retrieve("nope"))


if __name__ == "__main__":
    unittest.main()
