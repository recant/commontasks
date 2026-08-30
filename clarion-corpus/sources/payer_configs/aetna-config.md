---
id: src041
type: payer-config
date: 2026-07-23
title: "Payer config: Aetna (aetna.yaml) — dual CA bundle, retry, eligibility fallback"
payer: "[[payers/aetna]]"
maintainer: "[[people/jake-osei]]"
participants: ["[[people/jake-osei]]"]
---

# Payer config: Aetna (`aetna.yaml`)

Connectivity + eligibility configuration for [[payers/aetna]], revised after INC-2026-007 ([[postmortems/2026-07-29-aetna-eligibility-outage]]). Raw file beside this page as `aetna.yaml`.

Key behaviors: dual-bundle mTLS trust (survives unannounced CA rotations), exponential-backoff retry (no tight-loop hammering), and the cached-eligibility fallback with a 24-hour freshness TTL and explicit stale labeling.

```yaml
payer: aetna
payer_id: "60054"
connection:
  clearinghouse_route: primary
  submission_cycle: "18:00 America/New_York"

eligibility:
  realtime_270: true
  endpoint: "https://elig.aetna.example/x12/270"
  mtls:
    ca_bundle: dual            # legacy + 2026-07 rotated intermediate CA
    ca_bundle_files: ["aetna-ca-2024.pem", "aetna-ca-2026.pem"]
    chain_change_alert: true   # cert-chain monitoring (added 2026-07-24, all payers)
  retry:
    policy: exponential_backoff
    base_ms: 400
    max_attempts: 4
    jitter: true
  fallback:
    cached_271: true           # serve last good 271 when live check fails
    ttl_hours: 24              # freshness window for cached responses
    label_stale: true          # UI must mark cached results as cached
    queue_batch_270: true      # failed checks re-run on the overnight batch

changelog:
  - date: 2026-07-23
    by: jake.osei
    note: >
      INC-2026-007 remediation: dual-bundle trust (new intermediate fingerprint
      verified out-of-band), tight-loop retry replaced with exponential backoff,
      cached-271 fallback formalized at 24h TTL with stale labeling and
      overnight batch queue. Reviewed by marcus.webb.
  - date: 2026-02-10
    by: jake.osei
    note: Initial split from monolithic payer file; realtime 270/271 enabled.
```
