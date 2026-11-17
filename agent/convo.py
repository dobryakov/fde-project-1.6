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


_TRANS_CACHE = {}
COMPETITORS = ("crunchwell", "popsmith", "bluestem", "bluestem brew")


def compose(skill, profile, incoming, meta, fallback, lang, tag="negotiate"):
    """Write the reply wording with the model, around facts/rules fixed in code.

    The model gets the brand voice, the exact numbers, the hard do-nots and the
    allowed safe wording, and writes a short persuasive reply in the creator's
    language. We then validate it kept every number from the deterministic
    fallback, named no banned claim or competitor, and is non-empty — otherwise we
    use the fallback template. `meta` (the scored facts) is never touched here.
    """
    m = skill["meta"]
    first = first_name(profile)
    need_nums = re.findall(r"\d+", fallback)  # the facts the reply must preserve
    facts = []
    if meta.get("rate") is not None:
        facts.append(f"the commission is exactly {meta['rate']}% — never offer more")
    facts.append(f"the posting bonus is exactly ${m['bonus_amount']} for {m['bonus_videos']} "
                 f"videos within {m['bonus_days']} days of delivery")
    donots = ["never offer a flat fee, pay-per-post, or any upfront/signing fee",
              "never offer exclusivity", "never add a second product, extra sample or sweetener",
              "never name another brand / a competitor",
              f"make no product claims (never use: {', '.join(m.get('banned', []))})"]
    allowed = m.get("allowed") or []
    system = (f"You write one short reply (2-4 sentences) from Brightline, a TikTok Shop affiliate "
              f"agency, to a {m['brand']} creator named {first}. Warm, plain, no hype; use their name; "
              f"at most one concrete filming idea. Write in language code '{lang}'. "
              f"Facts you must keep exact: {'; '.join(facts)}. "
              f"Hard rules: {'; '.join(donots)}. "
              + (f"If they want to make a claim, say they can instead say: {', '.join(allowed)}. " if allowed else "")
              + ("You are declining their special ask — be kind but firm and do not grant it. "
                 if meta.get("stance") == "decline" else "")
              + "Answer their question directly first, then invite them to accept/post. Output only the message.")
    out = llm.complete(f'The creator said: "{incoming}". Write the reply.', system=system, tag=tag)
    out = (out or "").strip()
    low = out.lower()
    # Wrong numbers are a policy violation, so the draft may contain NO commission
    # percentage other than our rate, and NO dollar amount other than the bonus.
    pcts = [int(p) for p in re.findall(r"(\d+)\s*%", out)]
    dols = [int(d) for d in re.findall(r"\$\s*(\d+)", out)]
    rate = meta.get("rate")
    wrong_number = (rate is not None and any(p != int(rate) for p in pcts)) or \
                   any(d != int(m["bonus_amount"]) for d in dols)
    bad = (not out
           or any(n not in out for n in need_nums)
           or wrong_number
           or any((b or "").lower() in low for b in m.get("banned", []))
           or any(c in low for c in COMPETITORS))
    if bad:
        return render(fallback, lang)  # model off/unsafe: safe deterministic template
    return out, lang


def render(text_en, lang, must_keep=()):
    """Write `text_en` in the creator's language. English or a bad render -> unchanged.

    Cached by (text, lang) so a shared template (a bulk invite body) is translated
    once per language — that keeps outreach within LLM_MAX_CALLS. `must_keep`
    tokens (e.g. a name placeholder) and every number must survive the render, or
    we fall back to English honestly.
    """
    if not lang or lang == "en":
        return text_en, "en"
    key = (text_en, lang)
    if key in _TRANS_CACHE:
        return _TRANS_CACHE[key]
    nums = re.findall(r"\d+", text_en)
    out = llm.complete(
        text_en,
        system=(f"Translate the message into language code '{lang}', keeping it natural and warm. "
                f"Keep every number, percent and dollar amount exactly, and keep any ALLCAPS "
                f"placeholder token unchanged. Do not add any claims. Output only the translation."),
        tag="translate",
    )
    out = (out or "").strip()
    ok = bool(out) and all(n in out for n in nums) and all(tok in out for tok in must_keep)
    result = (out, lang) if ok else (text_en, "en")
    _TRANS_CACHE[key] = result
    return result


