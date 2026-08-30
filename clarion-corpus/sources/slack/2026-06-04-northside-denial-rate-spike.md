---
id: src024
type: slack
date: 2026-06-04
title: "#claims-ops: Northside May denial rate 14%?! (report gotcha)"
channel: "#claims-ops"
participants: ["[[people/sofia-chen]]", "[[people/jake-osei]]", "[[people/priya-nair]]", "[[people/dana-ortiz]]"]
---

# #claims-ops — 2026-06-04 (thread ran through 06-08)

**Sofia Chen** [09:05]
Drafting the May MBR and I need someone to sanity-check this before I panic: [[clients/northside-clinic]] May denial rate is coming out at **14.3%**. April was 8.1%. Nothing in their submission mix changed that I can see. That's almost a doubling??

**Dana Ortiz** [09:12]
please do not send that number anywhere yet — Luis will escalate to his CFO within the hour if he sees 14%. is it real?

**Sofia Chen** [09:15]
that's what im trying to find out. remits look… normal? the raw CARC counts don't feel like a doubling. something's off between the raw data and the mart

**Priya Nair** [09:22]
Gut check from the queue: I have NOT seen a Northside denial wave in daily work. If denials doubled, ops would have felt it. I'd suspect the report before the claims.

**Jake Osei** [10:03]
hmm. this smells like the May release — 2026.05.12 changed the internal claim status enum and I remember the reporting mart mapping table being on the "verify later" list :grimacing: let me diff the mart counts against raw 835 CARCs

**Jake Osei** [10:05]
(if I'm right, "denials" in the mart now includes things that aren't denials)

**Sofia Chen** [10:08]
that would explain why the raw CARCs don't match. holding the MBR. TK-1102 opened for the investigation

**Jake Osei** [16:42] *(2026-06-08)*
Confirmed. The 5/12 release renamed claim states, and the mart mapping was never updated — `pended_payer_request` and `awaiting_attachment` both fell through to `denied_other`. Every pend counted as a denial for May. Northside's true May denial rate recomputes to **~8.2%**, right in line with April. Fix + backfill in review, postmortem to follow.

**Sofia Chen** [16:50]
so the "spike" is pends being miscounted. THANK YOU. re-running the MBR on corrected data — Dana, corrected version to Luis by Thursday with a one-line note about the reporting fix.

**Priya Nair** [16:55]
Good catch all around. Rule for next time: when a rate doubles with no operational signal, suspect the pipeline first, page the client second (i.e., never).
