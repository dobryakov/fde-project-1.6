"""Conversation logic: classify a creator's reply, answer with structured meta,
and work a thread across the clock until it reaches a result.

Judgment about *what* to say (voice, filming ideas) can come from skills/LLM, but
the *facts* in `meta` are decided here from the brief so the sim judges us on
correct, consistent fields. Stance is `decline` on fee / exclusivity / claim /
competitor asks — those are brief-settled, never accepted.
"""
import re

import llm
from affiliate_center import SimError
from common import first_name, tier_rate

FEE_RE = re.compile(r"(flat fee|flat rate|upfront|up front|per video|per post|a post|signing (fee|bonus)|pay me|retainer|appearance fee|fijo|tarifa plana|d[oó]lares fijos|por adelantado|honorario)", re.I)
EXCL_RE = re.compile(r"(exclusiv|go exclusive|only your brand|stop posting other|lock me in|exclusividad)", re.I)
SWEET_RE = re.compile(r"(throw in|throw it in|toss in|add (the|a|an|some)|include (the|a|an|another)|extra (sample|product|bag|can|tub)|a second (sample|product)|both products|freebie)", re.I)
COMP_RE = re.compile(r"(crunchwell|popsmith|bluestem|another brand|other brand|competitor|gave me \d+%|offering me \d+%|pays \d+%|beat (that|them|it))", re.I)
CLAIM_RE = re.compile(r"(can i say|allowed to say|claim|cure|treat|heal|detox|clinically|dermatologist|non-?toxic|clean air|burns clean|smells clean)", re.I)
RATE_RE = re.compile(r"(commission|rate|percent|%|cut|how much|too low|bump|raise|more than|match)", re.I)
BONUS_RE = re.compile(r"(bonus|\$\d+|how do i (earn|get) the)", re.I)
SAMPLE_RE = re.compile(r"(sample|ship|send (me )?the|try it|free product)", re.I)
DECLINE_RE = re.compile(r"(no thanks|not a fit|not interested|pass\b|i'?ll pass|booked|don'?t think|maybe later|not right now)", re.I)
ACCEPT_RE = re.compile(r"(i'?m in|sounds good|let'?s do it|where do i (accept|sign)|send the invite|i accept|count me in)", re.I)


def send_msg(ac, cid, text, meta=None):
    try:
        return ac.send_message(cid, text, meta=meta) if meta else ac.send_message(cid, text)
    except TypeError:
        return ac.send_message(cid, text)


def send_inv(ac, cid, rate, text, meta=None):
    try:
        return ac.send_invite(cid, rate, text, meta=meta) if meta else ac.send_invite(cid, rate, text)
    except TypeError:
        return ac.send_invite(cid, rate, text)


def render(text_en, lang):
    """Write `text_en` in the creator's language. English or a bad render -> unchanged."""
    if not lang or lang == "en":
        return text_en, "en"
    nums = re.findall(r"\d+", text_en)
    out = llm.complete(
        text_en,
        system=(f"Translate the message into language code '{lang}', keeping it natural and warm. "
                f"Keep every number, percent and dollar amount exactly. Do not add any claims. "
                f"Output only the translation, no notes."),
        tag="translate",
    )
    out = (out or "").strip()
    if out and all(n in out for n in nums):
        return out, lang
    return text_en, "en"  # model off or dropped a number: stay in English, honestly


