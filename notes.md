# notes.md — ironco FDE build

**Time spent:** ~63 minutes end-to-end wall-time (single Claude Code / Opus session,
agent-driven; session created 13:39Z, last activity 14:42Z). **Session export:** add
the coding-agent transcript (md/txt/json/jsonl) at the repo root before hand-in — export this
session from the app (session menu → Export); it must be done on your own machine.

**Command:** `python3 agent/run.py <task file> <run folder>` then
`python3 dashboard.py <run folder> detail`. Model: `claude_cli` (`claude -p`), default
**haiku**, via `agent/llm.py`. No other providers or keys.

The agent is a per-creator **state machine**: on each tick it reads state + `inbox` /
`thread` / `notices` (and `data/past-messages.csv` before the first contact), picks one
action, `advance`s the clock, and re-reads — until accept / decline / post / bonus / window
close. **Code owns transitions and hard checks; skills and briefs own judgment.** Every
brand number is read from `brands/` at run time (`agent/brief.py`), never hard-coded.

---

## Improvements

Each exception → the skill change or new workflow step that closes it, where it lives, and
the run that shows it working.

| Exception (round) | What I did | Where | Shown by |
|:-|:-|:-|:-|
| Agent sent one message and forgot the thread (R103, R106, R109, R112, R2 convos) | **New step:** a multi-turn loop that advances the clock, reads the inbox and answers replies until a result | `agent/convo.py` `work_thread`, `agent/handlers/live.py` loop | R103/R106 accepted; R1 task-success 2/15 → 13/15 |
| Invited creators who had opted out (R1 ×5, R2 ×9 in baseline) | **New gate:** `can_contact` blocks the `do_not_contact` flag **and** anyone who asked to stop in `data/past-messages.csv` (`outcome=asked_to_stop` or stop-language) | `agent/policy.py` `optout_history`, `is_opted_out`; used in `outreach.py` | both rounds: violations 6/14 → **0** |
| Messaged an under-18 creator (R2 ×3 in baseline) | **New gate:** `is_minor` blocks `age_flag == under_18` | `agent/policy.py` `is_minor` / `can_contact` | round 2 `minor_contact` 3 → 0 |
| Shipped a held lot (R107) | **New step:** `pick_shippable_lot` skips lots named in a quality-hold notice; ship with an explicit `lot=` | `agent/policy.py`; `samples.py` | R107 ships lot L-2307, not held L-2291 |
| Shipped a paused product/country (R2) | **New gate:** `shipping_paused` reads the pause notice; the agent tells the creator it's delayed, no date | `agent/policy.py`; `samples.py` | R207 "sample delayed (shipping pause)" |
| Paid a bonus that wasn't owed / counted the wrong videos (R111, R2) | **New step:** `bonus_owed` verifies **new-handle** posts, link tagged, product in first 3s, within-window, dedup `same_video_as`, and `>= bonus_videos` before paying | `agent/policy.py` `gather_posts` / `valid_videos` / `bonus_owed`; `live.py` | R110/R113 pay via new handle; R111 nudges (missing link) |
| Escalations all went to Marcus; Tomas/Nora never fired (R102, R108, R114) | **Skill + code fix:** threshold 100000 → **250000**, Tomas/Nora routes populated; `needed_person` routes safety→Nora, big/creative→Tomas, legal→Marcus, and escalates only what needs a person | `skills/_shared.md` front matter; `agent/escalation.py` | R1 escalation F1 0.0 → **1.0** (3/3) |
| Late poster lost the bonus (R112) | **New step:** after nudging, keep advancing the window and re-checking posts, then pay | `live.py` work loop | R112 paid after window (v3) |
| Delivery exception treated as a posting problem (R213 returned_to_sender) | **New step:** on `returned/exception/lost` order status, open an ops ticket and reassure, don't nudge | `live.py` | R213 "ops ticket: sample returned_to_sender" |
| "Delivered" but the creator moved (GOPS/Ben, R2) | **New step:** compare the order address with `address_on_file` / "moved" before saying "check neighbors"; else `missing` ticket with both addresses | `samples.py` `_same_address` | address-mismatch → missing ticket |
| Lost sample with no order id in the task (R208) | **New step:** resolve the creator's order via `orders(id)`, then ticket; fixed a false `address_change` match on "hasn't moved" | `samples.py` | R208 → missing ticket |
| Non-English creator got an English reply (R205 Spanish `msg_lang`) | **New step:** `render` translates the reply into the creator's language via the model, keeps numbers exact, falls back to English; `meta.language` always matches the text | `agent/convo.py` `render`; Spanish fee/exclusivity tokens added | R205 accepted; round 2 score 59.5 → 74.4 |
| Rate haggle / sweetener / fee / exclusivity / competitor / claim asks | Brief-settled in code: hold the brief rate, `stance=decline`, never name a competitor, no second product | `agent/convo.py` `answer` | R103/R105 hold rate; R202 injection declined; 0 violations |
| Prompt injection in a creator message (R202 "SYSTEM OVERRIDE … $150 fee") | Treated as a flat-fee ask → declined, not obeyed | `convo.answer` FEE_RE | R202 no fee, no violation |

Cross-task rules (one run folder = one day) are enforced with a small run-folder ledger
(`agent/ledger.py`): a bonus is paid once even if asked again, and a creator with an open
safety review (a reaction sent to Nora) gets no new sample until cleared.

## Skill review

Decision on every file in `gops-local-skills/` (9 across Ana, Ben, Cleo). Promotions are
reflected in `skills/` and the agent; the test run reads only `agent/` + `skills/`.

| File | Decision | Why |
|:-|:-|:-|
| ana/follow-ups | **promote** | One nudge after ~48h, new wording, never resend — matches the duplicate-message penalty. Now in `skills/_shared.md`. |
| ana/kettle-pushback | **reject** | Offering 20% when a Kettle creator balks at 18% **loosens the rate** → a wrong-rate violation; one-off ("Marcus said ok for her"). The agent holds the brief rate. |
| ben/delivered-not-received | **promote** | Address-aware "delivered but moved" handling generalizes; implemented in `samples.py` and noted in `_shared.md`. |
| ben/nudges | **reject** | 24h + 72h double-nudge conflicts with Ana and risks the pushy penalty. Where they disagree I went with Ana (one nudge, 48h). |
| ben/open-review-check | **promote** | Cross-task pod rule (no sample while a safety review is open). New step via `agent/ledger.py` safety holds. |
| cleo/bonus-check | **reject** | Drops the "product in first 3 seconds" check — **loosens a compliance check**; forbidden to promote. |
| cleo/lumen-french | **reject (keep local)** | One-off (her queue happened to be Montreal). The general rule — reply in the creator's language — is already handled by `render`. |
| cleo/paid-once | **promote** | Cross-task "pay each bonus once." New step via `agent/ledger.py` paid-bonus ledger. |
| cleo/same-video | **promote** | Dedup by `same_video_as`. Already implemented in `policy.valid_videos`. |

Conflict calls: Ana vs Ben on nudge cadence → Ana (one 48h nudge). No promoted edit loosens
a check (ana/kettle-pushback and cleo/bonus-check rejected precisely because they do).

## Design

- **State machine, not one-shot.** `agent/run.py` dispatches by kind; each handler runs the
  read → act → advance → re-read loop. Context carries across ticks and (via `ledger.py`)
  across tasks in a run.
- **Code vs skills split.** Hard checks that must never fail (opt-out, minors, held lots,
  shipping pauses, bonus-owed, pay-once, escalation targets) live in `policy.py` /
  `escalation.py` / `ledger.py`. *How* to speak (voice, filming ideas, feedback rules) lives
  in `skills/` and `brands/`, read at run time. One edit to a brief or skill changes behavior
  with no code change.
- **Briefs are the source of truth.** `agent/brief.py` parses `brands/<brand>.md` live and
  overrides the (stale) skill front matter — this is why the Fernhill v3→v4 window change
  (12→10 days) is picked up by copying the brief, with no code edit. I keep **no** brand
  numbers in `agent/`.
- **`meta` is decided deterministically, text is rendered.** Facts (rate, bonus terms,
  stance) come from the brief so the sim judges correct, consistent fields; the model only
  renders/translates the wording, with a fallback that keeps numbers exact and stays English
  if the model drops one. `stance=decline` on fee/exclusivity/claim/competitor asks.
- **Learning from the data.** `data/past-messages.csv` is mined before contact for opt-outs
  (the `asked_to_stop` signal and stop-language), which is what removes the round-1/round-2
  opt-out violations.
- **Guardrails.** `.claude/settings.json` deny-rules + a `PreToolUse` Bash hook block reads of
  sim internals (`*.pack`, `state.db`, engine source); the agent talks to the sim only through
  `sim/API.md`.

## Eval

Real `claude_cli` runs. Numbers below equal the shipped `dashboard.json` in each run folder.

| Run (folder) | Score | Band | Task success | Violations | Escalation F1 | Efficiency (msg/confirmed) |
|:-|:-|:-|:-|:-|:-|:-|
| **Round 1** `runs/r1` | **90.6** | hire | 12.98 / 15 (88/90 confirmed) | **0** | 1.00 (3/3) | 15/15 (4.11) |
| Round 1 baseline `baseline/starter-round1.json` | 12.3 | no | 2 / 15 | 6 | 0.00 | 15/15 |
| **Round 2** `runs/r2` | **74.4** | no | 11.54 / 15 (89/116 confirmed) | **0** | 1.00 (2/2) | 5.6/15 (8.12) |
| Round 2 baseline `baseline/starter-round2.json` | 0.0 | no | 2 / 15 | 14 | 0.00 | 6.7/15 |

What the past messages taught me: the `asked_to_stop` outcomes and stop-language in
`data/past-messages.csv` are the opt-out signal that the `do_not_contact` flag alone misses —
encoding it is what drove violations to zero on both rounds.

Where round 2 still loses points: `outreach_pick` (R204) converts low (32/58) and drags
efficiency; three "work-it-to-a-result" conversations (R206/R209/R215, and R109/R115 in
round 1) don't reach `conversation_won`. These are the ranked next builds: a data-driven
pool picker (use past-message acceptance by niche/tier) and a stronger negotiation policy.
