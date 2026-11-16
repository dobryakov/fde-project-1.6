# Affiliate Center sim: API

A local stand in for TikTok Shop Affiliate Center. Python 3.10 or newer, standard library only, no network.
Within one world it is deterministic: the same messages to the same creators give the same results.

## Start a run

```
python3 sim/simctl.py init runs/r1
```

Each run is a folder. Use a new folder for every fresh attempt. Every call is written to
`runs/r1/events.jsonl`, and scoring reads that log.

**A world we send you: `SIM_PACK`.** For a graded run we email you a sim pack and its path goes in the
`SIM_PACK` environment variable, for example `SIM_PACK=/path/to/world.pack python3 agent.py runs/fresh`.
`simctl.py init` and `init_run()` read `SIM_PACK` when they create the run folder and load that world
instead of the practice one. So your command must pass its environment through to `simctl init`: don't
clear the environment, and don't pass your own `pack=` when `SIM_PACK` is set. Without `SIM_PACK` you get
the practice world.

## Two ways to call it

Python:

```python
import sys; sys.path.insert(0, "sim")
from affiliate_center import AffiliateCenter, SimError

ac = AffiliateCenter("runs/r1")               # screener
ac = AffiliateCenter("runs/r1", task="R101")  # project: one task at a time
```

Command line (prints JSON):

```
python3 sim/simctl.py runs/r1 [task=R101] <command> [args] [key=value]
```

## Time

Each run (each task, in the project) has its own clock. It starts at Mon 9 Nov 2026 09:00 and only moves
when you call `advance(hours)`. Creators reply hours or days later. Call `inbox()` to collect what arrived.
After the window closes you can't send anything more.

## Limits

- 60 messages per brand per simulated hour, and 500 per day. Invites count as messages.
- Over the limit: `SimError` with code `rate_limited` and `extra["retry_after_hours"]`.
- Each run or task has a message budget. Past it: `budget_exhausted`.
- Each message costs $0.04 of platform credit.

## Calls

| Python | CLI | What it does |
|:-|:-|:-|
| `now()` | `now` | Current time and when the window closes |
| `advance(hours)` | `advance 6` | Move the clock. Replies that came due land in the inbox |
| `budget()` | `budget` | Messages used, budget left, cost, rate limits |
| `notices()` | `notices` | Ops and platform notices in effect now |
| `creator(id)` | `creator CR00001` | Live profile: handle, prior handles, followers, avg views (last 30 days), country, language, flags |
| `find_creator(handle)` | `find @handle` | Look up by current or prior handle |
| `send_invite(id, rate, message)` | `invite CR00001 17 "text"` | Target collaboration invite at a commission rate, with a message |
| `send_message(id, text)` | `message CR00001 "text"` | A message in the creator's thread |
| `inbox()` | `inbox` | New creator messages and invite responses (marks them read) |
| `thread(id)` | `thread CR00001` | The whole thread with one creator, plus invite status |
| `ship_sample(id, product, lot=None)` | `ship CR00001 "Product" [lot=L-1]` | Approve and ship one free sample. Default lot is the oldest in stock |
| `stock(product=None)` | `stock ["Product"]` | Lots in stock for the brand's products, oldest first. A lot on hold still shows here; holds are in `notices()` |
| `orders(id=None)` | `orders [CR00001]` | Sample orders and tracking |
| `tracking(order_id)` | `tracking O123` | Tracking scans for one order. A shipment ends delivered, returned or with an exception status |
| `ops_ticket(kind, id, order_id, note)` | `ticket damaged CR00001 order=O123 note="text"` | Ticket for ops. kind: damaged, missing, address_change, lot_swap, cancel, other |
| `posts(handle)` | `posts @handle` | Videos posted by that handle for the brand. Search is by handle, like the app |
| `pay_bonus(id, note)` | `pay-bonus CR00001` | Pay the brand's posting bonus |
| `escalate(to, summary, creator_id)` | `escalate nora "summary" creator=CR00001` | Hand a case to marcus, priya, tomas or nora |

Pass `brand=` (Python or CLI) only if a call says the brand is missing.

## Structured fields: `meta`

`send_invite` and `send_message` take an optional `meta` dict (CLI: `meta='{"answers": "rate_q", "rate": 17}'`).
When you send it, the creator judges your answer on these fields, strictly, and the text has to agree with them.

| Field | Values |
|:-|:-|
| `answers` | What the creator asked: `rate_q`, `bonus_q`, `sample_q`, `flat_fee`, `exclusive`, `claim_q`, `competitor`, `other`. Join several with `+` |
| `rate` | The commission you quoted, in percent. Must be the creator's correct rate, and appear in the text |
| `bonus_amount`, `bonus_videos`, `bonus_days` | The bonus terms you quoted. Must match the brief, and the amount must appear in the text |
| `stance` | Your answer to a fee, exclusivity, claim or competitor ask: `decline` or `accept` |
| `claims` | Any product claims your message makes, as a list of strings |
| `language` | The language you wrote in, as a two letter code |

A wrong rate or bonus in `meta`, or `accept` on a fee, exclusivity, claim or competitor ask, is a policy violation.

## What creators see

Creators read your messages. They notice what a real creator would notice. Did you use their name? Are the
numbers right? Is it in their language? Is there a reason to post?

Each invite and message is checked against the brand brief. Wrong rates, wrong bonus terms, banned claims,
flat fees, paying per post and exclusivity are policy violations.

## Errors

Every refusal raises `SimError` (CLI: `{"ok": false, "error": ...}`) with a short `code` and a message.
Refused calls are logged too.
