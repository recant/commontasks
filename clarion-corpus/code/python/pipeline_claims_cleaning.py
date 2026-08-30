#!/usr/bin/env python3
"""pipeline_claims_cleaning.py — claim-intake data-cleaning pipeline (staged).

Author: Jake Osei (platform) · 2026-07-05
Related: SOP-001 (intake & scrubbing), the May reporting postmortem (the
fail-loud stage here exists BECAUSE of that incident).

Stages: normalize → validate → dedupe → map-status. Each stage returns
(clean_rows, rejects) so nothing disappears silently; rejects carry a reason.
Runs standalone on an embedded synthetic batch.
"""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import date

TODAY = date(2026, 8, 30)

# Canonical claim states after release 2026.05.12 (see the June postmortem —
# unknown states must FAIL LOUD, never bucket silently).
STATUS_MAP = {
    "paid": "paid", "denied_carc": "denied", "denied_other": "denied",
    "pended_payer_request": "pend", "awaiting_attachment": "pend",
    "in_process": "in_process", "submitted": "in_process",
}

@dataclass(frozen=True)
class RawClaim:
    claim_id: str
    member_id: str
    npi: str
    cpt: str
    dos: str          # ISO date string as exported by client PM systems
    billed: float
    status: str

BATCH = [
    RawClaim("C-9001", "M0031877", "1234567893", " 99214", "2026-08-10", 182.00, "paid"),
    RawClaim("C-9002", "M0031877", "1234567893", "99214 ", "2026-08-10", 182.00, "paid"),   # true dupe of C-9001
    RawClaim("C-9003", "M0044120", "1093817465", "97110", "2026-08-03", 78.50, "paid"),
    RawClaim("C-9004", "M0044120", "1093817465", "97110", "2026-08-10", 78.50, "paid"),     # SAME member/code/price, DIFFERENT week (legit PT series!)
    RawClaim("C-9005", "M0044120", "1093817465", "97110", "2026-08-17", 78.50, "pended_payer_request"),
    RawClaim("C-9006", "M0090316", "10938174",   "99213", "2026-08-12", 121.00, "submitted"),  # bad NPI (8 digits)
    RawClaim("C-9007", "M0054209", "1447382916", "99395", "2026-09-14", 156.00, "submitted"),  # future DOS
    RawClaim("C-9008", "M0012984", "1447382916", "90460", "2026-08-19", 64.00, "awaiting_attachment"),
    RawClaim("C-9009", "M0067333", "1093817465", "97140", "2026-08-17", 92.00, "denied_carc"),
]

def normalize(rows):
    """Trim whitespace, upper-case codes; never alter identifiers' content."""
    return [replace(r, cpt=r.cpt.strip().upper(), npi=r.npi.strip()) for r in rows], []

def validate(rows):
    clean, rejects = [], []
    for r in rows:
        if len(r.npi) != 10 or not r.npi.isdigit():
            rejects.append((r, "invalid NPI (must be 10 digits)"))
        elif date.fromisoformat(r.dos) > TODAY:
            rejects.append((r, "future date of service"))
        elif r.billed <= 0:
            rejects.append((r, "non-positive billed amount"))
        else:
            clean.append(r)
    return clean, rejects

def dedupe(rows):
    """Drop exact resubmission duplicates from client PM double-exports."""
    seen, clean, rejects = set(), [], []
    for r in rows:
        key = (r.member_id, r.cpt, r.billed)   # dedupe key
        if key in seen:
            rejects.append((r, f"duplicate of earlier row (key={key})"))
        else:
            seen.add(key)
            clean.append(r)
    return clean, rejects

def map_status(rows):
    clean, rejects = [], []
    for r in rows:
        if r.status not in STATUS_MAP:
            # Fail-loud: unknown states are a pipeline error, not a silent bucket.
            raise ValueError(f"unknown claim status {r.status!r} on {r.claim_id} — "
                             "update STATUS_MAP deliberately (postmortem 2026-06-10)")
        clean.append((r, STATUS_MAP[r.status]))
    return clean, rejects

def main():
    rows, batch_rejects = BATCH, []
    for stage in (normalize, validate, dedupe):
        rows, rejects = stage(rows)
        batch_rejects += [(r, why, stage.__name__) for r, why in rejects]
    mapped, _ = map_status(rows)

    print(f"Cleaning pipeline — in {len(BATCH)}, clean {len(mapped)}, "
          f"rejected {len(batch_rejects)}\n")
    for r, status in mapped:
        print(f"  KEEP  {r.claim_id} {r.cpt} dos={r.dos} → {status}")
    for r, why, stage in batch_rejects:
        print(f"  DROP  {r.claim_id} [{stage}] {why}")
    kept_pt = [r for r, _ in mapped if r.cpt == "97110"]
    print(f"\nSanity note: member M0044120 had a 3-visit weekly PT series (97110); "
          f"{len(kept_pt)} of 3 visits survived the pipeline.")

if __name__ == "__main__":
    main()
