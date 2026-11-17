"""Rank outreach-pick candidates by historical acceptance (learn from the data).

The pool-pick task invites a fixed number of creators from a large pool. Who we
pick decides the whole result. `data/past-messages.csv` shows acceptance varies
~15x by niche (cooking ~0.31 vs beauty ~0.02) and is higher at lower view tiers,
so sorting the pool by avg_views desc (the old behaviour) picks the *worst*
converters. Here we score each candidate by the acceptance rate of its niche and
view tier, learned from past outcomes, and the caller invites the top scorers.
"""
import csv
import os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
_MODEL = None
_MIN_N = 10  # need this many past messages before trusting a group's rate


def _view_bucket(v):
    v = int(v or 0)
    return "lo" if v < 15000 else "mid" if v < 40000 else "hi"


def _rates(pm, key):
    agg = defaultdict(lambda: [0, 0])
    for r in pm:
        agg[key(r)][0] += 1 if r.get("outcome") == "accepted" else 0
        agg[key(r)][1] += 1
    return {k: a / n for k, (a, n) in agg.items() if n >= _MIN_N}


def _model():
    global _MODEL
    if _MODEL is None:
        with open(os.path.join(ROOT, "data", "past-messages.csv"), encoding="utf-8") as f:
            pm = list(csv.DictReader(f))
        base = (sum(1 for r in pm if r.get("outcome") == "accepted") / len(pm)) if pm else 0.1
        _MODEL = {"base": base,
                  "niche": _rates(pm, lambda r: (r.get("niche") or "").strip().lower()),
                  "bucket": _rates(pm, lambda r: _view_bucket(r.get("avg_views_30d")))}
    return _MODEL


def acceptance_score(row):
    """Predicted acceptance for a creator, from past-message rates by niche and view tier."""
    m = _model()
    niche = (row.get("niche") or "").strip().lower()
    nr = m["niche"].get(niche, m["base"])
    br = m["bucket"].get(_view_bucket(row.get("avg_views_30d")), m["base"])
    # Niche is the stronger signal; view tier nudges it.
    return nr * 0.75 + br * 0.25


def rank(rows):
    """Pool candidates, best-converting first; tie-break toward lower view tiers."""
    return sorted(rows, key=lambda r: (-acceptance_score(r), int(r.get("avg_views_30d", 0) or 0)))
