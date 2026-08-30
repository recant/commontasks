---
id: src011
type: ticket
date: 2026-03-19
title: "TK-1041: Lakeview — Anthem PT denial batch (CO-97, mod 59)"
ticket: TK-1041
status: resolved
opened: 2026-03-19
resolved: 2026-04-03
assignee: "[[people/tom-reyes]]"
reporter: "[[people/karen-doyle]]"
client: "[[clients/lakeview-orthopedics]]"
payer: "[[payers/anthem]]"
participants: ["[[people/karen-doyle]]", "[[people/tom-reyes]]", "[[people/priya-nair]]"]
---

# TK-1041: Lakeview — Anthem PT denial batch (CO-97, mod 59)

**Reported via client portal by Karen Doyle ([[clients/lakeview-orthopedics]]), 2026-03-19:**

> Our PT claims to Anthem started denying in batches last week — the EOBs say CO-97 "bundled." Why are these suddenly denying when the exact same visits paid in February? Our providers are asking and I need an answer this week.

## Comments

**Tom Reyes — 2026-03-19 11:40**
Confirmed: 61 [[payers/anthem]] CO-97 denials on 97110+97140 same-day therapy pairs, $9,438 billed, first denial dated 3/12. Root cause per [[people/priya-nair]] (see #claims-ops 3/18): Anthem's March ClaimsXten update stopped honoring generic modifier 59 on NCCI PTP pairs — the specific X-subset modifier (XS) is now required on the column-2 code line with a distinct-site documentation pointer.

**Tom Reyes — 2026-03-19 16:55**
Corrected batch (all 61 claims, XS applied, doc pointers added) released on tonight's cycle. Watching remits.

**Priya Nair — 2026-03-24 09:15**
First corrected remits landing: 22 of the first 24 paid clean. Two need the documentation pointer fixed — different site notation. This confirms the XS approach for the whole batch.

**Tom Reyes — 2026-04-03 14:02**
Final tally: 54 of 61 corrected claims paid as of today's remit ($8,301 recovered). Remaining 7 are in normal adjudication, no new CO-97s. Karen notified via Dana. Marking resolved; the permanent scrubber fix (auto X-subset + line split) is tracked separately with [[people/jake-osei]].

## Resolution

Anthem March edit change; rebilled with XS on column-2 lines + documentation pointers. 54/61 paid by 4/3, rest in flight. Prevention: anthem config change (prefer_x_subset, line split) scoped with platform.
