# Baseline: starter agent

**This is the starting floor, not the goal.** Scores below are what the untouched starter gets under mock — the point we improve from. Hire bar is 86+; do not treat these numbers as a target or as “good enough.”

Source: `baseline/starter-round1.json`, `baseline/starter-round2.json` (starter agent, mock model, no LLM).

## Scores

| Run | Score | Band | Task success | Compliance | Escalation F1 |
|:-|:-|:-|:-|:-|:-|
| Round 1 | **12.3** | no hire | 2 / 15 (13.3%) | −12 (6 violations) | 0.0 |
| Round 2 | **0.0** | no hire | 2 / 15 (13.3%) | −20 (14 violations, capped) | 0.0 |

Hire bar is 86+. This is the floor we improve from.

### Round 1 parts

| Part | Points |
|:-|:-|
| Task success | 9.3 / 70 |
| Escalation | 0.0 / 15 |
| Efficiency | 15.0 / 15 |
| Compliance | −12 |
| Escalation cap | 0 |

### Round 2 parts

| Part | Points |
|:-|:-|
| Task success | 9.3 / 70 |
| Escalation | 0.0 / 15 |
| Efficiency | 6.7 / 15 |
| Compliance | −20 |
| Escalation cap | 0 |

### By kind

| Kind | Round 1 | Round 2 |
|:-|:-|:-|
| inbound | 2 / 5 | 1 / 4 |
| live | 0 / 6 | 1 / 6 |
| outreach | 0 / 1 | 0 / 2 |
| samples | 0 / 3 | 0 / 3 |

Easy inbound Q&A sometimes works (e.g. simple rate/bonus). Almost everything else fails.

---

## What’s wrong with the starter

### 1. Sends a message and forgets it

`inbound`, `live`, and many `samples` paths send one reply and stop. No multi-day loop of `advance` → `inbox` / `thread` → reply until accept, decline, post, or window close.

Failed conversation checks look like: `conversation_won: false`, `accepted: false` on labels such as `haggle_rate`, `ghost_then_rate`, `late_poster`, `competitor_exclusive`, `haggle_sweetener`.

### 2. Compliance holes

**Round 1 violations (6):**

- `opted_out_contact` × 5 — invites people who asked to stop (checks `do_not_contact` flag only; ignores stop language in `data/past-messages.csv`)
- `sample_rule` × 1 — ships against a held lot (`held_lot`)

**Round 2 violations (14):**

- `opted_out_contact` × 9
- `minor_contact` × 3 — no age / under-18 gate on invites
- `sample_rule` × 1 — ships while shipping is paused
- `bonus_not_owed` × 1 — pays bonus without enough valid videos in window

### 3. Escalation is wrong

Keyword routing in `_shared.md` / `route_escalation`:

- Almost everything hits **Marcus** (reactions, big creators, creative exceptions).
- Shared front matter: Tomas/Nora keyword lists empty; Marcus follower threshold **100K** vs pod rule **250K → Tomas**.
- Round 1: 6 made, 3 needed, precision 0.167, recall **0**.
- Round 2: 2 made, 2 needed, precision/recall **0**.

Examples: need `tomas` / `nora`, escalate to `marcus`.

### 4. Live campaign logic is thin

Pays or nudges from raw `len(posts)` with no:

- new-handle lookup (`posted_new_handle` → `paid: false`)
- missing-link / post fix (`post_fixed: false`)
- valid-in-window / content checks (`bonus_not_owed`)
- multi-turn deadline / claim handling

Round 1 live: **0 / 6**. Round 2 recovers one nudge task.

### 5. Samples ignore notices and edge cases

Does not read ops notices before shipping (held lot, shipping pause). Reaction / safety paths escalate to the wrong person. Lost / not-delivered cases often miss the right `ops_ticket`.

### 6. Outreach volume without policy

Often hits confirmed targets on segment outreach, but the task still fails on violations. Round 2 outreach overall (both tasks combined): **85 / 116** confirmed, 7.78 messages per confirmed — confirmed count under target and inefficient (efficiency 6.7 / 15 vs 15.0 / 15 in round 1). The pick task (R204, `outreach_pick`) alone is **23 / 58** confirmed at 13.8 messages per confirmed and fails its confirmed minimum.

---

## Architecture of the weakness

The starter is a thin kind-router (`outreach` / `inbound` / `samples` / `live`) with:

- regex keyword replies and escalation
- one-shot LLM draft (or template fallback under mock)
- no durable conversation state machine
- no systematic checks against past messages, age, notices, or bonus eligibility
- skills that are incomplete / misaligned with `pod.md` and briefs

Docs’ framing matches the data: decent on easy cases, weak on edges.

---

## What “better” has to mean

Not cosmetic prompt tweaks. Minimum bar for a real lift:

1. Multi-turn conversation loop with `advance` / inbox until outcome.
2. Policy gates: opted-out (flag + history), minors, notices, sample rules, bonus owed.
3. Correct escalation (Marcus / Priya / Tomas / Nora) and ops tickets vs expert escalations.
4. Live: verify posts (handle, link, window, count) before pay or nudge.
5. Judgment in skills + workflow steps so unseen test-run tasks generalize; numbers always read from `brands/` at run time.
