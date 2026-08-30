---
id: src039
type: ticket
date: 2026-07-21
title: "TK-1119: INC-2026-007 master — Aetna real-time eligibility outage"
ticket: TK-1119
status: resolved
opened: 2026-07-21
resolved: 2026-07-24
assignee: "[[people/jake-osei]]"
reporter: "[[people/jake-osei]]"
payer: "[[payers/aetna]]"
severity: sev-2
participants: ["[[people/jake-osei]]", "[[people/marcus-webb]]"]
---

# TK-1119: INC-2026-007 master — Aetna real-time eligibility outage

**Opened by Jake Osei, 2026-07-21 10:05** — master ticket for the [[payers/aetna]] 270/271 failure. Live narrative in #incidents; durable record here.

## Comments

**Jake Osei — 2026-07-21 12:40**
Root cause confirmed with Marcus: Aetna rotated the intermediate CA on their eligibility endpoint without trading-partner notice. Our pinned CA bundle rejects the new chain → mTLS handshake failure → timeouts. Scope by end of day: **2,347 eligibility checks failed or queued** between 09:14 and the 14:20 workaround.

**Jake Osei — 2026-07-21 14:25**
Mitigation live: cached-271 fallback (≤30 days, labeled) + overnight batch queue. Backfill tracked in TK-1121.

**Jake Osei — 2026-07-23 11:30**
Permanent fix deployed to aetna.yaml: dual-bundle trust carrying both the legacy and new intermediate CA (new chain fingerprint verified out-of-band against Aetna's published chain), plus retry policy switched to exponential backoff with jitter — no more tight-loop hammering during payer-side failures. Config change reviewed by Marcus.

**Jake Osei — 2026-07-24 10:15**
24 hours on the new bundle: error rate back to baseline (0.3%, normal noise). Also shipped the cert-chain monitoring alert for ALL payer mTLS endpoints (expiry + chain-change detection) — we will never again learn about a CA rotation from a timeout graph. Closing; incident review scheduled 7/28, postmortem to follow.

## Resolution

Unannounced Aetna intermediate-CA rotation vs our pinned bundle. Fixed 7/23 (dual CA bundle + backoff retry); cert-chain monitoring added 7/24 for all payers; review 7/28.
