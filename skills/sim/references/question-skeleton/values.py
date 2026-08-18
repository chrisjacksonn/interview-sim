"""Expected values, produced by running the reference against the suite's own
data. DATA and CASES live in tests_hidden.py, defined once; this reads them
from there, with the reference standing in for the candidate's solution."""

import copy
import sys

import reference

# tests_hidden does `from solution import solve`. During authoring there is
# no solution yet; the reference is the solution.
sys.modules["solution"] = reference

import tests_hidden  # noqa: E402  - needs the shim above

if __name__ == "__main__":
    before = copy.deepcopy(tests_hidden.DATA)
    for name, case in tests_hidden.CASES:
        print(name, "->", reference.solve(tests_hidden.DATA, case))
    print("input preserved:", tests_hidden.DATA == before)
