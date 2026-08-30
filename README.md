# CommonTasks

A tiny proof-of-concept for a **local SLM that can use a large private database and take actions** without sending the database to a cloud model.

The demo runs **Qwen3.5-4B** locally through [Ollama](https://ollama.com/library/qwen3.5%3A4b), keeps organizational data in SQLite, exposes a few narrowly-scoped tools, and lets the model retrieve only the records it needs before acting on a fake employee-support ticket.

## What it demonstrates

```text
employee request
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

## Run it

1. Install [Ollama](https://ollama.com/).
2. Pull the model:

```bash
ollama pull qwen3.5:4b
```

3. Run the demo:

```bash
python demo.py
```

The default request is:

```text
Handle ticket 1001 using the company knowledge base.
```

Or ask your own:

```bash
python demo.py "Handle ticket 1002 and tell me what you changed"
```

On first run, the script creates `commontasks.db` with **50,000 synthetic knowledge records** plus three fake employee-support tickets.

### Test the large-database retrieval without Ollama

```bash
python demo.py --db-only
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

## Architecture direction

A production version would replace the toy FTS index with a hybrid/vector retrieval layer and replace fake ticket actions with permissioned enterprise tools. The useful boundary is:

- **model:** local and relatively small;
- **knowledge:** external, private, and much larger than model context;
- **actions:** explicit allowlisted functions;
- **policy:** deterministic checks outside the model;
- **audit:** every retrieval and action logged.

This is the primitive needed for a later CommonTasks system where frequently solved employee tasks become reusable local skills rather than requiring a frontier model every time.
