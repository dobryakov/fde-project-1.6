"""Outreach batches: invite a segment (or pick from a pool), then work replies until the window closes."""
import csv
import os
import re

from affiliate_center import SimError
from common import ROOT, by_handle, creators, first_name

IDEAS = {"kettle-and-crumb": "a crunch close up in the first 3 seconds",
         "tidewater-coffee": "your first sip on a slow morning"}


def members(task):
    if task.get("segment"):
        with open(os.path.join(ROOT, task["segment"]), encoding="utf-8") as f:
            handles = [r["handle"] for r in csv.DictReader(f)]
        return [r for r in (by_handle(h) for h in handles) if r]
    with open(os.path.join(ROOT, task["pool"]), encoding="utf-8") as f:
        ids = [r["creator_id"] for r in csv.DictReader(f)]
    skip = set()
    for seg in task.get("exclude_segments", []):
        with open(os.path.join(ROOT, "data", "segments", seg + ".csv"), encoding="utf-8") as f:
            skip |= {r["handle"].lower() for r in csv.DictReader(f)}
    db = creators()
    rows = [db[i] for i in ids if i in db and db[i]["handle"].lower() not in skip]
    rows.sort(key=lambda r: -int(r["avg_views_30d"]))
    return rows


def invite_text(skill, row, rate):
    m = skill["meta"]
    return (f"Hi {first_name(row)}! We love your {row['niche']} videos. {m['brand']} would love to send you our {m['hero']}. "
            f"You'd earn {rate}% commission, plus a ${m['bonus_amount']} bonus for {m['bonus_videos']} videos posted within "
            f"{m['bonus_days']} days of delivery. Idea: {IDEAS.get(m['skill'], 'show it in the first 3 seconds')}.")


def answer(skill, row, text, rate):
    m = skill["meta"]
    low = text.lower()
    hi = f"Hi {first_name(row)}! "
    if re.search(r"flat|upfront|up front|per video|a post|charge|fee", low):
        return hi + f"We don't do flat fees. It's {rate}% commission plus the ${m['bonus_amount']} posting bonus."
    if re.search(r"exclusiv|other brands|still work with", low):
        return hi + "No exclusivity, you can post any other brand you like."
    if re.search(r"commission|rate|percent|cut|how much", low):
        return hi + f"Your commission is {rate}% on every sale. Accept the invite whenever you're ready."
    if re.search(r"bonus", low):
        return hi + (f"The bonus is ${m['bonus_amount']} once you post {m['bonus_videos']} videos within "
                     f"{m['bonus_days']} days of delivery.")
    if re.search(r"sample|ship|send product|try it", low):
        return hi + "Yes, we ship you a free sample once you accept the invite."
    if re.search(r"say|caption|hook|mention", low):
        return hi + "Please keep it to taste and texture. We can't make that kind of claim."
    return hi + "Thanks! Accept the invite whenever you're ready."


def run(task, ac, skill, log):
    m = skill["meta"]
    rows = members(task)
    line = m["targeted_min_views"]
    targets = [r for r in rows if r["do_not_contact"] != "yes" and int(r["avg_views_30d"]) >= line]
    budget = task["msg_budget"]
    invite_cap = int(budget * 0.75)
    sent = 0
    for r in targets:
        if sent >= invite_cap:
            break
        while True:
            try:
                ac.send_invite(r["creator_id"], m["targeted_rate"], invite_text(skill, r, m["targeted_rate"]))
                sent += 1
                break
            except SimError as e:
                if e.code == "rate_limited":
                    ac.advance(max(0.25, e.extra.get("retry_after_hours", 1)))
                    continue
                log(f"invite failed {r['creator_id']}: {e.code}")
                break
    accepted = 0
    db = creators()
    for _ in range(40):
        try:
            ac.advance(6)
        except SimError:
            break
        for item in ac.inbox()["items"]:
            r = db.get(item["creator_id"])
            if item["kind"] == "invite_accepted":
                accepted += 1
                continue
            low = item["text"].lower()
            if re.search(r"pass|no thanks|not a fit|booked|don't think", low):
                continue
            try:
                if re.search(r"invite|where do i accept", low):
                    ac.send_invite(item["creator_id"], m["targeted_rate"], invite_text(skill, r, m["targeted_rate"]))
                else:
                    ac.send_message(item["creator_id"], answer(skill, r, item["text"], m["targeted_rate"]))
            except SimError as e:
                if e.code in ("campaign_closed", "budget_exhausted"):
                    break
    log(f"invited {sent}, accepted {accepted}")
    return {"invited": sent, "accepted": accepted}
