---
id: src035
type: meeting
date: 2026-07-16
title: "Attachment strategy sync — no decision; tabled to Q4 planning"
participants: ["[[people/priya-nair]]", "[[people/marcus-webb]]", "[[people/tom-reyes]]", "[[people/jake-osei]]", "[[people/dana-ortiz]]"]
---

# Attachment strategy sync — 2026-07-16

**Attendees:** Priya, Marcus, Tom, Jake, Dana (notes)
**Purpose:** Decide the [[payers/masshealth]] attachment strategy raised in #eng-platform 7/9.

## Framing (Tom)

Backlog trend: 55–65 pends/week through spring, 70+ the last two weeks, heaviest for [[clients/harbor-family-medicine]]. Current process is SOP-011 manual (~9 hrs/week and growing with volume).

## Position A — API-pull responder (Marcus)

Build the electronic path: consume the 277 RFI, auto-match the claim, pull documentation from the client chart export, submit via the 275 transaction, log acks. Estimate: **2 sprints**. Marginal cost per pend after build near zero; removes the manual hours entirely; every response logged and queryable. "We are a claims automation company; our attachment answer cannot be a fax machine."

## Position B — proactive attach at submission (Priya)

Prevent the pend instead of answering it faster: the attachment-triggering claim types are predictable (therapy progress notes, TPL forms), so attach documentation proactively at submission for those types — by fax today, zero build. The pend cycle costs clients 3–6 weeks of payment delay per claim; prevention removes that delay entirely. Against the API path: MassHealth's electronic attachment intake is unreliable — Jake's own June testing showed silent drops over 8MB and acks that don't confirm claim-linkage; two June responses were received-but-never-linked.

## Discussion (recorded without resolution)

- Marcus on B: proactive attaching sends documents for the ~80% of flagged claims that would never pend — wasted handling and a permanent fax dependency.
- Priya on A: a responder still leaves the client waiting out the pend cycle, and builds on an intake that loses documents.
- Jake (neutral, technical): both failure modes are real; the 275 intake issues are payer-side and not on any published fix timeline.
- Dana (client lens): Harbor feels the delay acutely; either path beats the status quo — but she has no basis to pick between them.

## Outcome

**No decision.** Neither position moved. Given Q3 engineering capacity is committed (BrightPath pilot, Northside API), the strategy question is **tabled to Q4 planning** with a cost workup assigned to no one yet. Interim: SOP-011 manual process continues unchanged.

## Unrelated item recorded for the ops log (Priya)

MassHealth's **July 1 All-Provider Bulletin** changed retro-eligibility resubmissions: replacement claims must now carry **delay-reason code 9** and attach the **eligibility determination letter** — EVS span alone no longer suffices as proof. This supersedes our pre-July practice (no attachment when EVS showed the span). The 90-day window from the determination date is unchanged. Tom to apply on the next retro case; yet another reason to finally write the retro doc.
