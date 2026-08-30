---
id: src018
type: ai-chat
date: 2026-02-20
title: "AI chat: Tom — resubmitting an 837 rejected for NPI mismatch"
participants: ["[[people/tom-reyes]]"]
assistant: clarion-copilot
---

# AI chat — 2026-02-20 (Tom Reyes × Clarion Copilot)

**Tom Reyes [14:22]:**
got a 999 rejection on an 837 batch, says rendering NPI doesn't match enrollment. what's the process for fixing and resending?

**Clarion Copilot [14:22]:**
Per [[docs/sop-claims-intake-scrubbing]] (SOP-001): front-end 837 rejections must be corrected and resubmitted within 2 business days of the rejection notice. For an NPI mismatch specifically: fix at the source — correct the rendering NPI in the client's PM export or the crosswalk mapping, don't hand-edit in the clearinghouse UI. Verify the NPI is active and matches the credentialed record before releasing the corrected batch on the next 6pm cycle.

**Tom Reyes [14:25]:**
its a crosswalk issue, one provider got remapped. thx

**Clarion Copilot [14:25]:**
Noted. Crosswalk fixes go through a config ticket to [[people/jake-osei]] so the correction persists for future batches.
