---
id: src037
type: ai-chat
date: 2026-07-20
title: "AI chat: Nina — is there a doc for MassHealth retro-eligibility rebills?"
participants: ["[[people/nina-park]]"]
assistant: clarion-copilot
---

# AI chat — 2026-07-20 (Nina Park × Clarion Copilot)

**Nina Park [15:02]:**
I have a claim in my queue denied for no coverage, but there's a note saying the patient got MassHealth retroactively. Is there an SOP for this? I checked the four onboarding SOPs and don't see it.

**Clarion Copilot [15:02]:**
There is **no SOP for retro-eligibility rebills** — you've found one of the documented-as-undocumented processes. What the record shows, assembled from #claims-ops (2026-04-02) and ticket TK-1063:

1. Verify the retroactive coverage span in EVS/MMIS first — the span segment must cover the DOS.
2. Submit a **new** claim (not an adjustment), within **90 days of the eligibility determination date**, not the DOS.
3. As of the July 1 MassHealth bulletin (per the 2026-07-16 sync notes), replacement claims must also carry **delay-reason code 9** and attach the **eligibility determination letter**.

Caution: [[people/priya-nair]] is the only person who has run this end to end, and she has asked (twice, on the record) to be involved before submission — the EVS span reading has known gotchas. She is the right first stop.

**Nina Park [15:06]:**
ok so ask Priya. she's out in August right? what if this comes up while she's on PTO

**Clarion Copilot [15:06]:**
Her PTO is 2026-08-10 → 2026-08-21. There is no documented backup for this process — that gap has been flagged in the ops sync (2026-05-06) but not yet closed. If it can't wait, [[people/tom-reyes]] has done one supervised case (TK-1063) and knows the shape of it, but not the span-reading edge cases.

**Nina Park [15:08]:**
noted, going to Priya now while she's still here. thanks
