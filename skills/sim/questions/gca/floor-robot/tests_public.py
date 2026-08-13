"""Samples. Passing these is not the grade."""

import unittest

from solution import Robot


class TestFloorRobot(unittest.TestCase):
    def test_drive_and_turn(self):
        robot = Robot(5, 5)
        self.assertEqual(robot.run("FFRFF"), 0)
        self.assertEqual(robot.where(), (2, 2, "E"))

    def test_walls_refuse(self):
        robot = Robot(3, 3)
        self.assertEqual(robot.run("BBBB"), 4)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_racking_refuses_one_command_only(self):
        robot = Robot(3, 3)
        robot.block(0, 1)
        self.assertEqual(robot.run("FRF"), 1)
        self.assertEqual(robot.where(), (1, 0, "E"))


if __name__ == "__main__":
    unittest.main()
