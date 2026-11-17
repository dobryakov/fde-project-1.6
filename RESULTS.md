# RESULTS — ironco FDE build

End-to-end build ran against the plan in [PLAN.md](PLAN.md). Summary of what was built
and where it landed.

**Wall-time:** ~63 minutes end-to-end (single Claude Code / Opus session; created 13:39Z,
last activity 14:42Z), agent-driven.

## Results (real `claude_cli` runs)

| Run | Score | Band | Violations | Escalation F1 | Efficiency |
|:-|:-|:-|:-|:-|:-|
| **Round 1** (`runs/r1`) | **90.6** | hire | **0** | 1.00 (3/3) | 15/15 |
| **Round 2** (`runs/r2`) | **74.4** | — | **0** | 1.00 (2/2) | 5.6/15 |
| Baseline | 12.3 / 0.0 | no | 6 / 14 | 0.00 | — |

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

## Acceptance auditor: 20/22 DET pass

The 2 remaining are honest, not loosened (both earn partial credit on the dashboard):

- **AC-17** — round-2 outreach efficiency is **8.12** msg/confirmed (> 5 threshold); round 1
  is 4.11 (full marks). Dashboard efficiency: r1 15/15, r2 5.6/15.
- **AC-18** — outreach tasks short of target: `r1:R101` **88/90**, `r2:R201` **57/58**,
  `r2:R204` **32/58** (the `outreach_pick` task). Ranked next builds: a data-driven pool
  picker (past-message acceptance by niche/tier) and a stronger negotiation policy.

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
- **AC-33 final band: PARTIAL** — r1 90.6 (hire), r2 74.4; the 25-task test run is the real
  grade and r2 efficiency/conversion is the exposure.

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
