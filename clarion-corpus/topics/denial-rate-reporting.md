---
id: top_denial_reporting
type: topic
label: Denial-rate reporting methodology
---

# Denial-rate reporting

Owned by [[people/sofia-chen]]. The May gotcha: release 2026.05.12 silently remapped `pended_payer_request` and `awaiting_attachment` states to `denied_other` in the reporting mart, so the June MBR showed [[clients/northside-clinic]] at a 14.3% May denial rate. [[people/jake-osei]] traced it; the postmortem ([[postmortems/2026-06-10-may-release-report-regression]]) put the true May rate at 8.2%, fixed the mapping (mart v2), and added a regression test. Corrected MBR issued Jun 11.

Current definition: denial rate = CARC-denied claims ÷ adjudicated claims, pends excluded.
