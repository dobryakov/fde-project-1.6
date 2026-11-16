#!/usr/bin/env python3
"""The scorecard. Run it on any finished agent run.

    python3 dashboard.py runs/r1                  # terminal table, plus runs/r1/dashboard.json and .html
    python3 dashboard.py runs/r1 detail           # adds one line per task, with what failed
    python3 dashboard.py runs/r1 baseline=path/to/dashboard.json

It first closes the run: every task clock moves to the end of its window so creator replies,
posts and fixes that are still on their way land. After that the run is final. A conversation your
agent left half way is scored as it stands.

Score out of 100. Each part names what it measures (INSTRUCTIONS.md, "What we're looking for"):
  task success      70   share of tasks done right; outreach scores confirmed / target;    items 2, 5, 7
                         any policy violation in a task fails that task
  escalation        15   F1 of escalation precision and recall (right person, right task)  item 4
  efficiency        15   outreach messages per confirmed creator: 5 or fewer is full,     item 3
                         10 or more is zero
  compliance       -20   minus 2 per policy violation, up to minus 20                      item 4
  escalation cap         minus 1 for each escalation over 10 in a run (the experts take 10 a day,
                         and one run is one day; pod.md)
The total never goes below 0.
Bands on our test run of 25 new tasks: 92 and up strong, 86 to 91 hire, under 86 no hire.
Cost and wall time are shown for information. They are not scored.

Keys: the dashboard reads the expected outcomes from keys/<scenario>.key. The round 1 and round 2 keys
ship with the case.
"""
import argparse
import html
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "sim"))
import affiliate_center as ac  # noqa: E402


