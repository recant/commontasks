# CommonTasks

CommonTasks is a proof-of-concept for a **small language model that becomes much more useful by reading an organization's procedural memory at inference time**.

The model is **not trained or fine-tuned on the organization**. When an employee asks it to do something, CommonTasks retrieves the relevant internal procedure, reference rules, worked examples, and similar prior-agent cases from a local corpus. It then gives only that compact context plus the employee's new case details to a small model, which applies the retrieved procedure.

For this demo, inference uses **Liquid AI LFM2.5-2.6B through OpenRouter**. The 50,000-row synthetic company corpus stays in local SQLite; the whole database is never sent to OpenRouter.

## Core idea

```text
employee gives a new case
        |
        v
CommonTasks retrieval layer
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
small Liquid model via OpenRouter
        |
        v
apply procedure to the NEW details
        |
        v
structured answer / analysis / draft
```

The SLM does not have to memorize every company process in its weights. The corpus supplies the organization-specific knowledge at inference time.

For example:

```text
Analyze this incident: checkout is failing on about 35% of requests,
it started 12 minutes ago, and we have no evidence of data loss.
```

CommonTasks retrieves the internal incident-severity procedure, rubric, worked example, and similar historical cases. Liquid then applies that material to the new incident.

Or:

```text
Analyze these notes as an intelligence report:
Source A says the facility reopened Monday. Satellite reporting shows
vehicle activity Tuesday. Source B says it remains closed but gives no date.
```

The model retrieves the internal procedure for separating claims, evidence, contradictions, inference, and information gaps, then uses that procedure on the supplied notes.

## The corpus

On first run, `commontasks.db` is seeded with **50,000 synthetic procedural-memory records** across **27 task families**.

Each task has three authoritative/high-signal records:

1. **Procedure** — how the organization performs the task and what inputs are required.
2. **Reference** — organization-specific rules, thresholds, rubrics, or constraints.
3. **Worked example** — a representative employee input and a good prior-agent output.

That produces 81 authoritative records. The remaining rows simulate prior cases derived from past assistant conversations, wikis, runbooks, resolved support threads, operations notes, and training examples. Prior cases are examples, not authoritative policy.

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

The clinical demo is limited to **case abstraction and protocol/checklist lookup for clinician review**; it is not a diagnosis/prescribing system.

## Why this is different from training

No gradient updates happen. There is no employee fine-tune and no LoRA.

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

If the organization changes a process, it changes the corpus rather than retraining the model.

## Retrieval tools

The SLM gets four narrow tools:

- `search_corpus(query)` — search the 50,000-record corpus
- `get_corpus_record(record_id)` — read one complete result
- `get_task_context(task_name)` — load the procedure, reference, worked example, and a few prior cases
- `list_tasks()` — inspect the task catalog

The employee supplies the **current case facts**. Old examples may teach format/procedure, but their case-specific details must not be copied into the new case.

## Run the demo with Liquid + OpenRouter

Create an OpenRouter API key, then:

```bash
export OPENROUTER_API_KEY="your_key_here"
python3 webapp.py
```

Open:

```text
http://localhost:8000
```

The browser path is:

```text
browser
  -> local Python server
  -> local SQLite procedural-memory retrieval
  -> selected procedure/reference/examples
  -> OpenRouter
  -> liquid/lfm-2.5-2.6b:free
  -> answer
```

The default model and endpoint are:

```text
COMMONTASKS_MODEL=liquid/lfm-2.5-2.6b:free
COMMONTASKS_API_URL=https://openrouter.ai/api/v1/chat/completions
```

You can also use the command-line Liquid agent:

```bash
python3 liquid_agent.py "Triage this bug: the dashboard goes blank after switching workspaces in Chrome"
```

List the supported task families:

```bash
python3 liquid_agent.py --list-tasks
```

Test only the corpus/retrieval layer without making a model request:

```bash
python3 liquid_agent.py --db-only
```

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

## Privacy note

This repository contains synthetic demo data. The OpenRouter demo is not the architecture you would use for a genuinely air-gapped organization. The point of this version is to cheaply demonstrate that a small model can gain substantial task capability from retrieved procedural memory without any training.

## CommonTasks thesis

```text
general language/reasoning ability      -> small Liquid model
how our organization does this task     -> corpus
similar good past behavior              -> worked examples / prior cases
facts about this specific situation     -> employee input
```

The experiment is whether a small model can perform a much larger share of useful organizational work when the difficult organization-specific knowledge has already been externalized as searchable procedural memory.