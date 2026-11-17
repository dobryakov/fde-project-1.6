"""Escalation routing config in skills/_shared.md matches pod.md, not the stale starter.
Covers AC-15."""
import re

from _util import ROOT, bad, ok, read


def run(root=ROOT):
    res = []
    shared = read("skills", "_shared.md")
    if not shared:
        res.append(bad("AC-15", "skills/_shared.md missing"))
        return res

    probs = []
    m = re.search(r'escalate_marcus_followers_over:\s*(\d+)', shared)
    if not m:
        probs.append("escalate_marcus_followers_over not set")
    elif int(m.group(1)) != 250000:
        probs.append(f"follower threshold is {m.group(1)}, pod.md says 250000 (Tomas)")

    def listval(key):
        mm = re.search(rf'{key}:\s*(.*)', shared)
        return (mm.group(1).strip() if mm else "")

    if not listval("escalate_tomas"):
        probs.append("escalate_tomas list empty (should route >250K / creative exceptions)")
    if not listval("escalate_nora"):
        probs.append("escalate_nora list empty (should route health/skin/pet reaction, minors)")

    if probs:
        res.append(bad("AC-15", "; ".join(probs)))
    else:
        res.append(ok("AC-15", "escalation routing: Marcus threshold 250000, Tomas & Nora routes populated"))
    return res
