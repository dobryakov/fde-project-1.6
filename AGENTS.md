# AGENTS.md — ironco FDE project v1.6

What this case asks of you, distilled from `INSTRUCTIONS.md`, the hiring doc, and `pod.md`.

## Role

You join as a forward deployed engineer (FDE) in Brightline’s affiliates pod (TikTok Shop). The pod finds creators, invites them, ships samples, chases posts, and pays bonuses across five brands. Three GOPS (Ana, Ben, Cleo) run the agent daily; Marcus is the only route to clients.

Your job: own the **workflow** and the **company skills**. When the agent hits an exception, turn it into a skill fix or a new step so it does not happen twice. The starter agent is decent on easy cases and weak on edges — it sends a message and forgets it. Make it good and prove it.

## What they want (in short)

Build a reliable end-to-end workflow agent (outreach → reply → sample → post → bonus → follow-up), not one-off answers tuned to the visible tasks. Judgment lives in **skills** read at run time. After hand-in they run **25 new, harder tasks** on your final agent — that run is the grade.

## Criteria they score for

1. **Think agentically** — Build with a coding agent; put judgment in skills the agent reads at run time, not hard-coded answers for known tasks.
2. **Think in systems** — Move a creator through the whole chain; carry context step to step.
3. **Learn from the data before you act** — Mine `data/past-messages.csv`, each creator’s thread, and your own runs; put what works into skills.
4. **Show the pieces** — Vetting, messaging, reading replies, escalating, and deciding must be visible and checkable.
5. **Generalize** — Handle tasks never seen before; the test run is unmodified.
6. **Write the rules down first** — Briefs, notices, and brand feedback become rules the agent reads; checks use the same numbers as the briefs.
7. **Make the call** — When the brief settles it, decide and say so; do not hand hard calls back as questions; math must be right.
8. **Never loosen a check to pass** — Fix wrong output, not the test or threshold.
9. **Run the improvement loop** — Every exception ends as a skill fix or a new step / exception handler. A wording tweak is not enough when a step is needed.

## Three levels (do in order)

1. **Just do it** — Agent runs both rounds end to end and works each conversation to a result.
2. **Make it trustworthy** — Rules in skills, checks match briefs, zero policy violations, one edit to change a rule.
3. **Prove it’s better** — Evals with before/after numbers on both rounds, and what past messages taught you.

## How the project runs

| Step | You do | Key files |
|:-|:-|:-|
| Round 1 (~75 min) | Run starter on 15 tasks; find failures; upgrade agent + skills | `tasks/round1.jsonl` |
| Brand feedback | Read client notes; build new rules in | `feedback/brand-notes-after-round-1.md` |
| Round 2 (~60 min) | Save Fernhill v3 outside `brands/`, copy v4 over it; run 15 tasks in a different world | `tasks/round2.jsonl`, `sim/round2.pack`, `feedback/fernhill-skin-v4.md` |
| Skill review (~25 min) | Review GOPS local edits; promote / merge / reject / keep local | `gops-local-skills/` |
| Write-up (~20 min) | Write `notes.md` | |
| Hand in | Send everything listed below | |
| Their test run | They run your agent unchanged on 25 harder tasks with updated briefs | |

```bash
python3 agent/run.py tasks/round1.jsonl runs/r1
python3 dashboard.py runs/r1 detail

cp feedback/fernhill-skin-v4.md brands/fernhill-skin.md
python3 sim/simctl.py init runs/r2 pack=sim/round2.pack
python3 agent/run.py tasks/round2.jsonl runs/r2
python3 dashboard.py runs/r2 detail
```

Each dashboard run closes its run folder. Use a fresh folder per attempt. Briefs can change on the test run — the agent must read `brands/` at run time and never copy numbers into code.

## Creators push back

Tasks are multi-day conversations. Advance the clock (`advance`), read `inbox` / `thread`, reply until accept, decline, post, or the window closes. Pushy wording, duplicate messages, late replies, or nudging before they answer cost you the creator. A message sent and forgotten stalls.

## Improvement loop (after rounds 1 and 2)

Every exception (ghost, fee haggle, wrong address, late post, minor, etc.) must become:

- a **skill change**, or
- a **new task / step / exception handler** the agent now runs.

Some exceptions need a step (lookup, cross-task check, ticket), not better wording. Document each in `notes.md` → **Improvements**: exception → what you did → where (file/function/section) → run that shows it working.

## Skill review (GOPS)

