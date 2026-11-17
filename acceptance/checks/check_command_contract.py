"""The one-command contract and the untouched-sim rule. Covers AC-1, AC-4."""
import ast

from _util import ROOT, bad, exists, git_porcelain, ok, read


def run(root=ROOT):
    res = []

    # AC-1 agent/run.py exists, parses, takes TASKS_FILE RUN_DIR positionally
    src = read("agent", "run.py")
    if not exists("agent", "run.py"):
        res.append(bad("AC-1", "agent/run.py missing"))
    else:
        try:
            ast.parse(src)
            parses = True
        except SyntaxError as e:
            parses = False
            res.append(bad("AC-1", f"agent/run.py does not parse: {e}"))
        if parses:
            if "add_argument" in src and ("pos" in src or "TASKS_FILE" in src or "run_dir" in src):
                res.append(ok("AC-1", "agent/run.py parses and accepts TASKS_FILE RUN_DIR positionally"))
            else:
                res.append(bad("AC-1", "agent/run.py parses but positional TASKS_FILE/RUN_DIR not evident"))

    # AC-4 sim/ and dashboard.py untouched
    porc = git_porcelain("sim", "dashboard.py")
    if porc.startswith("__error__"):
        res.append(bad("AC-4", f"could not run git status: {porc}"))
    elif porc == "":
        res.append(ok("AC-4", "sim/ and dashboard.py have no tracked modifications"))
    else:
        res.append(bad("AC-4", f"tracked changes under sim/ or dashboard.py:\n{porc}"))

    return res
