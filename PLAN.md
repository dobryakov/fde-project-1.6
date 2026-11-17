# PLAN — ironco FDE build

Step-by-step build plan. AC IDs reference `acceptance/criteria.md` (the
`acceptance-auditor` subagent). Re-run `python3 acceptance/run.py` after each step
to watch `[DET]` checks flip green.

**Done already:** guardrails (`.claude/settings.json` deny-rules + Bash hook) and the
acceptance harness (`acceptance/`, `.claude/agents/acceptance-auditor.md`).

Critical path: 1 → 2 → 3/4/5/6 → 8 → 9 → 10 → 11 → 12 → 13.
Steps 3, 4, 6, 7 can parallelize once Step 1's loop interfaces are stable.

---

## Step 1 — Conversation state machine / multi-turn loop
- **Goal:** Drive each creator through the whole chain, not one message then stop.
- **Description:** In `agent/run.py` + `agent/handlers/`, replace the one-shot
  kind-router with a per-creator loop: read state + `inbox`/`thread`/`ops_notices`
  → choose action (message, invite, ship, ticket, escalate, pay, wait) → `advance`
  → re-read, until accept / decline / post / window closes. Carry context.
- **DoD:** A `haggle_rate` / `ghost_then_rate` / `late_poster` task reaches a
  terminal outcome, not a single send.
- **AC:** AC-8 (+ foundation for AC-12/17/18).
- **Cheaper model?** No — core architecture.

## Step 2 — Compliance gates (hard checks in code)
- **Goal:** Zero policy violations by construction.
- **Description:** Deterministic gates before any send/ship/pay: opt-out (flag AND
  stop-language in `data/past-messages.csv`), under-18 gate, honor `ops_notices`
  (held lot, shipping pause), sample rules (one per creator/product, no sample
  during open safety review), bonus-owed verification (valid videos in window,
  paid once). Numbers from `brands/` at runtime.
- **DoD:** Gate unit tests pass; `minor_contact`/`opted_out`/`held_lot` refused.
- **AC:** AC-12, AC-13 (+ AC-6).
- **Cheaper model?** Partly — haiku/sonnet subagent writes gate fns + tests.

## Step 3 — Escalation routing
- **Goal:** Right person, right reason, within the daily cap.
- **Description:** Fix `skills/_shared.md` front matter
  (`escalate_marcus_followers_over: 250000`, populate Tomas/Nora lists) and
  `route_escalation`: Marcus=client/paid/legal, Priya=shipping/data/suspicious,
  Tomas=>250K/creative, Nora=health/skin/pet/minor/unsettled claim; routine
  shipping → `ops_ticket`. Cap 10/run.
- **DoD:** Routing unit tests map sample cases to the right expert; cap enforced.
- **AC:** AC-14, AC-15, AC-16.
- **Cheaper model?** Yes — haiku subagent with tests.

## Step 4 — Data-mining + judgment-in-skills
- **Goal:** Read before acting; judgment in skills, not hard-coded.
- **Description:** Before first message, load creator's `past-messages.csv`
  history, `thread`, `ops_notices`; feed signal into decisions. `agent/skills.py`
  loads `brands/`+`skills/` at runtime; no brand numbers as literals in `agent/`.
- **DoD:** Pre-send context includes past-message outcomes; AC-6 stays green.
- **AC:** AC-6, AC-7, AC-9.
- **Cheaper model?** No for design; yes for the CSV helper.

## Step 5 — Live-campaign post verification
- **Goal:** Pay/nudge only on verified posts.
- **Description:** Before paying/nudging: verify handle (new-handle lookup), post
  link present/fixed, within window, count of valid videos. Multi-turn
  deadline/claim handling.
- **DoD:** `posted_new_handle`, `post_fixed`, `bonus_not_owed` resolve correctly.
- **AC:** AC-12/AC-13 (live paths).
- **Cheaper model?** No — tied to loop logic.

## Step 6 — Messaging + meta correctness
- **Goal:** Structured `meta` that agrees with text and briefs.
- **Description:** `meta=` on `send_invite`/`send_message` with right rate/bonus;
  `decline` on fee/exclusivity/claim/competitor asks; text matches fields.
