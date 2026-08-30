---
id: src055
type: ai-chat
date: 2026-08-12
title: "AI chat: Jake — BrightPath pilot status pull for eng review"
participants: ["[[people/jake-osei]]"]
assistant: clarion-copilot
---

# AI chat — 2026-08-12 (Jake Osei × Clarion Copilot)

**Jake Osei [16:20]:**
pull the brightpath pilot numbers for thursday's eng review — go-live to date

**Clarion Copilot [16:20]:**
[[payers/brightpath]] pilot ([[clients/summit-behavioral-health]] only), production since 2026-08-01 — twelve days in:

- **312 claims** submitted via the FHIR API
- **97.1% auto-adjudicated** without manual touch (9 claims routed to review, all payer-side pend reasons, none connector faults)
- **Median claim-status latency: ~4 seconds**, vs the ~11-day paper/clearinghouse status baseline for regionals
- **Zero submission failures, zero API contract changes** since go-live; monitoring green throughout
- Status polling running on the 15-minute cycle per config

Milestone context: 90-day pilot review lands ~**November 1** per the 5/6 decision — adjudication-quality data through October will drive the widen/hold call.

**Jake Osei [16:24]:**
good. flag for the deck: latency + auto-adjudication both beat the pilot success thresholds we sketched in the kickoff doc

**Clarion Copilot [16:24]:**
Both exceed the kickoff thresholds (auto-adjudication ≥90%, status latency ≤60s). Worth noting in the deck that twelve days is early — the November review remains the decision gate.
