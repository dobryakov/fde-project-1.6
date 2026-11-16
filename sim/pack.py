"""Read and write the sim's data packs. You should not need this file.

A pack holds the simulated platform: creator records as the platform sees them,
how creators behave, and the campaign setup. It is compressed so the sim loads fast.
"""
import base64
import hashlib
import json
import zlib

MAGIC = b"BLPK1\n"
_KEY = b"brightline/affiliate-center/v2"


def _mask(data):
    n = len(data)
    blocks = []
    i = 0
    while 32 * len(blocks) < n:
        blocks.append(hashlib.sha256(_KEY + i.to_bytes(4, "big")).digest())
        i += 1
    ks = b"".join(blocks)[:n]
    return (int.from_bytes(data, "big") ^ int.from_bytes(ks, "big")).to_bytes(n, "big")


def dump(obj, path):
    raw = zlib.compress(json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8"), 9)
    with open(path, "wb") as f:
        f.write(MAGIC + base64.b64encode(_mask(raw)))


def load(path):
    with open(path, "rb") as f:
        blob = f.read()
    if not blob.startswith(MAGIC):
        raise ValueError(f"{path} is not a sim pack")
    raw = _mask(base64.b64decode(blob[len(MAGIC):]))
    return json.loads(zlib.decompress(raw).decode("utf-8"))


def merge(base, overlay):
    """Overlay packs (round 2, or a world we send you) replace the scenario and add creators, pools and engine patches."""
    out = dict(base)
    out["creators"] = dict(base.get("creators", {}))
    out["creators"].update(overlay.get("creators", {}))
    pools = {k: dict(v) for k, v in base.get("pools", {}).items()}
    for intent, langs in overlay.get("pools", {}).items():
        pools.setdefault(intent, {})
        for lang, items in langs.items():
            pools[intent][lang] = items
    out["pools"] = pools
    if "brands" in overlay:  # a live brief change: the overlay's brand rules win
        out["brands"] = dict(base.get("brands", {}))
        out["brands"].update(overlay["brands"])
    if "scenario" in overlay:
        out["scenario"] = overlay["scenario"]
    for k in ("seed", "salt", "per_run_seed"):  # an overlay world can bring its own seed and signing salt
        if k in overlay:
            out[k] = overlay[k]
    out["engine_patch"] = base.get("engine_patch", "") + "\n" + overlay.get("engine_patch", "")
    out["pack_ids"] = base.get("pack_ids", []) + overlay.get("pack_ids", [])
    return out
