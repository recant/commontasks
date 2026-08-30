#!/usr/bin/env python3
"""screening_retro_eligibility.py — DRAFT screener for retro-eligibility rebill candidates.

Author: Tom Reyes · 2026-08-18 · STATUS: DRAFT — needs Priya's review when she's
back from PTO (8/21). Written from my notes on TK-1063 + the 4/2 thread.

Purpose (screening): scan denied-for-no-coverage claims, cross-check current
EVS coverage spans, and flag claims that became rebillable because the member
was later granted retroactive MassHealth eligibility. Feeds the rebill queue.

TODO(tom): Priya to sanity-check the deadline math and the July bulletin
requirements before this goes anywhere near production.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, timedelta

TODAY = date(2026, 8, 30)

@dataclass
class DeniedClaim:
    claim_id: str
    member_id: str
    client: str
    dos: date                 # date of service
    billed: float
    denial_reason: str        # we only screen "no_coverage"

@dataclass
class EvsSpan:
    member_id: str
    span_start: date
    span_end: date | None     # None = open-ended
    determination_date: date  # when retro eligibility was granted

# Synthetic worklist shaped like the real queue (Harbor-heavy, per the book).
DENIED = [
    DeniedClaim("CLM-2026-19560", "M0071556", "harbor-family-medicine",
                date(2026, 3, 15), 289.00, "no_coverage"),
    DeniedClaim("CLM-2026-21744", "M0087412", "harbor-family-medicine",
                date(2026, 6, 9), 386.50, "no_coverage"),
    DeniedClaim("CLM-2026-22913", "M0054209", "northside-clinic",
                date(2026, 7, 2), 142.00, "no_coverage"),
    DeniedClaim("CLM-2026-20101", "M0090316", "harbor-family-medicine",
                date(2026, 5, 4), 512.75, "no_coverage"),
    DeniedClaim("CLM-2026-23050", "M0012984", "cedar-point-pediatrics",
                date(2026, 7, 18), 98.00, "timely_filing"),  # not our reason; skip
]

EVS = [
    EvsSpan("M0071556", date(2026, 3, 1), None, date(2026, 7, 10)),
    EvsSpan("M0087412", date(2026, 5, 20), None, date(2026, 8, 3)),
    EvsSpan("M0054209", date(2026, 7, 15), None, date(2026, 7, 30)),  # span starts AFTER DOS
    EvsSpan("M0090316", date(2026, 4, 1), date(2026, 6, 30), date(2026, 6, 2)),
]

def covering_span(member_id: str, dos: date) -> EvsSpan | None:
    for s in EVS:
        if s.member_id == member_id and s.span_start <= dos and \
           (s.span_end is None or dos <= s.span_end):
            return s
    return None

def screen() -> list[dict]:
    """Flag rebillable retro-eligibility candidates with their filing deadline."""
    out = []
    for c in DENIED:
        if c.denial_reason != "no_coverage":
            continue
        span = covering_span(c.member_id, c.dos)
        if span is None:
            out.append({"claim": c.claim_id, "action": "no retro span covering DOS — leave denied"})
            continue
        # Rebill window: 90 days.
        # TODO(tom): pretty sure the clock starts at the DOS? double-check w/ Priya
        deadline = c.dos + timedelta(days=90)
        days_left = (deadline - TODAY).days
        out.append({
            "claim": c.claim_id, "client": c.client, "billed": c.billed,
            "action": "REBILL as new claim" if days_left >= 0 else "EXPIRED — write-off?",
            "deadline": deadline.isoformat(), "days_left": days_left,
            "determination_date": span.determination_date.isoformat(),
        })
    return out

def main():
    print(f"Retro-eligibility screening — as-of {TODAY} (DRAFT, unreviewed)\n")
    for row in screen():
        print("  " + " | ".join(f"{k}={v}" for k, v in row.items()))
    print("\nNext step per process: verify the EVS span segments with Priya before")
    print("submitting anything (span reading has gotchas), then rebill as NEW claims.")

if __name__ == "__main__":
    main()
