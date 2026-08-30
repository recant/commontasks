---
id: src025
type: ai-chat
date: 2026-06-05
title: "AI chat: Sofia — why would May denial rate jump 6 points?"
participants: ["[[people/sofia-chen]]"]
assistant: clarion-copilot
---

# AI chat — 2026-06-05 (Sofia Chen × Clarion Copilot)

**Sofia Chen [11:30]:**
A client's denial rate jumped from 8.1% to 14.3% month-over-month with no change in submission mix. What are the plausible causes, ranked?

**Clarion Copilot [11:30]:**
Ranked by likelihood given "no change in submission mix":

1. **Reporting/definition change** — did the denial-rate definition, status mapping, or data pipeline change between the two months? A release that alters claim-state semantics can shift the numerator without any real denial change. (There was a platform release on 2026-05-12; I can't see whether it touched reporting.)
2. **Payer edit/policy change** — a payer tightening an edit mid-month (compare CARC distribution by payer; a real edit change concentrates in specific codes, like the March [[payers/anthem]] CO-97 shift).
3. **Client-side data drift** — new provider, new service line, credentialing lapse.
4. **True adjudication change** — rarest for a 6-point single-month move without operational signal.

Discriminating test: reconcile the mart's denial counts against raw 835 CARC counts for both months. If the raw counts don't show the jump, it's #1.

**Sofia Chen [11:34]:**
raw CARCs don't show it. so #1. jake's already diffing the mart. thanks

**Clarion Copilot [11:34]:**
That's consistent with a mapping regression rather than a real denial spike. Hold client-facing numbers until the mart reconciles.
