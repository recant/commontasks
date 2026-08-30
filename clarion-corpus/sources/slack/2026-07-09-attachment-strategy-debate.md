---
id: src034
type: slack
date: 2026-07-09
title: "#eng-platform: MassHealth pend backlog — API-pull vs proactive fax (debate)"
channel: "#eng-platform"
participants: ["[[people/marcus-webb]]", "[[people/priya-nair]]", "[[people/tom-reyes]]", "[[people/jake-osei]]"]
---

# #eng-platform — 2026-07-09

**Tom Reyes** [09:48]
weekly pend report: [[payers/masshealth]] attachment pends hit **71 this week** — we usually run 55-65. thats ~9 hours of my week reading RFIs, pulling docs, faxing, logging control numbers. per SOP-011. not complaining just… data :melting_face:

**Marcus Webb** [10:02]
this is the thing I keep raising — we should build the API path. MassHealth publishes a 277 RFI electronically and accepts the 275 attachment transaction. We build a puller: RFI comes in, we match the claim, fetch the doc from the client's chart export, submit the 275, log the ack. Two sprints, and Tom's 9 hours become a monitoring dashboard. Responding to pends by fax in 2026 is embarrassing.

**Priya Nair** [10:19]
Respectfully — wrong end of the problem. By the time there's an RFI to respond to, the claim has already been sitting for weeks. The right move is **preventing the pend**: we know which claim types trigger attachment requests (therapy progress notes, TPL forms — it's a predictable list), so attach the documentation proactively at submission. Fax at submission works *today*, no build. And I don't trust MassHealth's electronic attachment intake — I've had submitted docs vanish into the void there this year.

**Marcus Webb** [10:26]
proactively attaching means we send docs for claims that would never have pended — that's wasted handling on ~80% of them. and "fax works today" is how orgs end up with a fax-shaped hole in their architecture for a decade. the API responder is deterministic, logged, and scales past Tom's hours

**Priya Nair** [10:34]
The 80% that never pend cost us a page of fax each. The 20% that do pend cost the client 3-6 weeks of payment delay each — that's the asymmetric side. Prevention beats faster reaction. And it's not nostalgia about fax, it's that their 275 intake *loses documents*, which turns your deterministic pipeline into deterministic resubmissions.

**Jake Osei** [10:52]
data point from my testing in June, no side taken: their 275 endpoint accepts and acks fine in the happy path, but it drops attachments over 8MB silently, and the ack codes don't distinguish "received" from "linked to claim" — two pends we responded to electronically in June show received-but-never-linked. fax confirmations are dumber but unambiguous. both approaches have a real failure mode

**Tom Reyes** [11:05]
so……. which way are we going? asking for my calendar

**Marcus Webb** [11:08]
needs a proper decision with costs on a whiteboard, not a slack scroll. scheduling a sync next week

**Priya Nair** [11:09]
Agreed on that much :handshake:
