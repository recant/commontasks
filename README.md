# CommonTasks

CommonTasks is a proof-of-concept for a **small language model that becomes much more useful by reading an organization's procedural memory at inference time**.

The model is **not trained or fine-tuned on the organization**. Instead, when an employee asks it to do something, it retrieves the relevant internal procedure, reference rules, worked examples, and similar prior-agent cases from a local corpus and applies that material to the employee's new details.

The intended deployment is **offline / intranet-only**. There is no OpenRouter, Claude, GPT, Groq, or public-internet fallback in the app. The default configuration expects an OpenAI-compatible model server reachable on the local machine or private network.

## Core idea

```text
employee gives a new case
        |
        v
small intranet SLM
        |
        +--> search_corpus("what task is this?")
        |
        +--> get_task_context(task)
                  |
                  +-- procedure
                  +-- reference rules
                  +-- worked example
                  +-- similar prior cases
        |
        v
SLM applies that procedure to the NEW details
        |
        v
structured answer / analysis / draft
```

The SLM does not have to memorize every company process in its weights. The corpus supplies the organization-specific knowledge at inference time.

For example, the employee can say:

```text
Analyze this incident: checkout is failing on about 35% of requests,
it started 12 minutes ago, and we have no evidence of data loss.
```

CommonTasks retrieves the internal incident-severity procedure and rubric, sees a worked example, and then applies that rubric to the new incident.

Or:

```text
Analyze these notes as an intelligence report:
Source A says the facility reopened Monday. Satellite reporting shows
vehicle activity Tuesday. Source B says it remains closed but gives no date.
```

The SLM retrieves the internal analysis procedure telling it how to separate claims, evidence, contradictions, source statements, inference, and information gaps. It then applies that procedure to the supplied report.

## The corpus

On first run, `commontasks.db` is seeded with **50,000 synthetic procedural-memory records** across **27 task families**.

Each task has three high-signal records:

1. **Procedure** — how the organization performs the task and what inputs are required.
2. **Reference** — organization-specific rules, thresholds, rubrics, or constraints.
3. **Worked example** — a representative employee input and a good prior-agent output.

That produces 81 authoritative/high-signal records. The rest of the 50,000-row corpus consists of synthetic prior cases derived from things such as past assistant conversations, internal wikis, runbooks, resolved support threads, operations notes, and training examples.

Those prior cases are not treated as authoritative facts. They are patterns the SLM can use after it retrieves the governing procedure/reference.

## Tasks currently represented

The demo corpus contains these 27 task families:

- `weekly_status_update` — turn rough work notes into the standard weekly update
- `meeting_action_items` — extract decisions, owners, actions, and missing owners/deadlines
- `customer_support_response` — draft a support reply using approved internal guidance
- `bug_report_triage` — turn a vague bug report into engineering-ready triage
- `incident_severity_triage` — apply the internal SEV rubric to a new incident
- `security_mfa_triage` — follow the procedure for unexpected MFA prompts
- `phishing_report_triage` — select the correct containment path from what the employee did
- `software_access_review` — prepare an access request and identify required approvals
- `expense_policy_check` — apply reimbursement rules to a specific expense
- `vendor_onboarding_review` — prepare vendor intake and determine Legal/Security review paths
- `travel_policy_check` — apply travel rules and flag exceptions before booking
- `laptop_replacement_triage` — apply IT replacement/safety criteria to a device problem
- `data_access_request_review` — apply least-privilege and data-sensitivity rules
- `change_request_review` — check a production change for validation and rollback completeness
- `deployment_readiness_check` — apply the release-readiness checklist
- `postmortem_draft` — turn incident notes into a factual blameless postmortem draft
- `project_status_risk_review` — extract milestone evidence, risks, dependencies, and decisions
- `contract_intake_check` — check Legal intake completeness without giving legal advice
- `procurement_comparison` — normalize vendor proposals using the internal comparison rubric
- `new_hire_onboarding_plan` — build a role-aware onboarding checklist
- `research_paper_triage` — extract question, design, result, limitations, and internal relevance
- `lab_sample_qc` — apply a research sample QC checklist and retrieve assay-specific rules
- `clinical_case_abstraction` — structure a patient case and retrieve protocol/checklist context for clinician review
- `intelligence_report_summary` — separate claims, evidence, contradictions, inference, and gaps
- `executive_brief` — turn long source material into a short decision-relevant brief
- `regulatory_submission_check` — compare a filing package to the internal completeness checklist
- `policy_question_answering` — answer ordinary employee policy questions from authoritative internal records

The clinical task is deliberately limited to **chart abstraction and protocol lookup**. It does not diagnose, prescribe, or make final clinical decisions.

## Why this is different from training

No gradient updates happen. There is no per-employee fine-tune and no LoRA.

Conceptually:

```text
base SLM
  +
retrieved organization procedure
  +
retrieved reference/rubric
  +
retrieved examples of how this task is normally handled
  +
new employee-provided case details
  =
answer
```

This means an organization can change a procedure by changing the corpus rather than retraining the model.

## Retrieval tools

The SLM gets four narrow tools:

- `search_corpus(query)` — search the entire 50,000-record corpus
- `get_corpus_record(record_id)` — read one complete result
- `get_task_context(task_name)` — load the procedure, reference, worked example, and a few prior cases for a task
- `list_tasks()` — inspect the task catalog

The system prompt tells the SLM to search before doing substantive work and to request missing case-specific inputs rather than copying facts from an old example.

## Offline / intranet inference

By default CommonTasks expects an OpenAI-compatible inference server at:

```text
http://127.0.0.1:1234/v1/chat/completions
```

The default model identifier is:

```text
LiquidAI/LFM2-2.6B
```

Both values are configurable. Your local model server may expose the model under a different identifier.

```bash
export COMMONTASKS_API_URL="http://127.0.0.1:1234/v1/chat/completions"
export COMMONTASKS_MODEL="LiquidAI/LFM2-2.6B"
export COMMONTASKS_API_KEY="local"
python3 webapp.py
```

Then open:

```text
http://localhost:8000
```

For an enterprise/air-gapped deployment, `COMMONTASKS_API_URL` can point to an inference server elsewhere on the private network instead of localhost.

There is intentionally **no external-provider fallback**. If the intranet model server cannot be reached, CommonTasks errors rather than sending the request somewhere else.

## Test the corpus without any model

You can verify database construction and retrieval without starting an SLM:

```bash
python3 demo.py --db-only
```

List the 27 tasks:

```bash
python3 demo.py --list-tasks
```

Or inspect retrieval from Python/CLI while developing.

## Example prompts

```text
Turn these messy meeting notes into decisions and action items: ...
```

```text
Review this production change: we are changing auth cache TTL from 5m to 30m...
```

```text
Triage this bug: the dashboard goes blank after switching workspaces in Chrome...
```

```text
Compare these two vendor proposals using our procurement rubric: ...
```

```text
Triage this paper for our question of whether intervention X changes biomarker Y: ...
```

```text
Structure this patient case for clinician review: age 67, fatigue, creatinine 1.1 to 1.9...
```

The important behavior is that the employee supplies **the current case facts**. The corpus supplies **how this organization handles that kind of case**.

## Design principle

The goal is not to prove that a 2.6B model has the same general intelligence as a frontier model.

The goal is to test whether, inside a fixed organization, a smaller model can perform a much larger share of useful work when the difficult organization-specific knowledge has already been externalized as searchable procedural memory:

```text
general language/reasoning ability      -> SLM
how our organization does this task     -> corpus
similar good past behavior              -> worked examples / prior cases
facts about this specific situation     -> employee input
```

That is the CommonTasks thesis.