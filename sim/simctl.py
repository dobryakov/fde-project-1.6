#!/usr/bin/env python3
"""Command line for the Brightline Affiliate Center sim. Every command prints JSON.

  python3 sim/simctl.py init RUN_DIR
  python3 sim/simctl.py RUN_DIR [task=R101] COMMAND [ARGS] [key=value ...]

Commands:
  now | advance HOURS | budget | notices
  creator CREATOR_ID | find HANDLE
  invite CREATOR_ID RATE "message" | message CREATOR_ID "text"
  inbox [all=yes] | thread CREATOR_ID
  ship CREATOR_ID "Product Name" [lot=L-1234] | stock ["Product Name"] | orders [CREATOR_ID] | tracking ORDER_ID
  ticket KIND CREATOR_ID [order=ORDER_ID] [note="text"]
  posts HANDLE | pay-bonus CREATOR_ID [note="text"]
  escalate TO "summary" [creator=CREATOR_ID]
Options anywhere: task=R101, brand=BRAND (only if a call asks for it).
init reads SIM_PACK from the environment when no pack= is given (a world we send you).
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from affiliate_center import AffiliateCenter, SimError, init_run  # noqa: E402

COMMANDS = {"now": 0, "budget": 0, "notices": 0, "advance": 1, "creator": 1, "find": 1, "invite": 3, "message": 2,
            "inbox": 0, "thread": 1, "ship": 2, "stock": (0, 1), "orders": (0, 1), "tracking": 1, "ticket": 2, "posts": 1,
            "pay-bonus": 1, "escalate": 2}
KV = re.compile(r"^(task|brand|lot|order|note|creator|all|limit|pack|meta)=(.*)$", re.S)


def parse(argv):
    opts, pos = {}, []
    it = iter(argv)
    for tok in it:
        if tok.startswith("--") and len(tok) > 2:      # old style flags still work
            key = tok[2:].replace("-", "_")
            if key in ("all",):
                opts["all"] = "yes"
            else:
                opts[{"run_dir": "run_dir", "creator": "creator"}.get(key, key)] = next(it, "")
            continue
        m = KV.match(tok)
        if m:
            opts[m.group(1)] = m.group(2)
        else:
            pos.append(tok)
    return opts, pos


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "help"):
        print(__doc__)
        return 0
    opts, pos = parse(argv)
    try:
        if pos and pos[0] == "init":
            run_dir = pos[1] if len(pos) > 1 else opts.get("run_dir", os.environ.get("SIM_RUN_DIR", "runs/current"))
            packs = [p for p in opts.get("pack", "").split(",") if p]
            out = init_run(run_dir, packs)
        else:
            if pos and pos[0] not in COMMANDS:
                run_dir = pos.pop(0)
            else:
                run_dir = opts.get("run_dir", os.environ.get("SIM_RUN_DIR", "runs/current"))
            if not pos or pos[0] not in COMMANDS:
                raise SimError("bad_request", f"unknown command. Known: init, {', '.join(COMMANDS)}")
            cmd, args = pos[0], pos[1:]
            ac = AffiliateCenter(run_dir, task=opts.get("task") or os.environ.get("SIM_TASK"))
            b = opts.get("brand")
            need = COMMANDS[cmd]
            lo, hi = need if isinstance(need, tuple) else (need, need)
            if not lo <= len(args) <= hi:
                raise SimError("bad_request", f"{cmd} takes {need} argument(s), got {len(args)}. See: simctl.py help")
            out = {
                "now": lambda: ac.now(),
                "budget": lambda: ac.budget(),
                "notices": lambda: ac.notices(),
                "advance": lambda: ac.advance(float(args[0])),
                "creator": lambda: ac.creator(args[0]),
                "find": lambda: ac.find_creator(args[0]),
                "invite": lambda: ac.send_invite(args[0], float(args[1]), args[2], brand=b,
                                                 meta=json.loads(opts["meta"]) if opts.get("meta") else None),
                "message": lambda: ac.send_message(args[0], args[1], brand=b,
                                                   meta=json.loads(opts["meta"]) if opts.get("meta") else None),
                "inbox": lambda: ac.inbox(unread_only=opts.get("all") != "yes", limit=int(opts.get("limit", 500))),
                "thread": lambda: ac.thread(args[0], brand=b),
                "ship": lambda: ac.ship_sample(args[0], args[1], lot=opts.get("lot"), brand=b),
                "stock": lambda: ac.stock(args[0] if args else None, brand=b),
                "orders": lambda: ac.orders(args[0] if args else None, brand=b),
                "tracking": lambda: ac.tracking(args[0]),
                "ticket": lambda: ac.ops_ticket(args[0], args[1], order_id=opts.get("order"), note=opts.get("note", ""), brand=b),
                "posts": lambda: ac.posts(args[0], brand=b),
                "pay-bonus": lambda: ac.pay_bonus(args[0], note=opts.get("note", ""), brand=b),
                "escalate": lambda: ac.escalate(args[0], args[1], creator_id=opts.get("creator")),
            }[cmd]()
        print(json.dumps(out, ensure_ascii=False, indent=1))
        return 0
    except SimError as e:
        print(json.dumps({"ok": False, "error": e.code, "message": e.message, **e.extra}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
