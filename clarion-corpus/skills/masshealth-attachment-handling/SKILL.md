---
id: skl_masshealth_attachments
type: skill
name: masshealth-attachment-handling
description: Handle a MassHealth attachment pend under today's manual process (the future strategy is undecided).
derived_from: ["[[docs/sop-claim-attachments]]", "[[meetings/2026-07-16-attachment-strategy-sync]]", "[[tickets/TK-1063-harbor-masshealth-retro]]"]
status: current
---

# Skill: masshealth-attachment-handling

**When to use:** a [[payers/masshealth]] claim sits in `pended_payer_request` / `awaiting_attachment` with a 277 RFI.

> **Strategy status — read this first:** the long-term approach (API-pull responder vs proactive attach-at-submission) is **an open, undecided question**, debated 7/9 and 7/16 and tabled to Q4 planning ([[topics/attachments-masshealth]]). This skill documents only the current SOP-011 manual process. Do not represent either proposal as the chosen direction.

## Steps (current process, per [[docs/sop-claim-attachments]])

1. Work the pend queue daily; calendar the deadline — documentation is due **within 10 business days of the RFI date**.
2. Read the 277 RFI for the requested document type (commonly therapy progress notes, TPL forms, eligibility determination letters).
3. Deliver: payer portal upload where supported, otherwise **fax with the standard cover sheet**, claim ID on every page.
   - Electronic 275 caution (Jake's June testing): attachments >8MB drop silently and acks don't confirm claim-linkage — fax confirmations are dumber but unambiguous.
4. Log the **attachment control number** on the ticket before closing the pend task.
5. Retro-eligibility claims (since the 2026-07-01 bulletin): the determination letter must be attached **at submission** with delay-reason code 9 — see [[topics/retro-eligibility]] and loop in [[people/priya-nair]].
6. Same document type pending repeatedly for one client → flag the pattern to Priya + the CSM instead of answering pends one at a time.
