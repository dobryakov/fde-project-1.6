"""Brand numbers must be read from brands/ (or skills/) at run time, not hard-coded into
agent code. We flag rate/bonus/threshold literals bound to rate/bonus/commission context
inside agent/*.py, and confirm a brand/skill file is loaded at run time. Covers AC-6."""
import os
import re

from _util import ROOT, agent_sources, bad, ok, read

# Numeric literals tied to money/rate/bonus context are the real risk. Generic loop
# counts like range(40) are not brand numbers, so we only flag numbers that sit next to a
# rate/bonus/commission/percent/$ cue.
CONTEXT = re.compile(
    r'(?:rate|commission|bonus|percent|%|\$|targeted|open_rate|bonus_amount|'
    r'bonus_videos|bonus_days|min_followers|min_views)',
    re.I,
)
# a number literal, optionally a percent/dollar form, on the same line as a money cue
LINE_NUM = re.compile(r'(?<![\w.])(\d{2,6})(?![\w.])')
# quoted string literals (docstring examples, format strings, prose) are not hard-coded
# brand constants; a real hard-coded rate/bonus is a bare numeric literal (bonus = 50),
# not a number inside quotes ('Fri 20 Nov'). Strip quoted spans before scanning numbers.
QUOTED = re.compile(r'"""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\'|"[^"]*"|\'[^\']*\'')


def _strip_quoted(s):
    return QUOTED.sub("", s)


def run(root=ROOT):
    res = []
    offenders = []
    for fp in agent_sources():
        with open(fp, encoding="utf-8", errors="replace") as f:
            for i, line in enumerate(f, 1):
                s = line.strip()
                if s.startswith("#"):
                    continue
                # drop inline comment and quoted-string spans before scanning for numbers
                code = _strip_quoted(s.split("#", 1)[0])
                if CONTEXT.search(code) and LINE_NUM.search(code):
                    s = code
                    # ignore obvious non-brand numbers
                    nums = [int(n) for n in LINE_NUM.findall(s)]
                    brandish = [n for n in nums if n in BRAND_NUMBERS]
                    if brandish:
                        offenders.append(f"{os.path.relpath(fp, ROOT)}:{i}: {s[:80]} -> {brandish}")

    runtime_load = False
    for fp in agent_sources() + [os.path.join(ROOT, "agent", "skills.py")]:
        txt = read_abs(fp)
        if re.search(r'(brands|skills)[/\\"\']', txt) and ("open(" in txt or "read" in txt or "parse(" in txt or "load(" in txt):
            runtime_load = True
            break

    if offenders:
        res.append(bad("AC-6", "brand numbers hard-coded in agent/: " + " | ".join(offenders[:6])))
    elif not runtime_load:
        res.append(bad("AC-6", "no brand/skill file loaded at run time by the agent"))
    else:
        res.append(ok("AC-6", "no hard-coded brand rate/bonus numbers in agent/; briefs/skills loaded at run time"))
    return res


def read_abs(fp):
    if not os.path.exists(fp):
        return ""
    with open(fp, encoding="utf-8", errors="replace") as f:
        return f.read()


# rates, bonus amounts, bonus video/day counts, follower & view thresholds from the five briefs
BRAND_NUMBERS = {
    12, 18, 17, 15, 20, 10, 16,            # commission rates
    50, 45, 40, 60, 70,                    # bonus amounts
    14, 21,                                 # bonus windows (days) that are brandish
    10000, 7000, 8000, 6000, 9000,          # targeted view thresholds
    3000, 1500, 2000, 1000, 2500, 5000,     # sample follower/view minimums
}
