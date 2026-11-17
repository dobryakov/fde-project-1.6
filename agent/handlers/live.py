"""Live campaigns: verify posts (new-handle lookup, link, window, count) before
paying, nudge with the calendar deadline when a video is missing or broken, and
answer creative/exception messages from the brief."""
import re

import ledger
from affiliate_center import SimError
from common import creators, first_name
from convo import CLAIM_RE, answer, send_msg
from escalation import holding_reply, needed_person, safety_holding_reply
from policy import bonus_owed, deadline_date, _parse_dt  # noqa: F401


def _order_for(ac, cid, order_id):
    try:
        orders = ac.orders(cid).get("orders", [])
    except Exception:
        return {}
    for o in orders:
        if o.get("order_id") == order_id:
            return o
    return orders[0] if orders else {}


def _creative_reply(task, skill, first, msg):
    """Brief-settled creative/exception answers (not escalations)."""
    m = skill["meta"]
    low = msg.lower()
    # Unattended / overnight burning candle -> safety rule: must be attended.
    if re.search(r"overnight|burning.*(night|unattended)|leave.*candle.*burn|timelapse", low) and task["brand"] == "lumen-home":
        return (f"Hi {first}! Love the idea, but we can't show a candle burning unattended — any lit "
                f"candle on camera needs to be attended. How about a cozy evening clip while you're in "
                f"the room, warm glow and all?")
    # Asking to skip the product-in-first-3-seconds rule.
    if re.search(r"skip.*(first 3|3 second)|first 3 seconds rule|before the .* show up|open with", low):
        return (f"Hi {first}! The product does need to be on screen in the first 3 seconds to qualify for "
                f"the ${m['bonus_amount']} bonus — but you can do your slow pan right after. Try a quick "
                f"hero shot first, then the room reveal.")
    # Late / sick, "does it still count": reassure with the calendar deadline.
    if re.search(r"sick|been ill|next week|late|still count|still get|miss the", low):
        return None  # handled below with the real deadline date
    return None


