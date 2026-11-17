"""Hard policy gates. Code owns these decisions, never the LLM.

These are the checks that keep the agent from the violations the dashboard
punishes: contacting an opt-out or a minor, shipping a held lot or a paused
product or a repeat sample, and paying a bonus that is not owed. Every number
comes from the brand brief at run time (via `skill["meta"]`, which `skills.load`
overrides from `brands/`); nothing here hard-codes a rate or a window.
"""
import csv
import datetime as dt
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
_PM = None

# Stop-language a creator uses to opt out, beyond the do_not_contact flag.
STOP_RE = re.compile(
    r"(please stop|stop messaging|stop contacting|unsubscribe|don'?t contact|"
    r"do not contact|remove me|take me off|opt[\s-]?out|no more messages|leave me alone)",
    re.I,
)
REACTION_RE = re.compile(
    r"(vomit|threw up|throw up|throwing up|got sick|made (her|him|them|my dog) sick|"
    r"rash|itch|itchy|scratching|reaction|break[\s-]?out|breaking out|hives|swollen|"
    r"swelling|allerg|upset (tummy|stomach)|diarrh|hives|seemed off|"
    r"acting weird|not herself|not himself)",
    re.I,
)


def _past_messages():
    global _PM
    if _PM is None:
        path = os.path.join(ROOT, "data", "past-messages.csv")
        with open(path, encoding="utf-8") as f:
            _PM = list(csv.DictReader(f))
    return _PM


def optout_history():
    """creator_ids who asked us to stop, learned from data/past-messages.csv.

    This is the 'read the data before acting' gate: a creator who said stop in a
    past thread must not be invited again, even if their flag is not set.
    """
    ids = set()
    for r in _past_messages():
        reply = r.get("creator_reply") or ""
        if r.get("outcome") == "asked_to_stop" or STOP_RE.search(reply):
            ids.add(r.get("creator_id"))
    return ids


def _dnc_flag(row):
    v = row.get("do_not_contact")
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("yes", "true", "1")


def is_opted_out(row):
    return _dnc_flag(row) or row.get("creator_id") in optout_history()


def is_minor(row):
    return str(row.get("age_flag", "")).strip().lower() == "under_18"


def can_contact(row):
    """(ok, reason). reason is 'opted_out' or 'minor' when blocked."""
    if is_opted_out(row):
        return False, "opted_out"
    if is_minor(row):
        return False, "minor"
    return True, None


# ---------------------------------------------------------------- samples ----

def _text(n):
    return (n.get("title", "") + " " + n.get("body", ""))


def held_lots(notices):
    lots = set()
    for n in notices:
        t = _text(n)
        if re.search(r"hold", t, re.I):
            lots |= set(re.findall(r"(L-\d+)", t))
    return lots


_COUNTRY_WORDS = {"CA": ("canada", "canadian"), "US": ("united states", "u.s.", " us ", "american")}


def shipping_paused(notices, product, country):
    for n in notices:
        t = _text(n).lower()
        if "pause" in t and product and product.lower() in t:
            words = _COUNTRY_WORDS.get((country or "").upper(), ())
            if not words or any(w.strip() in t for w in words):
                return True
    return False


def pick_shippable_lot(ac, product, notices):
    """Oldest lot that is not on hold, or None if every lot is held."""
    held = held_lots(notices)
    stock = ac.stock().get("stock", {})
    for lot in stock.get(product, []):  # oldest first
        if lot not in held:
            return lot
    return None


def already_sampled(ac, cid, product):
    try:
        orders = ac.orders(cid).get("orders", [])
    except Exception:
        return False
    return any(o.get("product") == product for o in orders)


def sample_decision(ac, skill, row, product, notices):
    """Decide whether/how to ship a sample. Returns (action, lot, reason).

    action: 'ship' | 'decline_below' | 'decline_repeat' | 'delay_shipping' |
            'blocked_hold'
    """
    m = skill["meta"]
    country = row.get("country")
    foll = int(row.get("followers", 0) or 0)
    views = int(row.get("avg_views_30d", 0) or 0)
    min_f = int(m.get("sample_min_followers", 0) or 0)
    min_v = int(m.get("sample_min_views", 0) or 0)
    if foll < min_f or (min_v and views < min_v):
        return "decline_below", None, "below sample minimums"
    if already_sampled(ac, row["creator_id"], product):
        return "decline_repeat", None, "already sampled this product"
    if shipping_paused(notices, product, country):
        return "delay_shipping", None, "shipping paused for this product/country"
    lot = pick_shippable_lot(ac, product, notices)
    if lot is None:
        return "blocked_hold", None, "all lots on hold"
    return "ship", lot, "ok"


# ------------------------------------------------------------------ bonus ----

def _parse_dt(s):
    if not s:
        return None
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(s, fmt)
        except ValueError:
            continue
    return None


def deadline_date(order, bonus_days):
    """Bonus deadline as a calendar date string, e.g. 'Fri 20 Nov' (Fernhill rule)."""
    d = _parse_dt(order.get("delivered_at"))
    if not d or not bonus_days:
        return None
    return (d + dt.timedelta(days=int(bonus_days))).strftime("%a %-d %b")


def gather_posts(ac, cid, task_handle):
    """All posts across the creator's current and prior handles (new-handle lookup)."""
    handles = []
    try:
        prof = ac.creator(cid)
        handles.append(prof.get("handle"))
        handles += prof.get("prior_handles", []) or []
    except Exception:
        prof = None
    if task_handle:
        handles.append(task_handle)
    seen, posts = set(), []
    for h in handles:
        if not h:
            continue
        try:
            for p in ac.posts(h).get("posts", []):
                vid = p.get("video_id")
                if vid not in seen:
                    seen.add(vid)
                    posts.append(p)
        except Exception:
            continue
    return posts, prof


def valid_videos(posts, skill, order, brand):
    """Posts that count toward the bonus, deduped and checked against the brief."""
    m = skill["meta"]
    delivered = _parse_dt(order.get("delivered_at")) if order else None
    days = int(m.get("bonus_days", 0) or 0)
    seen, valid, issues = set(), [], set()
    for p in posts:
        base = p.get("same_video_as") or p.get("video_id")
        if base in seen:
            continue
        if not p.get("product_in_first_3s", False):
            issues.add("product not in first 3 seconds")
            continue
        if not p.get("shop_link_tagged", False):
            issues.add("shop link not tagged")
            continue
        if brand == "lumen-home" and not p.get("lit_candle_attended", True):
            issues.add("lit candle unattended")
            continue
        pa = _parse_dt(p.get("posted_at"))
        if delivered and pa and (pa - delivered).days > days:
            issues.add("posted after the window")
            continue
        if delivered and pa and pa < delivered:
            continue
        seen.add(base)
        valid.append(p)
    return valid, issues


def bonus_owed(ac, skill, cid, task_handle, order):
    """(owed, valid_count, need, issues, posts). owed only when enough valid videos."""
    m = skill["meta"]
    need = int(m.get("bonus_videos", 0) or 0)
    posts, _ = gather_posts(ac, cid, task_handle)
    valid, issues = valid_videos(posts, skill, order, m.get("skill") or m.get("brand", ""))
    return (len(valid) >= need and need > 0), len(valid), need, issues, posts
