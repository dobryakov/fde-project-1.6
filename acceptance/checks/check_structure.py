"""Deliverable structure: README, notes.md + four headings, requirements.txt,
run folders with dashboard.json, session export, time-spent. Covers
AC-2, AC-22, AC-23, AC-24, AC-25, AC-27, AC-28."""
import glob
import os

from _util import ROOT, bad, exists, ok, p, read, run_dirs


def run(root=ROOT):
    res = []

    # AC-2 requirements.txt
    if exists("requirements.txt"):
        res.append(ok("AC-2", "requirements.txt present at repo root"))
    else:
        res.append(bad("AC-2", "requirements.txt missing at repo root"))

    # AC-22 repo has agent, skills, evals
    have = [d for d in ("agent", "skills") if exists(d)]
    evals = run_dirs()
    if len(have) == 2 and evals:
        res.append(ok("AC-22", f"agent/, skills/ present; {len(evals)} eval run folder(s)"))
    else:
        res.append(bad("AC-22", f"present={have}; eval run folders with dashboard.json={len(evals)}"))

    # AC-23 README with command + model/settings
    rd = read("README.md").lower()
    if not rd:
        res.append(bad("AC-23", "README.md missing"))
    elif "python3 agent/run.py" in rd and ("claude_cli" in rd or "haiku" in rd or "sonnet" in rd or "model" in rd):
        res.append(ok("AC-23", "README.md has the one command and a model/settings note"))
    else:
        res.append(bad("AC-23", "README.md lacks the one command and/or a model/settings note"))

    # AC-24 notes.md four headings
    nm = read("notes.md").lower()
    if not nm:
        res.append(bad("AC-24", "notes.md missing"))
    else:
        want = ["improvements", "skill review", "design", "eval"]
        missing = [h for h in want if h not in nm]
        if missing:
            res.append(bad("AC-24", f"notes.md missing heading(s): {missing}"))
        else:
            res.append(ok("AC-24", "notes.md has Improvements, Skill review, Design, Eval"))

    # AC-25 round-1 and round-2 run folders each with dashboard.json
    names = [os.path.basename(d) for d in evals]
    has_r1 = any("r1" in n or "round1" in n for n in names)
    has_r2 = any("r2" in n or "round2" in n for n in names)
    if has_r1 and has_r2:
        res.append(ok("AC-25", f"run folders present for both rounds: {names}"))
    else:
        res.append(bad("AC-25", f"need a round-1 and a round-2 run folder with dashboard.json; found {names}"))

    # AC-27 session export/transcript
    pats = ["*.md", "*.txt", "*.json", "*.jsonl"]
    export = []
    for sub in ("", "export", "exports", "transcripts", "session", "sessions"):
        base = p(sub) if sub else ROOT
        for pat in pats:
            for f in glob.glob(os.path.join(base, pat)):
                fn = os.path.basename(f).lower()
                if any(k in fn for k in ("export", "transcript", "session", "conversation", "claude")):
                    if os.path.getsize(f) > 2000:
                        export.append(os.path.relpath(f, ROOT))
    if export:
        res.append(ok("AC-27", f"session export/transcript found: {export[:3]}"))
    else:
        res.append(bad("AC-27", "no coding-agent session export/transcript (md/txt/json/jsonl) found"))

    # AC-28 time spent recorded
    blob = (read("notes.md") + "\n" + read("README.md")).lower()
    if any(k in blob for k in ("time spent", "hours spent", "how long", "spent:")) or \
       ("spent" in blob and "hour" in blob):
        res.append(ok("AC-28", "time-spent recorded in notes.md/README.md"))
    else:
        res.append(bad("AC-28", "time-spent not recorded in notes.md/README.md"))

    return res