def run(task, ac, skill, log):
    row = creators()[task["creator_id"]]
    cid = row["creator_id"]
    m = skill["meta"]
    first = first_name(row)
    msg = task.get("message") or ""
    order = _order_for(ac, cid, task.get("order_id"))
    deadline = deadline_date(order, m.get("bonus_days"))

    # 1) A message that needs a person.
    if msg:
        person = needed_person(task, skill, row, msg)
        if person:
            ac.escalate(person, f"{m['brand']} creator {row['handle']}: {msg}", creator_id=cid)
            ac.send_message(cid, safety_holding_reply(first) if person == "nora" else holding_reply(first, person))
            if person == "nora":
                ledger.mark_safety_hold(cid)
            log(f"escalated to {person}")
            return {"escalated": person}
        reply = _creative_reply(task, skill, first, msg)
        if reply is not None:
            ac.send_message(cid, reply)
            log("answered creative/exception")
        elif CLAIM_RE.search(msg.lower()):
            # A claim question (can I say X?): answer it with the brief/skill's
            # allowed vs banned wording before anything else (LLM-drafted).
            text, meta = answer(skill, row, msg, m.get("targeted_rate"))
            send_msg(ac, cid, text, meta)
            log("answered claim")
        elif deadline:
            # Late/sick or general: reassure with the calendar deadline.
            ac.send_message(cid, f"Hi {first}! No worries — as long as both videos are up by {deadline} "
                                 f"(within {m['bonus_days']} days of delivery), the ${m['bonus_amount']} "
                                 f"bonus still counts. Shout if you need a filming idea!")
            log("answered deadline")

    # Delivery never completed (returned/exception): the creator can't film, so
    # this is an ops problem, not a posting nudge.
    status = (order or {}).get("status", "")
    if status in ("returned_to_sender", "returned", "exception", "lost", "delivery_exception"):
        ac.ops_ticket("missing", cid, order_id=order.get("order_id"),
                      note=f"Sample {status}; needs a resend before the creator can post.")
        ac.send_message(cid, f"Hi {first}! Your sample didn't make it to you — I've asked ops to resend it, "
                             f"and we'll make sure you have time to post once it arrives.")
        log(f"ops ticket: sample {status}")
        return {"ticket": status}

    # Cross-task: never pay the same bonus twice (promoted from cleo/paid-once).
    if ledger.bonus_already_paid(cid):
        ac.send_message(cid, f"Hi {first}! Your ${m['bonus_amount']} bonus already went out — thanks again "
                             f"for the videos!")
        log("bonus already paid; not paying again")
        return {"paid": False, "reason": "already_paid"}

    # 2) Verify posts and pay if owed, else nudge with specifics + deadline.
    owed, valid, need, issues, posts = bonus_owed(ac, skill, cid, task.get("handle"), order)
    if owed:
        try:
            ac.pay_bonus(cid, note=f"{valid} valid videos")
            ledger.mark_bonus_paid(cid)
            ac.send_message(cid, f"Hi {first}! Thanks for the videos — your ${m['bonus_amount']} bonus is "
                                 f"on its way.")
            log(f"paid bonus ({valid}/{need})")
            return {"paid": True, "valid": valid}
        except SimError as e:
            log(f"pay_bonus refused: {e.code}")
            return {"paid": False, "error": e.code}

    # Not owed yet: nudge — but don't pile a nudge on top of a substantive answer
    # this tick (that reads as pushy). If we answered a question, let the work-loop
    # handle posting; otherwise nudge now, naming the real blocker.
    reason = ", ".join(sorted(issues)) if issues else f"{valid} of {need} videos so far"
    by = f" by {deadline}" if deadline else f" within {m['bonus_days']} days of delivery"
    # A posting nudge is always on-topic for a live campaign (it's what prompts the
    # creator to post and earn the bonus), so send it even after answering a message.
    nudge = (f"Hi {first}! You're at {valid} of {need} videos for the ${m['bonus_amount']} bonus"
             f"{(' — fix: ' + reason) if issues else ''}. Post the rest{by} and it's yours. "
             f"Idea: show the product in the first 3 seconds with the shop link tagged.")
    ac.send_message(cid, nudge)
    log(f"nudged ({valid}/{need}; {reason})")

    # 3) Work it over the window: advance, answer follow-ups, re-check posts so
    #    late posters still get paid.
    steps = max(2, int((task.get("days") or 2)))
    for _ in range(steps):
        try:
            ac.advance(24)
        except SimError:
            break
        try:
            for item in ac.inbox().get("items", []):
                if item.get("creator_id") != cid:
                    continue
                txt = item.get("text", "")
                person = needed_person(task, skill, row, txt)
                if person:
                    ac.escalate(person, f"{m['brand']} creator {row['handle']}: {txt}", creator_id=cid)
                    ac.send_message(cid, safety_holding_reply(first) if person == "nora" else holding_reply(first, person))
                    if person == "nora":
                        ledger.mark_safety_hold(cid)
                    log(f"escalated to {person}")
                    return {"escalated": person}
                # Answer only a specific creative/exception question; don't re-nudge
                # every step (duplicate messages lose the creator).
                reply = _creative_reply(task, skill, first, txt)
                if reply:
                    ac.send_message(cid, reply)
        except SimError:
            pass
        owed, valid, need, issues, posts = bonus_owed(ac, skill, cid, task.get("handle"), order)
        if owed:
            try:
                ac.pay_bonus(cid, note=f"{valid} valid videos")
                ledger.mark_bonus_paid(cid)
                ac.send_message(cid, f"Hi {first}! Both videos are up — your ${m['bonus_amount']} bonus is "
                                     f"on its way. Thank you!")
                log(f"paid bonus after window ({valid}/{need})")
                return {"paid": True, "valid": valid}
            except SimError as e:
                log(f"pay_bonus refused: {e.code}")
                break
    return {"paid": False, "valid": valid, "need": need}
