---
id: skl_aetna_outage_runbook
type: skill
name: aetna-eligibility-outage-runbook
description: Respond to a payer real-time-eligibility outage (distilled from INC-2026-007).
derived_from: ["[[postmortems/2026-07-29-aetna-eligibility-outage]]", "[[meetings/2026-07-28-aetna-incident-review]]", "[[payer_configs/aetna-config]]", "[[slack/2026-07-21-aetna-eligibility-outage]]"]
status: current
---

# Skill: aetna-eligibility-outage-runbook

**When to use:** a payer's real-time eligibility (270/271) connection degrades — timeout spikes, handshake failures, error-rate alerts. Written from INC-2026-007 ([[topics/aetna-eligibility-api]]); note the formal runbook action item is Jake's and this page is its seed.

## Steps

1. **Scope it (first 15 min):** is it one payer or all? One payer + clean others = payer-side. Check the cert-chain alert channel first — an unannounced **CA rotation** looks exactly like a capacity outage from the timeout graph.
2. **Declare:** sev-2 if front-desk workflows are degraded; master ticket + #incidents narrative; name an incident lead.
3. **Stabilize with the cached fallback:** the eligibility panel serves the last good 271 (24h TTL, stale-labeled — permanent capability per the 7/28 decision). Confirm it's engaging; queue failed checks for overnight batch 270.
4. **Client comms within the hour:** use Elena's outage template; phone the hardest-hit client. Honest + fast beat polished + slow (Harbor: "your cached mode saved our afternoon").
5. **Guardrail:** cached eligibility is a front-desk convenience, **never a claims-release basis** — scrub still requires live-or-fresh checks per [[docs/sop-claims-intake-scrubbing]].
6. **Fix:** for cert issues — verify the new chain fingerprint out-of-band, extend the dual bundle ([[payer_configs/aetna-config]] pattern), backoff retry. Get payer acknowledgment on record.
7. **Backfill:** re-run every queued check; stale-flag anything outside the cache window for manual re-verify before any claim releases (INC-007: 2,347 re-run, 2 true terminations caught).
8. **Close the loop:** incident review within a week, postmortem published, action items owned and dated.
