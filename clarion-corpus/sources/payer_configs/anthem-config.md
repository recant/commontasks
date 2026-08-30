---
id: src031
type: payer-config
date: 2026-06-30
title: "Payer config: Anthem (anthem.yaml) — line split + X-subset modifier rules"
payer: "[[payers/anthem]]"
maintainer: "[[people/jake-osei]]"
last_changed_by: "[[people/marcus-webb]]"
participants: ["[[people/marcus-webb]]", "[[people/jake-osei]]"]
---

# Payer config: Anthem (`anthem.yaml`)

Scrubber + submission configuration for [[payers/anthem]]. Full config below; the raw file lives beside this page as `anthem.yaml`.

Key behaviors: `anthem_line_split` keeps multi-unit therapy lines under Anthem's manual-review unit threshold, and `modifier_rules.prefer_x_subset` auto-swaps generic modifier 59 to the specific X-subset modifier on configured NCCI PTP pairs (column-2 line placement per [[topics/modifier-59]]).

```yaml
payer: anthem
payer_id: "660"
connection:
  clearinghouse_route: primary
  submission_cycle: "18:00 America/New_York"

edits:
  anthem_line_split: true          # split multi-unit therapy lines
  max_units_per_line: 4            # stay under ClaimsXten manual-review threshold
  split_codes: ["97110", "97112", "97140", "97530"]

modifier_rules:
  prefer_x_subset: true            # swap generic 59 -> specific X modifier
  placement: column_2_line         # X modifier must ride the column-2 code of the PTP pair
  require_doc_pointer: true        # claim note must carry distinct-site documentation pointer
  ptp_pairs:                       # per-pair configurable (per Vik: expect Q4 expansion)
    - {column_1: "97140", column_2: "97110", swap_to: "XS"}
    - {column_1: "97140", column_2: "97112", swap_to: "XS"}
    - {column_1: "97530", column_2: "97110", swap_to: "XS"}

reconsideration:
  window_days: 120                 # per SOP-007 §3
  channel: availity_portal

changelog:
  - date: 2026-06-30
    by: marcus.webb
    note: >
      Enabled anthem_line_split + prefer_x_subset (QBR commitment to Lakeview,
      due 6/30 — delivered on time). Pairs table seeded from March denial data;
      per-pair structure so Q4 edit expansions are config-only changes.
  - date: 2026-03-05
    by: jake.osei
    note: Initial config split out of the monolithic payer file.
```
