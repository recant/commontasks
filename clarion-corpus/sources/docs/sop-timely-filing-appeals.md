---
id: src003
type: sop
date: 2025-11-02
title: "SOP-007: Timely Filing & Appeals"
owner: "[[people/elena-vasquez]]"
status: stale
superseded_by: "[[expert_calls/2026-08-05-legal-call]]"
superseded_scope: "UHC appeal window — delegated-credentialing contracts (90 days per §7.3, per legal call 2026-08-05); the 60-day figure below applies only to standard non-delegated contracts"
participants: ["[[people/elena-vasquez]]"]
---

# SOP-007: Timely Filing & Appeals

**Effective:** 2025-11-02 · **Owner:** [[people/elena-vasquez]] · **Review cycle:** annual

> ⚠️ Staleness note (added by tooling 2026-08): the UHC reconsideration window in §3 is superseded for delegated contracts — see superseded_by.

## 1. Purpose

Define the filing and appeal deadlines Clarion works to for each payer, and the required appeal package.

## 2. Initial filing windows

| Payer | Initial timely filing |
|---|---|
| [[payers/anthem]] | 90 days from date of service |
| [[payers/unitedhealth]] | 180 days from date of service |
| [[payers/masshealth]] | 90 days from date of service |
| [[payers/aetna]] | 120 days from date of service |

## 3. Reconsideration / appeal windows

Every appeal package must include a copy of the remittance advice, the corrected claim, and a cover letter stating the reconsideration reason.

- [[payers/anthem]]: reconsiderations accepted within 120 days of the remittance date.
- [[payers/masshealth]]: adjustment requests within 90 days; Board of Hearings appeals must be filed within 30 days of the notice date.
- Reconsideration requests to UnitedHealthcare must be submitted within 60 days of the remittance advice date.
- [[payers/aetna]]: reconsiderations accepted within 180 days of the remittance date.

## 4. Missed windows

Claims past the applicable reconsideration window require operations-manager approval before write-off, with the reason logged on the ticket.

## 5. Calendar discipline

The deadline is calculated from the remittance advice date, not the date the denial was worked. The work queue displays days-remaining per claim; anything under 10 days is flagged red.

## Related

[[docs/sop-denial-management]] · [[docs/sop-claims-intake-scrubbing]]
