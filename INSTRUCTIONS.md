# ironco: forward deployed engineer project

*This case is representative of the work we do. Creators are our main focus right now. Brightline, its brands, creators and numbers are made up.*

*v1.6 · FDE seat · about 3 hours of work*

### Welcome to ironco

You join ironco as a forward deployed engineer (FDE). Brightline is a TikTok Shop affiliate agency we power with agents. You work in its affiliates pod, which finds creators for five brands, invites them, ships samples, chases posts and pays bonuses.

Day to day, an FDE builds and improves the agent and the company skills the GOPS run. You own the workflow: the steps a creator and a brand move through. When the agent hits an exception, you turn it into a skill fix or a new step.

The pod splits into workstreams: outreach, samples and live campaigns. Three Growth Operations Managers (GOPS), Ana, Ben and Cleo, run the agent every day and keep local skill edits. Each week you promote the good edits into the company skills.

Marcus, the account manager, is the only route to clients, and anything legal goes to him. Priya (ops), Tomas (creators) and Nora (claims and safety) handle the other escalations. `pod.md` says who owns what.

The starter agent is decent on easy cases and weak on the edges. It sends a message and forgets it. Your job is to make it good and prove it.

**Use Claude Code, Codex, Cursor or a similar coding agent. ChatGPT alone will automatically fail, so don't bother.**

We grade your work before any live session, and only a pass gets one. The bar is high on purpose, so plenty of good people won't clear it. Whatever happens, you'll get your score and specific feedback on your agent.

**We will run 25 new, harder tasks through your agent after you hand in. Be thoughtful. Don't be lazy.**

We call that run our test run. It is the grade.

**You own the workflow and the agent's skills. Every exception you see should end as a skill fix or a new step, so it doesn't happen again.**

## What we're looking for

We want to know if you can do the job. Nothing here is a trick, and every rule your agent needs is in this folder. It's hard because the job is hard.

1. **Think agentically.** Build with your coding agent, and put the judgment in skills your agent reads at run time, not in answers hard coded for the tasks you can see.
2. **Think in systems.** Your agent moves a creator and a brand through the whole chain: outreach, reply, back and forth, sample, posting, bonus and follow up. It carries what it learned from step to step.
3. **Learn from the data before you act.** Mine `data/past-messages.csv`, each creator's thread and your own runs. Put what works into the skills, then send.
4. **Show the pieces.** We can see how your agent vetted, messaged, read replies, escalated and chose. Something came in, a task got done, and the system got better.
5. **Generalize.** Build an agent that handles tasks it has never seen. Our test run gives it 25 harder ones, and it runs them unmodified.
6. **Write the rules down first.** Briefs, notices and brand feedback become rules your agent reads, and your checks use the same numbers as the briefs.
7. **Make the call.** When the brief settles it, your agent decides and says so. It doesn't hand a hard call back as a question, and its math is right.
8. **Never loosen a check to pass.** If an output is wrong, fix the output, not the test or the threshold.
9. **Run the improvement loop on skills and workflow.** An exception you see becomes a skill fix, or a new step or exception handler your agent runs. A wording tweak won't stop an exception that needs a step.

## Three levels

Do them in order.

1. **Just do it.** Your agent runs both rounds end to end and works each conversation to a result.
2. **Make it trustworthy.** Rules live in skills, checks match the briefs, policy violations are zero, and a rule change takes one edit.
3. **Prove it's better.** Evals with before and after numbers on both rounds, and what the past messages taught you.

## Creators push back

Creators in this sim behave like people. Over several sim days they reply, haggle on commission, ask for fees, go quiet, object to terms, ask a second question, or post late. What they do next depends on what your agent said, how and when it said it, and whether it read what they told us before. A message sent and forgotten stalls.

So a task isn't one message. Your agent advances the clock (`advance`), reads what came back (`inbox`, `thread`), and answers, until the creator accepts, declines or posts, or the task's window closes. Each conversation task says how many days it runs. Pushy wording, the same message twice, a reply days late, or a second nudge before they've answered all cost you the creator.

## How the project runs: round 1, feedback, round 2, skill review, then our test run

