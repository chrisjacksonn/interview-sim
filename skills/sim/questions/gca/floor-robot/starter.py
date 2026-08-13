"""Floor Robot.

Read problem.md for the full statement.
"""


class Robot:
    """A robot on a rectangular floor, with racking in the way."""

    def __init__(self, width, height):
        raise NotImplementedError

    def block(self, x, y):
        """Put racking on a square. False if refused."""
        raise NotImplementedError

    def place(self, x, y, facing):
        """Move the robot and point it. False if refused."""
        raise NotImplementedError

    def run(self, commands):
        """Execute the commands in order. Returns how many were refused."""
        raise NotImplementedError

    def where(self):
        """(x, y, facing)."""
        raise NotImplementedError