def answer(skill, profile, text, rate, idea=None, use_llm=True):
    """Return (reply_text, meta). The classification and `meta` facts are decided in
    code (never the model); the wording is drafted by the model under those
    constraints when `use_llm` (default), with the deterministic template as the
    safe fallback. meta.language always matches the language actually written.
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
        allowed = ", ".join(m.get("allowed") or [])
        safe = allowed or m.get("safe_wording") or "how it looks, feels and fits your routine"
        txt = (f"Hi {first}! We can't make that kind of claim, so please avoid it — but you're welcome "
               f"to say things like {safe}. Idea: {idea}.")
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
    if use_llm:
        txt, used_lang = compose(skill, profile, text, meta, fallback=txt, lang=lang)
    else:
        txt, used_lang = render(txt, lang)
    meta["language"] = used_lang
    return txt, meta


def _norm_msg(t):
    return re.sub(r"\s+", " ", (t or "").strip().lower())


def work_thread(ac, cid, skill, profile, rate, days, log, first=None,
                seed_text=None, reply_fn=None, resend_invite=False, invite_idea=None,
                persist_close=True):
    """Send `first` (text, meta) if given, then advance/inbox and keep answering
    every *new* creator message until the conversation reaches a result or the
    window closes. A creator conversation is "won" by staying with the thread:
    answering each objection the creator actually raises, not firing one message
    and forgetting it.

    - `seed_text`: the creator message the handler already answered (the task
      message). It is pre-marked seen so the loop never re-answers it when the sim
      replays it in the first inbox read (that caused a pushy duplicate).
    - `reply_fn(txt) -> (text, meta) | None`: how to answer a follow-up. Default is
      the brief-settled `answer()`. A None return means "nothing new to say" (skip,
      don't repeat ourselves).
    - `resend_invite`: after the first substantive answer, (re)send the open invite
      once at the brief `rate` so a haggling creator has a clear path to accept.

    Returns dict: {outcome: accepted|declined|open, replies: n}.
    """
    m = skill["meta"]
    fname = first_name(profile)
    idea = invite_idea or "show the product in the first 3 seconds"
    if reply_fn is None:
        def reply_fn(txt):
            return answer(skill, profile, txt, rate)
    seen = set()
    if seed_text:
        seen.add(_norm_msg(seed_text))
    last_sent = None
    sent_texts = set()
    if first:
        send_msg(ac, cid, first[0], first[1])
        last_sent = first[0]
        sent_texts.add(_norm_msg(first[0]))
    invite_resent = False
    accepted = declined = False
    replies = 0
    steps = max(6, int((days or 2) * 24 / 12))
    for step in range(steps):
        # Re-send the open invite once, after the creator has had the first answer,
        # so a haggler can accept at the brief rate (never a sweetened one).
        if resend_invite and not invite_resent and step == 1 and not (accepted or declined):
            inv_txt = (f"Hi {fname}! I've got your invite ready at {rate}% commission plus the "
                       f"${m['bonus_amount']} bonus for {m['bonus_videos']} videos within "
                       f"{m['bonus_days']} days — tap accept whenever you're set and we'll ship your "
                       f"sample. Idea: {idea}.")
            if _norm_msg(inv_txt) not in sent_texts:
                try:
                    send_inv(ac, cid, rate, inv_txt,
                             {"language": "en", "answers": "rate_q", "rate": rate})
                    last_sent = inv_txt
                    sent_texts.add(_norm_msg(inv_txt))
                except SimError:
                    pass
            invite_resent = True
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
            norm = _norm_msg(txt)
            if norm in seen:
                continue  # already handled (incl. the replayed seed message)
            seen.add(norm)
            replies += 1
            if DECLINE_RE.search(txt.lower()):
                declined = True
                continue
            out = reply_fn(txt)
            if not out:
                continue  # nothing new to add; don't repeat ourselves
            reply, meta = out
            if _norm_msg(reply) in sent_texts:
                # We'd repeat ourselves. On the negotiation path a warm close that
                # asks for the accept (holding the rate, no sweetener) is what
                # converts a creator who re-asks the same question — so send that
                # once instead of going silent. If even the close was already sent,
                # stay quiet (pushing a third identical nudge loses the creator).
                if not persist_close:
                    continue
                close = (f"Hi {fname}! {rate}% plus the ${m['bonus_amount']} bonus for "
                         f"{m['bonus_videos']} videos within {m['bonus_days']} days is a strong deal — "
                         f"no extra products, but I'd love to get you started. Want me to send your invite?")
                if _norm_msg(close) in sent_texts:
                    continue
                reply = close
                meta = {"language": "en", "answers": "rate_q", "rate": rate, "stance": "decline"}
            try:
                send_msg(ac, cid, reply, meta)
                last_sent = reply
                sent_texts.add(_norm_msg(reply))
            except SimError as e:
                if e.code in ("campaign_closed", "budget_exhausted", "rate_limited"):
                    break
        if accepted or declined:
            break
    outcome = "accepted" if accepted else "declined" if declined else "open"
    log(f"thread {outcome} after {replies} repl{'y' if replies == 1 else 'ies'}")
    return {"outcome": outcome, "replies": replies}