def answer(skill, profile, text, rate, idea=None):
    """Return (reply_text, meta). Never names a competitor; declines fee/excl/claim.

    The reply is rendered in the creator's language when we can; meta.language
    always matches the language actually written.
    """
    m = skill["meta"]
    first = first_name(profile)
    low = (text or "").lower()
    idea = idea or "show the product in the first 3 seconds"
    lang = profile.get("language", "en") or "en"
    base_meta = {"language": "en"}

    if FEE_RE.search(low):
        meta = {**base_meta, "answers": "flat_fee", "stance": "decline", "rate": rate}
        txt = (f"Hi {first}! We don't do flat fees or signing fees — it's {rate}% commission on "
               f"every sale, plus the ${m['bonus_amount']} posting bonus. Happy to get you set up.")
    elif EXCL_RE.search(low):
        meta = {**base_meta, "answers": "exclusive", "stance": "decline", "rate": rate}
        txt = (f"Hi {first}! No exclusivity on our side — you can post any other brand you like. "
               f"Your commission stays {rate}%.")
    elif COMP_RE.search(low) and RATE_RE.search(low):
        meta = {**base_meta, "answers": "rate_q+competitor", "stance": "decline", "rate": rate}
        txt = (f"Hi {first}! I can't match other offers, but {rate}% commission plus the "
               f"${m['bonus_amount']} bonus for {m['bonus_videos']} videos is a strong deal. Idea: {idea}.")
    elif SWEET_RE.search(low):
        # Tidewater feedback: no sweetener/second product on a haggle; hold the rate, offer an idea.
        meta = {**base_meta, "answers": "rate_q", "stance": "decline", "rate": rate}
        txt = (f"Hi {first}! I can't add an extra product, but {rate}% commission plus the "
               f"${m['bonus_amount']} bonus is a strong deal — and here's a filming idea: {idea}.")
    elif CLAIM_RE.search(low):
        meta = {**base_meta, "answers": "claim_q", "stance": "decline", "claims": []}
        txt = (f"Hi {first}! We have to keep claims off the table — please stick to how it looks, "
               f"feels and fits your routine. Idea: {idea}.")
    elif BONUS_RE.search(low) and not RATE_RE.search(low):
        meta = {**base_meta, "answers": "bonus_q", "bonus_amount": m["bonus_amount"],
                "bonus_videos": m["bonus_videos"], "bonus_days": m["bonus_days"]}
        txt = (f"Hi {first}! The bonus is ${m['bonus_amount']} once you post {m['bonus_videos']} "
               f"videos within {m['bonus_days']} days of delivery. Idea: {idea}.")
    elif SAMPLE_RE.search(low):
        meta = {**base_meta, "answers": "sample_q", "rate": rate}
        txt = (f"Hi {first}! Once you accept the invite we'll ship a free sample so you can film it. "
               f"Your commission is {rate}%.")
    else:  # Default: a rate question / general nudge, hold the brief rate.
        meta = {**base_meta, "answers": "rate_q", "rate": rate}
        txt = (f"Hi {first}! Your commission is {rate}% on every sale, plus a ${m['bonus_amount']} bonus "
               f"for {m['bonus_videos']} videos within {m['bonus_days']} days of delivery. "
               f"Accept the invite whenever you're ready — idea: {idea}.")
    txt, used_lang = render(txt, lang)
    meta["language"] = used_lang
    return txt, meta


def work_thread(ac, cid, skill, profile, rate, days, log, first=None):
    """Send `first` (text, meta) if given, then advance/inbox until a result.

    Returns dict: {outcome: accepted|declined|open, replies: n}.
    """
    if first:
        send_msg(ac, cid, first[0], first[1])
    accepted = declined = False
    replies = 0
    steps = max(4, int((days or 2) * 24 / 12))
    for _ in range(steps):
        try:
            ac.advance(12)
        except SimError:
            break
        try:
            items = ac.inbox().get("items", [])
        except SimError:
            break
        for item in items:
            if item.get("creator_id") != cid:
                continue
            kind = item.get("kind", "")
            if kind == "invite_accepted":
                accepted = True
                continue
            if kind == "invite_declined":
                declined = True
                continue
            txt = item.get("text", "")
            replies += 1
            if DECLINE_RE.search(txt.lower()):
                declined = True
                continue
            reply, meta = answer(skill, profile, txt, rate)
            try:
                send_msg(ac, cid, reply, meta)
            except SimError as e:
                if e.code in ("campaign_closed", "budget_exhausted", "rate_limited"):
                    break
        if accepted or declined:
            break
    outcome = "accepted" if accepted else "declined" if declined else "open"
    log(f"thread {outcome} after {replies} repl{'y' if replies == 1 else 'ies'}")
    return {"outcome": outcome, "replies": replies}
