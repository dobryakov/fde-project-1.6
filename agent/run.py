#!/usr/bin/env python3
"""Run the affiliate agent on a task file against the sim.

    python3 agent/run.py tasks/round1.jsonl runs/r1
    python3 agent/run.py tasks/round1.jsonl runs/r1b only=R111,R112

Then score it:  python3 dashboard.py runs/r1 detail
Keep this command line working: our test run uses it on tasks you have not seen.
"""
import argparse
import json
import os
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "sim"))

import ledger  # noqa: E402
import llm  # noqa: E402
import skills  # noqa: E402
from affiliate_center import AffiliateCenter, init_run  # noqa: E402
from handlers import inbound, live, outreach, samples  # noqa: E402

HANDLERS = {"outreach": outreach.run, "inbound": inbound.run, "samples": samples.run, "live": live.run}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pos", nargs="*", help="TASKS_FILE RUN_DIR [only=ID,ID]")
    ap.add_argument("--tasks")
    ap.add_argument("--run-dir")
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    for tok in list(args.pos):
        if tok.startswith("only="):
            args.only = tok[5:]
            args.pos.remove(tok)
    args.tasks = args.tasks or (args.pos[0] if args.pos else None)
    args.run_dir = args.run_dir or (args.pos[1] if len(args.pos) > 1 else None)
    if not args.tasks or not args.run_dir:
        ap.error("usage: python3 agent/run.py TASKS_FILE RUN_DIR [only=ID,ID]")
    run_dir = os.path.abspath(args.run_dir)
    if not os.path.exists(os.path.join(run_dir, "state.db")):
        init_run(run_dir)
    llm.set_log(run_dir)
    ledger.set_dir(run_dir)  # cross-task ledger: bonuses paid once, safety holds
    only = {t for t in args.only.split(",") if t}
    with open(args.tasks, encoding="utf-8") as f:
        tasks = [json.loads(line) for line in f if line.strip()]
    log_path = os.path.join(run_dir, "agent_log.jsonl")
    for task in tasks:
        if only and task["task_id"] not in only:
            continue
        t0 = time.time()
        notes = []
        rec = {"task_id": task["task_id"], "brand": task["brand"], "kind": task["kind"]}
        try:
            ac = AffiliateCenter(run_dir, task=task["task_id"])
            skill = skills.load(task["brand"])
            rec["result"] = HANDLERS[task["kind"]](task, ac, skill, notes.append)
            rec["status"] = "done"
        except Exception as e:
            rec["status"] = "error"
            rec["error"] = f"{type(e).__name__}: {e}"
            notes.append(traceback.format_exc(limit=3))
        rec["notes"] = notes
        rec["secs"] = round(time.time() - t0, 2)
        with open(log_path, "a") as f:
            f.write(json.dumps(rec) + "\n")
        print(f"{task['task_id']} {task['kind']:9s} {rec['status']:5s} {rec['secs']:6.1f}s  {(notes or [''])[-1][:80]}")
    print(f"LLM calls: {llm.calls_made()}")


if __name__ == "__main__":
    main()
