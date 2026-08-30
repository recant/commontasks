# CommonTasks

A proof-of-concept for a **hosted small language model that answers recurring employee questions and performs common company workflows using a large private knowledge store**.

The model does not run on the employee laptop. By default the demo calls Groq's hosted `llama-3.1-8b-instant`. The synthetic company knowledge remains in local SQLite, and the model only receives the small records returned by explicit retrieval tools.

The knowledge store is meant to stand in for information derived from a **GBrain-like company brain**: repeated Slack answers, handbooks, wikis, FAQs, policies, procedures, and past internal discussions.

## What the demo is now about

Employees should be able to ask normal questions such as:

- "How does PTO work?"
- "Can I expense a monitor for working from home?"
- "What should I do if I get a weird MFA prompt?"
- "How do I onboard a vendor?"

They can also ask CommonTasks to do recurring work:

- "I need Figma access so I can edit product mockups for the launch."
- "My laptop battery is failing and it dies in meetings. I need a replacement."
- "Submit my reimbursement for the $47.20 cab from the airport."

For workflows, CommonTasks retrieves the company procedure and then collects the employee-specific fields that procedure requires. It **must not invent missing details**. If a software-access workflow requires the application, business reason, and manager and the employee has only supplied the first two, CommonTasks asks for the manager before submitting anything.

## Architecture

```text
browser / employee request
        |
        v
local Python web server
        |
        +------> local SQLite company brain (~50,000 synthetic records)
        |             |
        |             +-- FAQ / policy / workflow retrieval
        |
        v
hosted small model (Groq by default)
        |
        +-- search_knowledge()
        +-- get_knowledge_record()
        +-- submit_workflow()
        +-- get_workflow_run()
```

The model never receives all 50,000 records. It searches, inspects the relevant record, and uses an allowlisted workflow tool when an action is appropriate.

## Company-brain data

On first run, `commontasks.db` is rebuilt with a `company-brain-v2` seed containing roughly 50,000 synthetic internal records.

High-signal records cover common topics such as:

- PTO and vacation
- expenses and reimbursement
- software/SaaS access
- laptop replacement
- business travel
- benefits
- payroll
- password/MFA/security incidents
- vendor onboarding
- remote-work equipment
- parental leave
- office visitors

The rest of the corpus simulates repeated material that a GBrain-style ingestion system could have summarized from Slack, internal FAQs, handbooks, wikis, and team notes. It exists to exercise retrieval over a knowledge base substantially larger than the model should receive in-context.

## Workflows

The demo currently includes these synthetic workflows:

- `software_access`
- `expense_reimbursement`
- `laptop_replacement`
- `travel_exception`
- `vendor_onboarding`

Each workflow has required fields enforced in Python, outside the model. `submit_workflow()` returns the exact missing fields rather than allowing the model to guess them. A deterministic expense rule also blocks reimbursements of $25 or more without a receipt.

Workflow submissions only write to the local synthetic `workflow_runs` table. They do not touch real company systems.

## Run it

You only need Python 3 and a Groq API key; Ollama is no longer used.

```bash
export GROQ_API_KEY="your_key_here"
python3 webapp.py
```

Then open:

```text
http://localhost:8000
```

The request path is:

```text
browser -> local Python server -> hosted small model
                              -> local SQLite company brain
                              -> local synthetic workflow runs
```

## Command-line use

Ask a normal company question:

```bash
python3 demo.py "How many PTO days do I get?"
```

Start a workflow conversationally:

```bash
python3 demo.py "I need Figma access to edit launch mockups"
```

CommonTasks should retrieve the software-access procedure and ask for any required detail you did not provide rather than inventing it.

### Test the database without any model API

```bash
python3 demo.py --db-only
```

This seeds the company brain, runs example searches, and deliberately attempts an incomplete software-access workflow so you can see the missing-field validation.

## Configuration

Defaults:

```text
COMMONTASKS_MODEL=llama-3.1-8b-instant
COMMONTASKS_API_URL=https://api.groq.com/openai/v1/chat/completions
COMMONTASKS_DB=commontasks.db
```

`GROQ_API_KEY` is used by default. You can instead set `COMMONTASKS_API_KEY` and point `COMMONTASKS_API_URL` at another OpenAI-compatible hosted chat-completions endpoint.

## Core design principle

CommonTasks should not be a giant chatbot that memorizes the company. The useful primitive is:

- **reasoning:** a cheap hosted small model;
- **company memory:** a much larger private external knowledge store;
- **retrieval:** only the relevant company information enters model context;
- **workflows:** reusable procedures discovered from company knowledge;
- **inputs:** employee-specific details must come from the employee or connected systems, never model guesses;
- **actions:** explicit allowlisted functions;
- **policy:** deterministic checks outside the model;
- **audit/state:** workflow runs are recorded separately from the language model.

A production version would replace the synthetic GBrain-like corpus with real permission-aware company data and replace the local workflow table with authenticated integrations into the systems employees already use.
