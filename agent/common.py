"""Helpers shared by the handlers: creator data, escalation routing, prompt building."""
import csv
import os

from llm import complete

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
_DB = {}


def creators():
    if not _DB:
        with open(os.path.join(ROOT, "data", "creators.csv"), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                _DB[r["creator_id"]] = r
                _DB["handle:" + r["handle"].lower()] = r
    return _DB


def by_handle(handle):
    return creators().get("handle:" + handle.lower())


def first_name(row):
    return (row.get("name") or "there").split()[0]


def tier_rate(skill, row):
    m = skill["meta"]
    return m["targeted_rate"] if int(row["avg_views_30d"]) >= m["targeted_min_views"] else m["open_rate"]


def route_escalation(skill, text, row=None):
    """Return the person to escalate to, or None, from the keyword lists in _shared.md."""
    low = (text or "").lower()
    sh = skill["shared"]
    for person in ("marcus", "priya", "tomas", "nora"):
        words = [w.strip() for w in str(sh.get("escalate_" + person, "")).split(",") if w.strip()]
        if any(w in low for w in words):
            return person
    line = sh.get("escalate_marcus_followers_over")
    if row and line and int(row["followers"]) > int(line):
        return "marcus"
    return None


def draft(skill, row, situation, fallback, tag):
    """Ask the model for a message to the creator. Falls back to a template if the model is off."""
    m = skill["meta"]
    system = (f"You write messages from Brightline, a TikTok Shop affiliate agency, to creators for {m['brand']}. "
              f"Write only the message text, nothing else.")
    prompt = (f"Shared rules:\n{skill['shared_body']}\n\nBrand skill:\n{skill['body']}\n\n"
              f"Facts: open rate {m['open_rate']}%, targeted rate {m['targeted_rate']}% for creators at or over "
              f"{m['targeted_min_views']} average views. Bonus ${m['bonus_amount']} for {m['bonus_videos']} videos within "
              f"{m['bonus_days']} days of delivery. Never say: {', '.join(m['banned'])}.\n\n"
              f"Creator: {first_name(row)} ({row['handle']}), {row['followers']} followers, {row['avg_views_30d']} avg views, "
              f"niche {row['niche']}, country {row['country']}.\n\nSituation:\n{situation}\n\nWrite the message.")
    out = complete(prompt, system=system, tag=tag)
    return out or fallback
