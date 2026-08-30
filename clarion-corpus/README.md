# Clarion Health demo corpus

A fully synthetic, benchmark-ready knowledge corpus for the offline **SLM + graph knowledge base** hackathon project. Fictional company: **Clarion Health** — B2B claims automation for healthcare providers, ~100 employees, Boston. In-world today: **2026-08-30**; activity window 2026-02-01 → 2026-08-25 (SOPs deliberately predate it — stale docs are part of the benchmark).

Everything here is generated per `demo-data-generation-plan.md` (v3 spec). All people, clients, payers, claims, and dollar amounts are fictional.

## What's in the box

| Piece | Where | Size |
|---|---|---|
| Source corpus (ground truth) | `sources/{slack,meetings,expert_calls,docs,emails,tickets,crm_notes,postmortems,payer_configs,ai_chats}/` | 60 md files (12 scenarios S1–S12, incl. **5 distractors**) |
| Entity pages (gbrain-native) | `people/` (16) · `clients/` (6) · `payers/` (5) · `topics/` (8) | 35 md files |
| Skill pages | `skills/*/SKILL.md` | 4 |
| Schema pack | `schema/clarion-v1.yaml` | 1 |
| Canonical registry | `entities.json` — **single source of truth**; edit this first, always | 1 |
| Claims layer | `claims.json` — 239 atomic claims with speaker, stance, status, and quote+line anchors | 1 |
| Graph | `graph_seed.json` — 371 nodes / 929 edges | 1 |
| Benchmark | `benchmark.json` — 60 items (12 query types × 5; 2 single_source / 2 cross_source / 1 distractor_trap each) | 1 |
| Build + checks | `build_db.py` (→ `clarion.db`, SQLite + FTS5) · `validate.py` | 2 |
| Tooling | `tools/derive.py` + `tools/claim_parts/` + `tools/edges_manual.json` (regenerate claims.json/graph_seed.json) | — |

## Build & validate

```
python3 tools/derive.py     # only if you edited claim parts / edges_manual / entities.json
python3 build_db.py         # writes clarion.db per the spec §2 DDL
python3 validate.py         # must print PASS
```

Stdlib only, no pip installs. `validate.py` enforces: JSON validity, unique IDs, every edge endpoint exists, every claim's source + speaker + anchor (exact quote at the stated line) resolve, temporal sanity (nothing after 2026-08-30; supersedes always newer→older), the S7 guard (the attachment debate must have NO resolution anywhere), question ask-counts, benchmark shape (60 items, 5/type, 2-2-1 difficulty mix) and gold-evidence existence, and wikilink resolution across all 99 md files.

## The designed traps (load-bearing for the benchmark)

- **Lexical honeypot:** `sources/docs/sop-timely-filing-appeals.md` (SOP-007, Nov 2025) says UHC reconsiderations = **60 days**. The truth since 2026-08-05: **90 days per §7.3** for delegated contracts (Rachel Goldman legal call → `clm_src014_02` supersedes `clm_src003_04`). FTS ranks the stale SOP first — `build_db.py`'s smoke test proves it — so naive RAG confidently answers 60. This is the demo kill-shot (benchmark `b_change_02`, verbatim from the spec).
- **Second stale SOP:** SOP-002 §4 still says "append modifier 59"; superseded for Anthem since March (X-subset).
- **Superseded number:** Northside's "14.3% May denial rate" was a reporting artifact (true: 8.2%) — a timeline or trend answer that repeats it fails.
- **Unresolved by design (S7):** Marcus (API-pull) vs Priya (proactive fax) on MassHealth attachments — both positions `status: current`, tabled to Q4, **nothing in the corpus settles it**. Consensus queries here must return "no consensus."
- **Near-misses:** HIPAA's 60-day breach-notification window (compliance policy), Aetna *paper appeals* in SOP-002, Riverbend go-live chatter.
- **Pure distractors (5):** expense SOP, PTO policy, phishing email, all-hands excerpt, office-move thread.

## The 12 headline demo queries (one per query type)

