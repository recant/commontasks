---
id: skl_uhc_appeal_90d
type: skill
name: uhc-appeal-window-90day
description: File a UHC reconsideration using the correct window for the client's contract type (§7.3 for delegated).
derived_from: ["[[expert_calls/2026-08-05-legal-call]]", "[[emails/2026-08-06-rachel-goldman-s73-memo]]", "[[tickets/TK-1130-harbor-uhc-appeal-window]]", "[[docs/sop-timely-filing-appeals]]"]
status: current
---

# Skill: uhc-appeal-window-90day

**When to use:** a [[payers/unitedhealth]] denial needs a reconsideration and the deadline matters — especially anything past day 60.

**The rule (per [[people/rachel-goldman]], 2026-08-05 call + written memo):**

| Contract type | Window | Authority |
|---|---|---|
| **Delegated-credentialing** participation agreement | **90 days** from remittance date | §7.3 of the agreement (controls over the manual) |
| Standard non-delegated | 60 days from remittance date | UHC provider administrative manual (and [[docs/sop-timely-filing-appeals]]) |

⚠️ SOP-007 currently shows only the 60 — it is marked stale for delegated contracts and awaits Elena's update. Do not write off a day-60+ claim before checking contract type.

## Steps

1. **Determine the contract type** for the client (delegated roster is being built per Rachel's memo; until then, ask [[people/elena-vasquez]]).
2. Compute days from the **remittance advice date** (not the worked date).
3. Delegated + ≤90 days → file via the **delegated-portal dispute queue** (the standard queue may auto-reject on the 60-day timer).
4. Cover letter: cite **§7.3 explicitly**, quote the ninety-day language, attach Rachel's memo.
5. Package per SOP-007 §3: remittance copy + corrected claim + cover letter.
6. Past the applicable window → ops-manager approval before write-off, reason logged.

**Precedent:** Harbor's CLM-2026-19882 was filed at day 72 under §7.3 (TK-1130) — a $9,840 write-off avoided.
