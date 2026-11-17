"""Scoreable outcomes from shipped runs/*/dashboard.json:
AC-12 zero violations, AC-14 escalation cap (<=10), AC-17 efficiency (<=5 msg/confirmed),
AC-18 confirmed >= target. Each criterion fails if there are no run folders to judge."""
from _util import ROOT, bad, load_dashboard, ok, run_dirs

import os


def run(root=ROOT):
    res = []
    runs = run_dirs()
    if not runs:
        for cid, what in [("AC-12", "violations"), ("AC-14", "escalation cap"),
                          ("AC-17", "efficiency"), ("AC-18", "confirmed vs target")]:
            res.append(bad(cid, f"no runs/*/dashboard.json to evaluate {what}"))
        return res

    names = [os.path.basename(d) for d in runs]

    # AC-12 zero violations across all runs
    viol = {}
    for d in runs:
        v = load_dashboard(d).get("violations", None)
        viol[os.path.basename(d)] = v
    bad_runs = {k: v for k, v in viol.items() if v is None or v > 0}
    if bad_runs:
        res.append(bad("AC-12", f"policy violations present: {bad_runs} (need 0 in every run)"))
    else:
        res.append(ok("AC-12", f"zero policy violations across runs {names}"))

    # AC-14 escalation cap <= 10, over_cap == 0
    over = {}
    for d in runs:
        esc = load_dashboard(d).get("escalation", {})
        calls = esc.get("calls")
        oc = esc.get("over_cap", 0)
        if calls is None or calls > 10 or oc:
            over[os.path.basename(d)] = {"calls": calls, "over_cap": oc}
    if over:
        res.append(bad("AC-14", f"escalation cap exceeded: {over} (<=10/run)"))
    else:
        res.append(ok("AC-14", f"escalations within 10/day in every run {names}"))

    # AC-17 efficiency: outreach messages_per_confirmed <= 5 (full efficiency band)
    eff = {}
    for d in runs:
        o = load_dashboard(d).get("outreach", {})
        mpc = o.get("messages_per_confirmed")
        if mpc is not None and mpc > 5:
            eff[os.path.basename(d)] = mpc
    if eff:
        res.append(bad("AC-17", f"outreach msg/confirmed over 5 (sub-full efficiency): {eff}"))
    else:
        res.append(ok("AC-17", "outreach efficiency at full band (<=5 msg/confirmed) where applicable"))

    # AC-18 confirmed >= target for outreach tasks
    short = {}
    for d in runs:
        for r in load_dashboard(d).get("per_task", []):
            if r.get("kind") == "outreach":
                c, t = r.get("confirmed", 0), r.get("target", 0)
                if t and c < t:
                    short[f"{os.path.basename(d)}:{r['task_id']}"] = f"{c}/{t}"
    if short:
        res.append(bad("AC-18", f"outreach below target: {short}"))
    else:
        res.append(ok("AC-18", "every outreach task meets its confirmed target"))

    return res