1. **Recall** — "What's the latest on the BrightPath pilot?" → 312 claims, 97.1% auto-adjudicated, live Aug 1 with Summit.
2. **Timeline** — "Full history of the Lakeview relationship" → go-live → mod-59 wave → $38k stuck claim → QBR → risk email → save (6 months, 5 source types).
3. **Person** — "Summarize Priya's guidance on MassHealth retro-eligibility."
4. **Decision** — "Why did we run the BrightPath pilot?" → decision + `justified_by` claims (Marcus capacity, Wanda economics, Vik's endorsement).
5. **Follow-up** — "What's overdue right now?" → Northside eligibility API (29 days late), outage runbook, Lakeview monthly report.
6. **Change** — "How long do we have to file a UHC reconsideration?" → **the honeypot**: 60→90 days supersedes chain with citations.
7. **Frequency** — "What do people keep asking?" → Anthem X-subset, retro-eligibility, UHC window (4 asks each).
8. **Consensus** — "Do internal and external experts agree on the Anthem fix?" → Priya + Vik, independent.
9. **Contradiction** — "Any unresolved disagreements?" → the attachment debate, both sides current.
10. **Evidence** — "Who says 90 days, on what authority?" → Rachel Goldman, §7.3, memo in writing.
11. **Routing** — "Nina has a retro case and Priya's OOO — who can help?" → effectively nobody: the bus factor, live.
12. **Gap** — "Which recurring questions have no doc?" → X-subset, retro-eligibility, attachment strategy (+ stale SOP-007).

## Benchmark protocol (`benchmark.json`)

Three conditions, same SLM: **A** SLM + graph traversal (this repo's graph), **B** SLM + naive RAG (`claims_fts` top-k over the same DB, no graph logic), **C** SLM alone. Per item: score retrieval (precision/recall@k of `gold_evidence` claim IDs — A vs B), answer correctness (keyword `rubric` per item, scriptable; or LLM-judge vs `gold_answer`), and attribution (does the answer cite the right source). `difficulty` splits results into single_source / cross_source / distractor_trap; the traps are where A should visibly beat B.

## Conventions

- **IDs:** `p_ c_ pay_ src clm_ q_ dec_ act_ top_ skl_ gap_`; claims are `clm_src{NNN}_{MM}` in order of appearance in the source.
- **Anchors:** `{"line": N, "quote": "exact substring"}` — the quote is authoritative; line numbers are machine-resolved by `tools/derive.py`. Re-run derive after editing any source file.
- **Edge directions:** person→claim `speaker_of` · claim→source `from_source` · claim→topic `about` · person→question `asked` · claim→question `answered` · doc-source→question `resolves` · newer-claim→older-claim `supersedes(scope)` · claim↔claim `contradicts(resolution)` / `supports` · decision→source `decided_in` · decision→claim `justified_by` · action_item→source `promised_in` · action_item→person `owned_by(promised_to)` · skill→source `derived_from` · person→topic `expert_in` · source→client/payer `involves` · earlier-source→later-source `precedes(chain)` · source→person `mentions`.
- **ai-chat claims** are attributed to the human participant (Copilot is not a graph node); the claim text says when content is the assistant's answer.
- **Consensus/contradiction clustering:** group claims by (topic, stance); e.g. `x_subset_required` held by Priya + Vik = consensus; `api_pull` vs `proactive_fax` both current = live contradiction.
- **Wikilinks** resolve by path-suffix (`[[expert_calls/2026-08-05-legal-call]]` → `sources/expert_calls/...`), per the schema pack.
- Note: Nina asked the retro question twice, so `graph_seed.json` has two `asked` edges for that pair; the DB's `(src,dst,type)` primary key keeps one — the question node's `ask_count` (4) is authoritative for frequency queries.
- **Gap detection rule:** question with ask_count ≥3 and no incoming `resolves` from a doc-type source. The UHC question *is* resolved (Rachel's memo) — its gap (`gap_sop007_stale`) is the subtler doc-maintenance kind, backed by the open `act_sop_update`.

## Out of scope here (per spec §9)

SLM prompting/harness, the 12 traversal-function implementations, and UI. This repo is data + DB build + validation only. Storage Option A (this SQLite build) vs Option B (gbrain import — the corpus is already gbrain-native) can be decided without regenerating anything.
