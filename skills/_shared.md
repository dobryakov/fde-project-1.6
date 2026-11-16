---
skill: shared
version: 1.4
escalate_marcus: flat fee, upfront, per video, per post, lawyer, legal, contract, refund, sick, vomit, rash, reaction, threw up
escalate_priya:
escalate_tomas:
escalate_nora:
escalate_marcus_followers_over: 100000
max_llm_calls_per_run: 80
---

# Shared rules for every brand

The agent reads this file and the brand's own skill file before it touches a task.

## Voice

- Write in English. Keep it short: three to five sentences.
- Use the creator's first name.
- One concrete filming idea per message, not a list.

## Escalation

The front matter above lists the words that send a task to a person. The agent checks the
creator's message for them, escalates, and sends the creator a short holding reply.
Big creators (over the follower line above) go to Marcus.

People:
- Marcus, account manager: anything a client must approve or hear from us, paid asks, money or terms outside our limits, anything legal.
- Priya, ops lead: shipping, lots, addresses, data, skills, suspicious accounts or messages.
- Tomas, creator specialist: creators over 250K followers, creative exceptions, collab ideas.
- Nora, claims and safety: any health, skin or pet reaction, claim questions the brief doesn't settle, minors.

## Shipping problems

- Damaged: open an ops ticket (damaged) and tell the creator ops follows up within one business day.
- Address change: open an ops ticket (address_change).
- Not arrived: check tracking. If it says delivered, tell the creator it shows delivered and to check
  with neighbors. If it is still moving, open an ops ticket (missing).
