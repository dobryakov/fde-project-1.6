"""Who, if anyone, a case needs. Escalate only what needs a person (pod.md).

Brief-settled asks (rates, bonuses, sample rules, banned claims, no flat fee /
per-post / exclusivity) are decided in code, not escalated. Routine shipping is
an ops_ticket, not an expert. This keeps escalation precision high and stays
under the 10/day cap.

Owners (pod.md):
  marcus — client/paid terms outside limits, legal, contracts, money disputes
  priya  — shipping/lots/addresses/data, suspicious accounts or messages
  tomas  — creators over 250K, creative exceptions, collab ideas
  nora   — health/skin/pet reactions, unsettled claims, minors
"""
import re

from policy import REACTION_RE

BIG_CREATOR = 250000

_COLLAB_RE = re.compile(
    r"(custom (code|collab|concept)|my own concept|recipe series|bigger collab|"
    r"co-?create|brand ambassador|long[\s-]?term (deal|partner)|ambassador|"
    r"series .* my (idea|concept)|exclusive line|co-?brand)",
    re.I,
)
# A creator asking to change/skip a posting requirement is a creative exception
# the pod routes to Tomas, not a self-serve decline.
_CREATIVE_EXC_RE = re.compile(
    r"(skip (the )?(first 3|3 second|link|rule)|skip the first 3 seconds rule|"
    r"exception to the|waive the|bend the rule|change the (rule|format|requirement)|"
    r"can we skip|without (the )?(link|first 3)|drop the (first 3|link))",
    re.I,
)
_LEGAL_RE = re.compile(
    r"(lawyer|legal|contract|sue|lawsuit|press|the media|journalist|refund|chargeback|dispute)",
    re.I,
)
_CLAIM_UNSETTLED_RE = re.compile(
    r"(is it safe|will it cure|can i say it (cures|treats|heals)|doctor|dermatologist "
    r"recommend|medical advice)",
    re.I,
)
# Suspicious / fraudulent account or message -> Priya (ops/data/suspicious).
_PRIYA_RE = re.compile(
    r"(hacked|compromised|phishing|scam|fraud|impersonat|not really me|someone (else )?"
    r"(took over|has my)|bot took|stolen account|chargeback scam|fake account)",
    re.I,
)


def needed_person(task, skill, profile, message):
    """Return the expert this case needs, or None. profile: dict with followers.

    Order matters: safety first, then big-creator/creative, then legal.
    """
    low = (message or "").lower()
    brand = task.get("brand", "")
    # Safety / health / pet / skin reaction, or minors -> Nora.
    if REACTION_RE.search(low):
        return "nora"
    if "minor" in low or "under 18" in low or "i'm 15" in low or "i am 16" in low:
        return "nora"
    # Big creators and creative/collab exceptions -> Tomas.
    try:
        foll = int((profile or {}).get("followers", 0) or 0)
    except (TypeError, ValueError):
        foll = 0
    if _COLLAB_RE.search(low) or _CREATIVE_EXC_RE.search(low):
        return "tomas"
    if foll >= BIG_CREATOR and re.search(r"collab|concept|series|custom|partner|ambassador|bigger", low):
        return "tomas"
    # Unsettled claim question (not a banned claim we simply refuse) -> Nora.
    if _CLAIM_UNSETTLED_RE.search(low) and brand in ("fernhill-skin", "brave-paws"):
        return "nora"
    # Suspicious / fraudulent account or message -> Priya.
    if _PRIYA_RE.search(low):
        return "priya"
    # Legal / money dispute / client-approval -> Marcus.
    if _LEGAL_RE.search(low):
        return "marcus"
    return None


def holding_reply(first, person):
    who = {"marcus": "our account manager", "priya": "our ops lead",
           "tomas": "our creator team", "nora": "our care team"}.get(person, "our team")
    return (f"Hi {first}! Thanks for reaching out. I've passed this to {who} and "
            f"they'll follow up with you soon.")
