# Acceptance Criteria — ironco FDE project v1.6

Derived from `AGENTS.md`, `INSTRUCTIONS.md`, `ironco-fde-hiring-doc.md`, `pod.md`,
`baseline.md`, `brands/`, `feedback/`, `README.md`, and `sim/API.md`. The grade is the
dashboard score on **their 25-task test run** minus up to 10 for a weak `notes.md`
Improvements section; bands: **≥92 strong, 86–91 hire, <86 no hire**.

Each criterion: statement · source · measurable pass condition · group tag.
`[DET]` = settled by a runnable check in `acceptance/checks/`.
`[LLM]` = needs human/LLM judgment; listed in `acceptance/llm-criteria.md`,
reported as `MANUAL`, never auto-passed.

Note on state: the real operator agent is **not built yet**. Most `[DET]` checks are
*expected to FAIL* right now. That is correct for this bootstrap run.

---

## A. The one-command contract & environment

- **AC-1 [DET]** — The command `python3 agent/run.py <task file> <run folder>` runs the
  agent on any `round1.jsonl`-shaped task file and is the stable entry point.
  Source: INSTRUCTIONS.md "Rules" / AGENTS.md "Hard rules".
  Pass: `agent/run.py` exists, is syntactically valid Python, and accepts
  `TASKS_FILE RUN_DIR` positionally (argparse `pos`).

- **AC-2 [DET]** — Must finish 25 tasks in 30 minutes in a clean Python 3.12 env, with
  any pip packages listed in `requirements.txt`.
  Source: INSTRUCTIONS.md "Rules".
  Pass: `requirements.txt` exists at repo root; agent imports only listed third-party
  packages (stdlib + listed). (Wall-time is verified at run time, not here.)

- **AC-3 [DET]** — Model calls go through `agent/llm.py` with default provider
  `claude_cli` (`claude -p`), model haiku or sonnet; no other API keys or providers added.
  Source: INSTRUCTIONS.md "Rules" / AGENTS.md "LLM vs mock".
  Pass: `agent/llm.py` default `PROVIDER` is `claude_cli`; default model resolves to
  haiku/sonnet; no new provider branch beyond the shipped set; no committed API-key file
  wired as default.

- **AC-4 [DET]** — `sim/` and `dashboard.py` are not edited.
  Source: INSTRUCTIONS.md "Rules" / AGENTS.md "Hard rules".
  Pass: `git status --porcelain sim dashboard.py` is empty (no tracked modifications).

- **AC-5 [DET]** — The agent talks to the sim only through `sim/API.md` calls; it never
  reads sim internals (`*.pack`, `state.db`, `sim/affiliate_center.py` internals beyond
  the public `AffiliateCenter`/`init_run`, `sim/pack.py`).
  Source: INSTRUCTIONS.md "Rules" / AGENTS.md "Hard rules".
  Pass: no file under `agent/` references `.pack`, `state.db`, `_core.pack`, `pack.py`,
  or opens a run-folder `state.db`.

## B. Reading the data before acting & no hard-coded numbers

- **AC-6 [DET]** — Brand numbers (rates, bonus amount/videos/days, sample thresholds) are
  read from `brands/` at run time, never copied into `agent/` code.
  Source: INSTRUCTIONS.md "Briefs change" / AGENTS.md "Hard rules" / baseline.md item 5.
  Pass: the brand-specific numeric literals from the briefs do not appear as rate/bonus
  constants in `agent/` source; `agent/skills.py` (or equivalent) loads `brands/` /
  `skills/` at run time.

- **AC-7 [LLM]** — Judgment lives in skills the agent reads at run time, not in answers
  hard-coded for the visible tasks. Source: criteria 1 ("Think agentically").

- **AC-8 [LLM]** — The agent moves a creator through the whole chain (outreach → reply →
  negotiate → sample → post → bonus → follow-up) as a durable multi-turn loop
  (`advance` → `inbox`/`thread` → act), not one message then stop.
  Source: baseline.md "What's wrong", AGENTS.md "Mental model".

- **AC-9 [LLM]** — Before sending, the agent mines `data/past-messages.csv` (opt-outs,
  what landed), each creator's `thread`, and the task `ops_notices`.
  Source: AGENTS.md criterion 3, INSTRUCTIONS.md "Learn from the data".

