"""Sample requests and shipping problems."""
import re

from common import creators, draft, first_name, route_escalation


def run(task, ac, skill, log):
    row = creators()[task["creator_id"]]
    cid = row["creator_id"]
    m = skill["meta"]
    msg = task.get("message") or ""
    low = msg.lower()
    person = route_escalation(skill, msg, row)
    if person:
        ac.escalate(person, f"{m['brand']} creator {row['handle']}: {msg}", creator_id=cid)
        ac.send_message(cid, f"Hi {first_name(row)}! So sorry to hear that. I've passed this to my team and we'll be in touch soon.")
        log(f"escalated to {person}")
        return {"escalated": person}
    if task.get("product_requested"):
        product = task["product_requested"]
        ok = int(row["followers"]) >= m["sample_min_followers"]
        if "sample_min_views" in m:
            ok = ok and int(row["avg_views_30d"]) >= m["sample_min_views"]
        if ok:
            res = ac.ship_sample(cid, product)
            text = draft(skill, row, f"We approved their free {product} sample (order {res['order_id']}). It ships within 5 "
                         f"business days and arrives 5 to 8 days after. Give one filming idea.",
                         f"Hi {first_name(row)}! Your {product} sample is approved and ships within 5 business days.", "sample_ok")
            ac.send_message(cid, text)
            log(f"shipped {product}")
            return {"shipped": product}
        text = draft(skill, row, "They asked for a free sample but are below our minimums. Decline kindly and offer the open "
                     "affiliate link.", f"Hi {first_name(row)}! We can't send a sample yet, but you can join our open affiliate link.",
                     "sample_no")
        ac.send_message(cid, text)
        log("declined sample")
        return {"declined": True}
    order = task.get("order_id")
    if re.search(r"damag|broken|crushed|cracked|leak", low):
        ac.ops_ticket("damaged", cid, order_id=order, note=msg)
        ac.send_message(cid, f"Hi {first_name(row)}! Sorry about that. Ops will follow up within one business day.")
        return {"ticket": "damaged"}
    if re.search(r"address|moved", low):
        ac.ops_ticket("address_change", cid, order_id=order, note=msg)
        ac.send_message(cid, f"Hi {first_name(row)}! Got it, ops will update your address.")
        return {"ticket": "address_change"}
    if re.search(r"arriv|never got|no sample|where|tracking|lost|hasn't moved|ship", low) and order:
        tr = ac.tracking(order)
        if tr["status"] == "delivered":
            ac.send_message(cid, f"Hi {first_name(row)}! Tracking shows it was delivered. Could you check with neighbors?")
            return {"told": "delivered"}
        ac.ops_ticket("missing", cid, order_id=order, note=msg)
        ac.send_message(cid, f"Hi {first_name(row)}! I've asked ops to track it down. They'll follow up within one business day.")
        return {"ticket": "missing"}
    if msg:
        text = draft(skill, row, f"The creator wrote: \"{msg}\". Reply helpfully.", f"Hi {first_name(row)}! Thanks for the note.", "sample_other")
        ac.send_message(cid, text)
        return {"replied": True}
    log("nothing to do")
    return {}
