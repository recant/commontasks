---
id: src023
type: ticket
date: 2026-05-27
title: "TK-1088: Lakeview — $38,450 arthroscopy claim stuck (CO-197 prior auth)"
ticket: TK-1088
status: resolved
opened: 2026-05-27
resolved: 2026-08-14
assignee: "[[people/priya-nair]]"
reporter: "[[people/karen-doyle]]"
client: "[[clients/lakeview-orthopedics]]"
payer: "[[payers/anthem]]"
participants: ["[[people/karen-doyle]]", "[[people/priya-nair]]", "[[people/tom-reyes]]"]
---

# TK-1088: Lakeview — $38,450 arthroscopy claim stuck (CO-197 prior auth)

**Reported via client portal by Karen Doyle ([[clients/lakeview-orthopedics]]), 2026-05-27:**

> Claim CLM-2026-18874 — shoulder arthroscopy with rotator cuff repair (CPT 29827), DOS 2026-04-22, billed $38,450 to [[payers/anthem]]. We HAD prior authorization for this surgery; the EOB dated 5/20 says CO-197, authorization absent. This is the biggest claim of our quarter and the surgeon is asking about it weekly. Please treat as urgent.

## Comments

**Tom Reyes — 2026-05-27 15:35**
Confirmed auth AUTH-88231-A exists in the payer portal, dated 4/10, for CPT 29827. So the denial isn't "no auth" — something about the match failed. Escalating to Priya.

**Priya Nair — 2026-05-29 10:12**
Found it. The authorization was issued under Lakeview's **group** NPI, but the claim went out with the **rendering** surgeon's NPI in the billing loop the auth-match reads. Per the CO-197 guidance in [[docs/sop-denial-management]] — verify the authorization was issued under the same NPI billed. Classic mismatch. Fix: corrected claim carrying the auth number explicitly, with the billing configuration matched to how the auth was issued.

**Priya Nair — 2026-06-04 09:41**
Corrected claim submitted 6/2. Also requested a reprocessing review with our Anthem provider-rep contact so this doesn't sit in the standard queue behind the correction.

**Priya Nair — 2026-06-24 14:30**
Status for today's QBR: Anthem confirms the corrected claim is in adjudication with the auth matched. No payment date committed. Karen is (reasonably) unhappy with the cycle time.

**Priya Nair — 2026-07-22 11:15**
Anthem rep says reprocessing was queued behind a system migration on their side. Chasing weekly. This is now a 3-month-old claim.

**Tom Reyes — 2026-08-14 16:44**
PAID on today's remit: $36,912 allowed (contractual adjustment $1,538), auth matched, no further denial codes. Karen notified by Dana same day. Closing.

## Resolution

Root cause: auth issued under group NPI vs rendering NPI on the claim — CO-197 mismatch. Corrected claim (6/2) + provider-rep reprocessing escalation; paid 2026-08-14, $36,912.
