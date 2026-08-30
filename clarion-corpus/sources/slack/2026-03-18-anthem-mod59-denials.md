---
id: src010
type: slack
date: 2026-03-18
title: "#claims-ops: Anthem CO-97 denial spike on PT claims (mod 59)"
channel: "#claims-ops"
participants: ["[[people/tom-reyes]]", "[[people/priya-nair]]", "[[people/sofia-chen]]", "[[people/jake-osei]]"]
---

# #claims-ops — 2026-03-18

**Tom Reyes** [10:04]
seeing a weird spike in [[payers/anthem]] denials on [[clients/lakeview-orthopedics]] PT claims since around 3/12. all CO-97, all the 97110 + 97140 same-day pairs. we billed these with modifier 59 like always?? anyone know whats going on

**Sofia Chen** [10:19]
Pulled the numbers: 61 Anthem CO-97 denials on Lakeview therapy pairs over the last 3 remit days, $9,438 billed. Same claim shapes were paying fine in early March. [[clients/northside-clinic]] shows the same pattern starting this week, smaller volume.

**Tom Reyes** [10:21]
so not a Lakeview data issue then. same claims, same modifiers, suddenly denying

**Priya Nair** [10:47]
OK I've seen this movie. Anthem pushed a ClaimsXten edit update this month — as of the March release, generic modifier 59 no longer bypasses their NCCI PTP edits. For the 97140 + 97110 pair you have to use the specific X-subset modifier instead — XS (separate structure) is the right one for distinct anatomic sites, and it needs to go on the column-2 code line, not the column-1 line.

**Priya Nair** [10:49]
Also make sure the claim note carries a documentation pointer supporting the distinct site — Anthem's edit will re-fire on resubmission without it. This is exactly the kind of thing they never announce loudly, it was buried in their March provider bulletin.

**Tom Reyes** [10:52]
TIL there are X modifiers :sweat_smile: so rebill the 61 with XS on the 97140 line?

**Priya Nair** [10:55]
Yes — corrected claims, XS on the column-2 line, documentation pointer in the note. Batch them tonight and they should clear. Karen's already asking, there's a ticket coming (TK-1041).

**Jake Osei** [11:10]
platform side: I can add a `prefer_x_subset` rule to the anthem config so the scrubber swaps 59 → XS on known PTP pairs automatically. also been meaning to turn on line splitting for multi-unit therapy lines, Anthem's edits hate those. will scope it

**Priya Nair** [11:14]
Do it — manual rebilling works for this batch but we shouldn't rely on billers remembering X-subset rules forever.

**Sofia Chen** [11:22]
Adding a watch on the CO-97 trend for both clients so we can confirm the fix lands in the remit data.

**Tom Reyes** [16:41]
update: corrected batch went out on tonights cycle. fingers crossed :crossed_fingers:
