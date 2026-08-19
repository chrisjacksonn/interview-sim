# Security

What this skill can do on your machine, why, and where the lines are.

## Capabilities and why they exist

- **Run Python** (`Bash(python3:*)`): the engine, grader, and clock are Python
  scripts, and generated questions are validated by running them. The
  permission is a prefix rule and cannot be narrowed to `session.py` alone,
  because permission rules match command prefixes and the install path varies
  per machine.
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
- **Writes are confined** to the session directory (`./interview-sim-sessions/`
  in the folder you run from, self-gitignored) and the session scratchpad.
  The engine refuses a generated question set placed inside your working
  directory, because it contains the answer key.
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
