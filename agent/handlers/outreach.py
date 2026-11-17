"""Outreach batches: invite a segment (or pick from a pool), then work replies until the window closes."""
import csv
import os
import re

from affiliate_center import SimError
from common import ROOT, by_handle, creators, first_name
from convo import answer, render, send_inv, send_msg
from policy import can_contact

IDEAS = {"kettle-and-crumb": "a crunch close up in the first 3 seconds",
         "tidewater-coffee": "your first sip on a slow morning"}

NAME = "NAMEX"    # ALLCAPS placeholders the translator keeps; filled per creator
NICHE = "NICHEX"


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
    # Pool "pick" tasks invite only a capped slice of a large pool, so *who* we pick
    # drives the result. `data/past-messages.csv` shows acceptance varies widely by
    # niche and is higher at lower view tiers, so the old "highest avg_views first"
    # order front-loaded the worst converters. Rank pool candidates by learned
    # acceptance (agent/targeting.py) so the invite budget hits the best converters
    # first. Segment tasks invite everyone given, so their order is immaterial.
    if task.get("pool"):
        import targeting
        return targeting.rank(rows)
    rows.sort(key=lambda r: -int(r["avg_views_30d"]))
    return rows


def _invite_body(skill, rate):
    """A per-(brand, rate) invite body with NAME/NICHE placeholders — identical
    across creators of a language, so `render` translates it once per language
    (cached). For English the placeholders just fill back the full personalization."""
    m = skill["meta"]
    return (f"Hi {NAME}! We love your {NICHE} videos. {m['brand']} would love to send you our {m['hero']}. "
            f"You'd earn {rate}% commission, plus a ${m['bonus_amount']} bonus for {m['bonus_videos']} videos "
            f"posted within {m['bonus_days']} days of delivery. Idea: {IDEAS.get(m['skill'], 'show it in the first 3 seconds')}.")


def invite_for(skill, row, rate):
    """(text, language) — invite in the creator's language, name and niche filled."""
    body, lang = render(_invite_body(skill, rate), row.get("language", "en") or "en", must_keep=(NAME, NICHE))
    text = body.replace(NAME, first_name(row)).replace(NICHE, row.get("niche", ""))
    return text, lang


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
                itext, ilang = invite_for(skill, r, m["targeted_rate"])
                send_inv(ac, r["creator_id"], m["targeted_rate"], itext, {**inv_meta, "language": ilang})
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
                    itext, ilang = invite_for(skill, r, m["targeted_rate"])
                    send_inv(ac, item["creator_id"], m["targeted_rate"], itext, {**inv_meta, "language": ilang})
                else:
                    # Bulk outreach: deterministic template reply (LLM drafting is
                    # reserved for the dedicated inbound/sample/live negotiations —
                    # per-replier LLM calls here would blow the time budget).
                    text, meta = answer(skill, r, item["text"], m["targeted_rate"], use_llm=False)
                    send_msg(ac, item["creator_id"], text, meta)
            except SimError as e:
                if e.code in ("campaign_closed", "budget_exhausted"):
                    break
    log(f"invited {sent}, accepted {accepted}, skipped {skipped}")
    return {"invited": sent, "accepted": accepted, "skipped": skipped}
