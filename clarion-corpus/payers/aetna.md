---
id: pay_aetna
type: payer
name: Aetna
---

# Aetna

Commercial payer. The 2026-07-21 real-time eligibility (270/271) outage — an unannounced intermediate-CA rotation broke our pinned mTLS trust ([[topics/aetna-eligibility-api]], INC-2026-007). 2,347 checks failed or queued over ~5 hours; 4 clients degraded.

Clarion config: [[payer_configs/aetna-config]] (dual CA bundle, exponential-backoff retry, cached-eligibility fallback with 24h TTL — made permanent 2026-07-28).
