# Security

What this skill can do on your machine, why, and where the lines are.

## Capabilities and why they exist

- **Run Python** (`Bash(python3:*)`): the engine, grader, and clock are
  Python scripts, and generated questions are validated by running them. A
  narrower pattern over the shell string was tried and abandoned: it is not an
  injection boundary (any pattern over a command is satisfiable by
  construction), so the behavioral rule below is the real line, stated
  honestly instead of scoped cosmetically. Writing a generated question also
  runs `cp` and `cat` through Bash to lay down and fill its files, and this
  pattern does not cover either one; those calls run on whatever permission
  mode you are already in, which is one more reason the skill asks for auto
  mode before research starts, not only to remove friction on the `python3`
  calls this bullet covers.
- **Fetch and search the web** (`WebFetch`, `WebSearch`): live research into
  what a company's screen currently is. This is the product's core mechanism;
  a version without it is a different tool.
- **Read and glob files**: the proctor re-reads your solution file, and only
  ever inside the session workspace and the skill's own directory.

## The lines

- **Fetched content is data, never instructions.** The skill's rules forbid
  executing or obeying anything found in a web page, and restrict `python3`
  to the engine and files the agent itself wrote in the session.
- **The engine opens no network connection.** `session.py` and `grade.py`
  import nothing that could; the clock and grading are entirely local.
  Research is done by the agent, exactly as if you searched yourself.
- **Grading runs your own code with no sandbox.** `submit` and `debrief` run
  your `solution.py`; the mutation gate, before the clock starts, runs
  `reference.py`, the untouched `starter.py`, and each mutant the same way.
  All of it happens in a subprocess with a timeout, so a hang or a crash
  cannot take down the session or corrupt the result channel. That subprocess
  is not a security boundary: it runs as you, with your filesystem and network
  access, because it is your own code on your own machine.
- **Writes are confined** to the session directory (`./interview-sim-sessions/`
  in the folder you run from, self-gitignored), throwaway OS temp directories
  the grader and the mutation gate each create and clean up per run, and one
  pair of files at the invoking directory itself: a `./timer` shim and the
  `.gitignore` entry that hides it, refreshed on every session start but never
  overwriting a `./timer` that is not already one of ours. The engine refuses
  a generated question set placed inside your working directory, because it
  contains the answer key.
- **It cannot change its own permissions.** Auto mode is suggested once, in
  words; only you can enable it. Know the trade when you do: auto mode
  approves this session's tool calls without prompting, which is what keeps a
  timed sitting uninterrupted and also what removes the prompt as a
  checkpoint. Scope it to a practice directory if that matters to you.
- **Nothing cheat-adjacent.** No interaction with live assessments or
  proctoring systems, ever. See [ETHICS.md](ETHICS.md).

## Residual risk, stated plainly

A skill that both fetches untrusted web content and executes an interpreter
carries prompt-injection risk in principle. The mitigations are the
behavioral rule above, source discipline (candidate-report pages only, hard
fetch ceilings), and the engine's own refusals. A scanner will still flag the
capability combination, and it is right that the combination exists: it is
the product.

## Reporting

Open an issue. Anything security-shaped is treated as urgent.
