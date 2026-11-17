"""Agent sends structured meta with send_message / send_invite. Covers AC-10."""
import re

from _util import ROOT, agent_sources, bad, ok


def run(root=ROOT):
    res = []
    found = []
    for fp in agent_sources():
        with open(fp, encoding="utf-8", errors="replace") as f:
            txt = f.read()
        # look for a meta= keyword argument on any send call
        for m in re.finditer(r'send_(?:invite|message)\s*\(', txt):
            tail = txt[m.start():m.start() + 400]
            if "meta" in tail:
                found.append(fp)
                break
        else:
            if re.search(r'\bmeta\s*=', txt) and "send_" in txt:
                found.append(fp)
    if found:
        res.append(ok("AC-10", f"meta= passed to send_* in {len(set(found))} file(s)"))
    else:
        res.append(bad("AC-10", "no meta= argument passed to send_invite/send_message in agent/"))
    return res
