"""Shared helpers for deterministic acceptance checks. Stdlib only."""
import glob
import json
import os
import re
import subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def p(*parts):
    return os.path.join(ROOT, *parts)


def exists(*parts):
    return os.path.exists(p(*parts))


def read(*parts):
    fp = p(*parts)
    if not os.path.exists(fp):
        return ""
    with open(fp, encoding="utf-8", errors="replace") as f:
        return f.read()


def run_dirs():
    """Every runs/* folder that contains a dashboard.json."""
    out = []
    base = p("runs")
    if not os.path.isdir(base):
        return out
    for d in sorted(glob.glob(os.path.join(base, "*"))):
        if os.path.isdir(d) and os.path.exists(os.path.join(d, "dashboard.json")):
            out.append(d)
    return out


def load_dashboard(run_dir):
    with open(os.path.join(run_dir, "dashboard.json"), encoding="utf-8") as f:
        return json.load(f)


def agent_sources():
    files = []
    for dp, _, fns in os.walk(p("agent")):
        for fn in fns:
            if fn.endswith(".py"):
                files.append(os.path.join(dp, fn))
    return files


def git_porcelain(*paths):
    try:
        out = subprocess.run(
            ["git", "status", "--porcelain", "--"] + list(paths),
            cwd=ROOT, capture_output=True, text=True, timeout=30,
        )
        return out.stdout.strip()
    except Exception as e:  # pragma: no cover
        return f"__error__:{e}"


def ok(cid, reason):
    return {"id": cid, "status": "PASS", "reason": reason}


def bad(cid, reason):
    return {"id": cid, "status": "FAIL", "reason": reason}