## C. Messaging / meta fields

- **AC-10 [DET]** — The agent sends structured `meta` with `send_message` / `send_invite`
  where it can. Source: INSTRUCTIONS.md "Rules" / sim/API.md "meta".
  Pass: `agent/` passes a `meta=` argument on at least one `send_invite`/`send_message`
  call path.

- **AC-11 [LLM]** — `meta` is correct: right rate, right bonus terms, `decline` stance on
  fee / exclusivity / claim / competitor asks, and the text agrees with the fields.
  A wrong rate/bonus or an `accept` on those asks is itself a violation.
  Source: sim/API.md "meta", AGENTS.md "Hard rules".

## D. Compliance (−2 per violation, cap −20; each violation also fails its task)

- **AC-12 [DET]** — Shipped graded runs have **zero** policy violations.
  The violation set: wrong rate/bonus, banned claim, flat fee, pay-per-post, exclusivity,
  contacting a `do_not_contact` (flag **or** stop-language in past-messages), contacting an
  under-18 creator, sample outside the rules (held lot, shipping pause, repeat sample,
  open safety review), bonus not owed / after window, anything brand feedback rules out.
  Source: INSTRUCTIONS.md "How it's scored", pod.md, feedback/.
  Pass: every `runs/*/dashboard.json` reports `violations == 0`.

- **AC-13 [LLM]** — The policy gates are genuinely present in code/skills (opt-out from
  flag+history, minor gate, notices honored, sample rules, bonus-owed verification),
  not just absent-by-luck on the seen tasks. Source: baseline.md "What better means" 2.

## E. Escalation (15 pts: precision + recall, right person; ≤10/day cap)

- **AC-14 [DET]** — No run makes more than 10 escalations (experts take 10/day; one run
  folder = one day; −1 per escalation over 10).
  Source: pod.md / INSTRUCTIONS.md scoring.
  Pass: every `runs/*/dashboard.json` has `escalation.calls <= 10` (and `over_cap == 0`).

- **AC-15 [DET]** — Escalation routing config matches `pod.md`, not the stale starter:
  Marcus follower threshold is **250000** (not 100000) and Tomas/Nora keyword routes are
  populated. Source: baseline.md item 3, pod.md experts.
  Pass: `skills/_shared.md` front matter has `escalate_marcus_followers_over: 250000`
  and non-empty `escalate_tomas` and `escalate_nora` lists.

- **AC-16 [LLM]** — Escalations go to the right person for the right reason (Marcus=client/
  paid/legal, Priya=shipping/data/suspicious, Tomas=>250K/creative, Nora=health/skin/pet/
  minor/unsettled claim); routine shipping is an `ops_ticket`, not an expert; only what
  needs a person is escalated. Source: pod.md, AGENTS.md "Experts".

## F. Efficiency (15 pts: outreach messages per confirmed creator)

- **AC-17 [DET]** — Outreach efficiency: messages per confirmed creator ≤ 5 earns full
  marks; ≥10 earns zero. Source: INSTRUCTIONS.md scoring, baseline.md item 6.
  Pass: every `runs/*/dashboard.json` with outreach reports
  `outreach.messages_per_confirmed <= 5` (full efficiency band).

- **AC-18 [DET]** — Outreach confirmed meets each task's target.
  Source: INSTRUCTIONS.md scoring ("confirmed against the target"), baseline.md item 6.
  Pass: for outreach tasks, `confirmed >= target` (dashboard per_task).

## G. Brand feedback rules (from feedback/, apply round 2 onward & test run)

- **AC-19 [DET]** — The five post-round-1 feedback rules are written into `skills/` so the
  agent reads them: (a) never name a competitor to a creator; (b) no sweetener/second
  sample on a rate haggle, one sample per creator per product, offer a filming idea;
  (c) any dog reaction → Nora, no new product until cleared, don't tell the creator it
  wasn't the product; (d) Fernhill bonus deadline given as a calendar date; (e) Lumen
  banned words (natural/all natural/chemical free/burns clean/smells clean), allowed
  words (cozy, warm glow, hand poured). Source: feedback/brand-notes-after-round-1.md.
  Pass: each rule's distinctive tokens are present in the relevant `skills/` file(s).

