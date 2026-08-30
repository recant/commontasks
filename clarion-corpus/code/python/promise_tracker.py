#!/usr/bin/env python3
"""promise_tracker.py — commitment/action-item tracker over the live registry.

Author: Dana Ortiz (with Jake) · 2026-08-25
Related: query type 5 (Follow-up); reads ../../entities.json directly, so this
is a WORKING tool over the corpus, not a mock — the same data the graph serves.

Reports every action item grouped by status, computes days overdue against the
registry's in-world today, and cross-checks that each stored status matches
what the dates imply (a mini-validator for commitment hygiene).
"""
from __future__ import annotations
import json
from datetime import date
from pathlib import Path

REG = Path(__file__).resolve().parents[2] / "entities.json"

def main():
    reg = json.loads(REG.read_text(encoding="utf-8"))
    today = date.fromisoformat(reg["meta"]["today"])
    people = {p["id"]: p["name"] for p in reg["people"]}
    items = reg["action_items"]

    by_status: dict[str, list] = {"overdue": [], "open": [], "done": []}
    inconsistencies = []
    for a in items:
        due = date.fromisoformat(a["due"])
        implied = "overdue" if (a["status"] != "done" and due < today) else a["status"]
        if implied != a["status"]:
            inconsistencies.append((a["id"], a["status"], implied))
        by_status[a["status"]].append((a, due))

    print(f"Commitment tracker — {len(items)} action items, as-of {today}\n")
    for status in ("overdue", "open", "done"):
        print(f"[{status.upper()}] ({len(by_status[status])})")
        for a, due in sorted(by_status[status], key=lambda x: x[1]):
            owner = people[a["owner"]]
            promised = f" → promised to {people[a['promised_to']]}" if a.get("promised_to") else ""
            delta = (today - due).days
            when = (f"{delta}d LATE" if status == "overdue"
                    else f"due {due}" if status == "open"
                    else f"done {a.get('done_date', '?')}")
            print(f"  {a['id']:16s} {owner:14s} {when:12s} {a['label']}{promised}")
        print()

    if inconsistencies:
        print("⚠ status/date inconsistencies (fix entities.json):")
        for iid, stored, implied in inconsistencies:
            print(f"  {iid}: stored={stored}, dates imply={implied}")
    else:
        print("✓ all stored statuses consistent with due dates")

if __name__ == "__main__":
    main()
