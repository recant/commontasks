---
id: src027
type: ticket
date: 2026-06-08
title: "TK-1102: Reporting — May denial-rate discrepancy investigation"
ticket: TK-1102
status: resolved
opened: 2026-06-08
resolved: 2026-06-11
assignee: "[[people/jake-osei]]"
reporter: "[[people/sofia-chen]]"
client: "[[clients/northside-clinic]]"
participants: ["[[people/sofia-chen]]", "[[people/jake-osei]]"]
---

# TK-1102: Reporting — May denial-rate discrepancy investigation

**Opened by Sofia Chen, 2026-06-08:**

> Mart-computed May denial rates disagree with raw 835 CARC counts across clients — most visibly Northside (mart says 14.3%, raw CARCs suggest ~8%). MBRs are HELD until this reconciles. Need root cause and a corrected backfill.

## Comments

**Jake Osei — 2026-06-08 14:20**
Reproduced. Mart "denied" count for Northside May = 402 claims; raw 835s show 231 claims with CO/PR denial CARCs. The 171-claim difference matches the count of claims sitting in pend states. Pulling the mart mapping table history.

**Jake Osei — 2026-06-08 16:35**
Root cause: release 2026.05.12 renamed the internal claim-state enum. The mart mapping table wasn't updated, so `pended_payer_request` and `awaiting_attachment` fell through the mapping's default branch into `denied_other`. Every pend counted as a denial from 5/12 onward.

**Jake Osei — 2026-06-09 11:02**
Fix merged: mart mapping v2 with explicit rows for all new state names and a **fail-loud default** (unknown state = pipeline error, not a silent bucket). Backfill of May running now.

**Jake Osei — 2026-06-10 09:40**
Backfill complete + regression test added (report totals vs raw CARC counts, tolerance 0.2%, runs on every release). Postmortem published. Handing back to Sofia for the corrected MBR.

**Sofia Chen — 2026-06-11 10:15**
Corrected MBR generated — Northside May true rate 8.2%. Sent to Dana for client delivery with the reporting-fix note. Closing.

## Resolution

Mart mapping regression from release 2026.05.12 (pends counted as denials). Mapping v2 + fail-loud default + backfill + release regression test. Corrected MBR issued 6/11.
