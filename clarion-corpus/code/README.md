# Clarion code layer — demo scripts for debugging queries

Supplementary to the 60-source corpus: **in-fiction Clarion Health tools** (Python for the business-analyst side, TypeScript for the platform side). Each file carries an author, date, and history header tying it to the existing storylines, so debugging questions can be answered *through the graph* — symptom → code → postmortem/ticket → claims.

> Not registered in `entities.json` (the spec's source manifest is frozen at 60 and `validate.py` enforces it). Treat this as a candidate `type: code` source layer — registering these files + extracting claims from their headers/changelogs is a deliberate follow-up decision, not a default.

## Catalog

| File | Author (fiction) | What it is | Story tie-in |
|---|---|---|---|
| `python/analyzer_client_mix.py` | Sofia | **Analyzer**: per-client patient/claims profile — demographics (age bands), payer mix, insurance amounts (billed/allowed), condition categories, E/M level-4 share vs benchmark, first-pass rate | Produces the Harbor ~68%-vs-44% audit screen (S10) |
| `python/screening_retro_eligibility.py` | Tom (DRAFT) | **Screening**: flags denied-no-coverage claims that became rebillable via retro MassHealth eligibility, with filing deadlines | S2/S12 — drafted while Priya was on PTO 🐛 |
| `python/pipeline_claims_cleaning.py` | Jake | **Data-cleaning pipeline**: normalize → validate → dedupe → fail-loud status map, rejects carry reasons | Fail-loud stage exists because of the June postmortem 🐛 |
| `python/campaign_next_action.py` | Dana | **Campaign tool**: next-best-action for September from each account's past CRM actions (renewal outreach, module demo, training, check-in) | Encodes the Cedar Point module-demo playbook (S11) 🐛 |
| `python/promise_tracker.py` | Dana + Jake | **Commitment tracker** — a *working* tool: reads `../entities.json`, reports done/open/overdue with days late, cross-checks status vs dates | Query type 5 (Follow-up) as executable code |
| `typescript/denialRateMart.ts` | Jake | Reporting-mart status mapping v2 + denial-rate metric; keeps the buggy v1 for the record and reproduces 14.3% vs 8.2% as a regression test | THE S3 artifact (postmortem 2026-06-10) |
| `typescript/eligibilityFallback.ts` | Jake | Cached-eligibility fallback: backoff retry, 24h TTL, stale labeling, never-release-claims guardrail; demo replays a compressed INC-2026-007 | S9 (postmortem 2026-07-29) |
| `typescript/modifierSwap.ts` | Marcus | X-subset auto-swap + line split with a toy Anthem PTP edit; self-test proves column-2 placement clears the edit and column-1 doesn't | S1/S6 (mirrors `anthem.yaml`, the QBR commitment) |

## Run everything

```
cd code
for f in python/*.py; do python3 "$f"; done      # all runnable, stdlib only
for f in typescript/*.ts; do node "$f"; done      # Node ≥23 (native type stripping)
```

All eight run green as committed (the Python "bugs" run fine — they produce *wrong answers*, which is the point).

## New benchmark/query types this layer enables

The corpus's 12 query types are retrieval-shaped; code adds three debugging-shaped ones worth prototyping:

- **13. Debug (symptom → root cause):** "Northside's May denial rate doubled — why?" → graph walks symptom → `denialRateMart.ts` history → postmortem claims → the supersedes chain. The answer cites code *and* provenance.
- **14. Code-history (why is this code like this?):** "Why does the status map throw instead of defaulting?" → the fail-loud rule traces to postmortem 2026-06-10. "Why exponential backoff?" → INC-2026-007.
- **15. Find-the-bug (review against the graph):** hand the SLM a script plus the relevant claims and ask what's wrong. The three planted bugs below are the gold labels — each is wrong *specifically because it contradicts recorded tribal knowledge*, so graph-grounded review should beat code-only review. That's the same A-vs-B ablation as the retrieval benchmark, applied to code review.

## 🐛 Planted bugs (spoilers — gold labels for query type 15)

1. **`screening_retro_eligibility.py`** — the deadline is computed as `dos + 90` days. Priya's recorded rule (Slack 4/2, claim `clm_src012_03`): the 90-day clock runs from the **eligibility determination date**, not the DOS. Consequence in the demo output: CLM-2026-19560 and CLM-2026-20101 are marked EXPIRED though both are actually filable (one has a single day left — money about to be wrongly written off), and CLM-2026-21744 shows false urgency. Bonus finding: the July-1 bulletin requirements (delay-reason code 9 + determination letter, `clm_src035_07`) are missing entirely. In-fiction excuse: drafted by Tom while Priya was OOO — the bus factor writing bugs in real time.
2. **`pipeline_claims_cleaning.py`** — the dedupe key is `(member_id, cpt, billed)` with **no date of service**, so a weekly PT series (same member, same 97110, same price — exactly how therapy bills) collapses to one visit: the demo prints "1 of 3 visits survived." Two legitimate claims silently dropped = revenue loss, and an echo of the postmortem's own lesson that silent data handling turns drift into wrong numbers.
3. **`campaign_next_action.py`** — the "don't market to clients we owe work" suppression rule fires on *any* open internal item, so Lakeview gets **no touch 31 days before its renewal** (because our own report is overdue) and Northside goes quiet too. A reasonable-sounding hygiene rule that suppresses exactly the accounts most needing contact — findable only by connecting the rule to the renewal timeline in the CRM claims.

The TypeScript files are intentionally the *fixed* versions carrying their bug history in comments — they serve query types 13/14 (explain the incident/history), while the Python bugs serve type 15 (find it).
