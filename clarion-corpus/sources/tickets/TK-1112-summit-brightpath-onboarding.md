---
id: src021
type: ticket
date: 2026-05-18
title: "TK-1112: Summit — BrightPath pilot connector setup"
ticket: TK-1112
status: resolved
opened: 2026-05-18
resolved: 2026-08-01
assignee: "[[people/marcus-webb]]"
reporter: "[[people/dana-ortiz]]"
client: "[[clients/summit-behavioral-health]]"
payer: "[[payers/brightpath]]"
participants: ["[[people/marcus-webb]]", "[[people/jake-osei]]", "[[people/dana-ortiz]]"]
---

# TK-1112: Summit — BrightPath pilot connector setup

**Opened by Dana Ortiz, 2026-05-18** — engineering tracker for the pilot decided at the 5/6 ops sync.

> Scope: FHIR R4 connector against BrightPath's pilot API — claim submission + claim status resources only, eligibility explicitly out of pilot scope. Summit Behavioral Health volume only. Target: sandbox certification Jul 15, production go-live Aug 1.

## Comments

**Marcus Webb — 2026-06-02 11:05**
Sandbox access provisioned. Their FHIR conformance statement is actually accurate, which is a pleasant surprise. Building submission first, status polling second. Version-pinning the API per the kickoff doc (they reserve 30-day-notice changes).

**Dana Ortiz — 2026-06-10 09:30**
Summit BAA amendment fully signed as of today (Elena's compliance review done last week). Contract-side blocker cleared.

**Marcus Webb — 2026-07-12 17:48**
Sandbox certification PASSED — all 14 of BrightPath's certification scenarios green on the first formal run. Three days ahead of the Jul 15 target.

**Jake Osei — 2026-07-30 15:10**
BrightPath payer config live: routing rule for Summit tax IDs, status-poll schedule (15-min cycle), alerting on submission failures + status latency. Go/no-go with Dana tomorrow.

**Marcus Webb — 2026-08-01 10:02**
Production go-live complete. First 9 Summit claims submitted via API this morning, all acknowledged in under 10 seconds. Closing; pilot monitoring continues on the eng dashboard through the 90-day review.

## Resolution

Connector certified 7/12, config live 7/30, pilot in production 8/1 limited to Summit per the decision. 90-day review data collection underway.
