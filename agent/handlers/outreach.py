"""Outreach batches: invite a segment (or pick from a pool), then work replies until the window closes."""
import csv
import os
import re

from affiliate_center import SimError
from common import ROOT, by_handle, creators, first_name
from convo import answer, send_inv, send_msg
from policy import can_contact

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


def run(task, ac, skill, log):
    m = skill["meta"]
    rows = members(task)
    line = m["targeted_min_views"]
    # Gate: skip opt-outs (flag OR stop-language in past-messages) and minors,
    # and only invite creators who qualify for the targeted rate.
    targets = [r for r in rows if can_contact(r)[0] and int(r["avg_views_30d"]) >= line]
    skipped = len(rows) - len(targets)
    inv_meta = {"answers": "rate_q", "rate": m["targeted_rate"], "bonus_amount": m["bonus_amount"],
                "bonus_videos": m["bonus_videos"], "bonus_days": m["bonus_days"]}
    budget = task["msg_budget"]
    # Pool "pick" tasks convert at a lower rate, so spend more of the budget on
    # invites; segment tasks keep headroom for replies.
    invite_cap = int(budget * (0.9 if task.get("pool") else 0.75))
    sent = 0
    for r in targets:
        if sent >= invite_cap:
            break
        while True:
            try:
                send_inv(ac, r["creator_id"], m["targeted_rate"], invite_text(skill, r, m["targeted_rate"]),
                         {**inv_meta, "language": "en"})
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
            if r is None:
                continue
            try:
                if re.search(r"invite|where do i accept", low):
                    send_inv(ac, item["creator_id"], m["targeted_rate"],
                             invite_text(skill, r, m["targeted_rate"]), {**inv_meta, "language": "en"})
                else:
                    text, meta = answer(skill, r, item["text"], m["targeted_rate"])
                    send_msg(ac, item["creator_id"], text, meta)
            except SimError as e:
                if e.code in ("campaign_closed", "budget_exhausted"):
                    break
    log(f"invited {sent}, accepted {accepted}, skipped {skipped}")
    return {"invited": sent, "accepted": accepted, "skipped": skipped}
