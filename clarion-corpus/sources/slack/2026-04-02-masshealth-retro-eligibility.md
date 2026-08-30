---
id: src012
type: slack
date: 2026-04-02
title: "#claims-ops: MassHealth retro-eligibility rebill process"
channel: "#claims-ops"
participants: ["[[people/tom-reyes]]", "[[people/priya-nair]]", "[[people/dana-ortiz]]"]
---

# #claims-ops — 2026-04-02

**Tom Reyes** [13:32]
question for the group: [[clients/harbor-family-medicine]] has a claim we denied-out in Feb — patient had no coverage on the date of service. Amy just told Dana the patient got approved for [[payers/masshealth]] *retroactively* last week, coverage backdated to January. can we… rebill that? how does that even work

**Dana Ortiz** [13:36]
+1 want to know too, Amy's asking whether to resubmit on their side or whether we handle it

**Priya Nair** [14:05]
We handle it. This is retro-eligibility, it comes up a few times a quarter with MassHealth-heavy panels. Process:

1. First verify the retroactive coverage span in EVS/MMIS — you need to see the eligibility segment actually covering the DOS before touching the claim. Don't trust the phone answer, pull the span.
2. Then submit a **new** claim, not an adjustment — the original was denied for no coverage, there's nothing to adjust.
3. Timely filing runs from the eligibility **determination date**, not the date of service. You get 90 days from the determination date to submit, and the remit will process clean against the retro span. No attachment is needed when EVS shows the span — the eligibility record itself is the proof.

**Tom Reyes** [14:09]
determination date = the date MassHealth approved the retro coverage? where do i find that

**Priya Nair** [14:12]
Yes. It's on the eligibility determination letter the member gets, and the EVS span record carries it. For the Harbor one: determination was 3/28, so the clock runs to late June. Plenty of time.

**Priya Nair** [14:15]
Honestly I'm the only one who's done these end to end — one of these days we should write the process down properly :sweat_smile: until then, grab me before submitting, the EVS span check has a couple of gotchas with span segments.

**Tom Reyes** [14:18]
noted lol. filing a ticket for the Harbor claim so this has a paper trail

**Dana Ortiz** [14:20]
telling Amy we've got it — thanks P :pray:
