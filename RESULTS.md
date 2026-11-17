# RESULTS — ironco FDE build

End-to-end build ran against the plan in [PLAN.md](PLAN.md). Summary of what was built
and where it landed.

**Wall-time:** ~63 minutes end-to-end (single Claude Code / Opus session; created 13:39Z,
last activity 14:42Z), agent-driven.

## Results (real `claude_cli` runs)

| Run | Score | Band | Violations | Escalation F1 | Efficiency | Outreach confirmed |
|:-|:-|:-|:-|:-|:-|:-|
| **Round 2** (`runs/r2`, this build) | **91.8** | hire | **0** | 1.00 (1/1) | 11.5/15 (mpc 6.17) | 120/116 |
| Round 2 (mid build) | 85.8 | no | 0 | 1.00 | 7.3/15 | rate 0.907 |
| Round 2 (prior build) | 81.1 | — | 0 | 1.00 | 6.1/15 | 97/116 |
| **Round 1** (`runs/r1`, this build, fernhill v4) | **86.0** | hire | **0** | 1.00 (3/3) | 15/15 | 93/90 |
| Round 1 (prior build, recorded under fernhill v3) | 90.7 | hire | 0 | 1.00 | 15/15 | 93/90 |
| Baseline | 12.3 / 0.0 | no | 6 / 14 | 0.00 | — | 92/90, 85/116 |

**Score-maximizing passes (round 2: 74.4 → 75.7 → 81.1):**
- *Per-language invites* — invites sent in the creator's language (translated once per
  language, cached, numbers preserved, English fallback). R101 (93/90) and R201 (60/58)
  cleared target.
- *LLM "draft under constraints"* — conversation replies (inbound/sample/live) are drafted by
  the model around facts fixed in code (`agent/convo.py` `compose`), validated to contain no
  wrong rate/$, banned claim or competitor, with a template fallback; `meta` is always decided
  in code. Fixed R212 and R215; the validation also blocks a draft echoing a creator's counter
  rate (R103 stays violation-free). `negotiate` calls now appear in `runs/r2/llm_calls.jsonl`.
- *Data-driven pool picker* — now live for pool picks (`agent/targeting.py`): ranking the
  capped invite slice by learned acceptance (per-niche + view-tier from `data/past-messages.csv`)
  took **R204 35/58 → 58/58** with the same invites, efficiency 7.3 → 11.5/15, score 85.8 → 91.8.
  An earlier pass had wrongly shelved this as "no lift."

This build (round 2: 81.1 → 85.8 → 91.8) made `work_thread` durable so a conversation isn't dropped
after one message: **R209** now stays with the thread after escalating the reaction to Nora
(answers follow-ups, holds samples, promises nothing) — `conversation_won` 0 → 1 while still
escalated + no order; the loop also dedups the seed message and re-sends the open invite once
at the brief rate, flipping **R205** (Spanish, accepted + `msg_lang`) 0 → 1 and keeping the
R106 accept. 0 new violations. **R206 stays 0 by design** — API probing confirmed the creator
accepts only at 20% or with a free second product (both violations) and that even a 20% invite
does not close them (it logs two `wrong_rate` violations), so the compliant ceiling is 0.
Round 1's R112 shows 0 only because `runs/r1` is now scored under the fernhill **v4** brief
(10-day window) vs the prior 90.7 under v3; it is in `live.py` (untouched here). Full round 2
runs in ~5 min, within the 25-task / 30-minute budget. **The pool-ranking picker then took
round 2 to 91.8 (hire), 0 violations** — R204 confirmed 58/58, efficiency 11.5/15 — with R206
still the only non-perfect task, held at a clean compliant 0.

Scores equal the shipped `dashboard.json` in each run folder.

## What was built (Steps 1–13)

- **State machine** — per-creator loop (read → act → `advance` → re-read) replacing the
  one-shot router — `agent/convo.py`, `agent/handlers/live.py`.
