"""Deliberately wrong: silently skips unrecognised characters instead of counting them

Used by tools/qa.py to prove the hidden suite can tell this from correct.
"""

FACINGS = ("N", "E", "S", "W")
DELTAS = {"N": (0, 1), "E": (1, 0), "S": (0, -1), "W": (-1, 0)}


class Robot:
    def __init__(self, width, height):
        if not isinstance(width, int) or isinstance(width, bool) or width < 1:
            raise ValueError("width must be a positive integer")
        if not isinstance(height, int) or isinstance(height, bool) or height < 1:
            raise ValueError("height must be a positive integer")
        self.width = width
        self.height = height
        self.x = 0
        self.y = 0
        self.facing = "N"
        self._blocked = set()

    def _on_floor(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

    def _free(self, x, y):
        return self._on_floor(x, y) and (x, y) not in self._blocked

    def block(self, x, y):
        if not self._on_floor(x, y) or (x, y) == (self.x, self.y):
            return False
        self._blocked.add((x, y))
        return True

    def place(self, x, y, facing):
        if facing not in FACINGS or not self._free(x, y):
            return False
        self.x, self.y, self.facing = x, y, facing
        return True

    def _step(self, sign):
        dx, dy = DELTAS[self.facing]
        target = (self.x + dx * sign, self.y + dy * sign)
        if not self._free(target[0], target[1]):
            return False
        self.x, self.y = target
        return True

    def run(self, commands):
        refused = 0
        for command in commands:
            if command == "L":
                self.facing = FACINGS[(FACINGS.index(self.facing) - 1) % 4]
            elif command == "R":
                self.facing = FACINGS[(FACINGS.index(self.facing) + 1) % 4]
            elif command == "F":
                if not self._step(1):
                    refused += 1
            elif command == "B":
                if not self._step(-1):
                    refused += 1
            else:
                pass
        return refused

    def where(self):
        return (self.x, self.y, self.facing)
