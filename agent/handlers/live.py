"""Live campaigns: check posts, pay the bonus when it is owed, nudge creators who have not posted."""
from common import creators, draft, first_name, route_escalation


def run(task, ac, skill, log):
    row = creators()[task["creator_id"]]
    cid = row["creator_id"]
    m = skill["meta"]
    msg = task.get("message")
    if msg:
        person = route_escalation(skill, msg, row)
        if person:
            ac.escalate(person, f"{m['brand']} creator {row['handle']}: {msg}", creator_id=cid)
            ac.send_message(cid, f"Hi {first_name(row)}! Thanks for telling us. I've passed this to my team.")
            return {"escalated": person}
        text = draft(skill, row, f"The creator wrote: \"{msg}\". Reply helpfully.", f"Hi {first_name(row)}! Thanks for the note.", "live_reply")
        ac.send_message(cid, text)
        return {"replied": True}
    posts = ac.posts(task["handle"])["posts"]
    if len(posts) >= m["bonus_videos"]:
        ac.pay_bonus(cid, note=f"{len(posts)} videos")
        ac.send_message(cid, f"Hi {first_name(row)}! Thanks for the videos. Your ${m['bonus_amount']} bonus is on its way.")
        log("paid bonus")
        return {"paid": True}
    situation = (f"They have posted {len(posts)} of {m['bonus_videos']} videos. Nudge them to post: remind them of the "
                 f"${m['bonus_amount']} bonus for {m['bonus_videos']} videos within {m['bonus_days']} days of delivery, "
                 f"and give one filming idea.")
    fallback = (f"Hi {first_name(row)}! Hope you're enjoying the {m['hero']}. Post {m['bonus_videos']} videos within "
                f"{m['bonus_days']} days of delivery to earn the ${m['bonus_amount']} bonus. Idea: show it in the first 3 seconds.")
    ac.send_message(cid, draft(skill, row, situation, fallback, "nudge"))
    log("nudged")
    return {"nudged": True}