| Step | About | You do | Files |
|:-|:-|:-|:-|
| Round 1 | 75 minutes | Run the starter agent on 15 tasks across the five brands. Find what fails, then upgrade the agent and skills | `tasks/round1.jsonl` |
| Brand feedback | | Read the clients' notes. They add rules nobody wrote down before. Build them in. Assume every change you'd suggest to the pod is approved | `feedback/brand-notes-after-round-1.md` |
| Round 2 | 60 minutes | Fernhill Skin moved to brief v4 (notice N-120). First save a copy of the v3 `brands/fernhill-skin.md` outside `brands/`, then copy `feedback/fernhill-skin-v4.md` over it. Then run your upgraded agent on 15 new tasks in a different world (a world is one copy of the sim: its creators' replies and live data), with the feedback in force. Refine again | `tasks/round2.jsonl`, `sim/round2.pack` |
| Skill review | 25 minutes | Review the GOPS edits and fold the good ones into `skills/` (below) | `gops-local-skills/` |
| Write up | 20 minutes | `notes.md` (below) | |
| Hand in | | Send your work (below) | |
| Our test run | | We run the agent you handed in, unchanged, on 25 new, harder tasks with their data, a sim pack and updated briefs (some numbers will have changed, so your agent must read the briefs at run time). We use your one command on our side and score the run by replaying every action. Nothing to schedule. If it won't run for us, we send it back once for you to fix | |

```
python3 agent/run.py tasks/round1.jsonl runs/r1
python3 dashboard.py runs/r1 detail

cp feedback/fernhill-skin-v4.md brands/fernhill-skin.md
python3 sim/simctl.py init runs/r2 pack=sim/round2.pack
python3 agent/run.py tasks/round2.jsonl runs/r2
python3 dashboard.py runs/r2 detail
```

Each dashboard run closes its run folder. Start a fresh folder for each attempt. To rerun round 1 after the copy, put your saved v3 Fernhill brief back first.

**Briefs change.** Our test run comes with updated briefs, and some numbers will be different. Your agent must read `brands/` at run time, never copy numbers into code.

## After rounds 1 and 2: the improvement loop

Every exception your agent hit in rounds 1 and 2 (a ghost, a fee haggle, a wrong address, a late post, a minor, anything) should end as one of two things: a skill change, or a new task, step or exception handler in your workflow that your agent now runs. Some exceptions need a step, not better wording: a lookup, a check against what happened in an earlier task, a ticket. Our test run includes exceptions only a step catches.

In `notes.md`, under **Improvements**: one row per exception you saw, what your agent now does about it (skill change or new step), where it lives (file and function or section), and the run that shows it working. It counts toward your total (below). Some exceptions in rounds 1 and 2 have no GOPS note about them at all, and only a step you add catches them.

## The skill review: the GOPS edits

`gops-local-skills/` holds edits three GOPS made to their own copies of the skills. Fold in what would help every GOPS. Where a GOPS kept patching the same exception by hand, add it as a workflow step, not just a note. Some of it is good. Some of it fits one creator or one day. Some of it shouldn't go anywhere.

1. Read each local skill and check it against the briefs, `pod.md` and the data.
2. In `notes.md`, under **Skill review**: every file in `gops-local-skills/`, marked promote, merge, reject or keep local, with one or two lines on why. Where two of them disagree, say which way you went and why.
3. Edit `skills/` and your agent to match.

Our test run uses only your agent and `skills/`. Your agent must not read that folder. What you didn't promote isn't in the run.

## The setup

| Brand | State | Tasks |
|:-|:-|:-|
| Kettle & Crumb | Outreach at scale, about 10,000 creators | Outreach batches and creator conversations |
| Tidewater Coffee | Outreach at scale, about 10,000 creators | Outreach batches and creator conversations |
| Brave Paws | Samples going out, creators having problems | Sample requests, shipping problems, conversations |
| Fernhill Skin | Live campaign, some creators haven't posted | Campaign checks and conversations |
| Lumen Home | Live campaign, some creators haven't posted | Campaign checks and conversations |

- `brands/` holds the briefs, the source of truth. Where a skill disagrees with a brief, the brief wins.
- `skills/` is what the agent reads. Some skills are stale or incomplete.
- `gops-local-skills/` holds three GOPS's own skill edits, for the skill review.
- `agent/` is the starter agent. It drives each task through the sim (`sim/API.md`).
- `pod.md` has the experts, what you decide yourself, and how ops works.
- `data/past-messages.csv` holds past outreach messages with replies, answers and outcomes. Each creator's `thread()` shows what was said before this task started.
- Each task carries the ops notices in effect when it starts (`ops_notices`). Read them before you act.

## Rules

- **Keep the command.** `python3 agent/run.py <task file> <run folder>` must run your agent on any task file shaped like `tasks/round1.jsonl`, and finish 25 tasks in 30 minutes. We run it in a clean Python 3.12 environment, so list any packages in `requirements.txt`.
- **Model calls go through `agent/llm.py`.** Keep its default `claude_cli` provider: it runs `claude -p`, which works on your Claude Code subscription with no API key, and our test run uses the same path with our own login. Use haiku or sonnet. Don't add other API keys or providers.
- **Send structured fields with your messages if you can.** `send_message` and `send_invite` take `meta` (see `sim/API.md`). With `meta`, your answer is judged on those fields, strictly, and the text must agree.
- **Don't edit `sim/` or `dashboard.py`, and don't read the sim's internals** (pack contents, engine source, or a run folder's `state.db`) to learn outcomes. Doing so fails the case. Your agent talks to the sim only through the calls in `sim/API.md`. We read your session export.

