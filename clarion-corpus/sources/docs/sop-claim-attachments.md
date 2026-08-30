---
id: src007
type: sop
date: 2026-03-10
title: "SOP-011: Claim Attachments Handling"
owner: "[[people/tom-reyes]]"
reviewed_by: "[[people/priya-nair]]"
status: current
participants: ["[[people/tom-reyes]]", "[[people/priya-nair]]"]
---

# SOP-011: Claim Attachments Handling

**Effective:** 2026-03-10 · **Owner:** [[people/tom-reyes]] · **Reviewed by:** [[people/priya-nair]]

## Purpose

Describe the current process for responding to payer requests for additional documentation (attachment pends), primarily from [[payers/masshealth]].

> Scope note: this SOP documents the process as it operates today. It does not prescribe a future attachment strategy; workflow changes are decided in ops/eng planning.

## Current process

1. **Monitor.** Check the pend queue daily for claims in `pended_payer_request` or `awaiting_attachment` status. MassHealth pends currently run roughly 55–65 per week across clients, heaviest for [[clients/harbor-family-medicine]].
2. **Identify the request.** Read the 277 RFI (request for information) to determine the document type requested — commonly therapy progress notes, TPL (third-party liability) forms, or the eligibility determination letter.
3. **Respond within the window.** Requested documentation must be returned within 10 business days of the RFI date; calendar the deadline on the ticket when the pend is first worked.
4. **Delivery method.** Upload via the payer portal where the payer supports it; otherwise fax the documentation with the standard cover sheet, claim ID on every page.
5. **Log it.** Record the attachment control number (portal confirmation or fax confirmation) on the ticket before closing the pend task.
6. **Aging.** Pends older than 7 days appear on the daily aging report; the queue owner chases outstanding documentation from the client.

## Escalation

Repeated pends of the same document type for one client suggest a submission-side gap — flag the pattern to [[people/priya-nair]] and the CSM rather than answering pends one at a time.

## Related

[[docs/sop-claims-intake-scrubbing]] · [[docs/sop-denial-management]]
