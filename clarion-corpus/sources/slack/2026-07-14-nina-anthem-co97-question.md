---
id: src032
type: slack
date: 2026-07-14
title: "#claims-ops: Nina — Anthem CO-97 on PT claims, what's the fix? (re-ask)"
channel: "#claims-ops"
participants: ["[[people/nina-park]]", "[[people/tom-reyes]]", "[[people/priya-nair]]"]
---

# #claims-ops — 2026-07-14

**Nina Park** [11:12]
week-2 question :raising_hand: I picked up a [[clients/lakeview-orthopedics]] PT claim denied CO-97 by [[payers/anthem]] — same-day 97110+97140. [[docs/sop-denial-management]] §4 says append modifier 59 for distinct services, so I prepped a corrected claim with 59… and the resubmission preview flagged it would likely deny again? What am I missing?

**Tom Reyes** [11:20]
ah you've hit the famous one. the SOP is out of date for Anthem specifically — since their March edit update plain 59 doesn't clear their PTP edits anymore. you need the **X-subset modifier (XS)** on the column-2 line (the 97110 here) + a distinct-site documentation pointer in the note. the scrubber actually auto-swaps it now for the configured pairs, which is why the preview flagged your manual 59

**Nina Park** [11:24]
that explains it — the preview was protecting me from the SOP :melting_face: is the X-subset thing written anywhere I should've looked?

**Tom Reyes** [11:27]
…slack threads from March and two ticket resolutions (TK-1041, TK-1077). so, no, not really written anywhere a new person would look

**Priya Nair** [11:41]
And that's the problem in one screenshot. Nina, you did the right thing — followed the doc, hit the wall, asked. For the record this is at least the **fourth time this year** someone's needed the Anthem X-subset answer (Tom in March, Karen via ticket, Dana on the Vik call, now Nina). SOP-002 §4 still says the pre-March thing. The config auto-swap catches the configured pairs, but humans keep needing the *why*. Adding the SOP-002 update to the doc-debt list… again.

**Nina Park** [11:44]
for what it's worth, a two-line box in the SOP ("Anthem: use XS on column-2, not 59 — see anthem config") would've saved me a day :sweat_smile:

**Priya Nair** [11:45]
Noted, and you writing that box might be the fastest path to it existing :eyes:
