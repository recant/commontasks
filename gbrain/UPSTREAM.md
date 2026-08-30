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

### Tests
- **Added** `test/ai/local-only-profile.test.ts` (10 tests) covering tier
  resolution across key combinations and the fail-loud gate.
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
