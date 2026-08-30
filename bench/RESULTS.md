# Clarion benchmark — condition A vs B (retrieval only)

First measured comparison of the SLM-retuned gbrain against the naive-RAG
baseline, on the 60-item Clarion benchmark. **No model is involved** — this is
retrieval precision/recall against `gold_evidence`, so it runs offline.

## Method

`gold_evidence` names *claim* ids; each claim carries a `source_id`. Condition B
retrieves claims directly (FTS5 over `claims_fts`, exactly what `build_db.py`
indexes); condition A retrieves *pages*. Both are mapped to **source-document**
granularity, the only level the two share — comparing A's pages to B's claims
directly would not be apples-to-apples.

Entity pages (`people/`, `clients/`, `topics/`) can never be gold hits, since no
claim is anchored to them. That is deliberate: the graph's job is to help *find*
the right source docs, not to substitute for them.

Reproduce:
```bash
cd gbrain && GBRAIN_BRAIN_PATH=<brain> bun run ../bench/run_benchmark.ts
```

## Results (k=10, 60 items)

| condition | P@k | R@k | avg #returned |
|---|---|---|---|
| B — naive RAG (FTS5 claims) | 14.5 | 80.8 | 10.0 |
| **A — gbrain `slm`** | **21.0** | 74.9 | **6.3** |
| A — gbrain `balanced` | 14.2 | 81.2 | 10.0 |

### Recall@10 by query type

| type | B | A `slm` | A `balanced` |
|---|---|---|---|
| follow_up | 56.7 | **80.0** | **86.7** |
| frequency | 63.3 | **83.3** | **83.3** |
| person | 83.3 | **90.0** | **90.0** |
| timeline | 53.3 | 53.3 | 53.3 |
| recall | 70.0 | 70.0 | 70.0 |
| contradiction | 80.0 | 73.3 | 73.3 |
| gap | 90.0 | 78.3 | 78.3 |
| consensus | 93.3 | 83.3 | 93.3 |
| change | 100.0 | 83.3 | 83.3 |
| decision | 100.0 | 90.0 | 90.0 |
| evidence | 100.0 | 63.3 | 83.3 |
| routing | 80.0 | **50.0** | 90.0 |

## Reading these honestly

**The `slm` precision gain is real but partly mechanical.** It returns 6.3 docs
where the others return 10, and precision is computed over the actual returned
count. In absolute terms `slm` finds ~1.32 gold docs per query vs `balanced`'s
~1.42 — about 93% of the gold hits in 63% of the results. For a 4k-context
generator that is the intended trade, and it is what the bundle was designed to
do. It is *not* evidence that `slm` retrieves better.

**Two caveats materially understate condition A:**

1. **No vector arm.** The brain is keyless, so `vector search unavailable
   (missing_env)` — A ran keyword + graph only, against B's keyword. Every
   embedding host is blocked in this environment, so the hybrid half of hybrid
   retrieval is simply absent.
2. **Generic `search` for all 60 questions.** The 12 query types map onto
   specialised gbrain ops — `routing`→`whoknows`, `contradiction`→
   `find_contradictions`, `change`→`delta`/`find_trajectory`,
   `timeline`→`chronicle_*` — and the runner uses none of them. The types where
   A trails (routing, evidence, timeline) are precisely those.

**Where the graph already shows through:** `follow_up` (+23 to +30 pts),
`frequency` (+20), `person` (+7). These are the multi-hop questions where
traversal beats keyword matching, and they move without any vector arm at all.

**Where `slm` is actively hurting:** `routing` drops to 50.0 vs `balanced`'s
90.0 — autocut is trimming expert-routing answers. Worth investigating before
trusting `slm` as a default; it may need `autocut: false` for routing intents,
or those queries should route to `whoknows` instead of generic search.

## Not yet measured

- Answer quality against `gold_answer`/`rubric` — needs a generator.
- Condition C (SLM alone) — needs a generator.
- Vector-arm contribution — needs an embedding provider.
