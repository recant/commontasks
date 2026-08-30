---
id: src026
type: postmortem
date: 2026-06-10
title: "Postmortem: release 2026.05.12 status-mapping regression in reporting mart"
incident: REPORT-2026-05
severity: SEV-3 (data quality, client-facing numbers held before exposure)
participants: ["[[people/jake-osei]]", "[[people/sofia-chen]]", "[[people/marcus-webb]]"]
---

# Postmortem: reporting-mart status-mapping regression (release 2026.05.12)

**Authors:** [[people/jake-osei]] (platform), [[people/sofia-chen]] (reporting) · **Reviewed:** [[people/marcus-webb]] · **Published:** 2026-06-10

## Summary

Release 2026.05.12 renamed the internal claim-state enum. The reporting mart's status-mapping table was not updated in the same change, so from 5/12 onward the pend states `pended_payer_request` and `awaiting_attachment` fell through the mapping default into `denied_other`. Denial rates for May were overstated for every client — most visibly [[clients/northside-clinic]], whose draft MBR showed 14.3% against a true rate of 8.2%. The wrong number was caught in draft review and never reached a client.

## Timeline

- **2026-05-12** — Release ships; enum renamed; mart mapping left on the "verify later" list.
- **2026-06-04 09:05** — Sofia flags the implausible Northside draft number in #claims-ops; MBRs held.
- **2026-06-04 09:22** — Priya's operational gut-check (no denial wave felt in the queue) points suspicion at the pipeline.
- **2026-06-08** — TK-1102: Jake reproduces (mart 402 "denied" vs 231 raw CARC denials; difference = pend count) and identifies the fell-through mapping.
- **2026-06-09** — Mapping v2 merged (explicit rows + fail-loud default); May backfill runs.
- **2026-06-10** — Regression test added (mart totals vs raw 835 CARC counts, 0.2% tolerance, every release); this postmortem published.
- **2026-06-11** — Corrected MBR issued: Northside May true denial rate 8.2%, in line with April's 8.1%.

## Root cause & contributing factors

1. **Root cause:** enum rename shipped without the dependent mart mapping update — the two live in different repos with no shared schema contract.
2. **Contributing:** the mapping's default branch silently bucketed unknown states instead of failing; silent defaults turn schema drift into wrong numbers rather than errors.
3. **Contributing:** no automated reconciliation between mart aggregates and raw 835 CARC counts existed before this incident.

## What went well

Layered review worked: an implausible number + an operational gut-check stopped a wrong client-facing figure at draft stage. The definition of the metric itself was never wrong — denial rate remains CARC-denied claims ÷ adjudicated claims, pends excluded.

## Action items (all completed)

| Item | Owner | Status |
|---|---|---|
| Mart mapping v2 with explicit state rows | [[people/jake-osei]] | done 6/9 |
| Fail-loud default for unknown states | [[people/jake-osei]] | done 6/9 |
| May backfill + corrected MBR | [[people/sofia-chen]] | done 6/11 |
| Release regression test: mart vs raw CARC reconciliation | [[people/jake-osei]] | done 6/10 |
| Schema-change checklist adds "grep dependent mapping tables" | [[people/marcus-webb]] | done 6/10 |