def read_jsonl(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def load_key(data, key=None):
    path = key or os.path.join(HERE, "keys", data["scenario"]["name"] + ".key")
    if not os.path.exists(path):
        raise SystemExit(f"no key for scenario {data['scenario']['name']} (looked for {path}). Pass key=PATH.")
    k = ac._pack.load(path)
    if k.get("scenario") != data["scenario"]["name"]:
        raise SystemExit(f"key {path} is for {k.get('scenario')}, run is {data['scenario']['name']}")
    return k["expect"]


def summarize(run_dir, settle=True, key=None):
    run_dir = os.path.abspath(run_dir)
    data, mod, eng = ac.engine_for(run_dir)
    expect = load_key(data, key)
    events_path = os.path.join(run_dir, "events.jsonl")
    if settle and not any(e["type"] == "settled" for e in mod["iter_events"](events_path)):
        mod["settle"](eng)
    chain_ok, _ = mod["verify_chain"](events_path, eng.salt)
    res = mod["evaluate_all"](eng, expect)
    n = len(res)
    succ = sum(r["success"] for r in res)
    vio = [dict(v, task_id=r["task_id"]) for r in res for v in r["violations"]]
    # escalation precision and recall
    made = [(r["task_id"], to) for r in res for to in r["escalated_to"]]
    good = 0
    for r in res:
        for to in r["escalated_to"]:
            if to == r["escalation_needed"] or to in r["escalation_optional"]:
                good += 1
    needed = [r for r in res if r["escalation_needed"]]
    hit = sum(1 for r in needed if r["escalation_needed"] in r["escalated_to"])
    prec = good / len(made) if made else (1.0 if not needed else 0.0)
    rec = hit / len(needed) if needed else 1.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    esc_cap = data["scenario"].get("escalation_cap")
    esc_calls = sum(1 for e in mod["iter_events"](events_path) if e["type"] == "escalated")
    over_cap = max(0, esc_calls - esc_cap) if esc_cap is not None else 0
    out = [r for r in res if r["kind"] == "outreach"]
    conf = sum(r.get("confirmed", 0) for r in out)
    tgt = sum(r.get("target", 0) for r in out)
    omsgs = sum(r["messages"] for r in out)
    mpc = round(omsgs / conf, 2) if conf else None
    allmsgs = sum(r["messages"] for r in res)
    llm = read_jsonl(os.path.join(run_dir, "llm_calls.jsonl"))
    alog = read_jsonl(os.path.join(run_dir, "agent_log.jsonl"))
    evs = list(mod["iter_events"](events_path))
    wts = [e["wt"] for e in evs if e["ns"] not in ("_sim",) and "wt" in e]
    by = lambda key: {k: {"n": len(v), "success": round(sum(x["success"] for x in v), 2),
                          "rate": round(sum(x["success"] for x in v) / len(v), 3)} for k, v in _group(res, key).items()}
    by_ns = {}
    for e in evs:
        if e["type"] in ("message_sent", "invite_sent"):
            by_ns.setdefault(e["ns"], []).append(e.get("text", ""))
    for r in res:
        if r["success"] < 1 and r["kind"] != "outreach":
            r["sent_text"] = (by_ns.get(r["task_id"]) or [""])[-1][:400]
    live_nudge = [r for r in res if "posted_after" in r["checks"]]
    samples = [r for r in res if r["kind"] == "samples"]
    score_parts = {
        "task_success_70": round(70 * succ / n, 1) if n else 0,
        "escalation_15": round(15 * f1, 1),
        "efficiency_15": round(15 * max(0.0, min(1.0, (10 - mpc) / 5)), 1) if mpc else 0.0,
        "compliance_penalty": -round(min(20.0, 2.0 * len(vio)), 1),
        "escalation_cap_penalty": -float(over_cap),
    }
    total = round(max(0.0, sum(score_parts.values())), 1)
    return {
        "run_dir": run_dir, "scenario": data["scenario"]["name"], "log_untampered": chain_ok,
        "score": total, "band": "strong" if total >= 92 else "hire" if total >= 86 else "no", "parts": score_parts,
        "measures": {"task_success_70": "2 systems, 5 generalizes, 7 makes the call", "escalation_15": "4 shows the pieces (chose well)",
                     "efficiency_15": "3 learns from the data", "compliance_penalty": "4 vetting", "escalation_cap_penalty": "4 shows the pieces (escalates rarely)"},
        "tasks": n, "task_success": round(succ, 2), "task_success_rate": round(succ / n, 3) if n else 0,
        "untouched_tasks": [r["task_id"] for r in res if not r["touched"]],
        "by_brand": by("brand"), "by_kind": by("kind"), "by_type": by("type"),
        "violations": len(vio), "violations_by_kind": dict(Counter(v["kind"] for v in vio)), "violation_list": vio,
        "outreach": {"confirmed": conf, "target": tgt, "messages": omsgs, "messages_per_confirmed": mpc},
        "samples": {"tasks": len(samples), "done_right": sum(r["success"] for r in samples),
                    "shipped_right": sum(r["success"] for r in samples if "order" in r["checks"]),
                    "problems_resolved": sum(r["success"] for r in samples if "ticket" in r["checks"] or "no_ticket" in r["checks"]),
                    "escalated": sum(1 for r in samples if r["escalated_to"])},
        "live": {"nudge_tasks": len(live_nudge), "posting_recovered": sum(1 for r in live_nudge if r["checks"].get("posted_after")),
                 "posting_rate_recovered": round(sum(1 for r in live_nudge if r["checks"].get("posted_after")) / len(live_nudge), 3) if live_nudge else None},
        "escalation": {"made": len(made), "needed": len(needed), "precision": round(prec, 3), "recall": round(rec, 3), "f1": round(f1, 3),
                       "list": [f"{t}:{to}" for t, to in made], "calls": esc_calls, "cap": esc_cap, "over_cap": over_cap},
        "cost": {"messages": allmsgs, "platform_usd": round(allmsgs * data["scenario"].get("cost_per_message", 0.04), 2),
                 "llm_calls": len(llm), "llm_secs": round(sum(x.get("secs", 0) for x in llm), 1),
                 "llm_errors": sum(1 for x in llm if x.get("error"))},
        "wall_secs": round(max(wts) - min(wts), 1) if wts else None,
        "agent_errors": [a["task_id"] for a in alog if a.get("status") == "error"],
        "per_task": res,
    }


def _group(res, key):
    g = defaultdict(list)
    for r in res:
        g[r[key]].append(r)
    return dict(sorted(g.items()))


def row(label, s):
    o = s["outreach"]
    return (f"{label:12s} {s['score']:6.1f} {s['task_success_rate'] * 100:6.0f}% {s['violations']:5d} "
            f"{o['confirmed']:4d}/{o['target']:<4d} {str(o['messages_per_confirmed']):>6s} "
            f"{s['escalation']['precision']:5.2f} {s['escalation']['recall']:5.2f} "
            f"{str(s['live']['posting_rate_recovered']):>6s} ${s['cost']['platform_usd']:<7.2f} {s['cost']['llm_calls']:4d}")


def render(s, base=None, show_tasks=False):
    print(f"\nRun {s['run_dir']}  scenario {s['scenario']}  log ok: {s['log_untampered']}  band: {s['band']}")
    print(f"\n{'':12s} {'score':>6s} {'tasks':>7s} {'viol':>5s} {'confirmed':>9s} {'msg/c':>6s} {'prec':>5s} {'rec':>5s} {'posted':>6s} {'platform':8s} {'llm':>4s}")
    print(row("this run", s))
    if base:
        print(row("baseline", base))
    print("\nScore parts: " + ", ".join(f"{k} {v}" for k, v in s["parts"].items()))
    print("\nBy brand:   " + "  ".join(f"{k} {v['success']}/{v['n']}" for k, v in s["by_brand"].items()))
    print("By kind:    " + "  ".join(f"{k} {v['success']}/{v['n']}" for k, v in s["by_kind"].items()))
    print("By type:")
    for k, v in s["by_type"].items():
        print(f"  {k:28s} {v['success']}/{v['n']}")
    if s["violations"]:
        print("\nViolations:")
        for v in s["violation_list"]:
            print(f"  {v['task_id']} {v['kind']:24s} {v.get('creator_id') or '':8s} {v.get('detail', '')[:90]}")
    print(f"\nEscalations made: {', '.join(s['escalation']['list']) or 'none'}")
    if s["escalation"].get("over_cap"):
        print(f"Over the escalation cap: {s['escalation']['calls']} escalations, cap {s['escalation']['cap']}, minus {s['escalation']['over_cap']}")
    if s["untouched_tasks"]:
        print(f"Untouched tasks: {', '.join(s['untouched_tasks'])}")
    if s["agent_errors"]:
        print(f"Agent errors: {', '.join(s['agent_errors'])}")
    if show_tasks:
        print("\nPer task:")
        for r in s["per_task"]:
            failed = [k for k, v in r["checks"].items() if not v]
            extra = f" confirmed {r.get('confirmed')}/{r.get('target')}" if r["kind"] == "outreach" else ""
            vio = f" violations: {','.join(v['kind'] for v in r['violations'])}" if r["violations"] else ""
            print(f"  {r['task_id']} {r['brand'][:12]:12s} {r['type']:26s} {r['success']:.2f}{extra}"
                  f"{'  failed: ' + ','.join(failed) if failed else ''}{vio}")
            if r.get("sent_text"):
                print(f"        last message sent: {r['sent_text'][:200]}")


def write_html(s, base, path):
    rows = "".join(f"<tr><td>{html.escape(r['task_id'])}</td><td>{html.escape(r['brand'])}</td><td>{html.escape(r['type'])}</td>"
                   f"<td>{r['success']:.2f}</td><td>{html.escape(', '.join(k for k, v in r['checks'].items() if not v))}</td>"
                   f"<td>{html.escape(', '.join(v['kind'] for v in r['violations']))}</td></tr>" for r in s["per_task"])
    head = lambda x, lab: (f"<tr><td>{lab}</td><td>{x['score']}</td><td>{x['task_success_rate']:.0%}</td><td>{x['violations']}</td>"
                           f"<td>{x['outreach']['confirmed']}/{x['outreach']['target']}</td><td>{x['escalation']['f1']}</td>"
                           f"<td>{x['live']['posting_rate_recovered']}</td><td>${x['cost']['platform_usd']}</td><td>{x['cost']['llm_calls']}</td></tr>")
    doc = (f"<!doctype html><meta charset=utf-8><title>Agent dashboard</title><style>body{{font:14px system-ui;margin:24px}}"
           f"table{{border-collapse:collapse;margin:12px 0}}td,th{{border:1px solid #ccc;padding:4px 8px;text-align:left}}</style>"
           f"<h1>Agent dashboard</h1><p>{html.escape(s['run_dir'])}</p><table><tr><th></th><th>score</th><th>tasks</th><th>violations</th>"
           f"<th>confirmed</th><th>escalation F1</th><th>posting recovered</th><th>platform</th><th>model calls</th></tr>"
           f"{head(s, 'this run')}{head(base, 'baseline') if base else ''}</table><table><tr><th>task</th><th>brand</th><th>type</th>"
           f"<th>success</th><th>failed checks</th><th>violations</th></tr>{rows}</table>")
    with open(path, "w") as f:
        f.write(doc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("extra", nargs="*", help="detail, baseline=PATH, key=PATH")
    ap.add_argument("--baseline", default=None, help="a dashboard.json to show as the baseline row")
    ap.add_argument("--tasks", action="store_true", help="print one line per task")
    a = ap.parse_args()
    for tok in a.extra:
        if tok == "detail":
            a.tasks = True
        elif tok.startswith("baseline="):
            a.baseline = tok[9:]
        elif tok.startswith("key="):
            a.key = tok[4:]
    s = summarize(a.run_dir, key=getattr(a, "key", None))
    bpath = a.baseline
    if bpath is None:
        guess = os.path.join(HERE, "baseline", "starter-" + s["scenario"].replace("fde-project-", "") + ".json")
        if os.path.exists(guess):
            bpath = guess
    base = None
    if bpath and os.path.exists(bpath):
        with open(bpath) as f:
            base = json.load(f)
    render(s, base, a.tasks)
    with open(os.path.join(s["run_dir"], "dashboard.json"), "w") as f:
        json.dump(s, f, indent=1)
    write_html(s, base, os.path.join(s["run_dir"], "dashboard.html"))
    print(f"\nWrote {os.path.join(s['run_dir'], 'dashboard.json')} and dashboard.html")


if __name__ == "__main__":
    main()
