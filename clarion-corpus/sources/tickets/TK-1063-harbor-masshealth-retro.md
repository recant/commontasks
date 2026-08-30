---
id: src015
type: ticket
date: 2026-04-06
title: "TK-1063: Harbor — MassHealth denial, patient granted retro eligibility"
ticket: TK-1063
status: resolved
opened: 2026-04-06
resolved: 2026-05-08
assignee: "[[people/tom-reyes]]"
reporter: "[[people/amy-tran]]"
client: "[[clients/harbor-family-medicine]]"
payer: "[[payers/masshealth]]"
participants: ["[[people/amy-tran]]", "[[people/tom-reyes]]", "[[people/priya-nair]]"]
---

# TK-1063: Harbor — MassHealth denial, patient granted retro eligibility

**Reported via client portal by Amy Tran ([[clients/harbor-family-medicine]]), 2026-04-06:**

> Claim CLM-2026-11203 (DOS 2026-02-11, $214) denied for no coverage in February. The patient's MassHealth application was approved on 2026-03-28 with coverage retroactive to mid-January, so the visit date is now covered. Can this be rebilled? What do you need from us?

## Comments

**Tom Reyes — 2026-04-07 10:20**
Process per [[people/priya-nair]] (#claims-ops 4/2): verify the retro span in EVS/MMIS, then submit a new claim (not an adjustment) within 90 days of the eligibility determination date (3/28 here → deadline late June).

**Tom Reyes — 2026-04-09 15:44**
EVS span check done with Priya — retro segment 2026-01-17 through present, covers the 2/11 DOS. She had to walk me through reading the span segments; there's a two-segment overlap thing I would not have caught on my own. New claim queued for tonight's cycle.

**Priya Nair — 2026-04-10 09:02**
Span verified, claim released. Flag for the future: this process lives entirely in my head and Tom just experienced why that's a problem. Adding to the someday-document-this pile.

**Tom Reyes — 2026-05-08 11:31**
Paid on today's remit, $214 allowed against the retro span, no pend. Closing. Amy notified.

## Resolution

Retro-eligibility rebill: EVS span verified (retro to 2026-01-17), new claim submitted within the 90-day determination-date window, paid 2026-05-08.
