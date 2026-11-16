"""A creator wrote to us about an outreach brand. Escalate if the rules say so, else reply."""
from common import creators, draft, first_name, route_escalation, tier_rate


def run(task, ac, skill, log):
    row = creators()[task["creator_id"]]
    msg = task.get("message") or ""
    person = route_escalation(skill, msg, row)
    if person:
        ac.escalate(person, f"{task['brand']} creator {row['handle']} wrote: {msg}", creator_id=row["creator_id"])
        ac.send_message(row["creator_id"], f"Hi {first_name(row)}! Thanks for the note. I'm checking with my team and will get back to you.")
        log(f"escalated to {person}")
        return {"escalated": person}
    rate = tier_rate(skill, row)
    m = skill["meta"]
    situation = (f"The creator wrote: \"{msg}\"\nTheir commission rate is {rate}%. Answer their question and ask them to "
                 f"accept the invite.")
    fallback = (f"Hi {first_name(row)}! Your commission is {rate}% and there's a ${m['bonus_amount']} bonus for "
                f"{m['bonus_videos']} videos within {m['bonus_days']} days of delivery. Accept the invite whenever you're ready.")
    text = draft(skill, row, situation, fallback, tag="inbound")
    ac.send_message(row["creator_id"], text)
    log("replied")
    return {"replied": True}
