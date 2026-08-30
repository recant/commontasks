---
id: src053
type: slack
date: 2026-08-13
title: "#claims-ops: Whitfield findings — Harbor E/M audit plan"
channel: "#claims-ops"
participants: ["[[people/elena-vasquez]]", "[[people/priya-nair]]", "[[people/sofia-chen]]"]
---

# #claims-ops — 2026-08-13

**Elena Vasquez** [10:20]
Sharing yesterday's coding-review outcome (call notes filed). Headline: Dr. Whitfield's independent 240-encounter sample puts [[clients/harbor-family-medicine]] at **68% level-4 (99214) share vs a ~44% family-medicine benchmark**. Before I open the audit ticket — gut check from this group: does anyone see a reason the 68 number could be an artifact? I'd rather find a sampling hole now than in front of a payer.

**Sofia Chen** [10:41]
checked it against our own claims data just now: full-population billed-code distribution for Harbor established visits YTD = **67.8% at 99214**. his sample matches the population within a rounding error. it's not a sampling artifact, that's just their distribution

**Priya Nair** [10:48]
And it's the same shape I flagged in May from the April data — three independent looks now (my eyeball, Sofia's population number, Whitfield's stratified sample) landing on the same answer. The distribution question is settled; the *documentation* question is what the audit answers. Worth repeating his line: fix the records, not the ratio — nobody blanket-downcodes anything.

**Elena Vasquez** [11:02]
agreed and so recorded. TK-1135 going up today: 60 Harbor encounters, MDM-first scoring per the 2021 guidelines, due Sep 15, Whitfield co-reviews. Sofia — can you pull the stratified sample per his methodology note by end of next week?

**Sofia Chen** [11:05]
yep, stratifying by provider + visit month so no one doc or season dominates. by the 21st

**Elena Vasquez** [11:07]
:white_check_mark: and comms note: Amy hears this from Dana as proactive quality work BEFORE any audit activity touches their charts. no client learns about a compliance review from a records request.
