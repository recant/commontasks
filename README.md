# CommonTasks

A tiny proof-of-concept for a **local SLM that can use a large private database and take actions** without sending the database to a cloud model.

The demo runs **Qwen3.5-4B** locally through [Ollama](https://ollama.com/library/qwen3.5%3A4b), keeps organizational data in SQLite, exposes a few narrowly-scoped tools, and lets the model retrieve only the records it needs before acting on a fake employee-support ticket.

## What it demonstrates

```text
browser / employee request
      |
      v
local Python server
      |
      v
local Qwen3.5-4B
      |
      +---- search_knowledge() ----> 50,000-row local SQLite KB
      |                                  |
      +---- get_knowledge_record() <------+
      |
      +---- get_ticket()
      +---- add_ticket_note()  ------> local fake ticket DB
      +---- set_ticket_status() ------> local fake ticket DB
```

The important point is that the SLM **does not ingest the whole database into its context window**. The database stays local; the model gets compact tool results and can make an allowed state change based on the retrieved information.

## Why Qwen3.5-4B?

For this demo the important capability is **reliable tool/function calling**, not just chatbot quality. Qwen3.5-4B is a small Apache-2.0 model with native tool support and an Ollama build around 3.4 GB, making it practical on ordinary developer hardware.

The model is configurable with `COMMONTASKS_MODEL`, so swapping in another local model takes one environment variable.

## Browser chatbot

After installing Ollama and pulling the model:

```bash
ollama pull qwen3.5:4b
python3 webapp.py
```

Then open:

```text
http://localhost:8000
```

The website is entirely local:

```text
browser -> localhost:8000 -> Python -> Ollama -> Qwen3.5-4B
                                      -> SQLite knowledge + tickets
```

No Flask, Node, or frontend build step is required.

## Command-line demo

```bash
python3 demo.py
```

The default request is:

```text
Handle ticket 1001 using the company knowledge base.
```

Or ask your own:

```bash
python3 demo.py "Handle ticket 1002 and tell me what you changed"
```

On first run, the script creates `commontasks.db` with **50,000 synthetic knowledge records** plus three fake employee-support tickets.

### Test the large-database retrieval without Ollama

```bash
python3 demo.py --db-only
```

That seeds the database and runs the retrieval path without invoking a model.

## Example flow

For ticket `1001`, the model can:

1. read the ticket,
2. search 50,000 local records for `AUTH_TOKEN_MISMATCH`,
3. retrieve the relevant staging secret-rotation runbook,
4. add a note describing the approved next steps,
5. mark the ticket `in_progress` because this toy agent cannot actually verify the infrastructure health check.

The write tools deliberately affect **only the synthetic SQLite ticket table**. This keeps the example safe while showing the same agent pattern that could later sit in front of real enterprise APIs with authentication, permissions, approval gates, and audit logs.

## The real retrieval layer: `gbrain/`

The demo above is a proof of concept. The production path is a vendored, SLM-retuned copy of
[GBrain](https://github.com/garrytan/gbrain) in [`gbrain/`](gbrain/) — a Postgres + pgvector
brain with hybrid retrieval, a zero-LLM knowledge graph, cited synthesis with gap analysis, and
a crash-safe job queue. See [`gbrain/UPSTREAM.md`](gbrain/UPSTREAM.md) for the pinned upstream
commit and the full inventory of local changes.

GBrain assumes a frontier model throughout. Three things had to change before it could run on a
local few-billion-parameter model:

1. **The agent loop refused local models outright.** The Ollama recipe declared
   `supports_tools: false`, so every local model classified as `unusable:no_tools` and was
   rejected at all three subagent gates. Tool support is a property of the *model's* chat
   template, not the endpoint, so it is now a per-model predicate — `qwen3.5:4b` is admitted,
   `tinyllama` is still correctly refused.
2. **Tier defaults were Anthropic-only.** A local runtime is now a recognized provider, added
   last so every cloud-keyed install resolves exactly as it did before.
3. **The subagent gate failed *quietly* to the cloud.** When a model couldn't run the tool
   loop, gbrain warned on stderr and silently fell back to `anthropic:claude-sonnet-4-6` — the
   job still ran, and the prompts plus every retrieved page still left the machine. Under
   `GBRAIN_LOCAL_ONLY` that fallback is now a hard error.

### The `slm` search mode

Retrieval is also retuned for a small generator. `gbrain config set search.mode slm`
selects a fourth mode bundle sized against the SLM's real bottleneck:

| Knob | `conservative` | `slm` | Why |
|---|---|---|---|
| `tokenBudget` | 4000 | **3000** | Fits a 4–8k window with room for the system prompt |
| `searchLimit` | 10 | **6** | A small model reasons worse over a sprawling candidate set |
| `graph_signals` | off | **on** | Zero-LLM. Free accuracy |
| `relationalRetrieval` | off | **on** | Zero-LLM |
| `contextual_retrieval` | none | **title** | Pure string concat. Free |
| `reranker` | off | **on, local** | Qwen3-Reranker 0.6B via llama.cpp — no API, no egress |
| `autocut` | off | **on** | Trustworthy only *because* the reranker fires |

The non-obvious part: `slm` is **not** a cheaper `conservative`. Conservative
exists to spend less money on a capable model, so it trims the free knobs too.
Here the bottleneck is the model's reasoning and local inference bills nothing, so
the zero-LLM retrieval arms all go back **on** — a weak generator needs better
retrieval, not less of it.

The reranker default is deliberately local: a reranker receives the query *and the
candidate document texts*, so a hosted one would ship your knowledge base to a
third party on every search. If you never launch llama-server, reranking fails
open and autocut disables itself, so search degrades rather than breaks.

### Local-only configuration

```bash
export GBRAIN_LOCAL_ONLY=1          # nothing leaves the machine; no silent cloud fallback
export GBRAIN_LOCAL_MODEL=ollama:qwen3.5:4b   # optional, this is the default

# REQUIRED: raise Ollama's context window before starting it (see below)
export OLLAMA_CONTEXT_LENGTH=16384
ollama serve &

ollama pull qwen3.5:4b && ollama pull nomic-embed-text
gbrain config set search.mode slm

# Optional: the local reranker (biggest accuracy lever for a small model)
llama-server --model qwen3-reranker-0.6b.gguf --alias qwen3-reranker-0.6b \
  --reranking --port 8081
```

All tiers deliberately resolve to the same local model: Ollama evicts and reloads weights when
the requested model changes, so a per-tier split would thrash RAM and add a cold start to every
tier crossing.

That includes **`gbrain think`**, the synthesis step. Upstream it runs on the `deep` tier
(Opus-class) — the most expensive route in the system, and the one that would otherwise ship every
retrieved page off-machine. Under `GBRAIN_LOCAL_ONLY` it resolves to the same local qwen as
everything else, and a test pins that so a future change to the tier chain can't quietly send
synthesis back to the cloud.

### Set `OLLAMA_CONTEXT_LENGTH` — this one bites silently

Neither gbrain nor any OpenAI-compatible client can set Ollama's `num_ctx` per request; it comes
from the model's Modelfile or the `OLLAMA_CONTEXT_LENGTH` environment variable read by
`ollama serve`. Ollama's default is small (2–4k depending on version), and when a prompt exceeds it
Ollama **truncates rather than erroring**.

That matters most for `think`, which sends the retrieved pages, takes and graph plus a compound JSON
schema in one call. Truncated silently, the model emits malformed or partial JSON, the parse fails,
and synthesis degrades with nothing in the logs pointing at the real cause. 16384 comfortably fits
the `slm` mode's 3000-token retrieval budget plus the system prompt and the JSON envelope.

### Verifying

```bash
cd gbrain && bun install
bun run typecheck
bun test test/ai/local-only-profile.test.ts test/ai/capabilities.test.ts
```

`bun run verify` is upstream CI tooling that does not survive vendoring — its guards resolve
their root via `git rev-parse --show-toplevel`, which now finds this repo rather than `gbrain/`.
`UPSTREAM.md` explains the workaround and records the upstream baseline.

## Architecture direction

A production version would replace the toy FTS index with a hybrid/vector retrieval layer and replace fake ticket actions with permissioned enterprise tools. The useful boundary is:

- **model:** local and relatively small;
- **knowledge:** external, private, and much larger than model context;
- **actions:** explicit allowlisted functions;
- **policy:** deterministic checks outside the model;
- **audit:** every retrieval and action logged.

This is the primitive needed for a later CommonTasks system where frequently solved employee tasks become reusable local skills rather than requiring a frontier model every time.
