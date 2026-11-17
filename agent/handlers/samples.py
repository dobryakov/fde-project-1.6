"""Sample requests and shipping problems. Hard gates (held lot, shipping pause,
repeat sample, minimums) live in policy; reactions go to Nora."""
import re

import ledger
from common import creators, first_name
from convo import answer, send_msg, work_thread
from escalation import holding_reply, needed_person, safety_holding_reply
from policy import sample_decision


def _delivery_address(ac, cid, order_id):
    try:
        for o in ac.orders(cid).get("orders", []):
            if o.get("order_id") == order_id:
                return (o.get("address") or "").strip()
    except Exception:
        pass
    return ""


def _norm_addr(a):
    return re.sub(r"[^a-z0-9]+", " ", (a or "").lower()).strip()


def _same_address(a, b):
    na, nb = _norm_addr(a), _norm_addr(b)
    if not na or not nb:
        return True  # unknown -> don't assume a mismatch
    # Compare the street-number + first token, which is enough to spot a move.
    return na.split()[:3] == nb.split()[:3]


def _safety_followup(first, person, txt):
    """Reply to a follow-up while a safety/expert review is open. Never ships,
    promises a product, gives a date, or says it wasn't our product. Returns None
    when there's nothing new to add (so we don't repeat ourselves)."""
    low = (txt or "").lower()
    who = "Nora from our care team" if person == "nora" else "our team"
    # "Who / when will be in touch?"
    if re.search(r"who|when|how long|hear back|get back|be in touch|reach out|contact me", low):
        return (f"Hi {first}! {who} will reach out to you directly — usually within a day or two. "
                f"Thanks so much for your patience.", None)
    # Asking for a new/another product while the review is open.
    if re.search(r"send|ship|another|fish oil|next (one|product)|more|sample|try", low):
        return (f"Hi {first}! While our care team takes a look, we're holding off on sending anything "
                f"new — I don't want to ship more until we've checked in. I'll be in touch as soon as "
                f"we can.", None)
    # A thank-you / acknowledgement needs no further message.
    if re.search(r"thank|thanks|ok\b|okay|got it|sounds good|appreciate|no worries", low):
        return None
    # Anything else: a short, warm reassurance (no product talk, no claims).
    return (f"Hi {first}! Totally hear you — {who} will follow up directly and we'll make sure you're "
            f"looked after. Appreciate you flagging it.", None)


