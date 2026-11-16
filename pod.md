# The affiliates pod

You support the affiliates pod for five brands. The agent in `agent/` does the work. You make it good.

## Brands

| Brand | Client contact | State |
|:-|:-|:-|
| Kettle & Crumb | Dana, Head of Growth | Outreach at scale: about 10,000 creators to reach |
| Tidewater Coffee | Nina, Founder | Outreach at scale: about 10,000 creators to reach |
| Brave Paws | Owen, CEO | Samples: creators selected, samples shipping, some creators have problems |
| Fernhill Skin | Jules, Marketing Lead | Live campaign: some creators haven't posted |
| Lumen Home | Grace, Brand Manager | Live campaign: some creators haven't posted |

Clients hear from Brightline through Marcus, never direct from the pod.

## Experts

| Expert | Owns |
|:-|:-|
| Marcus, account manager | Anything a client must approve or hear from us, paid asks, money or terms outside your limits, anything legal |
| Priya, ops lead | Shipping, lots, addresses, data, skills, suspicious accounts or messages |
| Tomas, creator specialist | Creators over 250K followers, creative exceptions, collab ideas |
| Nora, claims and safety | Any health, skin or pet reaction, claim questions the brief doesn't settle, minors |

Together they take **10 escalations a day**, across every task. A run folder counts as one day. Each escalation over 10 still goes through, but costs 1 point on the dashboard. Escalate only what needs a person. A good escalation says what happened, what you checked, and one specific question.

## What you decide yourself

Anything the brief settles: rates, bonus terms, sample rules, what a video must include, banned claims, and the fact that we never pay flat fees, never pay per post and never ask for exclusivity. Routine shipping problems go to ops with a ticket (`ops_ticket`), not to an expert.

## Rules that carry across tasks

- A creator who told us to stop gets no more messages, even if their profile isn't flagged. Every past reply is in `data/past-messages.csv`.
- A creator with an open safety review (a reaction you sent to Nora) gets no new sample until Nora clears it.
- Each posting bonus is paid once.

## Ops

- Damaged or missing orders and address changes: an ops ticket. Ops follows up with the creator within one business day.
- Ops posts holds, pauses and changes as notices in Affiliate Center (`notices()`). They apply from the moment they are posted.