`gops-local-skills/` has Ana’s, Ben’s, and Cleo’s local edits. Fold in what helps every GOPS. If a GOPS kept patching the same exception by hand, add a workflow step, not just a note. Some edits are good; some are one-off; some must be rejected.

In `notes.md` → **Skill review**: every file, marked promote / merge / reject / keep local, with 1–2 lines why. Where two disagree, say which way you went. Edit `skills/` and the agent to match. The test run uses only your agent and `skills/` — do not read `gops-local-skills/` at run time.

## Brands / setup

| Brand | State |
|:-|:-|
| Kettle & Crumb | Outreach at scale |
| Tidewater Coffee | Outreach at scale |
| Brave Paws | Samples / shipping problems |
| Fernhill Skin | Live campaign |
| Lumen Home | Live campaign |

- `brands/` — source of truth; brief wins over skill.
- `skills/` — what the agent reads (some are stale).
- `agent/` — starter agent; drives tasks via `sim/API.md`.
- `pod.md` — experts, what you decide yourself, ops rules.
- `data/past-messages.csv` — past outreach with outcomes.
- Tasks carry `ops_notices` — read them before acting.

## Hard rules

- Use **Claude Code, Codex, Cursor, or a similar coding agent**. ChatGPT alone fails.
- Keep the command: `python3 agent/run.py <task file> <run folder>` — must finish 25 tasks in 30 minutes. List packages in `requirements.txt`. Clean Python 3.12 on their side.
- Model calls go through `agent/llm.py` with default `claude_cli` (`claude -p`). Use haiku or sonnet. No other API keys/providers.
- Send structured `meta` with `send_message` / `send_invite` when you can.
- **Do not edit** `sim/` or `dashboard.py`.
- **Do not read** sim internals (pack contents, engine source, run folder `state.db`) to learn outcomes — that fails the case. Talk only through `sim/API.md`.
- About **3 hours** of work.

## Scoring (dashboard out of 100)

| Part | Points |
|:-|:-|
| Task success | 70 |
| Escalation (precision + recall, right person) | 15 |
| Efficiency (outreach messages per confirmed creator) | 15 |
| Compliance | −2 per policy violation (cap −20); violation also fails the task |
| Escalation cap | −1 per escalation over 10 in a run (one run folder = one day) |

Policy violations include: wrong rate/bonus, banned claim, flat fee, pay-per-post, exclusivity, contacting do_not_contact or under-18, sample outside rules, bonus not owed / after window, anything brand feedback rules out.

**Your total** = dashboard score on their test run, minus up to **10** for a weak Improvements section in `notes.md` (0–5 scale; −2 per point under 5).

Bands: **≥92** strong · **86–91** hire · **&lt;86** no hire.

Also required to pass:

- Eval numbers in `notes.md` match shipped `dashboard.json` (they replay).
- Session export/transcript from a coding agent (md/txt/json/jsonl with your turns + tool calls/edits). No export = no pass. ChatGPT chat does not count.
- No loosened check, test, or threshold (including promoting a GOPS skill that loosens a check).

Skill review is graded through the test run via what you put in `skills/`.

## What to send back

1. Repo (zip or GitHub) with agent, skills, evals.
2. `README.md` — one command, model, settings.
3. `notes.md` with four headings:
   - **Improvements** — each exception → skill change or new step.
   - **Skill review** — decision on every GOPS edit.
   - **Design** — what you reached for and why; judgment in skills vs code.
   - **Eval** — before/after scores on both rounds; name the run folder next to every score.
4. Those run folders, each with `dashboard.json`.
5. Coding-agent session export/transcript.
6. How long you spent.

## If you pass: live review (30 min)

- **10 min present** — one-page artifact for a busy exec from another department: what the pod needed, what you built, impact; close with what you’d build next ranked by impact on pod numbers.
- **20 min Q&A** — agent and `notes.md` open; expect questions on next builds for a real pod and why.

## Experts (from `pod.md`)

| Expert | Owns |
|:-|:-|
| Marcus | Client, paid asks, terms outside limits, legal |
| Priya | Shipping, lots, addresses, data, skills, suspicious accounts |
| Tomas | Creators &gt;250K, creative exceptions, collabs |
| Nora | Health/skin/pet reactions, unsettled claims, minors |

Experts take **10 escalations a day**. Escalate only what needs a person. Brief-settled decisions (rates, bonuses, sample rules, banned claims, no flat fees / per-post / exclusivity) you decide yourself. Routine shipping → `ops_ticket`, not an expert.

Cross-task rules: stop if they asked to stop; no new sample while a safety review is open; each posting bonus paid once.
