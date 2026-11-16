# ironco: forward deployed engineer project

*This case is representative of the work we do. Creators are our main focus right now. Brightline, its brands, creators and numbers are made up.*

Start with `INSTRUCTIONS.md`, then `pod.md`.

```
python3 agent/run.py tasks/round1.jsonl runs/r1
python3 dashboard.py runs/r1 detail
```

- `brands/`: the five brand briefs, the source of truth
- `feedback/`: what the clients said after round 1 (read it after your round 1 run), and the Fernhill v4 brief for round 2
- `skills/`: the agent's skill files, one per brand plus `_shared.md`
- `gops-local-skills/`: three GOPS's own skill edits, for the skill review
- `agent/`: the starter agent (`run.py`, `handlers/`, `llm.py`)
- `tasks/round1.jsonl`: 15 tasks; `tasks/round2.jsonl`: 15 more in a second world (`python3 sim/simctl.py init runs/r2 pack=sim/round2.pack`)
- `data/`: creators, outreach segments and pools, and `past-messages.csv`
- `sim/`: the Affiliate Center sim (`sim/API.md`)
- `dashboard.py`: the scorecard (`keys/` holds the expected outcomes for both rounds)
- `baseline/`: the starter agent's dashboard on each round

Python 3.10 or newer. The starter's model calls go through `agent/llm.py`, which runs your local `claude -p` by default. Keep that provider: our test run uses it. `LLM_PROVIDER=mock` runs it with no model at all.

Replace this file with your own README when you send your work back.
