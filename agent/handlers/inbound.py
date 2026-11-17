"""A creator wrote to us (or replied to an invite). Escalate if it needs a
person, otherwise answer with correct meta and work the thread to a result."""
from common import creators, first_name, tier_rate
from convo import ACCEPT_RE, answer, work_thread
from escalation import holding_reply, needed_person


def run(task, ac, skill, log):
    row = creators()[task["creator_id"]]
    cid = row["creator_id"]
    msg = task.get("message") or ""
    rate = tier_rate(skill, row)

    person = needed_person(task, skill, row, msg)
    if person:
        ac.escalate(person, f"{task['brand']} creator {row['handle']}: {msg}", creator_id=cid)
        ac.send_message(cid, holding_reply(first_name(row), person))
        log(f"escalated to {person}")
        return {"escalated": person}

    # First reply, with structured meta, then advance until accept/decline/close.
    if msg:
        text, meta = answer(skill, row, msg, rate)
    else:  # a ghost: no message yet, nudge them to accept
        text, meta = answer(skill, row, "", rate)
    res = work_thread(ac, cid, skill, row, rate, task.get("days"), log, first=(text, meta),
                      seed_text=msg, resend_invite=bool(msg))
    return {"replied": True, **res}