def run(task, ac, skill, log):
    row = creators()[task["creator_id"]]
    cid = row["creator_id"]
    m = skill["meta"]
    first = first_name(row)
    msg = task.get("message") or ""
    low = msg.lower()
    order = task.get("order_id")
    try:
        notices = ac.notices().get("notices", [])
    except Exception:
        notices = []

    # 1) Anything that needs a person (a reaction goes to Nora, even if the
    #    creator calls it unrelated; we never tell them it wasn't the product).
    person = needed_person(task, skill, row, msg)
    if person:
        ac.escalate(person, f"{m['brand']} creator {row['handle']}: {msg}", creator_id=cid)
        hold_text = safety_holding_reply(first) if person == "nora" else holding_reply(first, person)
        if person == "nora":
            ledger.mark_safety_hold(cid)  # no new sample until Nora clears (pod rule)
        log(f"escalated to {person}")
        # Stay with the thread across the window: keep reassuring and answering the
        # creator's follow-ups (e.g. "who's in touch?", "can you send X?") while the
        # review is open — ship nothing, promise nothing, re-escalate nothing, never
        # say it wasn't the product. A one-and-done message loses the conversation.
        res = work_thread(ac, cid, skill, row, m.get("targeted_rate"), task.get("days"), log,
                          first=(hold_text, None), seed_text=msg,
                          reply_fn=lambda txt: _safety_followup(first, person, txt),
                          persist_close=False)
        return {"escalated": person, **res}

    # 2) A sample request: decide with the gates, ship a shippable lot.
    product = task.get("product_requested")
    if product:
        # Cross-task: a creator with an open safety review gets no new sample
        # until Nora clears it (promoted from ben/open-review-check).
        if ledger.has_safety_hold(cid):
            ac.send_message(cid, f"Hi {first}! We're holding new samples for you until our care team has "
                                 f"checked in — thanks for your patience.")
            log("sample held (open safety review)")
            return {"held": "safety_review"}
        action, lot, reason = sample_decision(ac, skill, row, product, notices)
        if action == "ship":
            res = ac.ship_sample(cid, product, lot=lot)
            ac.send_message(cid, f"Hi {first}! Your {product} sample is approved and ships within 5 "
                                 f"business days. Idea: show it in the first 3 seconds.")
            log(f"shipped {product} lot {lot}")
            return {"shipped": product, "lot": lot, "order_id": res.get("order_id")}
        if action == "delay_shipping":
            ac.send_message(cid, f"Hi {first}! That one's delayed right now, so I can't ship it yet — "
                                 f"I'll let you know as soon as it's available.")
            log("sample delayed (shipping pause)")
            return {"delayed": product}
        if action == "decline_repeat":
            ac.send_message(cid, f"Hi {first}! It looks like you've already had a {product} sample — we "
                                 f"send one per creator per product. Happy to help you film it!")
            log("declined repeat sample")
            return {"declined": "repeat"}
        if action == "blocked_hold":
            ac.ops_ticket("lot_swap", cid, order_id=order, note=f"All {product} lots on hold; needs a clear lot")
            ac.send_message(cid, f"Hi {first}! Give me a day to get your {product} sorted — I'll be in touch.")
            log("sample blocked by hold; ops ticket")
            return {"ticket": "lot_swap"}
        # decline_below
        ac.send_message(cid, f"Hi {first}! You're just under our sample minimums for now, but you can join "
                             f"our open affiliate link and earn the open rate — ask again once you grow.")
        log("declined sample (below minimums)")
        return {"declined": "below_minimums"}

    # 3) Shipping problems -> ops tickets (routine, not an expert).
    if re.search(r"damag|broken|crushed|cracked|leak|smash", low):
        ac.ops_ticket("damaged", cid, order_id=order, note=msg)
        ac.send_message(cid, f"Hi {first}! Sorry about that — ops will follow up within one business day.")
        return {"ticket": "damaged"}
    if re.search(r"\baddress\b|\bi moved\b|\bwe moved\b|moved to|new (address|place)|wrong (house|address)", low):
        ac.ops_ticket("address_change", cid, order_id=order, note=msg)
        ac.send_message(cid, f"Hi {first}! Got it — ops will update your address.")
        log("address change ticket")
        return {"ticket": "address_change"}
    if re.search(r"arriv|never got|no sample|where.?s|tracking|lost|hasn'?t moved|not moved|still waiting|didn'?t (come|arrive)", low):
        if not order:  # resolve the creator's order if the task didn't name one
            try:
                os_ = ac.orders(cid).get("orders", [])
                order = os_[0]["order_id"] if os_ else None
            except Exception:
                order = None
        if not order:
            ac.ops_ticket("missing", cid, order_id=None, note=msg)
            ac.send_message(cid, f"Hi {first}! Let me chase that down — ops will follow up within one business day.")
            log("missing ticket (no order id)")
            return {"ticket": "missing"}
        try:
            tr = ac.tracking(order)
            status = tr.get("status")
        except Exception:
            status = None
        if status == "delivered":
            # Address-aware check (promoted from ben/delivered-not-received): only
            # say "check with neighbors" when it shipped to the address we have now.
            ship_addr = _delivery_address(ac, cid, order)
            on_file = (row.get("address_on_file") or "").strip()
            moved = bool(re.search(r"moved|new (address|place)|different address|wrong address", low))
            if moved or (ship_addr and on_file and not _same_address(ship_addr, on_file)):
                ac.ops_ticket("missing", cid, order_id=order,
                              note=f"Delivered to old address '{ship_addr}'; current on file '{on_file}'. {msg}")
                ac.send_message(cid, f"Hi {first}! It looks like it went to an old address — I've asked ops to "
                                     f"track it down and resend to your current address within one business day.")
                return {"ticket": "missing", "reason": "address_mismatch"}
            ac.send_message(cid, f"Hi {first}! Tracking shows it was delivered — could you check with "
                                 f"neighbors or your mailroom?")
            return {"told": "delivered"}
        ac.ops_ticket("missing", cid, order_id=order, note=msg)
        ac.send_message(cid, f"Hi {first}! I've asked ops to track it down; they'll follow up within one "
                             f"business day.")
        return {"ticket": "missing"}

    # 4) Otherwise it's a question/haggle: answer with correct meta.
    if msg:
        text, meta = answer(skill, row, msg, m.get("targeted_rate"))
        # Bonus haggles ("1 video for part of the bonus"): the bonus is all-or-nothing.
        if re.search(r"part of the bonus|partial|1 video|one video|fewer videos|half the", low):
            text = (f"Hi {first}! The ${m['bonus_amount']} bonus is paid once all {m['bonus_videos']} "
                    f"videos are up within {m['bonus_days']} days of delivery — it's all or nothing, but "
                    f"I can help you plan quick ones. Idea: show it in the first 3 seconds.")
            meta = {"answers": "bonus_q", "bonus_amount": m["bonus_amount"],
                    "bonus_videos": m["bonus_videos"], "bonus_days": m["bonus_days"],
                    "language": "en"}
        # Multi-day conversations ("work it to a result"): keep answering replies.
        if task.get("days"):
            res = work_thread(ac, cid, skill, row, m.get("targeted_rate"), task.get("days"), log,
                              first=(text, meta), seed_text=msg, resend_invite=False)
            return {"replied": True, **res}
        send_msg(ac, cid, text, meta)
        log("answered")
        return {"replied": True}

    log("nothing to do")
    return {}
