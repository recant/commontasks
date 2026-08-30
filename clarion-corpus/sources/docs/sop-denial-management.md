---
id: src002
type: sop
date: 2025-10-20
title: "SOP-002: Denial Management Workflow"
owner: "[[people/priya-nair]]"
status: stale
superseded_by: "[[expert_calls/2026-04-14-vik-malhotra-payer-ops]]"
superseded_scope: "Anthem NCCI PTP edits — the 'append modifier 59' guidance in §4 no longer clears Anthem edits since their March 2026 ClaimsXten update (X-subset modifier required)"
participants: ["[[people/priya-nair]]"]
---

# SOP-002: Denial Management Workflow

**Effective:** 2025-10-20 · **Owner:** [[people/priya-nair]] · **Review cycle:** annual

> ⚠️ Staleness note (added by tooling): §4 modifier guidance superseded for [[payers/anthem]] — see superseded_by.

## 1. Intake of denials

Remittance files (835) post nightly. Denials route to the work queue by CARC group. Denials must be worked within 5 business days of remittance posting.

## 2. Triage by CARC

| CARC | Meaning | First action |
|---|---|---|
| CO-4 | Procedure inconsistent with modifier | Review modifier usage vs NCCI |
| CO-16 | Missing information | Identify missing element from RARC |
| CO-29 | Timely filing expired | See [[docs/sop-timely-filing-appeals]] |
| CO-97 | Bundled/included in another service | Check NCCI PTP pair; consider modifier |
| CO-197 | Precertification/authorization absent | Pull the auth record and verify the authorization was issued under the same NPI billed on the claim before resubmitting |

## 3. Bundling denials (CO-97)

For services denied as bundled where documentation supports separately identifiable services, unbundle per NCCI guidance and resubmit the corrected claim.

## 4. Modifier guidance

Where the medical record supports a distinct encounter, session, or anatomic site, append modifier 59 to the secondary procedure to indicate a distinct procedural service, and resubmit. Keep a documentation pointer in the claim note.

## 5. Payer-specific channels

- [[payers/anthem]]: reconsiderations via Availity portal.
- [[payers/aetna]]: reconsiderations may also be submitted by mail using the paper Provider Dispute form (allow 30–45 days).
- [[payers/masshealth]]: use the POSC portal; attachment pends follow [[docs/sop-claim-attachments]].
- [[payers/unitedhealth]]: reconsiderations via the UHC provider portal.

## 6. Escalation

Batches of >25 same-pattern denials for one client are an incident: open a ticket, tag the CSM, and post in #claims-ops.

## Related

[[docs/sop-claims-intake-scrubbing]] · [[docs/sop-timely-filing-appeals]]
