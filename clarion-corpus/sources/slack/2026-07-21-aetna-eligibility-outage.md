---
id: src038
type: slack
date: 2026-07-21
title: "#incidents: Aetna 270/271 eligibility API failing (INC-2026-007)"
channel: "#incidents"
participants: ["[[people/jake-osei]]", "[[people/marcus-webb]]", "[[people/dana-ortiz]]", "[[people/tom-reyes]]", "[[people/elena-vasquez]]"]
---

# #incidents — 2026-07-21 (INC-2026-007)

**Jake Osei** [09:14]
:warning: alerts firing on the [[payers/aetna]] real-time eligibility connection — 270/271 requests timing out. Error rate climbing fast, currently ~40% and rising. Investigating.

**Jake Osei** [09:31]
now at **61% timeout rate** and holding. Other payer connections are clean — this is Aetna-specific. Front-end eligibility panels will be showing spinners/errors for Aetna members.

**Dana Ortiz** [09:40]
confirming client impact: [[clients/harbor-family-medicine]] front desk just called — they can't verify Aetna patients at check-in. expect the same from [[clients/northside-clinic]], [[clients/lakeview-orthopedics]], [[clients/riverbend-imaging]] as morning schedules fill

**Jake Osei** [10:02]
declaring a formal incident: **INC-2026-007**, sev-2. TK-1119 opened as master ticket. I'm on it full time, Marcus looped in.

**Jake Osei** [11:45]
root cause hypothesis: it's not capacity, it's the **TLS handshake**. Their endpoint started presenting a cert chain with a different intermediate CA than the one in our pinned bundle — handshake fails, we time out on retry loops. Looks like Aetna rotated their intermediate CA without notice.

**Marcus Webb** [12:30]
confirmed from the packet capture — mTLS handshake failing on chain validation, our side rejects. this is exactly the failure mode cert pinning buys you when the payer doesn't announce rotations :upside_down_face: options: trust the new chain (verify fingerprint out-of-band first) and/or serve cached eligibility while we fix

**Jake Osei** [14:20]
**workaround live:** eligibility panel now serves the most recent cached 271 response when it's ≤30 days old (clearly labeled as cached), and all failed checks are queued for an overnight batch 270 run. Front-desk workflows are functional again. Error alerts quieted.

**Elena Vasquez** [14:55]
client comms: outage notice + workaround explanation went to all four affected clients at 14:47 (Dana delivered by phone to Harbor, they were hit hardest). No PHI exposure in this incident — connectivity only.

**Jake Osei** [16:50]
Aetna provider-tech line acknowledged the CA rotation on their side ("planned maintenance, notification may not have reached all trading partners" :expressionless:). Permanent fix plan for tomorrow: dual-bundle trust (old + new CA, fingerprint-verified) + retry with exponential backoff instead of the tight loop. Will run the queued backfill tonight — tracking in TK-1121.

**Tom Reyes** [17:02]
front desks confirmed working on cached mode at Harbor + Northside. quiet on the phones finally
