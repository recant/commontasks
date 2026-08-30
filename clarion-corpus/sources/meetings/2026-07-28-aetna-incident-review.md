---
id: src042
type: meeting
date: 2026-07-28
title: "Aetna outage incident review (INC-2026-007) — decision: permanent cached-eligibility fallback"
participants: ["[[people/jake-osei]]", "[[people/marcus-webb]]", "[[people/elena-vasquez]]", "[[people/dana-ortiz]]", "[[people/priya-nair]]"]
---

# INC-2026-007 incident review — 2026-07-28

**Attendees:** Jake (incident lead), Marcus, Elena, Dana, Priya
**Notes:** Elena · Postmortem doc to follow 7/29 (Jake)

## 1. Incident recap (Jake)

Final numbers for the record: [[payers/aetna]] real-time eligibility degraded **2026-07-21 from 09:14 to the 14:20 workaround** (~5 hours), peaking at a 61% timeout rate. **2,347 eligibility checks failed or were queued**; four clients' front-desk workflows degraded (Harbor hit hardest, plus Northside, Lakeview, Riverbend). Zero claims released on stale eligibility, zero PHI exposure. Root cause: Aetna rotated the intermediate CA on their mTLS eligibility endpoint without trading-partner notice, and our pinned single-CA bundle correctly-but-unhelpfully rejected the new chain.

## 2. What held up / what didn't

- **Held:** alerting caught it in minutes; the cached-271 workaround restored front desks within ~5 hours; the overnight backfill cleared the queue with no stale releases.
- **Didn't:** we had no cert-chain monitoring, so the first signal was user-facing timeouts rather than a chain-change alert; the tight-loop retry amplified load during the failure.

## 3. Decision

**DECISION (Jake proposing, Marcus + Elena concurring, recorded by Elena):** The cached-eligibility fallback becomes a **permanent, always-on capability** rather than an incident workaround — cached 271 served automatically when a live check fails, **24-hour freshness TTL**, and a visible **stale flag in the UI** so front desks always know they're seeing cached data. Rationale: the outage proved graceful degradation is the difference between a 5-hour inconvenience and a lost clinic day; payer-side failures are a when, not an if.

Priya's ops caveat, accepted into the decision: cached eligibility is a front-desk convenience, not a claims-release basis — scrub still requires a live-or-fresh check per SOP-001.

## 4. Action items

| # | Item | Owner | Due | Status at review |
|---|---|---|---|---|
| 1 | Cert-chain monitoring alert, all payer mTLS endpoints | [[people/jake-osei]] | Aug 1 | **done 7/24** (shipped during incident follow-up) |
| 2 | Client-facing outage comms template | [[people/elena-vasquez]] | Aug 1 | **done 7/25** (used retroactively as the INC-007 recap to clients) |
| 3 | Eligibility-cache TTL config rolled out to **all** payers, not just Aetna | [[people/marcus-webb]] | Sep 5 | open |
| 4 | Payer eligibility-outage **runbook** (detection → workaround → comms → backfill) | [[people/jake-osei]] | Aug 15 | open |

## 5. Client-impact postscript (Dana)

All four affected clients received the recap; Harbor's Amy Tran replied "your cached mode saved our afternoon." One cost to log honestly: the outage week consumed the integration capacity that was earmarked for the [[clients/northside-clinic]] eligibility API, pushing that commitment further into September.
