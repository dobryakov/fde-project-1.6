"""A small per-run ledger that carries state across tasks in one run folder.

Some pod rules are cross-task (one run folder = one day): a bonus is paid once
even if the creator asks again in a later task, and a creator with an open safety
review gets no new sample until Nora clears it. A single task's AffiliateCenter
can't see the others, so we persist a tiny JSON ledger in the run folder and read
it before paying a bonus or shipping a sample.

Promoted from GOPS edits: cleo/paid-once and ben/open-review-check.
"""
import json
import os

_PATH = None


def set_dir(run_dir):
    global _PATH
    _PATH = os.path.join(run_dir, "agent_ledger.json")


def _load():
    if not _PATH or not os.path.exists(_PATH):
        return {"paid_bonuses": [], "safety_holds": []}
    try:
        with open(_PATH, encoding="utf-8") as f:
            d = json.load(f)
    except Exception:
        return {"paid_bonuses": [], "safety_holds": []}
    d.setdefault("paid_bonuses", [])
    d.setdefault("safety_holds", [])
    return d


def _save(d):
    if not _PATH:
        return
    with open(_PATH, "w", encoding="utf-8") as f:
        json.dump(d, f)


def bonus_already_paid(cid):
    return cid in _load()["paid_bonuses"]


def mark_bonus_paid(cid):
    d = _load()
    if cid not in d["paid_bonuses"]:
        d["paid_bonuses"].append(cid)
        _save(d)


def has_safety_hold(cid):
    return cid in _load()["safety_holds"]


def mark_safety_hold(cid):
    d = _load()
    if cid not in d["safety_holds"]:
        d["safety_holds"].append(cid)
        _save(d)