- **AC-20 [LLM]** — Those feedback rules actually change agent behavior (correct routing,
  wording, deadlines), not merely text pasted in. Source: feedback/ + test-run framing.

- **AC-21 [DET]** — Fernhill round-2 swap handled: v3 Fernhill brief saved outside
  `brands/` before v4 copied over, and the bonus window honored as **10 days** for round 2.
  Source: INSTRUCTIONS.md round-2 step, feedback/fernhill-skin-v4.md.
  Pass: a saved copy of the v3 Fernhill brief exists outside `brands/`
  (e.g. `*fernhill*v3*` backup), OR the shipped `brands/fernhill-skin.md` is v4 (10 days)
  with the backup retained.

## H. Deliverables — "What to send back"

- **AC-22 [DET]** — Repo contains agent, skills, and evals.
  Source: INSTRUCTIONS.md "What to send back" 1.
  Pass: `agent/`, `skills/`, and at least one `runs/*` eval folder exist.

- **AC-23 [DET]** — `README.md` present with the one command and the model/settings used.
  Source: INSTRUCTIONS.md "What to send back" 2.
  Pass: `README.md` exists and contains `python3 agent/run.py` and a model/provider note.

- **AC-24 [DET]** — `notes.md` present with all four headings: **Improvements**, **Skill
  review**, **Design**, **Eval**. Source: INSTRUCTIONS.md "What to send back" 3.
  Pass: `notes.md` exists and contains each of the four headings.

- **AC-25 [DET]** — Run folders are shipped, each with a `dashboard.json`.
  Source: INSTRUCTIONS.md "What to send back" 4.
  Pass: at least one round-1 and one round-2 `runs/*` folder each contain `dashboard.json`.

- **AC-26 [DET]** — Eval numbers in `notes.md` match the shipped `dashboard.json` scores
  (they replay; a mismatch fails the project).
  Source: INSTRUCTIONS.md "How it's scored".
  Pass: every `runs/<folder>: <score>` named in the notes Eval table equals that folder's
  `dashboard.json["score"]`.

- **AC-27 [DET]** — A coding-agent session export/transcript is present (md/txt/json/jsonl)
  with the builder's turns and tool calls/edits. No export = no pass.
  Source: INSTRUCTIONS.md "What to send back" 5.
  Pass: a transcript file (md/txt/json/jsonl) exists at repo root or an `export/`-like
  location, non-trivial in size.

- **AC-28 [DET]** — Time-spent is recorded. Source: INSTRUCTIONS.md "What to send back" 6.
  Pass: `notes.md` or `README.md` states time spent.

## I. Judgment deliverables (LLM-graded)

- **AC-29 [LLM]** — Improvements section (0–5): every round-1 and round-2 exception ends as
  a named skill change or new step/handler, with file/function/section and the run that
  shows it working. Below 5 costs 2 points each under the total.
  Source: INSTRUCTIONS.md "improvement loop", AGENTS.md scoring note.

- **AC-30 [LLM]** — Skill review: a promote / merge / reject / keep-local decision with
  reason for **every** file in `gops-local-skills/` (9 files across Ana, Ben, Cleo), the
  conflicts called, and `skills/` edited to match; no promoted edit loosens a check.
  Source: INSTRUCTIONS.md "skill review", AGENTS.md.

- **AC-31 [LLM]** — No check, test, or threshold was loosened to pass (including promoting
  a GOPS skill that loosens a check). Source: INSTRUCTIONS.md item 8 / "How it's scored".

- **AC-32 [DET]** — The agent and `skills/` do not read `gops-local-skills/` at run time
  (the test run uses only `agent/` + `skills/`).
  Source: INSTRUCTIONS.md "skill review".
  Pass: no file under `agent/` or `skills/` references `gops-local-skills`.

## J. Final band

- **AC-33 [LLM]** — Total (dashboard on the 25-task test run minus the notes deduction)
  lands in the hire band or better (≥86; strong ≥92), with the Eval table showing
  before/after on both rounds and the run folder named next to every score.
  Source: INSTRUCTIONS.md "How it's scored". This is the roll-up verdict and is judged
  against the shipped run folders plus the (future) test run.
