---
id: pay_anthem
type: payer
name: Anthem
---

# Anthem

Commercial payer. March 2026 ClaimsXten edit update stopped honoring generic modifier 59 on NCCI PTP pairs — the root of the [[topics/modifier-59]] denial spike at [[clients/lakeview-orthopedics]] and [[clients/northside-clinic]]. Requires the specific X-subset modifier (usually XS) on the column-2 code line.

Clarion config: [[payer_configs/anthem-config]] (`anthem_line_split: true`, `prefer_x_subset: true`, updated 2026-06-30).
