---
id: src040
type: ticket
date: 2026-07-22
title: "TK-1121: Backfill queued eligibility checks after Aetna outage"
ticket: TK-1121
status: resolved
opened: 2026-07-22
resolved: 2026-07-23
assignee: "[[people/jake-osei]]"
reporter: "[[people/tom-reyes]]"
payer: "[[payers/aetna]]"
parent: TK-1119
participants: ["[[people/jake-osei]]", "[[people/tom-reyes]]"]
---

# TK-1121: Backfill queued eligibility checks after Aetna outage

**Opened by Tom Reyes, 2026-07-22 08:40** — child of TK-1119. All eligibility checks that failed or queued during INC-2026-007 need re-running so today's schedules and pending claims aren't sitting on stale or missing eligibility.

## Comments

**Jake Osei — 2026-07-22 09:15**
Overnight batch 270 run completed against the still-degraded endpoint using the workaround path: **2,347 queued checks processed, 2,306 returned clean 271s**. The remaining 41 are members whose cached data was older than the 30-day window — flagged `stale-eligibility` on the affected claims so ops re-verifies before release.

**Tom Reyes — 2026-07-23 10:05**
Worked the 41 flagged claims this morning post-fix: all re-verified against the live endpoint, 39 clean, 2 legitimately termed coverage (routed to normal ineligible workflow — they'd have failed anyway, at least now we know before submission). Queue is zero. Closing.

## Resolution

2,347 queued checks backfilled (2,306 clean overnight; 41 flagged stale re-verified live on 7/23; 2 true terminations routed normally). No claim released on stale eligibility.