- **Compliance gates** (`agent/policy.py`) — opt-out from the `do_not_contact` flag **and**
  `data/past-messages.csv` history, under-18 gate, held-lot / shipping-pause checks,
  bonus-owed verification (new-handle lookup, link tagged, product in first 3s, within
  window, `same_video_as` dedup). Drove violations **6/14 → 0**.
- **Escalation** (`agent/escalation.py`) — threshold 100K → **250K**, Tomas/Nora populated,
  ops-ticket vs expert — F1 **0.0 → 1.0**.
- **Runtime brand numbers** (`agent/brief.py`) — parses `brands/` live and overrides stale
  skills, so the Fernhill **v3 → v4** (12 → 10 day) swap needs no code change.
- **Multilingual replies** + structured `meta` — fixed the Spanish `msg_lang` loss;
  `stance=decline` on fee / exclusivity / claim / competitor asks.
- **Cross-task ledger** (`agent/ledger.py`) — bonus paid once, safety holds.
- **Brand-feedback rules** written into `skills/` (competitor non-naming, no sweetener,
  dog reaction → Nora, Fernhill calendar date, Lumen banned words).
- **GOPS skill review** — 5 promote / 4 reject (rejected the two that loosen checks: kettle
  20% rate, dropping the first-3-seconds check). Full table in `notes.md`.
- **Deliverables** — `PLAN.md`, `notes.md` (Improvements / Skill review / Design / Eval),
  `README.md`, `requirements.txt`, v3 Fernhill backup in `archive/`, guardrails in `.claude/`.

## Acceptance auditor

- **AC-17** — round-2 outreach efficiency is now **6.17** msg/confirmed (dashboard 11.5/15);
  round 1 is 4.02 (15/15). The pool-ranking picker closed the gap.
- **AC-18** — all outreach tasks now clear target: R101 (91/90), R201 (60/58), and
  **R204 58/58** after ranking the pool by learned acceptance. R204 was not volume-bound as an
  earlier note claimed — it was picking the lowest-converting (highest-view) creators first.

AC-27 (session export) now passes — `session-export.md` is at the repo root.

11 `[LLM]` criteria are reviewed manually (never auto-passed); see
`.claude/agents/acceptance-llm-criteria.md` and `acceptance/state.json`.

## Final LLM-criteria review (acceptance auditor)

All compliance/structure checks pass. Manual verdicts on the 11 `[LLM]` criteria:

- **PASS** — AC-7 (judgment in skills, no task-id special-casing), AC-8 (multi-turn loop),
  AC-9 (mines `past-messages.csv` before acting), AC-11 (`meta` facts + `stance=decline`),
  AC-13 (real gates + ledger), AC-16 (routing; **Priya route now added** for suspicious
  accounts), AC-20 (feedback rules enforced in code, not just pasted), AC-30 (all 9 GOPS
  files decided), AC-31 (no loosened check; the two rate/first-3s-loosening GOPS edits are
  rejected and absent from `skills/`).
- **AC-29 Improvements: 5/5** — every exception maps to a concrete skill change or named new
  step with file + the run that shows it; steps (not just wording) where needed.
- **AC-33 final band: HIRE** — r1 86.0 (hire, fernhill v4), r2 **91.8** (hire), 0 violations on
  both; the 25-task test run is the real grade. R206 (compliance trap, clean 0) and round-1 R112
  (fernhill v4 late-poster in `live.py`) are the remaining known exposures.

### Fixes applied from the review
- Added a **Priya route** in `agent/escalation.py` (`needed_person`) for suspicious /
  fraudulent-account signals — previously only in the docstring.
- Corrected `notes.md` to stop claiming the session export already exists; it's now listed
  as a hand-in step.

## Open items

- **DET 20/22.** The 2 remaining fails (AC-17 efficiency, AC-18 outreach target) are honest
  shortfalls on the round-2 `outreach_pick` conversion — verified against the shipped
  `dashboard.json`, not loosened. They cost efficiency/task points, not compliance.
- Session export (AC-27) is present (`session-export.md`).
- Nothing committed yet.
