"""Load skill files: a front matter block of `key: value` lines, then free text."""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS = os.path.join(HERE, "..", "skills")


def parse(path):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    meta, body = {}, text
    if text.startswith("---"):
        _, fm, body = text.split("---", 2)
        for line in fm.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
    for k, v in list(meta.items()):
        if v.isdigit():
            meta[k] = int(v)
    return meta, body.strip()


def load(brand):
    import brief  # local import to avoid cycles
    meta, body = parse(os.path.join(SKILLS, brand + ".md"))
    shared_meta, shared_body = parse(os.path.join(SKILLS, "_shared.md"))
    meta["products"] = [p.strip() for p in str(meta.get("products", "")).split(";") if p.strip()]
    meta["banned"] = [p.strip() for p in str(meta.get("banned", "")).split(",") if p.strip()]
    # The brand brief in brands/ is the source of truth for every number. Read it
    # at run time and let it override the (possibly stale) skill front matter.
    brief_vals = brief.parse_brief(brand)
    meta.update(brief_vals)
    return {"meta": meta, "body": body, "shared": shared_meta, "shared_body": shared_body}
