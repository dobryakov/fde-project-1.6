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
    meta, body = parse(os.path.join(SKILLS, brand + ".md"))
    shared_meta, shared_body = parse(os.path.join(SKILLS, "_shared.md"))
    meta["products"] = [p.strip() for p in str(meta.get("products", "")).split(";") if p.strip()]
    meta["banned"] = [p.strip() for p in str(meta.get("banned", "")).split(",") if p.strip()]
    return {"meta": meta, "body": body, "shared": shared_meta, "shared_body": shared_body}
