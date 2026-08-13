# Floor Robot

A warehouse robot drives around a rectangular floor, taking instructions as a
string. Racking blocks some squares, and the floor has walls: the robot does not
fall off the edge and it does not drive through racking.

Build a class `Robot`.

## The API

```python
Robot(width, height)
```

A floor `width` squares across and `height` squares deep. `(0, 0)` is the
bottom-left square, `(width - 1, height - 1)` is the top-right. Both are at
least 1. Anything else raises `ValueError`.

The robot starts at `(0, 0)` facing `"N"`. Facings are `"N"`, `"E"`, `"S"`,
`"W"`.

```python
block(x, y) -> bool
```

Put racking on a square. `True` if it was blocked, `False` if the square is off
the floor or the robot is standing on it.

```python
place(x, y, facing) -> bool
```

Move the robot to a square and point it somewhere, ignoring whatever is in
between. `False` if the square is off the floor, blocked, or the facing is not
one of the four, in which case the robot does not move at all.

```python
run(commands) -> int
```

Execute a string of commands, in order:

- `"L"` turn ninety degrees left, `"R"` turn ninety degrees right
- `"F"` move one square forward, `"B"` move one square back without turning

Return **the number of commands that could not be carried out**: moves into a
wall or into racking. Turns always work. An unrecognised character is also a
refusal, and is counted, and changes nothing.

A blocked move stops that command only. The rest of the string still runs.

```python
where() -> tuple
```

`(x, y, facing)`.

## Examples

```python
robot = Robot(5, 5)
robot.run("FFRFF")
robot.where()          # (2, 2, 'E')
```

```python
robot = Robot(3, 3)
robot.run("BBBB")      # 4, it starts at the bottom-left facing north
robot.where()          # (0, 0, 'N')
```

```python
robot = Robot(3, 3)
robot.block(0, 1)
robot.run("FRF")       # 1, the F into the racking is refused, the rest runs
robot.where()          # (1, 0, 'E')
```

## Constraints

- Commands are a string, possibly empty. Case matters: `"f"` is not `"F"`, it is
  an unrecognised character.
- Command strings can be up to 200,000 characters, on a floor up to 1,000 by
  1,000.
- `block` on an already-blocked square is fine and returns `True`.
- Only the constructor raises. Everything else returns a value.
