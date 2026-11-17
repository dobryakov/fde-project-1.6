"""Eval numbers in notes.md must equal the shipped dashboard.json scores (they replay).
Covers AC-26."""
import json
import os
import re

from _util import ROOT, bad, ok, p, read


def run(root=ROOT):
    res = []
    notes = read("notes.md")
    if not notes:
        res.append(bad("AC-26", "notes.md missing; cannot verify eval numbers match dashboard.json"))
        return res

    # Find patterns like 'runs/r2-final: 88.4' or 'runs/r1 ... 88.4'
    pairs = re.findall(r'runs/([A-Za-z0-9._\-]+)[^\d\n]{0,40}?(\d{1,3}(?:\.\d)?)', notes)
    if not pairs:
        res.append(bad("AC-26", "no 'runs/<folder>: <score>' entries found in notes.md Eval section"))
        return res

    mismatches, checked = [], 0
    for folder, score_s in pairs:
        dpath = p("runs", folder, "dashboard.json")
        if not os.path.exists(dpath):
            mismatches.append(f"{folder}: no dashboard.json")
            continue
        with open(dpath, encoding="utf-8") as f:
            actual = json.load(f).get("score")
        try:
            claimed = float(score_s)
        except ValueError:
            continue
        checked += 1
        if actual is None or abs(float(actual) - claimed) > 0.05:
            mismatches.append(f"{folder}: notes={claimed} dashboard={actual}")

    if mismatches:
        res.append(bad("AC-26", "eval/dashboard mismatch: " + "; ".join(mismatches)))
    elif checked == 0:
        res.append(bad("AC-26", "no notes score could be matched to an existing dashboard.json"))
    else:
        res.append(ok("AC-26", f"all {checked} notes eval score(s) match dashboard.json"))
    return res
