"""Produce every expected value by running the reference. Data and cases are
defined once, here; run it, paste the printed answers into the suites."""

import copy

from reference import solve

DATA = []  # the dataset every case runs against

CASES = [
    # ("test_name", CASE_ARGS),
]

if __name__ == "__main__":
    before = copy.deepcopy(DATA)
    for name, case in CASES:
        print(name, "->", solve(DATA, case))
    print("input preserved:", DATA == before)
