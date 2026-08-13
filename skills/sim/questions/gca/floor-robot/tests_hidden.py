"""Floor Robot hidden suite.

Never copied into a session workspace.

Weighted toward turning, which is where a working-looking robot is usually
wrong in one direction only, and toward the rule that a refused command stops
that command rather than the rest of the string.
"""

import unittest

from solution import Robot


class TestFloorRobot(unittest.TestCase):
    # --- starting state ---

    def test_starts_at_the_origin_facing_north(self):
        self.assertEqual(Robot(5, 5).where(), (0, 0, "N"))

    def test_an_empty_command_string_does_nothing(self):
        robot = Robot(5, 5)
        self.assertEqual(robot.run(""), 0)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_a_one_by_one_floor_is_allowed(self):
        robot = Robot(1, 1)
        self.assertEqual(robot.run("FFFF"), 4)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_a_zero_dimension_raises(self):
        with self.assertRaises(ValueError):
            Robot(0, 5)
        with self.assertRaises(ValueError):
            Robot(5, 0)

    def test_a_negative_dimension_raises(self):
        with self.assertRaises(ValueError):
            Robot(-3, 5)

    # --- turning ---

    def test_right_from_north_is_east(self):
        robot = Robot(5, 5)
        robot.run("R")
        self.assertEqual(robot.where()[2], "E")

    def test_left_from_north_is_west(self):
        robot = Robot(5, 5)
        robot.run("L")
        self.assertEqual(robot.where()[2], "W")

    def test_four_rights_come_home(self):
        robot = Robot(5, 5)
        robot.run("RRRR")
        self.assertEqual(robot.where()[2], "N")

    def test_four_lefts_come_home(self):
        robot = Robot(5, 5)
        robot.run("LLLL")
        self.assertEqual(robot.where()[2], "N")

    def test_the_whole_compass_rightwards(self):
        robot = Robot(5, 5)
        seen = []
        for _ in range(4):
            robot.run("R")
            seen.append(robot.where()[2])
        self.assertEqual(seen, ["E", "S", "W", "N"])

    def test_the_whole_compass_leftwards(self):
        robot = Robot(5, 5)
        seen = []
        for _ in range(4):
            robot.run("L")
            seen.append(robot.where()[2])
        self.assertEqual(seen, ["W", "S", "E", "N"])

    def test_turning_never_refuses(self):
        robot = Robot(1, 1)
        self.assertEqual(robot.run("LRLRLR"), 0)

    # --- moving ---

    def test_forward_goes_the_way_it_faces(self):
        robot = Robot(5, 5)
        robot.run("F")
        self.assertEqual(robot.where(), (0, 1, "N"))
        robot.run("RF")
        self.assertEqual(robot.where(), (1, 1, "E"))

    def test_back_does_not_turn_the_robot(self):
        robot = Robot(5, 5)
        robot.run("FFB")
        self.assertEqual(robot.where(), (0, 1, "N"))

    def test_back_from_each_facing(self):
        robot = Robot(5, 5)
        robot.place(2, 2, "E")
        robot.run("B")
        self.assertEqual(robot.where(), (1, 2, "E"))
        robot.place(2, 2, "S")
        robot.run("B")
        self.assertEqual(robot.where(), (2, 3, "S"))

    def test_a_longer_drive(self):
        robot = Robot(5, 5)
        self.assertEqual(robot.run("FFRFF"), 0)
        self.assertEqual(robot.where(), (2, 2, "E"))

    # --- walls ---

    def test_the_north_wall_refuses(self):
        robot = Robot(3, 3)
        self.assertEqual(robot.run("FFF"), 1)
        self.assertEqual(robot.where(), (0, 2, "N"))

    def test_the_east_wall_refuses(self):
        robot = Robot(3, 3)
        self.assertEqual(robot.run("RFFF"), 1)
        self.assertEqual(robot.where(), (2, 0, "E"))

    def test_the_south_and_west_walls_refuse(self):
        robot = Robot(3, 3)
        self.assertEqual(robot.run("BB"), 2)
        self.assertEqual(robot.run("RBB"), 2)
        self.assertEqual(robot.where(), (0, 0, "E"))

    def test_a_refused_move_does_not_stop_the_rest(self):
        robot = Robot(3, 3)
        self.assertEqual(robot.run("BRF"), 1)
        self.assertEqual(robot.where(), (1, 0, "E"))

    # --- racking ---

    def test_racking_refuses_a_move(self):
        robot = Robot(3, 3)
        robot.block(0, 1)
        self.assertEqual(robot.run("F"), 1)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_driving_around_racking(self):
        robot = Robot(3, 3)
        robot.block(0, 1)
        self.assertEqual(robot.run("RFLFF"), 0)
        self.assertEqual(robot.where(), (1, 2, "N"))

    def test_blocking_off_the_floor_is_refused(self):
        robot = Robot(3, 3)
        self.assertIs(robot.block(5, 5), False)
        self.assertIs(robot.block(-1, 0), False)

    def test_blocking_the_robot_s_own_square_is_refused(self):
        robot = Robot(3, 3)
        self.assertIs(robot.block(0, 0), False)
        self.assertEqual(robot.run("F"), 0)

    def test_blocking_twice_is_fine(self):
        robot = Robot(3, 3)
        self.assertIs(robot.block(1, 1), True)
        self.assertIs(robot.block(1, 1), True)

    def test_racking_blocks_a_backward_move_too(self):
        robot = Robot(3, 3)
        robot.place(1, 1, "N")
        robot.block(1, 0)
        self.assertEqual(robot.run("B"), 1)
        self.assertEqual(robot.where(), (1, 1, "N"))

    # --- placing ---

    def test_place_moves_and_points(self):
        robot = Robot(5, 5)
        self.assertIs(robot.place(3, 4, "S"), True)
        self.assertEqual(robot.where(), (3, 4, "S"))

    def test_place_ignores_what_is_in_between(self):
        robot = Robot(5, 5)
        robot.block(0, 1)
        self.assertIs(robot.place(0, 3, "N"), True)
        self.assertEqual(robot.where(), (0, 3, "N"))

    def test_place_off_the_floor_is_refused_and_changes_nothing(self):
        robot = Robot(3, 3)
        robot.place(1, 1, "E")
        self.assertIs(robot.place(9, 9, "N"), False)
        self.assertEqual(robot.where(), (1, 1, "E"))

    def test_place_onto_racking_is_refused(self):
        robot = Robot(3, 3)
        robot.block(2, 2)
        self.assertIs(robot.place(2, 2, "N"), False)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_a_bad_facing_is_refused(self):
        robot = Robot(3, 3)
        self.assertIs(robot.place(1, 1, "up"), False)
        self.assertIs(robot.place(1, 1, "n"), False)
        self.assertEqual(robot.where(), (0, 0, "N"))

    # --- unrecognised commands ---

    def test_an_unknown_command_is_counted_and_changes_nothing(self):
        robot = Robot(5, 5)
        self.assertEqual(robot.run("X"), 1)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_commands_are_case_sensitive(self):
        robot = Robot(5, 5)
        self.assertEqual(robot.run("f"), 1)
        self.assertEqual(robot.where(), (0, 0, "N"))

    def test_a_space_is_not_a_command(self):
        robot = Robot(5, 5)
        self.assertEqual(robot.run("F F"), 1)
        self.assertEqual(robot.where(), (0, 2, "N"))

    def test_refusals_of_every_kind_add_up(self):
        robot = Robot(2, 2)
        robot.block(1, 1)
        # B into the south wall, X unknown, F to (0,1) works, R faces east,
        # F into the racking at (1,1).
        self.assertEqual(robot.run("BXFRF"), 3)
        self.assertEqual(robot.where(), (0, 1, "E"))

    # --- scale ---

    def test_a_long_command_string(self):
        robot = Robot(1000, 1000)
        self.assertEqual(robot.run("F" * 200000), 200000 - 999)
        self.assertEqual(robot.where(), (0, 999, "N"))

    def test_a_long_circuit(self):
        robot = Robot(1000, 1000)
        robot.run(("F" * 999 + "R") * 4)
        self.assertEqual(robot.where(), (0, 0, "N"))


if __name__ == "__main__":
    unittest.main()
