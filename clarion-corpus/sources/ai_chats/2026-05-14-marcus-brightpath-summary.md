---
id: src020
type: ai-chat
date: 2026-05-14
title: "AI chat: Marcus — summarize BrightPath pilot decision for eng kickoff"
participants: ["[[people/marcus-webb]]"]
assistant: clarion-copilot
---

# AI chat — 2026-05-14 (Marcus Webb × Clarion Copilot)

**Marcus Webb [09:40]:**
what exactly did we commit to on the brightpath pilot? writing the eng kickoff doc and want the decision terms right

**Clarion Copilot [09:40]:**
From the 2026-05-06 ops sync ([[meetings/2026-05-06-ops-sync]]), decision by Grace Kim: run the [[payers/brightpath]] pilot in Q3, limited to [[clients/summit-behavioral-health]] claims only, revisit at 90 days with adjudication data before widening. Rationale recorded: bounded downside (one client, revenue-neutral pilot pricing), counterparty validated by Vik Malhotra's April assessment, strategic read on API-first claims flow.

Your committed deliverable: FHIR R4 connector (claim submission + status resources, eligibility out of pilot scope), sandbox certification by Jul 15. Related: Dana owns the Summit BAA amendment (Jun 15), Jake owns payer config + monitoring (Jul 31) for an Aug 1 go-live.

**Marcus Webb [09:44]:**
good. flagging in the doc that their contract lets them change the API on 30 days notice per vik, so we version-pin and keep the adapter thin

**Clarion Copilot [09:44]:**
That caveat is in the Vik call notes ([[expert_calls/2026-04-14-vik-malhotra-payer-ops]]) — citing it in the kickoff doc is consistent with the record.
