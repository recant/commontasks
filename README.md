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

### Local-only configuration

```bash
export GBRAIN_LOCAL_ONLY=1          # nothing leaves the machine; no silent cloud fallback
export GBRAIN_LOCAL_MODEL=ollama:qwen3.5:4b   # optional, this is the default
ollama pull qwen3.5:4b && ollama pull nomic-embed-text
```

All tiers deliberately resolve to the same local model: Ollama evicts and reloads weights when
the requested model changes, so a per-tier split would thrash RAM and add a cold start to every
tier crossing.

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
