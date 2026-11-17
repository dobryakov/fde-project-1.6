# ironco FDE — affiliate workflow agent

A reliable end-to-end workflow agent for Brightline's TikTok Shop affiliates pod. It moves a
creator through the whole chain — outreach → reply → negotiate → sample → post → bonus →
follow-up — as a per-creator state machine, reading the brief, thread, notices and past
messages before each action. Judgment lives in skills/briefs read at run time; hard checks
and transitions live in code.

## Run it

```bash
python3 agent/run.py tasks/round1.jsonl runs/r1
```

```bash
python3 dashboard.py runs/r1 detail
```

Round 2 (second world, Fernhill v4 brief):

```bash
cp feedback/fernhill-skin-v4.md brands/fernhill-skin.md
```

```bash
python3 sim/simctl.py init runs/r2 pack=sim/round2.pack
```

```bash
python3 agent/run.py tasks/round2.jsonl runs/r2
```

For a graded world, pass it through the environment (`SIM_PACK=/path/world.pack …`); the
command passes the environment through to `simctl init`.

## Model and settings

- Model calls go through `agent/llm.py`, provider **`claude_cli`** (`claude -p`), default
  model **haiku**. No other providers or API keys. `LLM_MAX_CALLS` caps calls per run (80).
- `LLM_PROVIDER=mock` runs with no model (templates only) for fast plumbing checks.
- Python 3.12, **standard library only** — see `requirements.txt` (no pip install needed).

## Layout

- `agent/` — `run.py` (dispatch + loop), `brief.py` (runtime brand numbers), `policy.py`
  (compliance gates), `escalation.py` (routing), `convo.py` (replies + meta + translation),
  `ledger.py` (cross-task bonus/safety state), `handlers/` (outreach, inbound, samples, live).
- `brands/` — briefs, the source of truth for every number (read at run time).
- `skills/` — voice, process and feedback rules the agent reads.
- `acceptance/` — self-built acceptance-criteria auditor (`python3 acceptance/run.py`).
- `notes.md` — Improvements, Skill review, Design, Eval.

## Results (real `claude_cli` runs)

| Run | Score | Band | Violations | Escalation F1 |
|:-|:-|:-|:-|:-|
| Round 1 (`runs/r1`, Fernhill v4) | 86.0 | hire | 0 | 1.00 |
| Round 2 (`runs/r2`) | 91.8 | hire | 0 | 1.00 |
| Baseline R1 / R2 | 12.3 / 0.0 | no | 6 / 14 | 0.00 |

Round 2 outreach efficiency 11.5/15 (6.17 msg/confirmed, 120/116 confirmed) after ranking pool
picks by learned acceptance. R206 (`haggle_sweetener`) is held at a clean compliant 0 — the
creator only accepts at a rate/sweetener that would be a policy violation.
