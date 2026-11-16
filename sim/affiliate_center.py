"""Brightline Affiliate Center: a local stand in for TikTok Shop Affiliate Center.

Python 3.10+, standard library only, no network. Everything is deterministic:
the same messages sent to the same creators give the same results.

    from affiliate_center import AffiliateCenter, SimError
    ac = AffiliateCenter("runs/r1")              # screener: one campaign
    ac = AffiliateCenter("runs/r1", task="R101") # project: one task at a time

Simulated time
    Each run (each task in the project) has its own clock. It starts at
    Mon 9 Nov 2026 09:00 and only moves when you call advance(hours).
    Creators reply hours or days later. Call inbox() to collect what arrived.

Limits
    60 messages per brand per simulated hour and 500 per day. Invites count as
    messages. Over the limit you get SimError("rate_limited") with
    retry_after_hours. Each run or task has a message budget (see budget()).
    Each message costs $0.04 of platform credit.

Every call is written to <run_dir>/events.jsonl. Scoring reads that log.

SIM_PACK
    If SIM_PACK is set when a run folder is created (simctl init or init_run with
    no packs), the sim loads that world instead of the practice one.
"""
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
import pack as _pack  # noqa: E402

_CACHE = {}


class SimError(Exception):
    """Raised for anything the platform refuses. .code is a short string, .extra has details."""

    def __init__(self, code, message, extra=None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.extra = extra or {}


def _load(packs):
    key = tuple(packs)
    if key not in _CACHE:
        data = _pack.load(os.path.join(_HERE, "_core.pack"))
        for p in packs:
            data = _pack.merge(data, _pack.load(p))
        mod = {"__name__": "affiliate_core"}
        exec(compile(data["engine_src"] + "\n" + data.get("engine_patch", ""), "<affiliate-core>", "exec"), mod)
        _CACHE[key] = (data, mod)
    return _CACHE[key]


def _run_meta(run_dir):
    meta = os.path.join(run_dir, "run.json")
    if os.path.exists(meta):
        with open(meta) as f:
            return json.load(f)
    return {}


def _run_packs(run_dir):
    return _run_meta(run_dir).get("packs", [])


def engine_for(run_dir):
    """(data, module, engine) for a run folder. The scorer uses this."""
    run_dir = os.path.abspath(run_dir)
    data, mod = _load(_run_packs(run_dir))
    return data, mod, mod["Engine"](run_dir, data, nonce=_run_meta(run_dir).get("nonce"))


def init_run(run_dir, packs=(), nonce=None):
    """Create a fresh run folder. packs: extra scenario packs, such as a world we send you."""
    run_dir = os.path.abspath(run_dir)
    if os.path.exists(os.path.join(run_dir, "state.db")):
        raise SimError("exists", f"{run_dir} already has a run. Use a new folder.")
    if not packs and os.environ.get("SIM_PACK"):  # a world we send you (see API.md, SIM_PACK)
        packs = [p for p in os.environ["SIM_PACK"].split(os.pathsep) if p]
    os.makedirs(run_dir, exist_ok=True)
    packs = [os.path.abspath(p) for p in packs]
    data, mod = _load(packs)
    meta = {"packs": packs}
    if data.get("per_run_seed"):
        import secrets
        meta["nonce"] = nonce or secrets.token_hex(8)
    with open(os.path.join(run_dir, "run.json"), "w") as f:
        json.dump(meta, f)
    eng = mod["Engine"](run_dir, data, create=True, nonce=meta.get("nonce"))
    eng.init_run()
    return {"ok": True, "run_dir": run_dir, "scenario": data["scenario"]["name"],
            "tasks": sorted(k for k in data["scenario"].get("ns_meta", {}) if k not in ("*", "main"))[:3] or ["main"]}


class AffiliateCenter:
    def __init__(self, run_dir, task=None):
        self.run_dir = os.path.abspath(run_dir)
        data, mod = _load(_run_packs(self.run_dir))
        self._mod = mod
        self._data = data
        self._eng = mod["Engine"](self.run_dir, data, ns=task, nonce=_run_meta(self.run_dir).get("nonce"))
        meta = self._eng.task_meta(self._eng.ns)
        if task and task not in data["scenario"].get("ns_meta", {}):
            raise SimError("unknown_task", f"no task {task} in this run")
        self._default_brand = (meta.get("brands") or [None])[0]

    def _call(self, name, *args, **kw):
        eng = self._eng
        eng.begin()
        try:
            eng.deliver()
            out = getattr(eng, "api_" + name)(*args, **kw)
            eng.commit()
            return out
        except self._mod["SimError"] as e:
            eng.commit()  # keep the log of refused calls
            raise SimError(e.code, e.message, e.extra) from None
        except Exception:
            eng.rollback()
            raise

    def _b(self, brand):
        b = brand or self._default_brand
        if not b:
            raise SimError("bad_request", "brand is required for this task")
        return b

    # time and limits
    def now(self):
        """Current simulated time for this run or task, and when its window closes."""
        return self._call("now")

    def advance(self, hours):
        """Move this clock forward. Creator replies that came due land in inbox()."""
        return self._call("advance", hours)

    def budget(self):
        """Messages used, message budget, platform cost and rate limits."""
        return self._call("budget")

    def notices(self):
        """Ops and platform notices in effect now (holds, pauses, changes). Read before you act."""
        return self._call("notices")

    # creators
    def creator(self, creator_id):
        """Live profile from the platform: handle, prior handles, followers, avg views (last 30 days), country, language, flags."""
        return self._call("get_creator", creator_id)

    def find_creator(self, handle):
        """Look a creator up by current or prior handle."""
        return self._call("find", handle)

    # outreach
    def send_invite(self, creator_id, rate, message, brand=None, meta=None):
        """Send a target collaboration invite at a commission rate (percent), with a message.
        The creator accepts, replies with a question, declines or ignores it. meta: see API.md."""
        return self._call("send_invite", self._b(brand), creator_id, rate, message, meta)

    def send_message(self, creator_id, text, brand=None, meta=None):
        """Send a message in the creator's thread: answers, follow ups, nudges. meta: see API.md."""
        return self._call("send_message", self._b(brand), creator_id, text, meta)

    def inbox(self, unread_only=True, limit=500):
        """Creator messages and invite responses that have arrived. Marks them read."""
        return self._call("inbox", unread_only, limit)

    def thread(self, creator_id, brand=None):
        """Full message thread with one creator, plus the invite status."""
        return self._call("thread", self._b(brand), creator_id)

    # samples
    def ship_sample(self, creator_id, product, lot=None, brand=None):
        """Approve and ship one free sample. lot defaults to the oldest lot in stock."""
        return self._call("ship_sample", self._b(brand), creator_id, product, lot)

    def stock(self, product=None, brand=None):
        """Lots in stock for the brand's products, oldest first. Holds are in notices(), not here."""
        return self._call("stock", self._b(brand), product)

    def orders(self, creator_id=None, brand=None):
        """Sample orders for the brand, optionally for one creator, with tracking."""
        return self._call("orders", self._b(brand), creator_id)

    def tracking(self, order_id):
        """Tracking scans for one order."""
        return self._call("tracking", order_id)

    def ops_ticket(self, kind, creator_id, order_id=None, note="", brand=None):
        """Open a ticket with the ops team. kind: damaged, missing, address_change, lot_swap, cancel, other."""
        return self._call("ops_ticket", self._b(brand), kind, creator_id, order_id, note)

    # live campaigns
    def posts(self, handle, brand=None):
        """Videos posted by a handle for this brand (search is by handle, like the app)."""
        return self._call("posts", self._b(brand), handle)

    def pay_bonus(self, creator_id, note="", brand=None):
        """Pay the brand's posting bonus to a creator."""
        return self._call("pay_bonus", self._b(brand), creator_id, note)

    # people
    def escalate(self, to, summary, creator_id=None):
        """Hand a case to a person: marcus, priya, tomas or nora. They take a limited number per day."""
        return self._call("escalate", to, creator_id, summary)