## How it's scored

The dashboard, out of 100:

| Part | Points | Tests |
|:-|:-|:-|
| Task success: share of tasks done right; outreach scores confirmed creators against the target; a conversation counts when it reaches the right result | 70 | Think in systems; Generalize; Make the call |
| Escalation: precision and recall, the right person on the tasks that need one | 15 | Show the pieces |
| Efficiency: outreach messages per confirmed creator | 15 | Learn from the data |
| Compliance: minus 2 per policy violation, up to minus 20. Any violation also fails its task | penalty | Show the pieces |
| Escalation cap: minus 1 for each escalation over 10 in a run. A run folder counts as one day, and the experts take 10 escalations a day (`pod.md`). The extra escalations still go through | penalty | Show the pieces |

Policy violations are: a wrong rate or bonus, a banned claim, a flat fee, paying per post, exclusivity, contacting a do_not_contact or under 18 creator, a sample outside the rules, a bonus that isn't owed, promising the bonus after the window, and anything the brand feedback rules out.

**Your total** is your dashboard score on our test run minus up to 10 points for the Improvements section of `notes.md`. We read it on a 0 to 5 scale and take off 2 points for each point under 5. A full read lists every round 1 and 2 exception, each ending as a skill change or a named new step, with the run that shows it.

**The verdict is the band your total falls in:** 92 and up is strong, 86 to 91 is hire, under 86 is no hire. To pass you also need:

- Eval section numbers in `notes.md` that match your shipped `dashboard.json` files. We replay those runs ourselves, and a number that doesn't match fails the project.
- Your session export or transcript from Claude Code, Codex, Cursor or a similar coding agent: md, txt, json or jsonl, with your own turns visible and the agent's tool calls or file edits in it (in Claude Code, `/export`). A ChatGPT chat isn't a session export. No export means no pass.
- No loosened check, test or threshold (see "Never loosen a check to pass"). That includes promoting a GOPS skill that loosens a check.

The skill review is graded through the test run, not separately. The test run uses your `skills/`, so what you promoted well lifts your band and what you promoted badly costs you. A one-off promoted as a general rule scores down.

A person reads `notes.md` and your skills diff alongside the band. If you pass, we book a 30 minute live session: we change one rule, you change your agent's instructions, rerun and check the output with us, and you name the root cause of one failure.

## What to send back

1. The repo, zipped or on GitHub, with your agent, skills and evals.
2. `README.md` with the one command, and the model and settings you used.
3. `notes.md`, short, with four headings:
   1. **Improvements**: each exception you saw and the skill change or new step it became (above).
   2. **Skill review**: your decision on every GOPS edit (above).
   3. **Design**: what you reached for and why, which judgment lives in skills and which in code.
   4. **Eval**: before and after scores on both rounds, as a short table. Name the run folder next to every score, for example `runs/r2-final: 88.4`. Don't repeat the lessons from Improvements.
4. Those run folders, each with its `dashboard.json`.
5. Your session export or transcript from Claude Code, Codex, Cursor or a similar coding agent: md, txt, json or jsonl, with your own turns visible and the agent's tool calls or file edits in it (in Claude Code, `/export`). A ChatGPT chat isn't a session export. No export means no pass.
6. How long you spent.
