"""Level 3 samples. A sanity check, not the grade."""

import unittest

from solution import LockerSystem


class TestLevel3(unittest.TestCase):
    def test_purge_removes_due_parcels(self):
        system = LockerSystem()
        system.store("p1", "A", 10)
        system.store("p2", "B", 20)
        system.store("p3", "C")
        self.assertEqual(system.purge(5), 0)
        self.assertEqual(system.purge(10), 1)
        self.assertIsNone(system.locate("p1"))
        self.assertEqual(system.parcel_count(), 2)

    def test_undated_parcels_never_expire(self):
        system = LockerSystem()
        system.store("p1", "A", 10)
        system.store("p2", "B")
        system.purge(1000)
        self.assertEqual(system.lockers_in_use(), ["B"])

    def test_expires_at_reports_the_deadline(self):
        system = LockerSystem()
        system.store("p1", "A", 42)
        self.assertEqual(system.expires_at("p1"), 42)
        self.assertIsNone(system.expires_at("missing"))

    def test_old_two_argument_store_still_works(self):
        system = LockerSystem()
        self.assertTrue(system.store("p1", "A"))
        self.assertEqual(system.locate("p1"), "A")


if __name__ == "__main__":
    unittest.main()
