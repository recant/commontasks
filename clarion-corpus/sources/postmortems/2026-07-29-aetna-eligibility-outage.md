---
id: src043
type: postmortem
date: 2026-07-29
title: "Postmortem INC-2026-007: Aetna eligibility API outage 2026-07-21"
incident: INC-2026-007
severity: sev-2
participants: ["[[people/jake-osei]]", "[[people/marcus-webb]]", "[[people/elena-vasquez]]"]
---

# Postmortem INC-2026-007: Aetna eligibility API outage

**Author:** [[people/jake-osei]] · **Reviewed:** [[people/marcus-webb]], [[people/elena-vasquez]] · **Published:** 2026-07-29

## Summary

On 2026-07-21, real-time eligibility (270/271) against [[payers/aetna]] degraded from **09:14 to 14:20 EDT**, peaking at a **61% timeout rate**. Aetna had rotated the intermediate CA on its eligibility endpoint without trading-partner notification; Clarion's pinned single-CA trust bundle rejected the new chain, failing the mTLS handshake. **2,347 eligibility checks failed or queued**, and front-desk verification degraded at four clients ([[clients/harbor-family-medicine]] hardest, plus [[clients/northside-clinic]], [[clients/lakeview-orthopedics]], [[clients/riverbend-imaging]]). A cached-eligibility workaround restored functionality at 14:20; the permanent connectivity fix shipped 2026-07-23. No claim was released on stale eligibility and no PHI was exposed.

## Timeline (2026-07-21 unless noted, EDT)

| Time | Event |
|---|---|
| 09:14 | Timeout alerts fire on Aetna 270/271; error rate ~40% and climbing |
| 09:31 | 61% timeout rate; other payers confirmed clean — Aetna-specific |
| 09:40 | First client impact reports (Harbor front desk) |
| 10:02 | INC-2026-007 declared, sev-2; TK-1119 master opened |
| 11:45 | Root-cause hypothesis: cert chain — endpoint presenting an unknown intermediate CA |
| 12:30 | Packet capture confirms mTLS chain-validation failure on our side |
| 14:20 | Workaround live: cached 271 (≤30 days, labeled) + overnight batch-270 queue |
| 14:47 | Client notifications out to all four affected clients |
| 16:50 | Aetna acknowledges unannounced CA rotation ("planned maintenance") |
| 07-22 | Backfill: 2,347 queued checks re-run overnight (TK-1121); 41 stale-flagged for manual re-verify |
| 07-23 | Permanent fix deployed: dual-CA trust bundle + exponential-backoff retry (aetna.yaml) |
| 07-24 | Error rate at baseline for 24h; cert-chain monitoring shipped for **all** payer endpoints |

## Root cause

Single-CA certificate pinning met an unannounced payer-side intermediate-CA rotation. The pinning behaved as designed — reject unknown chains — but the design assumed payers announce rotations. Contributing: the retry policy was a tight loop that amplified connection pressure during the failure, and **no cert-chain monitoring existed**, so the first signal was user-facing timeouts instead of a chain-change alert days earlier (the new chain was visible in Aetna's staging environment from 7/16).

## Impact

~5 hours of degraded front-desk eligibility verification at four clients; 2,347 checks failed/queued (all backfilled within 24h; 2 true coverage terminations caught); zero stale-eligibility claim releases; zero PHI exposure. Reputational cost mostly absorbed by fast comms — and one real schedule cost: the remediation week displaced the [[clients/northside-clinic]] eligibility-API work.

## What went well

Minutes-level detection; a workaround that restored clinics in hours; honest same-day client comms; a backfill design that refused to release claims on stale data.

## Action items

| Item | Owner | Due | Status |
|---|---|---|---|
| Dual-CA bundle + backoff retry in aetna.yaml | [[people/jake-osei]] | 7/23 | done |
| Cert-chain monitoring, all payer mTLS endpoints | [[people/jake-osei]] | 8/1 | done 7/24 |
| Client outage-comms template | [[people/elena-vasquez]] | 8/1 | done 7/25 |
| Cached-eligibility fallback permanent (24h TTL + UI stale flag) — per 7/28 review decision | [[people/jake-osei]] | in config | done 7/23 (ratified 7/28) |
| Eligibility-cache TTL config for all payers | [[people/marcus-webb]] | 9/5 | open |
| Payer eligibility-outage runbook | [[people/jake-osei]] | 8/15 | open |
