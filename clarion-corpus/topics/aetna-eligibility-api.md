---
id: top_aetna_elig_api
type: topic
label: Aetna real-time eligibility integration
---

# Aetna eligibility API (270/271)

[[payers/aetna]] real-time eligibility integration, owned by [[people/jake-osei]]. INC-2026-007 (Jul 21): an unannounced intermediate-CA rotation broke our pinned mTLS trust — 61% timeout peak, 2,347 checks failed or queued, 4 clients degraded over ~5 hours. Timeline and analysis in [[postmortems/2026-07-29-aetna-eligibility-outage]].

Standing changes: dual CA bundle + backoff retry in [[payer_configs/aetna-config]] (Jul 23), cert-chain monitoring (Jul 24), and the Jul 28 decision to make the cached-eligibility fallback permanent (24h TTL, stale flag in UI). Runbook still unwritten (overdue, Jake).
