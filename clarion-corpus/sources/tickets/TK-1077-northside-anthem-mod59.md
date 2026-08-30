---
id: src016
type: ticket
date: 2026-04-21
title: "TK-1077: Northside — Anthem therapy denials recurring (mod 59)"
ticket: TK-1077
status: resolved
opened: 2026-04-21
resolved: 2026-05-06
assignee: "[[people/tom-reyes]]"
reporter: "[[people/luis-romero]]"
client: "[[clients/northside-clinic]]"
payer: "[[payers/anthem]]"
participants: ["[[people/luis-romero]]", "[[people/tom-reyes]]", "[[people/priya-nair]]"]
---

# TK-1077: Northside — Anthem therapy denials recurring (mod 59)

**Reported via client portal by Luis Romero ([[clients/northside-clinic]]), 2026-04-21:**

> We're still getting [[payers/anthem]] CO-97 denials on rehab therapy visits — smaller numbers than what I hear hit your ortho clients, but it keeps recurring. Weren't these supposed to be fixed? Our billers are re-doing work every week.

## Comments

**Tom Reyes — 2026-04-21 14:12**
Same root cause as TK-1041 (Lakeview): Anthem's March X-subset requirement on NCCI PTP pairs. Northside's recurrence is because their billers keep submitting new claims with plain 59 — each fresh batch re-hits the edit. The March fix was a rebill, not a prevention.

**Priya Nair — 2026-04-22 10:05**
Two-part fix: (1) rebill the open denials with XS on the column-2 lines, (2) their billers need a short training on X-subset usage until our scrubber auto-swap ships — Northside submits more hand-keyed claims than Lakeview, so prevention has to include the humans. Flagging the training need to Dana for the next client call.

**Tom Reyes — 2026-05-06 16:20**
Rebilled batches from 4/22 and 4/29 both paying (34 of 38 clean so far). Auto-swap config still pending on platform's queue. Closing the ticket; training request is with Dana for the June call agenda.

## Resolution

Same Anthem X-subset root cause as TK-1041. Open denials rebilled with XS (34/38 paid by 5/6). Prevention handed off: biller training (Dana/Priya, June client call) + scrubber auto-swap (platform backlog).
