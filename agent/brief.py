"""Parse the brand brief in `brands/<brand>.md` at run time.

The briefs in `brands/` are the source of truth for every number (rates, bonus
terms, sample thresholds, ship countries). Skills can go stale and briefs can
change on the test run, so the agent reads the brief live and never trusts a
number copied elsewhere. Values parsed here override the skill front matter.

If a field can't be parsed, it is simply omitted and the caller falls back to the
skill value — the agent never invents a number.
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BRANDS = os.path.join(HERE, "..", "brands")
_CACHE = {}


def _int(s):
    return int(str(s).replace(",", "").strip())


def _search(pat, text, cast=_int, flags=re.I):
    m = re.search(pat, text, flags)
    return cast(m.group(1)) if m else None


def parse_brief(brand):
    """Return a dict of numbers/lists read from brands/<brand>.md (cached)."""
    if brand in _CACHE:
        return _CACHE[brand]
    path = os.path.join(BRANDS, brand + ".md")
    out = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            t = f.read()
        out["open_rate"] = _search(r"Open rate\s*\|\s*(\d+)\s*%", t)
        out["targeted_rate"] = _search(r"Targeted rate\s*\|\s*(\d+)\s*%", t)
        out["targeted_min_views"] = _search(r"averaging\s*([\d,]+)\s*or more views", t)
        mb = re.search(r"\$([\d,]+)\s*for\s*(\d+)\s*videos?\s*posted within\s*(\d+)\s*days", t, re.I)
        if mb:
            out["bonus_amount"] = _int(mb.group(1))
            out["bonus_videos"] = _int(mb.group(2))
            out["bonus_days"] = _int(mb.group(3))
        out["sample_min_followers"] = _search(r"Minimum\s*([\d,]+)\s*followers", t)
        out["sample_min_views"] = _search(r"Minimum average of\s*([\d,]+)\s*views", t)
        mh = re.search(r"hero product is (?:the\s*)?\*\*(.+?)\*\*", t, re.I)
        if mh:
            out["hero"] = mh.group(1).strip()
        # Ship countries: the briefs say "to the US and Canada only".
        ship = []
        low = t.lower()
        if "united states" in low or re.search(r"\bus\b", low) or "u.s." in low:
            ship.append("US")
        if "canada" in low:
            ship.append("CA")
        out["ship_countries"] = ship or ["US", "CA"]
        out["brief_version"] = (re.search(r"·\s*(v\d+)\s*·", t) or [None, None])[1]
    _CACHE[brand] = {k: v for k, v in out.items() if v is not None}
    return _CACHE[brand]
