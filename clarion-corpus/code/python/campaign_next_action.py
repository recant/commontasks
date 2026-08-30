#!/usr/bin/env python3
"""campaign_next_action.py — next-best-action planner for client campaigns.

Author: Dana Ortiz (customer success) · 2026-08-24
Related: the CRM notes (crm_notes/*.md), pricing-renewals topic, the vaccine-
module demo that turned the Cedar Point negotiation.

Reads each account's recent CRM event history ("past actions") and proposes the
next campaign step for September: renewal outreach, module demo, training
offer, QBR scheduling, or a win-back touch. Rules, not ML — every suggestion
must be explainable to Wanda in one sentence.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date

TODAY = date(2026, 8, 30)

@dataclass
class Account:
    client: str
    contract_end: date
    events: list[tuple[date, str]]          # (date, event_type) — past actions
    open_internal_items: list[str] = field(default_factory=list)
    modules_owned: set[str] = field(default_factory=set)

BOOK = [
    Account("lakeview-orthopedics", date(2026, 9, 30),
            [(date(2026, 8, 15), "renewal_verbal_commit"), (date(2026, 8, 14), "big_claim_paid"),
             (date(2026, 8, 10), "weekly_digest"), (date(2026, 7, 30), "risk_email_received")],
            open_internal_items=["monthly quality report (overdue since 8/25)"]),
    Account("northside-clinic", date(2027, 3, 31),
            [(date(2026, 7, 22), "training_delivered"), (date(2026, 7, 14), "dashboard_shipped"),
             (date(2026, 6, 17), "commitment_call")],
            open_internal_items=["eligibility batch API (overdue since 8/1)"]),
    Account("cedar-point-pediatrics", date(2026, 11, 1),
            [(date(2026, 8, 20), "renewal_offer_sent"), (date(2026, 8, 18), "module_demo"),
             (date(2026, 8, 11), "counter_received")],
            modules_owned=set()),
    Account("harbor-family-medicine", date(2027, 1, 31),
            [(date(2026, 8, 6), "appeals_filed"), (date(2026, 4, 9), "ticket_resolved")]),
    Account("summit-behavioral-health", date(2027, 5, 31),
            [(date(2026, 8, 1), "pilot_go_live"), (date(2026, 6, 10), "baa_signed")]),
    Account("riverbend-imaging", date(2027, 4, 30),
            [(date(2026, 5, 4), "go_live")]),
]

def days_to_renewal(a: Account) -> int:
    return (a.contract_end - TODAY).days

def days_since_touch(a: Account) -> int:
    return (TODAY - max(d for d, _ in a.events)).days

def next_action(a: Account) -> tuple[str, str]:
    """Return (action, one-sentence why). Rule order = priority order."""
    last = {etype for _, etype in a.events}

    # Hygiene rule: don't market to a client we currently owe work.
    if a.open_internal_items:
        return ("SUPPRESS — no campaign touch",
                f"open internal item(s): {'; '.join(a.open_internal_items)} — "
                "deliver before we sell")

    if "renewal_offer_sent" in last and days_to_renewal(a) < 90:
        return ("HOLD + prep counter-close",
                "offer is on their table; next touch is their move (answer due Sep 5)")
    if days_to_renewal(a) < 60 and "renewal_verbal_commit" not in last:
        return ("RENEWAL OUTREACH", "inside 60 days of contract end with no commitment")
    if "renewal_verbal_commit" in last:
        return ("PAPERWORK NUDGE + reference ask",
                "verbal commit in hand; convert to signature and ask for a referenceable quote")
    if "pilot_go_live" in last:
        return ("PILOT STATS SHARE", "send the 97% auto-adjudication numbers — success story in motion")
    if "module_demo" not in last and "wellness" not in a.modules_owned and days_to_renewal(a) > 90:
        return ("MODULE DEMO OFFER", "cross-sell window open; the Cedar Point demo playbook works")
    if days_since_touch(a) > 60:
        return ("CHECK-IN CALL", f"{days_since_touch(a)} days since last touch — too quiet")
    return ("MONITOR", "healthy cadence; no action beats a noisy one")

def main():
    print(f"September campaign plan — generated {TODAY}\n")
    for a in sorted(BOOK, key=days_to_renewal):
        action, why = next_action(a)
        print(f"  {a.client:28s} renewal in {days_to_renewal(a):>3d}d → {action}")
        print(f"  {'':28s} why: {why}\n")

if __name__ == "__main__":
    main()
