---
id: src019
type: ai-chat
date: 2026-04-08
title: "AI chat: Sofia — CARC CO-97 vs CO-4 meaning"
participants: ["[[people/sofia-chen]]"]
assistant: clarion-copilot
---

# AI chat — 2026-04-08 (Sofia Chen × Clarion Copilot)

**Sofia Chen [10:11]:**
For the March MBR I need to explain the denial mix shift. Difference between CO-97 and CO-4 in plain english?

**Clarion Copilot [10:11]:**
From the CARC triage table in [[docs/sop-denial-management]]:
- **CO-97** — the benefit for this service is included in another service already adjudicated: the payer considers it bundled. The March spike on [[payers/anthem]] therapy pairs is this code.
- **CO-4** — the procedure code is inconsistent with the modifier used, or a required modifier is missing: a modifier-level problem rather than a bundling determination.

Practical distinction for the MBR: CO-97 says "we won't pay this separately"; CO-4 says "your modifier usage is wrong or absent." The Anthem March denials present as CO-97 because the edit stopped accepting the modifier as a bypass — the modifier isn't invalid (that would be CO-4), it's no longer sufficient.

**Sofia Chen [10:15]:**
perfect, using that framing. thanks
