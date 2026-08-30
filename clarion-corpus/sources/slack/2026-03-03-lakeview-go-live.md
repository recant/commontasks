---
id: src009
type: slack
date: 2026-03-03
title: "#client-success: Lakeview Orthopedics go-live"
channel: "#client-success"
participants: ["[[people/dana-ortiz]]", "[[people/priya-nair]]", "[[people/marcus-webb]]", "[[people/grace-kim]]"]
---

# #client-success — 2026-03-03

**Dana Ortiz** [09:12]
:tada: [[clients/lakeview-orthopedics]] is LIVE as of last night. First production batch went out on the 6pm cycle yesterday — 412 claims submitted, zero front-end rejections. Karen said the go-live call was "the smoothest vendor cutover we've done." Huge thanks to everyone who pitched in on the crosswalk.

**Grace Kim** [09:20]
Amazing work team. 14-provider ortho group is exactly the segment we want more of. What payer mix are we looking at?

**Dana Ortiz** [09:24]
Mostly [[payers/anthem]] (~55% of volume), then [[payers/unitedhealth]] and a bit of [[payers/masshealth]] for the PT side. Their PT department is busy — lots of 97110/97140 therapy pairs.

**Marcus Webb** [09:31]
one integration note: their PM system exports CPT units in a weird nested field, we flatten it in the adapter. watch multi-unit therapy lines for the first few weeks, that's the spot most likely to act up

**Priya Nair** [09:38]
Will keep an eye on the denial queue as remits start landing. Ortho + PT with heavy Anthem is a combo where edit behavior matters a lot — first remits should tell us within two weeks.

**Dana Ortiz** [09:41]
Karen Doyle is the office manager and our day-to-day contact — she's sharp and responsive, let's keep her that happy :crossed_fingers:

**Grace Kim** [09:44]
:clap: :clap: put a go-live recap in the Friday update pls
