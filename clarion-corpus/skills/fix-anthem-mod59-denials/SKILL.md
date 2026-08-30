---
id: skl_anthem_mod59
type: skill
name: fix-anthem-mod59-denials
description: Clear an Anthem CO-97 denial on same-day therapy pairs (post-March-2026 X-subset rules).
derived_from: ["[[slack/2026-03-18-anthem-mod59-denials]]", "[[expert_calls/2026-04-14-vik-malhotra-payer-ops]]", "[[payer_configs/anthem-config]]", "[[tickets/TK-1041-lakeview-anthem-mod59-batch]]"]
status: current
---

# Skill: fix-anthem-mod59-denials

**When to use:** an [[payers/anthem]] claim with same-day NCCI PTP therapy pairs (e.g. 97140 + 97110) denies **CO-97** despite modifier 59.

**Why it happens:** since Anthem's March 2026 ClaimsXten release, generic modifier 59 no longer bypasses their PTP edits ([[topics/modifier-59]]). Confirmed independently by [[people/priya-nair]] (remit analysis) and [[people/vik-malhotra]] (ex-Anthem).

## Steps

1. Confirm the pattern: CO-97, same-day PTP pair, modifier 59 on the claim.
2. Verify documentation supports a **distinct anatomic site** — if it doesn't, the denial is correct; write off per [[docs/sop-denial-management]].
3. Corrected claim: replace 59 with the **X-subset modifier (usually XS)** on the **column-2 code line** — an X modifier on the column-1 line does nothing.
4. Add a distinct-site **documentation pointer** in the claim note (the edit re-fires without it).
5. Multi-unit lines: keep ≤4 units/line (the scrubber's `anthem_line_split` handles this automatically for configured codes — see [[payer_configs/anthem-config]]).
6. Resubmit on the nightly cycle; corrected claims typically clear on the next remit (TK-1041: 54/61 paid within two weeks).

**Prevention:** `prefer_x_subset` in anthem.yaml auto-swaps configured pairs; hand-keyed client claims still need biller training (see the Northside recurrence, TK-1077).

**Heads-up:** Vik expects Anthem to widen X-subset enforcement in the Q4 edit release — new failing pairs belong in the config's `ptp_pairs` table, not in one-off rebills.
