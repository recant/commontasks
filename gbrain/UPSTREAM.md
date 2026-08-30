# Vendored GBrain — upstream provenance and local changes

This directory is a vendored copy of [garrytan/gbrain](https://github.com/garrytan/gbrain),
retuned so CommonTasks can run it against a local small language model (SLM)
instead of a frontier one.

| | |
|---|---|
| **Upstream** | https://github.com/garrytan/gbrain |
| **Pinned commit** | `7b7921d86141c4e4086e50828de9a867a6814247` |
| **Upstream version** | `0.47.6.0` |
| **Vendored** | 2026-08-30 |
| **License** | See `LICENSE` (unchanged from upstream) |

Vendored with `.git` removed. All 4,630 upstream-tracked files are present and
committed; nothing is filtered by the nested `.gitignore`.

## Why this fork exists

GBrain assumes a frontier model at every LLM-touching stage. Three consequences
made it unusable for a local-only deployment, which is CommonTasks' entire
premise:

1. The Ollama recipe declared `supports_tools: false`, so `classifyCapabilities`
   returned `unusable:no_tools` and the subagent/agent loop was refused at all
   three gates. **Recurring agent tasks on a local model were impossible.**
2. Tier defaults were Anthropic-only, with no local provider entry.
3. `enforceSubagentCapable` responded to an unusable verdict by *silently*
   falling back to `anthropic:claude-sonnet-4-6`. On a local-only install that
   is not a degradation — it is an unannounced egress of the job's prompts and
   every page the loop retrieves.

## Local changes

Kept deliberately surgical so upstream rebases stay tractable. Four source files
and five test files; `gateway.ts` is byte-identical to upstream.

### `src/core/ai/types.ts` (~9 lines)
Widened `ChatTouchpoint.supports_tools` from `boolean` to
`boolean | ((modelId: string) => boolean)`, matching the predicate form
`supports_subagent_loop` already used.

`supports_structured_outputs` was deliberately **left** as a plain `boolean`:
on Ollama, constrained decoding is enforced by the server for whatever model is
loaded, so it is an endpoint property, not a per-model one. Tool calling is the
opposite — it needs a tool-aware chat template, which is a model property.

### `src/core/ai/capabilities.ts` (~10 lines)
Resolve the `supports_tools` predicate once and share the result between
`supportsToolCalling` and `supportsParallelTools`, so the two cannot disagree
for a given model id.

### `src/core/ai/recipes/ollama.ts` (~77 lines)
The core fix. Adds `isToolCapableOllamaModel(modelId)`, an anchored family
allowlist matched against the tag-stripped model id, and points
`supports_tools` / `supports_subagent_loop` at it. Sets
`supports_structured_outputs: true` (server property, see above). Version
boundaries are load-bearing: `llama3` shipped without tool calling and
`llama3.1` added it, so the pattern must not treat the former as a prefix of
the latter.

Unlisted families still answer `false` — fail-closed, preserving the previous
conservative posture for the tiny completion-only models an Ollama install also
serves.

### `src/core/model-config.ts` (~81 lines)
- `DEFAULT_LOCAL_CHAT_MODEL`, `localTierDefault()`, `isLocalOnlyProfile()`.
- Appends an `ollama` entry to `PROVIDER_TIER_DEFAULTS`, **last**, so every
  cloud-keyed install resolves exactly as before.
- `GBRAIN_LOCAL_ONLY` promotes local defaults above the cloud entries, so a
  stray leftover API key cannot silently reclaim them.
- **`enforceSubagentCapable` now throws instead of falling back when
  `GBRAIN_LOCAL_ONLY` is set.** This is the privacy-relevant change: a stderr
  warning is not sufficient, because under the old path the job still ran and
  the prompts still shipped.
- The `degraded:no_caching` warning no longer advises switching to Anthropic
  when running locally, where inference costs wall-clock rather than tokens.

### `src/core/search/mode.ts` + `src/core/ai/defaults.ts` — the `slm` mode (Phase 2)
Adds a fourth search mode. `SearchMode`, `SEARCH_MODES` (appended **last**, so the
three existing modes keep their positions in every report and picker), and a
`MODE_BUNDLES.slm` entry.

`slm` is **not** a cheaper `conservative`. The two trim different things because
they are sized against different bottlenecks: conservative spends less money on a
capable model, so it cuts the LLM-billed knobs *and* the free ones. Here the
bottleneck is the generator's reasoning and local inference bills nothing — so
this bundle keeps conservative's LLM-spend posture while taking balanced's
**zero-LLM** posture in full (`graph_signals`, `relationalRetrieval`,
`contextual_retrieval: 'title'`). Those are pure SQL and string concat; disabling
them to save milliseconds while asking a 4B model to compensate with reasoning it
does not have is the wrong trade.

`DEFAULT_LOCAL_RERANKER_MODEL` is new in `ai/defaults.ts` (the one code home the
seam test enforces). A reranker receives the query **and the candidate document
texts**, so a hosted default would ship brain content off-machine on every
search — the same class of leak Phase 1 closed for chat. 0.6B rather than the
recipe's 4B placeholder: this profile already spends its RAM on a local chat model.

`autocut: true` is legitimate here only because the reranker fires. If the
operator never launches llama-server, `rerank.ts` fails open and `applyAutocut`
no-ops on fewer than 2 finite scores, so search degrades to plain RRF rather than
cutting on a meaningless curve.

`reranker_top_n_in: 24` deliberately exceeds `searchLimit: 6`. The D4 invariant is
"no unscored tail", which needs `top_n_in >= searchLimit`, not equality — and
scoring a wider pool than we return is what lets the cross-encoder promote a good
chunk from rank 20 into the returned six.

No `KNOBS_HASH_VERSION` bump: the cache key already folds `mode=` and every knob
value, so a new mode gets a distinct key automatically and existing modes' hashes
are untouched.

### `src/core/search/expansion.ts` — expansion width (Phase 2)
`MAX_QUERIES` 3→5 and the alternatives cap 2→4, **gated to the local profile**. A
small model's paraphrases cluster tightly around the original, so each variant
recovers fewer synonym misses. Read from the environment rather than threaded
through `expandQuery`'s signature, which every caller invokes with a bare query
string. The sanitization layer is untouched — prompt-injection defense, not tuning.

### Mode-enumeration call sites (Phase 2)
A fourth mode surfaced six compile errors and four runtime string comparisons the
compiler could not catch. The eval commands now reuse the existing
`isSearchMode()` guard instead of hand-rolling a fourth three-way check, so
`--mode slm` is accepted — without this the Phase 6 eval baseline cannot run.
`telemetry.ts` and the `graph-embedding` doctor check list `slm` explicitly rather
than letting it fall through their `balanced` catch-all: it wants the same answer
today, but an accidental match would go stale silently.

`types.ts` re-spells the mode union inline rather than importing `SearchMode` —
that module is a deliberate zero-import leaf, and `search/mode.ts` imports
`CRMode` from it.

### Tests
- **Added** `test/ai/local-only-profile.test.ts` (11 tests) covering tier
  resolution across key combinations and the fail-loud gate.
- **Extended** `test/reranker-default-seam.test.ts` with the local-reranker
  privacy invariant, the autocut/reranker coupling, and the zero-LLM arms.
- **Extended** `test/query-sanitization.test.ts` with the widened cap — the
  existing "caps at 2" test is the guard that this stays opt-in.
- **Updated** the mode-count assertions in `test/search-mode.test.ts` and
  `test/eval-run-all.test.ts` to derive from `SEARCH_MODES` instead of
  hardcoding 3.
- **Updated** `test/ai/capabilities.test.ts`, `test/ai/recipe-ollama.test.ts`,
  `test/ollama-recipe.test.ts`, `test/ai/gateway-chat.test.ts` — these pinned
  the old `supports_tools: false` contract. Each was rewritten to assert the new
  per-model contract on *both* sides (a tool-capable model is admitted, a
  completion-only one is still refused), which is stronger coverage than the
  boolean assertions they replace.

## New environment variables

| Var | Effect |
|---|---|
| `GBRAIN_LOCAL_ONLY` | `1`/`true`/`yes`/`on`. Local tier defaults outrank cloud keys, and a tool-incapable subagent model becomes a hard error instead of a cloud fallback. |
| `GBRAIN_LOCAL_MODEL` | Local chat model for every tier (default `ollama:qwen3.5:4b`). A bare tag is prefixed with `ollama:`. |

All four tiers resolve to the *same* local model on purpose: Ollama evicts and
reloads weights when the requested model changes, so a four-model tier split
would thrash RAM and add a cold start to every tier crossing.

## Running upstream's checks against this copy

`bun run typecheck` and `bun test` work normally from this directory.

`bun run verify` does **not** fully work here, and this is a vendoring artifact
rather than a defect in the changes. Many guard scripts resolve their root with
`git rev-parse --show-toplevel`, which now returns the *outer* CommonTasks repo,
so they look for `scripts/*.tsv` in the wrong place and scan
`test/fixtures/guards/**/bad/fixture.ts` — files that are deliberately bad, as
negative fixtures for those same guards.

Baseline for comparison: a pristine upstream clone passes **55/55** checks; this
copy reports 13 failures, none of which reference the changed files. Some guards
honor a `GBRAIN_GUARD_ROOT` override:

```bash
GBRAIN_GUARD_ROOT="$PWD" bun run verify
```

### Test batches are not order-independent — always diff against upstream

Running a large set of test files in ONE `bun test` invocation produces failures
that do not occur when the same files run alone. gbrain shards these across
runners in CI, so the condition never arises upstream. Measured on the 125-file
Phase 2 batch: **pristine upstream fails 13 of them**, and this copy fails the
same 13.

So a raw failure count means nothing here. The only meaningful signal is the
**diff** of failing test NAMES against a pristine clone running the identical
batch:

```bash
run() { (cd "$1" && bun test $FILES > "$2" 2>&1); \
  grep -oE '^\(fail\) .*' "$2" | sed 's/ \[[0-9.]*ms\]//' | sort -u; }
run /path/to/pristine-gbrain /tmp/up.txt  > /tmp/up_fails.txt
run "$PWD"                   /tmp/mine.txt > /tmp/my_fails.txt
comm -13 /tmp/up_fails.txt /tmp/my_fails.txt   # empty = no regressions
```

This is how the three real Phase 2 regressions (mode-count assertions) were
separated from the 13 pre-existing ones.

Gate on `bun run typecheck` plus the unit suite instead:

```bash
cd gbrain
bun install
bun run typecheck
bun test test/ai/local-only-profile.test.ts test/ai/capabilities.test.ts
bash scripts/run-unit-parallel.sh
```

## Rebasing onto a newer upstream

1. Clone the new upstream tag beside this tree.
2. Diff each file listed above against its old and new upstream versions.
3. The Ollama recipe change is the one most likely to conflict — upstream may
   fix the stale `supports_tools: false` itself, in which case drop our version
   and keep theirs.
4. Re-run the verification commands above and update the pinned commit here.

The family allowlist in `ollama.ts` **will** go stale exactly as upstream's
blanket `false` did. The durable fix is a runtime probe driven by
`gbrain models doctor` rather than a hardcoded list; treat the list as a
stopgap.
