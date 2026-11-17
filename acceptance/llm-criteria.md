# Acceptance — LLM-decision criteria (MANUAL)

These criteria need judgment a script cannot settle. `acceptance/run.py` lists them as
`MANUAL` and never auto-passes them. Ids match `acceptance/criteria.md`. A future LLM or
human pass uses the rubric below against the live repo (and, for AC-33, the test run).

---

### AC-7 — Judgment in skills, not hard-coded answers
- Look at: `agent/handlers/*`, `agent/*.py`, `skills/*.md`. Does per-task behavior come
  from reading `skills/` + `brands/` at run time, or are there branches keyed to specific
  task_ids / creator_ids / seen phrasings?
- Pass: rates, bonuses, routing, wording guidance flow from skills/briefs; no answer is
  pinned to a known task id or memorized visible-task output. Fail if you find `if
  task_id == "R1xx"` style special-casing or brand numbers inline (see AC-6).

### AC-8 — Whole-chain, multi-turn operator loop
- Look at: each handler. Is there a real `while window open:` loop that `advance`s, reads
  `inbox`/`thread`, and re-acts until accept/decline/post/close — across samples, live,
  inbound, outreach?
- Pass: conversations are worked to a result (negotiate, ship, wait for post, pay bonus,
  follow up), not one send-and-stop. Fail if any kind sends once and returns.

### AC-9 — Read the data before acting
- Look at: where the agent decides to message/invite. Does it consult
  `data/past-messages.csv` (stop-language + prior outcome for this creator), the creator's
  `thread`, and the task `ops_notices` before the first send?
- Pass: a pre-send gate reads history + notices and suppresses/adjusts accordingly. Fail if
  it only checks the `do_not_contact` flag or ignores notices.

### AC-11 — meta correctness
- Look at: `meta` dicts built for `send_invite`/`send_message`, against the brand brief.
- Pass: `rate` equals the creator's correct brief rate and appears in text; bonus fields
  match the brief; `stance` is `decline` for fee/exclusivity/claim/competitor asks;
  `claims` carries no banned claim; text agrees with fields. Fail on any wrong number or an
  `accept` on those asks.

### AC-13 — Policy gates genuinely present
- Look at: opt-out (flag + history), minor/under-18 gate, notices (held lot, shipping
  pause), sample rules (one per product, repeat-sample block, open-safety-review block),
  bonus-owed verification (valid videos in window, handle match, link present).
- Pass: each gate is a real code/skill check that would block the bad action on an unseen
  task. Fail if a gate is missing or only pattern-matches the visible cases.

### AC-16 — Right person, right reason, right channel
- Look at: escalation routing + ops-ticket logic vs `pod.md`.
- Pass: Marcus = client-approval/paid/terms-outside-limits/legal; Priya = shipping/lots/
  addresses/data/suspicious; Tomas = >250K followers/creative/collab; Nora = health/skin/
  pet reaction/minor/unsettled claim. Routine shipping/address/damage → `ops_ticket`, not
  an expert. Brief-settled calls are decided, not escalated. Fail on wrong routee,
  over-escalation, or escalating a brief-settled decision.

### AC-20 — Feedback rules change behavior
- Look at: the five feedback rules (AC-19) in action, not just pasted text.
- Pass: no competitor name ever emitted to a creator even when the creator names one;
  rate-haggle replies offer a filming idea, never a second sample; any dog reaction routes
  to Nora, blocks new product, and thanks without blaming/clearing the product; Fernhill
  bonus deadline rendered as a calendar date computed from delivery + current brief window;
  Lumen banned words never emitted, allowed words available. Fail if any rule is inert.

### AC-29 — Improvements section (0–5)
- Look at: `notes.md` → Improvements.
- Pass (5): every distinct exception seen in rounds 1 and 2 (ghost, fee haggle, wrong
  address, late post, minor, held lot, shipping pause, repeat sample, reaction, bonus-not-
  owed, new-handle, missing-link, competitor-named, etc.) has a row: exception → skill
  change or named new step/handler → file+function/section → the run that shows it. Some
  exceptions require a *step*, not wording. Deduct toward 0 for missing exceptions, vague
  "improved wording" fixes where a step was needed, or no run cited.

### AC-30 — Skill review decisions
- Look at: `notes.md` → Skill review vs the 9 files in `gops-local-skills/`
  (ana: kettle-pushback, follow-ups; ben: delivered-not-received, open-review-check,
  nudges; cleo: same-video, bonus-check, paid-once, lumen-french).
- Pass: each file marked promote / merge / reject / keep-local with 1–2 line reason;
  conflicts between GOPS resolved with a stated direction; `skills/` actually edited to
  reflect promotes/merges; repeated hand-patches turned into a workflow step. Fail on any
  unaddressed file or a promote that contradicts a brief/pod.md.

### AC-31 — No loosened checks
- Look at: diffs to `acceptance/checks/`, any test/threshold, and promoted GOPS skills.
- Pass: wrong outputs were fixed, not checks softened; no promoted GOPS edit weakens a
  policy gate, rate, bonus rule, or sample rule. Fail on any threshold relaxed to pass or a
  loosening edit promoted.

### AC-33 — Final band (roll-up verdict)
- Look at: shipped `runs/*/dashboard.json` + the Eval table + (when available) the 25-task
  test-run score, minus the AC-29 deduction.
- Pass: total ≥ 86 (hire); ≥ 92 (strong). Eval table shows before/after on both rounds
  with the run folder named next to every score. This is the final human verdict.