- **DoD:** meta present on send paths; fields spot-checked against briefs.
- **AC:** AC-10, AC-11.
- **Cheaper model?** Partly — wiring cheap; correctness review with me.

## Step 7 — Env & command contract
- **Goal:** Clean reproducible run.
- **Description:** Add `requirements.txt` (stdlib-only → minimal); confirm
  `agent/llm.py` default `claude_cli` + haiku/sonnet; entry point stable.
- **DoD:** Fresh-env import check passes.
- **AC:** AC-1, AC-2, AC-3.
- **Cheaper model?** Yes — trivial; haiku subagent.

## Step 8 — Round 1 run + iterate
- **Goal:** Real-LLM round-1 score well above the 12.3 floor.
- **Description:** `python3 agent/run.py tasks/round1.jsonl runs/r1` →
  `dashboard.py runs/r1 detail`; mock for plumbing, then real Claude; fix
  failures; fresh folder per attempt. Each exception → skill fix or new step.
- **DoD:** `runs/r1/dashboard.json`: 0 violations, efficiency in band, esc ≤10.
- **AC:** AC-12, AC-14, AC-17, AC-18, AC-25.
- **Cheaper model?** No — real agent + my judgment.

## Step 9 — Brand feedback rules into skills
- **Goal:** Encode the five post-round-1 client rules.
- **Description:** Into `skills/`: no competitor naming; no sweetener/2nd sample on
  haggle (offer filming idea); dog reaction → Nora + no new product until cleared
  + don't blame product; Fernhill deadline as calendar date; Lumen banned/allowed
  words.
- **DoD:** Distinctive tokens in the right files; behavior changes.
- **AC:** AC-19, AC-20.
- **Cheaper model?** Yes — haiku subagent transcribes; I verify behavior.

## Step 10 — Fernhill v3 backup + v4 swap + Round 2 run
- **Goal:** Round-2 world, 10-day window honored.
- **Description:** Save v3 Fernhill brief outside `brands/`,
  `cp feedback/fernhill-skin-v4.md brands/fernhill-skin.md`,
  `sim/simctl.py init runs/r2 pack=sim/round2.pack`, run round 2, iterate.
- **DoD:** `runs/r2/dashboard.json` in band; v3 backup retained.
- **AC:** AC-21, AC-25 (+ AC-12/14/17/18 on r2).
- **Cheaper model?** No — run + iteration.

## Step 11 — GOPS skill review
- **Goal:** Fold in helpful GOPS edits; reject one-offs/loosenings.
- **Description:** For all 9 files in `gops-local-skills/` (Ana/Ben/Cleo):
  promote / merge / reject / keep-local with reason; edit `skills/` to match;
  never promote an edit that loosens a check; nothing reads `gops-local-skills/`
  at runtime.
- **DoD:** Decision per file; `skills/` updated; AC-32 green.
- **AC:** AC-30, AC-31, AC-32.
- **Cheaper model?** Partly — sonnet subagent drafts; I make final calls.

## Step 12 — notes.md write-up
- **Goal:** The graded narrative + eval numbers.
- **Description:** Four headings — Improvements (exception → skill change/new step +
  file/section + run), Skill review, Design, Eval (before/after both rounds, run
  folder named per score). Record time spent.
- **DoD:** Headings present; Eval numbers equal shipped `dashboard.json`.
- **AC:** AC-24, AC-26, AC-28, AC-29.
- **Cheaper model?** Partly — sonnet subagent drafts; I own Improvements quality.

## Step 13 — README, session export, final audit
- **Goal:** Ship-ready, in the hire band.
- **Description:** Replace `README.md` (one command, model, settings); export the
  coding-agent transcript; run `python3 acceptance/run.py` until all `[DET]` pass
  and manually clear `[LLM]` criteria against the rubric.
- **DoD:** Auditor exit 0 on DET; all `[LLM]` reviewed; total ≥86.
- **AC:** AC-23, AC-27, AC-33.
- **Cheaper model?** No — final verification with me.
