"""Boundary rules: agent never reaches sim internals, and neither agent nor skills read
gops-local-skills at run time. Covers AC-5, AC-32."""
import os

import re

from _util import ROOT, agent_sources, bad, ok, p, read

# Pack files and pack.py are never legitimate for the agent. state.db is forbidden only
# when the agent OPENS/READS it for content; the starter's os.path.exists(...state.db)
# gate (used by init_run) is the public pattern and is allowed.
PACK_TOKENS = [".pack", "_core.pack", "round2.pack", "pack.py"]
STATE_READ = re.compile(r'(?:sqlite3|\.connect\s*\(|open\s*\([^)]*state\.db)', re.I)


def run(root=ROOT):
    res = []

    # AC-5 no sim-internal access from agent code. Importing the public API
    # (affiliate_center import AffiliateCenter / init_run) is allowed.
    hits = []
    for fp in agent_sources():
        txt = read_rel(fp)
        rel = os.path.relpath(fp, ROOT)
        for tok in PACK_TOKENS:
            if tok in txt:
                hits.append(f"{rel}: '{tok}'")
        if "state.db" in txt and STATE_READ.search(txt):
            hits.append(f"{rel}: opens/reads state.db")
    if hits:
        res.append(bad("AC-5", "agent references sim internals: " + "; ".join(hits)))
    else:
        res.append(ok("AC-5", "agent/ references no sim internals (*.pack / state.db / pack.py)"))

    # AC-32 agent and skills do not read gops-local-skills at run time
    gops_hits = []
    for fp in agent_sources():
        if "gops-local-skills" in read_rel(fp):
            gops_hits.append(os.path.relpath(fp, ROOT))
    skills_dir = p("skills")
    if os.path.isdir(skills_dir):
        for fn in os.listdir(skills_dir):
            fp = os.path.join(skills_dir, fn)
            if os.path.isfile(fp):
                with open(fp, encoding="utf-8", errors="replace") as f:
                    if "gops-local-skills" in f.read():
                        gops_hits.append(os.path.relpath(fp, ROOT))
    if gops_hits:
        res.append(bad("AC-32", "run-time read of gops-local-skills in: " + ", ".join(gops_hits)))
    else:
        res.append(ok("AC-32", "neither agent/ nor skills/ read gops-local-skills at run time"))

    return res


def read_rel(fp):
    with open(fp, encoding="utf-8", errors="replace") as f:
        return f.read()
