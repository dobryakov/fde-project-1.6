#!/usr/bin/env python3
"""Acceptance runner for the ironco FDE project.

Runs every deterministic check under acceptance/checks/, lists the LLM-decision criteria
as MANUAL (never auto-passed), writes acceptance/state.json, prints a summary, and exits
non-zero if any deterministic check fails or any required artifact is missing.

    python3 acceptance/run.py

Stdlib only. The real operator agent is not built yet, so most deterministic checks are
expected to FAIL on a bootstrap run. That is correct — checks are never softened to pass.
"""
import datetime
import importlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CHECKS_DIR = os.path.join(HERE, "checks")
ROOT = os.path.abspath(os.path.join(HERE, ".."))
sys.path.insert(0, CHECKS_DIR)

LLM_FILE = os.path.join(HERE, "llm-criteria.md")


def discover_checks():
    mods = []
    for fn in sorted(os.listdir(CHECKS_DIR)):
        if fn.startswith("check_") and fn.endswith(".py"):
            mods.append(fn[:-3])
    return mods


def llm_ids():
    ids = []
    if os.path.exists(LLM_FILE):
        with open(LLM_FILE, encoding="utf-8") as f:
            for line in f:
                m = re.match(r'#{2,3}\s*(AC-\d+)\b', line.strip())
                if m:
                    ids.append(m.group(1))
    return ids


def main():
    results = []
    errors = []
    for modname in discover_checks():
        try:
            mod = importlib.import_module(modname)
            importlib.reload(mod)
            out = mod.run(ROOT)
            for r in out:
                r["check"] = modname
                results.append(r)
        except Exception as e:  # a broken check is a FAIL, never a silent pass
            errors.append((modname, repr(e)))
            results.append({"id": "?", "check": modname, "status": "ERROR", "reason": repr(e)})

    # sort by AC number where possible
    def keyf(r):
        m = re.match(r'AC-(\d+)', str(r.get("id", "")))
        return (int(m.group(1)) if m else 999, r.get("check", ""))
    results.sort(key=keyf)

    det_passed = [r for r in results if r["status"] == "PASS"]
    det_failed = [r for r in results if r["status"] in ("FAIL", "ERROR")]
    manual = llm_ids()

    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    overall = "FAIL" if det_failed else "PASS"

    state = {
        "timestamp": now,
        "root": ROOT,
        "rollup": {
            "det_total": len(results),
            "det_passed": len(det_passed),
            "det_failed": len(det_failed),
            "llm_manual": len(manual),
            "overall": overall,
        },
        "deterministic": results,
        "llm_manual": [{"id": i, "status": "MANUAL"} for i in manual],
    }
    with open(os.path.join(HERE, "state.json"), "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    # ---- readable summary ----
    print("=" * 72)
    print("ironco FDE — Acceptance audit")
    print(f"when: {now}")
    print("=" * 72)
    print("\nDETERMINISTIC CHECKS [DET]")
    for r in results:
        mark = {"PASS": "PASS", "FAIL": "FAIL", "ERROR": "ERR "}[r["status"]]
        print(f"  [{mark}] {str(r.get('id','?')):7s} {r['reason']}")
    print("\nLLM-DECISION CRITERIA [LLM] — MANUAL (never auto-passed):")
    print("  " + (", ".join(manual) if manual else "(none found)"))
    print("  See acceptance/llm-criteria.md for the review rubric.")

    print("\n" + "-" * 72)
    print(f"ROLLUP  det_passed={len(det_passed)}  det_failed={len(det_failed)}  "
          f"llm_manual={len(manual)}  overall={overall}")
    if errors:
        print("Check errors:")
        for m, e in errors:
            print(f"  {m}: {e}")
    print("state written to acceptance/state.json")
    print("-" * 72)

    sys.exit(0 if overall == "PASS" else 1)


if __name__ == "__main__":
    main()
