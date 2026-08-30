---
id: src001
type: sop
date: 2025-09-15
title: "SOP-001: Claims Intake & Scrubbing"
owner: "[[people/priya-nair]]"
status: current
participants: ["[[people/priya-nair]]"]
---

# SOP-001: Claims Intake & Scrubbing

**Effective:** 2025-09-15 · **Owner:** [[people/priya-nair]] · **Review cycle:** annual

## Purpose

Standardize how client claim files enter the Clarion platform and what must be verified before an 837 leaves our clearinghouse connection.

## Scope

All professional (837P) and institutional (837I) claims for all clients and payers.

## Procedure

1. **File receipt.** Client PM system drops or SFTP-pushes the daily claim batch. The intake service acknowledges within 15 minutes; failures page the on-call engineer.
2. **Pre-submission scrub.** Every claim must pass the scrub checklist before release. Verify rendering and billing NPI are active and match the credentialed record, verify member eligibility for the date of service, and confirm any required prior authorization number is present on the claim.
3. **Eligibility verification.** Run a real-time 270/271 eligibility check at intake for every claim where the payer supports it; fall back to the most recent cached response when the payer connection is degraded.
4. **Edits.** Apply payer-specific edit packs from the payer config files before release. Do not hand-edit claims in the clearinghouse UI; fix at the source or via config.
5. **Rejections.** Front-end 837 rejections (999/277CA) must be corrected and resubmitted within 2 business days of the rejection notice.
6. **Release.** Claims passing scrub release to payers on the 6pm ET daily cycle.

## Escalation

Scrub-rule questions go to #claims-ops. Config changes go through [[people/jake-osei]] with a ticket.

## Related

[[docs/sop-denial-management]] · [[docs/sop-timely-filing-appeals]] · [[docs/sop-claim-attachments]]
