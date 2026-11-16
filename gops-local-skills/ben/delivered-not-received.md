---
skill: delivered-not-received (local)
owner: Ben
base: skills/_shared.md (Shipping problems)
---

# Tracking says delivered, creator says it never came

The company skill says: if tracking says delivered, tell the creator to check with neighbors. That is right only
when the parcel went to the address we have now.

Before you answer:
1. Read the delivery address on the order (`orders(id)`).
2. Compare it with `address_on_file` in `data/creators.csv`, and read the creator's message and thread for "moved"
   or a new address.
3. Different address: the parcel went to their old place. Open a `missing` ticket with both addresses in the note,
   and tell the creator ops will track it down and resend within one business day. No "check with neighbors".
4. Same address: the company skill's answer is fine.

I patched this by hand three times this week. Each creator had moved and told us.
