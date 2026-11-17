# Acceptance audit

Run it with:

```
python3 acceptance/run.py
```

Stdlib only, no pip dependencies. It runs every deterministic check in
`acceptance/checks/`, writes `acceptance/state.json`, prints a per-criterion summary, and
exits non-zero if any deterministic check fails or any required artifact is missing.

The full, numbered criteria list is `acceptance/criteria.md`, derived from `AGENTS.md`,
`INSTRUCTIONS.md`, `ironco-fde-hiring-doc.md`, `pod.md`, `baseline.md`, `brands/`,
`feedback/`, `README.md`, and `sim/API.md`.

Criteria split into two groups:

- **`[DET]` — deterministic.** Settled by a runnable script in `acceptance/checks/`
  (structure, one-command contract, untouched sim, provider constraints, no hard-coded
  brand numbers, boundaries, meta usage, escalation config, feedback rules, shipped-run
  scores, eval-matches-notes). These print `PASS`/`FAIL` with a reason.
- **`[LLM]` — judgment.** Things a script cannot settle: judgment-in-skills, whole-chain
  operator loop, read-the-data-first, meta correctness, policy gates genuinely present,
  right-person/right-reason escalation, feedback rules changing behavior, the notes
  Improvements section (0–5), the GOPS skill-review decisions, no-loosened-checks, and the
  final band. These live in `acceptance/llm-criteria.md` with a review
  rubric. The runner lists them as **MANUAL** and **never auto-passes them** — they must be
  judged by a reviewer or an LLM pass.

Checks are honest about the repo's current state. Until the real operator agent is built,
most `[DET]` checks are *expected to FAIL*. Checks are never stubbed or softened to pass;
a wrong check gets fixed to be correct, and a criterion that truly cannot be scripted moves
to the `[LLM]` file instead.
