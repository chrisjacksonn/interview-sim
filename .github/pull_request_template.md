## What this changes

<!-- One or two lines. -->

## If this adds a question

- [ ] `python3 tools/qa.py` passes locally
- [ ] The question is **original**. Not copied, paraphrased, or reconstructed
      from any real assessment, from anywhere, including from sitting one
      yourself
- [ ] At least three files in `mutants/`, each a plausible wrong answer
- [ ] Expected values in the hidden tests were checked against a throwaway
      brute force, not worked out by hand

If the gate says your reference fails, check the test before the code. Every
time that has happened here, the expected value was wrong rather than the
solution.

## If this changes the engine

- [ ] `python3 -m unittest discover -s tests` passes
- [ ] Python 3.9 syntax, standard library only, no new imports outside stdlib
- [ ] Exit codes unchanged, or SKILL.md updated to match

See [CONTRIBUTING.md](../CONTRIBUTING.md).
