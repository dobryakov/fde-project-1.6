"""The five post-round-1 brand feedback rules are written into skills/ so the agent reads
them. Covers AC-19. (Behavioral correctness is AC-20, LLM.) Also AC-21 Fernhill v4 swap."""
import glob
import os

from _util import ROOT, bad, ok, p, read


def _skills_blob():
    blob = ""
    sd = p("skills")
    if os.path.isdir(sd):
        for fn in sorted(os.listdir(sd)):
            if fn.endswith(".md"):
                blob += "\n" + read("skills", fn).lower()
    return blob


def run(root=ROOT):
    res = []
    blob = _skills_blob()

    rules = {
        "KandC-no-competitor": ["competitor"],
        "Tidewater-no-sweetener": ["sweeten", "second sample", "one sample", "filming idea"],
        "BravePaws-reaction-to-Nora": ["nora"],
        "Fernhill-calendar-date": ["calendar date", "by fri", "deadline as", "calendar"],
        "Lumen-banned-words": ["burns clean", "chemical free", "all natural", "clean air"],
    }
    missing = []
    for name, toks in rules.items():
        if not any(t in blob for t in toks):
            missing.append(name)
    if missing:
        res.append(bad("AC-19", f"feedback rules not found in skills/: {missing}"))
    else:
        res.append(ok("AC-19", "all five post-round-1 feedback rules present in skills/"))

    # AC-21 Fernhill v4 swap: the v3 brief (window = 12 days) saved as a copy OUTSIDE
    # brands/ before v4 is copied over. A real backup is a copy of the brief, so we require
    # the v3 window marker in the file, not just the brand name (skills/brand files differ).
    fern = read("brands", "fernhill-skin.md").lower()
    is_v4 = ("v4" in fern and "10 days" in fern) or "within 10 days of delivery" in fern
    backups = []
    for f in glob.glob(os.path.join(ROOT, "**", "*.md"), recursive=True):
        rp = os.path.relpath(f, ROOT)
        top = rp.split(os.sep)[0]
        if top in ("brands", "feedback", "skills", "gops-local-skills", "acceptance"):
            continue
        try:
            with open(f, encoding="utf-8", errors="replace") as fh:
                txt = fh.read().lower()
        except Exception:
            continue
        if "fernhill" in txt and "within 12 days of delivery" in txt:
            backups.append(rp)
    if backups:
        res.append(ok("AC-21", f"v3 Fernhill backup saved outside brands/: {backups[:3]}"
                      + ("; brands/ is v4" if is_v4 else "")))
    else:
        res.append(bad("AC-21", "no v3 Fernhill brief backup saved outside brands/ (round-2 swap step)"))

    return res
