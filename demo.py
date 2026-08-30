#!/usr/bin/env python3
"""CommonTasks: small intranet model + large procedural-memory corpus.

No model training is required. The model retrieves procedures, reference material,
worked examples, and synthetic prior-agent cases from SQLite at inference time,
then applies the retrieved procedure to the employee's new case.

The model endpoint is expected to be inside the organization's network and expose
an OpenAI-compatible /v1/chat/completions API. No public-internet fallback exists.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

DB_PATH = Path(os.environ.get("COMMONTASKS_DB", "commontasks.db"))
MODEL_API_URL = os.environ.get(
    "COMMONTASKS_API_URL", "http://127.0.0.1:1234/v1/chat/completions"
)
MODEL_API_KEY = os.environ.get("COMMONTASKS_API_KEY", "local")
MODEL = os.environ.get("COMMONTASKS_MODEL", "LiquidAI/LFM2-2.6B")
SEED_VERSION = "procedural-memory-v1"

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS corpus (
    id INTEGER PRIMARY KEY,
    task TEXT NOT NULL,
    kind TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS corpus_fts USING fts5(
    task, kind, title, body, tags, content='corpus', content_rowid='id'
);
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

TASK_SPECS: list[dict[str, Any]] = [
    {
        "name": "weekly_status_update",
        "title": "Write a weekly status update",
        "description": "Turn rough work notes into the organization's standard concise weekly update.",
        "keywords": "weekly status update progress blockers priorities manager",
        "required": ["work_completed", "current_work", "blockers"],
        "procedure": [
            "Group information into Completed, In progress, Blockers, and Next.",
            "Prefer concrete outcomes over activity descriptions.",
            "Do not invent metrics, dates, owners, or completion status.",
            "Keep ordinary updates under 180 words unless the employee asks for detail.",
        ],
        "reference": "Managers prefer outcome-first bullets. Minor implementation details are omitted unless they affect schedule or risk.",
        "example_user": "This week I fixed export retries, met Acme about the pilot, and started billing alerts. Waiting on Finance for pricing.",
        "example_answer": "Completed: fixed export retries; met Acme and confirmed pilot requirements. In progress: billing alerts. Blocker: final pricing from Finance. Next: finish alerts and incorporate pricing into the pilot plan.",
    },
    {
        "name": "meeting_action_items",
        "title": "Extract decisions and action items from meeting notes",
        "description": "Convert messy notes into decisions, owners, actions, and unresolved questions.",
        "keywords": "meeting notes action items decisions owners follow-up",
        "required": ["meeting_notes"],
        "procedure": [
            "Separate explicit decisions from proposals or discussion.",
            "For each action, include owner and deadline only if stated.",
            "Put unstated owners or deadlines under Missing details rather than guessing.",
            "List unresolved questions separately.",
        ],
        "reference": "A decision requires clear agreement in the notes; silence or brainstorming is not a decision.",
        "example_user": "Decided to ship on Thursday. Maya will update docs Tuesday. Need somebody to ask Legal about the new terms.",
        "example_answer": "Decision: ship Thursday. Action: Maya — update docs — Tuesday. Missing owner: contact Legal about the new terms.",
    },
    {
        "name": "customer_support_response",
        "title": "Draft a support response from internal guidance",
        "description": "Use support policy and similar solved cases to produce a customer-facing response.",
        "keywords": "support customer reply bug issue response troubleshooting",
        "required": ["customer_problem"],
        "procedure": [
            "Restate the problem in one sentence.",
            "Give the shortest approved troubleshooting path from the corpus.",
            "Ask only for information required by that path.",
            "Never claim a fix was deployed or an account was changed unless the employee says it happened.",
        ],
        "reference": "Support replies should be concise, specific, and avoid exposing internal-only implementation details.",
        "example_user": "Customer says CSV export stays on 'processing' for 20 minutes.",
        "example_answer": "Acknowledge the stuck export, ask for workspace and approximate export time, then follow the export-job lookup procedure before suggesting a retry.",
    },
    {
        "name": "bug_report_triage",
        "title": "Turn a bug report into an engineering-ready triage",
        "description": "Structure an issue, identify missing reproduction data, and suggest the correct internal queue.",
        "keywords": "bug triage reproduction expected actual logs engineering issue",
        "required": ["problem_description"],
        "procedure": [
            "Extract observed behavior, expected behavior, reproduction steps, environment, and impact.",
            "Mark each missing field explicitly.",
            "Classify as UI, backend, data, auth, performance, or unknown using the evidence provided.",
            "Do not assign root cause without evidence.",
        ],
        "reference": "Engineering accepts incomplete reports, but reproduction steps and environment are the highest-value missing fields to request.",
        "example_user": "The dashboard is blank after I switch from Team A to Team B in Chrome.",
        "example_answer": "Observed: dashboard becomes blank after workspace switch. Environment: Chrome. Missing: version, console error, reproducibility, expected view. Queue: UI unless logs indicate an API/data failure.",
    },
    {
        "name": "incident_severity_triage",
        "title": "Classify an operational incident using the internal severity rubric",
        "description": "Apply the organization's incident rubric to a newly described outage or degradation.",
        "keywords": "incident severity sev outage degradation production impact users",
        "required": ["impact", "scope", "duration_or_start_time"],
        "procedure": [
            "Determine whether production is unavailable, materially degraded, or unaffected.",
            "Estimate scope only from supplied evidence: all users, a segment, one customer, or unknown.",
            "Apply the severity rubric in the reference record.",
            "State uncertainty and missing evidence; never lower severity because data is absent.",
        ],
        "reference": "SEV1: widespread production unavailability, confirmed data-loss risk, or critical security compromise. SEV2: major degradation or important customer segment blocked. SEV3: limited degradation/workaround exists. SEV4: minor issue/no material production impact.",
        "example_user": "Checkout errors for roughly 35% of requests for 12 minutes; no data loss seen.",
        "example_answer": "SEV2 under the rubric: major production degradation affecting a substantial share of checkout. Escalate if scope grows or data-loss evidence appears.",
    },
    {
        "name": "security_mfa_triage",
        "title": "Triage an unexpected MFA prompt",
        "description": "Follow the internal account-security response for suspicious authentication prompts.",
        "keywords": "security mfa prompt login suspicious authentication account",
        "required": ["what_happened"],
        "procedure": [
            "Tell the employee not to approve an unexpected prompt.",
            "Ask whether they initiated a login and whether any prompt was approved.",
            "If an unexpected prompt was approved, follow the suspected-compromise procedure immediately.",
            "Do not ask the employee to share passwords, recovery codes, or secrets.",
        ],
        "reference": "Unexpected MFA prompts are treated as possible credential compromise until Security rules that out.",
        "example_user": "I got two MFA pushes while I was at lunch. I didn't approve them.",
        "example_answer": "Do not approve further prompts. Report the event through the internal Security channel and confirm whether you initiated any login around that time.",
    },
    {
        "name": "phishing_report_triage",
        "title": "Triage a suspected phishing message",
        "description": "Classify what happened and select the correct internal containment steps.",
        "keywords": "phishing email link attachment credential security suspicious",
        "required": ["message_description", "interaction_status"],
        "procedure": [
            "Determine whether the employee only received the message, clicked a link, opened an attachment, or entered credentials.",
            "Use the corresponding containment path from the reference.",
            "Preserve the message for Security review; do not forward it to coworkers.",
            "Never ask for passwords or secrets.",
        ],
        "reference": "Received only: report and delete after capture. Clicked/opened: report immediately and follow endpoint checks. Credentials entered: treat as suspected compromise and start credential-reset/security response.",
        "example_user": "I clicked a fake DocuSign link but closed it before entering anything.",
        "example_answer": "Treat as clicked-link exposure: report immediately, preserve the message, and follow the endpoint-check path. No credential reset is implied unless credentials were entered or Security directs it.",
    },
    {
        "name": "software_access_review",
        "title": "Prepare a software-access request",
        "description": "Determine required details and approval path for SaaS or internal-system access.",
        "keywords": "software access permissions saas figma github notion admin",
        "required": ["application", "business_reason", "manager"],
        "procedure": [
            "Identify the application and requested access level if supplied.",
            "Capture the concrete business reason and approving manager.",
            "Privileged/admin access additionally requires duration and may trigger Security review.",
            "Never invent manager, access level, or duration.",
        ],
        "reference": "Standard collaboration access follows manager approval. Privileged or sensitive-system access requires least-privilege review and may require Security/system-owner approval.",
        "example_user": "I need Figma to edit launch mockups. My manager is Priya Shah.",
        "example_answer": "Complete standard request: application Figma; reason edit launch mockups; manager Priya Shah. Access level was not specified, so request standard access rather than admin.",
    },
    {
        "name": "expense_policy_check",
        "title": "Check an expense against reimbursement policy",
        "description": "Apply the internal expense rules to a specific purchase or reimbursement case.",
        "keywords": "expense reimbursement receipt cost center purchase finance",
        "required": ["merchant_or_item", "amount", "business_purpose", "receipt_status"],
        "procedure": [
            "Check category eligibility and any category-specific cap.",
            "Check receipt requirement.",
            "Identify missing submission fields.",
            "Distinguish 'appears eligible' from 'approved'; the model never approves spend.",
        ],
        "reference": "General expenses must be submitted within 30 days. Receipts are required at $25 or more. Remote-work equipment has a $500 calendar-year cap in this synthetic company.",
        "example_user": "Can I expense a $310 monitor for my home office? I have the receipt.",
        "example_answer": "It appears eligible as remote-work equipment and is below the $500 annual cap, assuming you have remaining stipend. Receipt requirement is satisfied. Final reimbursement still follows Finance review.",
    },
    {
        "name": "vendor_onboarding_review",
        "title": "Prepare a vendor-onboarding package",
        "description": "Collect vendor facts and determine which internal reviews are required.",
        "keywords": "vendor procurement onboarding security legal contract spend data",
        "required": ["vendor_name", "business_purpose", "owner", "annual_spend", "data_access", "contract_status"],
        "procedure": [
            "Capture vendor, owner, business purpose, annual spend, data access, and contract status.",
            "If company/customer data is accessed, add Security review.",
            "If contract terms are non-standard or unknown, add Legal review.",
            "Do not infer data sensitivity or contract status.",
        ],
        "reference": "Procurement owns vendor intake. Security review is mandatory for vendors handling sensitive data; Legal reviews non-standard agreements.",
        "example_user": "We want Acme Analytics, $18k/year, owned by Elena, to analyze customer usage data. They sent their paper.",
        "example_answer": "Procurement intake plus Security review because customer data is involved, and Legal review because vendor paper needs review. Missing: precise business purpose if 'analyze usage data' is not sufficient for the intake form.",
    },
    {
        "name": "travel_policy_check",
        "title": "Check a trip against business-travel policy",
        "description": "Apply travel rules and identify required approvals before booking.",
        "keywords": "travel flight hotel trip policy exception approval",
        "required": ["destination", "trip_purpose", "estimated_cost"],
        "procedure": [
            "Check whether the request is ordinary travel or an exception.",
            "Flag fare-class, budget, or booking-channel exceptions.",
            "State required approval before booking.",
            "Do not invent fares, dates, or manager approval.",
        ],
        "reference": "Use the company travel portal. Economy is standard for flights under 6 hours. Budget or policy exceptions require approval before booking.",
        "example_user": "Boston to London for a customer workshop, about $2,200. Can I book premium economy?",
        "example_answer": "This needs an exception review because the requested cabin differs from the default policy. Provide flight duration/itinerary and obtain approval before booking.",
    },
    {
        "name": "laptop_replacement_triage",
        "title": "Triage a laptop replacement request",
        "description": "Use IT replacement criteria to decide what information is needed and the appropriate route.",
        "keywords": "laptop replacement battery hardware device broken it",
        "required": ["current_device", "problem", "work_impact", "location"],
        "procedure": [
            "Distinguish cosmetic issues from safety, reliability, loss, or material work blockage.",
            "For lost devices, route to Security immediately.",
            "For battery swelling or other safety concern, tell the employee to stop using the device and follow IT safety procedure.",
            "Do not invent serial number or location.",
        ],
        "reference": "IT prioritizes unsafe, lost, failing, or materially work-blocking devices. Normal replacements enter IT review.",
        "example_user": "My MacBook battery lasts 25 minutes and it dies during customer calls. I'm in the Boston office.",
        "example_answer": "Replacement review is appropriate: failing battery materially blocks work. Required facts supplied except exact device model if 'MacBook' is too broad for asset lookup.",
    },
    {
        "name": "data_access_request_review",
        "title": "Prepare a data-access request",
        "description": "Apply least-privilege and data-sensitivity rules to a request for internal data.",
        "keywords": "data access database warehouse pii sensitive permission least privilege",
        "required": ["dataset_or_system", "business_reason", "access_needed", "duration"],
        "procedure": [
            "Identify the system/dataset, business reason, exact access needed, and duration.",
            "Determine sensitivity from the retrieved data-classification reference, not from guesses.",
            "Prefer read-only and time-bounded access when it satisfies the stated need.",
            "Sensitive data requires the corresponding data-owner/security approval.",
        ],
        "reference": "Customer-identifiable data and credentials are restricted. Broad production write access is never the default for analytical work.",
        "example_user": "I need read access to production customer events for two weeks to debug duplicate billing.",
        "example_answer": "Request is specific and time-bounded, but production customer events may be restricted. Route through data-owner approval and use the least-privileged read path available.",
    },
    {
        "name": "change_request_review",
        "title": "Review a production change request",
        "description": "Check a planned change for required rollout, validation, and rollback information.",
        "keywords": "change request production rollout rollback deployment maintenance",
        "required": ["change_summary", "impact_scope", "validation_plan", "rollback_plan"],
        "procedure": [
            "Check change scope and user impact.",
            "Verify a concrete validation plan exists.",
            "Verify rollback criteria and rollback steps exist.",
            "Flag missing owner, monitoring, or maintenance-window details when relevant.",
        ],
        "reference": "High-impact production changes require explicit validation and rollback. 'We can revert' is not a rollback plan unless steps and trigger are stated.",
        "example_user": "We will change the auth cache TTL from 5m to 30m for all users, monitor login errors, and revert the config if errors rise >1%.",
        "example_answer": "The request has scope, monitoring, rollback trigger, and rollback action. Missing: deployment owner and expected validation window if required by the change form.",
    },
    {
        "name": "deployment_readiness_check",
        "title": "Check whether a release is ready to deploy",
        "description": "Apply the release-readiness checklist to a specific release.",
        "keywords": "deploy release readiness tests rollback monitoring launch",
        "required": ["release_summary", "test_status", "monitoring_plan", "rollback_plan"],
        "procedure": [
            "Confirm required tests completed or explicitly note exceptions.",
            "Confirm monitoring covers the changed behavior.",
            "Confirm rollback is executable.",
            "List unresolved blockers; never declare 'safe' when required evidence is missing.",
        ],
        "reference": "Readiness means evidence is present, not that the model predicts nothing will go wrong.",
        "example_user": "Payments v2 passed unit and staging tests; canary dashboard is ready; rollback is feature-flag off. Load test is still running.",
        "example_answer": "Not fully ready under the checklist because the stated load test is unresolved. Other readiness elements are present.",
    },
    {
        "name": "postmortem_draft",
        "title": "Draft an incident postmortem from notes",
        "description": "Transform incident notes into timeline, impact, contributing factors, and follow-ups without inventing root cause.",
        "keywords": "postmortem incident timeline root cause contributing factors actions",
        "required": ["incident_notes"],
        "procedure": [
            "Build a factual timeline from timestamped evidence.",
            "Separate confirmed cause from hypotheses and contributing factors.",
            "Describe impact quantitatively only when numbers are supplied.",
            "Turn follow-ups into specific actions; leave owner/date blank when not supplied.",
        ],
        "reference": "Postmortems are blameless. Do not assign personal fault or convert an unverified hypothesis into root cause.",
        "example_user": "10:02 alerts fired. 10:08 on-call saw DB pool saturation. 10:14 rolled back release. 10:18 recovered. We think new retry logic amplified connections.",
        "example_answer": "Timeline: alerts 10:02; DB pool saturation identified 10:08; rollback 10:14; recovery 10:18. Suspected contributing factor: new retry logic; root cause remains unconfirmed.",
    },
    {
        "name": "project_status_risk_review",
        "title": "Review a project's status and risks",
        "description": "Use the portfolio-review format to separate progress, risks, dependencies, and decisions needed.",
        "keywords": "project status risk dependency milestone decision portfolio",
        "required": ["project_notes"],
        "procedure": [
            "Extract milestone status from explicit evidence.",
            "List risks with evidence and likely consequence, not invented probability.",
            "List external dependencies and decisions needed.",
            "Call out contradictory status claims.",
        ],
        "reference": "Green/yellow/red status must be justified by evidence. Missing schedule data means status may be 'unknown', not automatically green.",
        "example_user": "API done. Mobile integration is 2 weeks late because vendor SDK is unstable. Launch date hasn't changed yet.",
        "example_answer": "Progress: API complete. Risk: mobile integration is two weeks late due to vendor SDK instability. Dependency: vendor SDK. Schedule status is at least at risk; unchanged launch date is an assertion, not evidence the risk is resolved.",
    },
    {
        "name": "contract_intake_check",
        "title": "Check a contract package for intake completeness",
        "description": "Identify missing business/legal intake fields without giving legal advice.",
        "keywords": "contract legal intake agreement msa dpa terms review",
        "required": ["counterparty", "business_purpose", "contract_type", "commercial_value", "data_or_security_relevance"],
        "procedure": [
            "Check that the standard intake metadata is present.",
            "Identify whether privacy/security review is implicated from stated data handling.",
            "Flag non-standard paper for Legal review.",
            "Do not interpret legal rights, give legal advice, or approve terms.",
        ],
        "reference": "Legal intake requires counterparty, business owner/purpose, agreement type, value, term if known, and data/security relevance.",
        "example_user": "Acme sent a two-year MSA for $60k. They'll process customer email addresses for analytics.",
        "example_answer": "Intake implicates Legal plus privacy/security review because customer identifiers are processed. Missing: business owner/purpose and any known termination/renewal details requested by the form.",
    },
    {
        "name": "procurement_comparison",
        "title": "Compare vendor proposals using the internal rubric",
        "description": "Normalize proposals across cost, requirements, security, implementation, and contract status.",
        "keywords": "procurement compare vendors proposals cost security implementation",
        "required": ["proposal_details"],
        "procedure": [
            "Create a side-by-side comparison using only provided proposal facts.",
            "Separate hard requirements from preferences.",
            "Call out missing information rather than scoring it as zero.",
            "Do not make the final purchasing decision.",
        ],
        "reference": "Default comparison dimensions: total cost, required functionality, implementation effort, security/data posture, support, and contract exceptions.",
        "example_user": "Vendor A is $20k and has SSO, 2-week setup. Vendor B is $15k, SSO unclear, 1-week setup.",
        "example_answer": "A: $20k, SSO yes, 2-week setup. B: $15k, SSO unknown, 1-week setup. Key information gap: B's SSO support. Do not treat unknown SSO as absent until confirmed.",
    },
    {
        "name": "new_hire_onboarding_plan",
        "title": "Build a new-hire onboarding checklist",
        "description": "Generate the organization's role-aware onboarding plan from start-date and role details.",
        "keywords": "new hire onboarding start role access training manager",
        "required": ["role", "team", "start_date", "manager"],
        "procedure": [
            "Use the baseline onboarding checklist.",
            "Add role-specific access/training from the corpus.",
            "Separate day-one prerequisites from first-week tasks.",
            "Do not invent accounts or approvals already completed.",
        ],
        "reference": "Baseline: identity account, device, payroll/benefits orientation, security training, team intro, manager goals, and role-specific access.",
        "example_user": "New backend engineer starts Sept 14 on Payments; manager is Lee Chen.",
        "example_answer": "Day-one: identity/device, security training, team intro. First week: repo/CI access, development environment, Payments architecture walkthrough, manager goals. Exact production access should follow least-privilege policy.",
    },
    {
        "name": "research_paper_triage",
        "title": "Triage a research paper for an internal research team",
        "description": "Extract question, method, result, limitations, and relevance to an internal research objective.",
        "keywords": "research paper literature triage methods results limitations relevance",
        "required": ["paper_text_or_summary", "research_question"],
        "procedure": [
            "State the paper's research question and study design.",
            "Extract the main result without overstating causality.",
            "List major limitations visible in the supplied material.",
            "Assess relevance to the employee's stated research question, not general importance.",
        ],
        "reference": "Do not infer methods/results absent from the supplied paper text. Separate authors' claims from demonstrated evidence.",
        "example_user": "We care about whether intervention X changes biomarker Y. This paper reports a randomized 8-week study with n=84 and a 12% reduction vs 3% placebo.",
        "example_answer": "Directly relevant: randomized design measures the requested intervention/biomarker relationship. Main reported effect: 12% vs 3% reduction over 8 weeks. Need uncertainty estimates, attrition, and endpoint definition before judging strength.",
    },
    {
        "name": "lab_sample_qc",
        "title": "Review a lab sample against an internal QC checklist",
        "description": "Apply sample-acceptance and metadata-completeness rules for a research workflow.",
        "keywords": "lab sample qc quality control specimen metadata assay research",
        "required": ["sample_type", "collection_time", "storage_conditions", "assay", "observed_qc"],
        "procedure": [
            "Check metadata completeness.",
            "Compare storage/handling facts to the assay-specific reference.",
            "Flag QC values outside the documented range.",
            "Do not invent a pass/fail threshold; retrieve it from the corpus.",
        ],
        "reference": "This synthetic research workflow is for sample QC only, not clinical diagnosis. Thresholds are assay-specific and must come from the relevant protocol record.",
        "example_user": "Plasma, collected 09:20, frozen at -80C after 50 minutes, RNA assay, RIN 7.8.",
        "example_answer": "Metadata is mostly complete. Retrieve the RNA-assay handling window and RIN threshold before deciding whether the sample meets the research QC criteria.",
    },
    {
        "name": "clinical_case_abstraction",
        "title": "Structure a patient case for clinician review",
        "description": "Organize supplied patient information against an internal clinical-review checklist; not diagnosis or treatment.",
        "keywords": "patient clinical case chart labs medications symptoms timeline review",
        "required": ["case_details"],
        "procedure": [
            "Extract demographics supplied, presenting problem, timeline, relevant vitals/labs, medications, allergies, and major comorbidities.",
            "Identify missing fields required by the retrieved protocol.",
            "Summarize abnormal or changing values descriptively without independently diagnosing.",
            "Surface applicable protocol references for an authorized clinician; do not prescribe, diagnose, or make the final clinical decision.",
        ],
        "reference": "This demo supports chart abstraction and protocol lookup only. High-stakes diagnosis, prescribing, and treatment decisions remain with authorized clinicians.",
        "example_user": "67-year-old with fatigue; creatinine rose from 1.1 to 1.9 over two weeks; meds include lisinopril; no allergy info provided.",
        "example_answer": "Structured review: age 67; symptom fatigue; renal marker increased 1.1→1.9 over two weeks; lisinopril listed. Missing: allergies, current vitals, dose, other medications, relevant history, and protocol-specific fields. Route the structured summary and retrieved protocol to the clinician.",
    },
    {
        "name": "intelligence_report_summary",
        "title": "Analyze an internal intelligence report",
        "description": "Separate claims, evidence, source characterization, contradictions, and information gaps.",
        "keywords": "intelligence report source evidence claim confidence contradiction gap analyst",
        "required": ["report_text"],
        "procedure": [
            "Extract key claims and the evidence cited for each.",
            "Keep source statements separate from analyst inference.",
            "Identify contradictions and corroboration.",
            "List important information gaps and what evidence would resolve them.",
        ],
        "reference": "Confidence language must reflect the supplied sourcing and corroboration; never invent source access, reliability, or certainty.",
        "example_user": "Source A says the facility reopened Monday. Satellite note says vehicle activity resumed Tuesday. Source B says it remains closed but gives no date.",
        "example_answer": "Evidence is mixed: Source A and observed vehicle activity support resumed operations, while undated Source B conflicts. Gap: direct evidence of facility operations rather than perimeter activity.",
    },
    {
        "name": "executive_brief",
        "title": "Turn a long internal report into an executive brief",
        "description": "Produce a short judgment-evidence-uncertainty brief using the organization's format.",
        "keywords": "executive brief summary judgment evidence uncertainty leadership",
        "required": ["source_material", "audience_or_decision"],
        "procedure": [
            "Lead with 1-3 key judgments relevant to the stated audience/decision.",
            "Support each judgment with the strongest supplied evidence.",
            "State uncertainty and material dissent.",
            "End with decisions or follow-ups required, if any.",
        ],
        "reference": "The brief should be decision-relevant, not a section-by-section summary of the source material.",
        "example_user": "Leadership needs to decide whether to delay launch. QA found two severe bugs, one has a workaround; load test is 20% below target.",
        "example_answer": "Key judgment: launch carries material reliability risk because one severe bug lacks a stated workaround and load performance is below target. Decision needed: accept risk, remediate, or delay. Missing: user impact and remediation timeline.",
    },
    {
        "name": "regulatory_submission_check",
        "title": "Check a regulatory submission package for completeness",
        "description": "Compare a package against an internal filing checklist without making regulatory/legal judgments.",
        "keywords": "regulatory submission filing checklist completeness compliance",
        "required": ["submission_type", "package_contents"],
        "procedure": [
            "Retrieve the checklist for the named submission type.",
            "Mark each required artifact present, missing, or unclear.",
            "Identify version/date inconsistencies.",
            "Do not claim regulatory compliance or approval; route substantive interpretation to the responsible expert.",
        ],
        "reference": "Completeness checking is administrative support. Regulatory interpretation and sign-off remain with authorized staff.",
        "example_user": "Package includes cover letter, study report v3, labeling v2, and signed form; checklist also mentions statistical appendix.",
        "example_answer": "Present: cover letter, study report v3, labeling v2, signed form. Potentially missing: statistical appendix. Verify the submission-specific checklist and document versions before handoff.",
    },
    {
        "name": "policy_question_answering",
        "title": "Answer a recurring company-policy question",
        "description": "Retrieve the governing internal policy and answer a normal employee question without guessing.",
        "keywords": "policy faq pto benefits payroll office remote work company question",
        "required": ["question"],
        "procedure": [
            "Search for the narrowest applicable policy/reference.",
            "Answer from that record, not from generic model knowledge.",
            "Mention exceptions or missing eligibility facts that materially affect the answer.",
            "If no internal source supports the answer, say so.",
        ],
        "reference": "CommonTasks should prefer authoritative internal records over repeated chat snippets when they conflict.",
        "example_user": "How much can I spend on a home-office monitor?",
        "example_answer": "The synthetic remote-work policy allows up to $500 per calendar year for approved equipment, subject to normal expense rules and remaining annual allowance.",
    },
]

def _core_records() -> list[tuple[str, str, str, str, str]]:
    rows: list[tuple[str, str, str, str, str]] = []
    for spec in TASK_SPECS:
        required = ", ".join(spec["required"])
        procedure = "\n".join(f"{i+1}. {step}" for i, step in enumerate(spec["procedure"]))
        rows.append((
            spec["name"],
            "procedure",
            f"Procedure: {spec['title']}",
            f"Purpose: {spec['description']}\nRequired user inputs: {required}\nProcedure:\n{procedure}",
            f"procedure {spec['keywords']}",
        ))
        rows.append((
            spec["name"],
            "reference",
            f"Reference: {spec['title']}",
            spec["reference"],
            f"reference policy {spec['keywords']}",
        ))
        rows.append((
            spec["name"],
            "worked_example",
            f"Worked example: {spec['title']}",
            f"Employee input:\n{spec['example_user']}\n\nGood prior-agent output:\n{spec['example_answer']}",
            f"example prior-agent {spec['keywords']}",
        ))
    return rows

SOURCES = [
    "approved handbook",
    "internal wiki",
    "team runbook",
    "past assistant conversation",
    "resolved support thread",
    "operations note",
    "training example",
]

def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn

def seed_database(rows: int = 50_000) -> dict[str, Any]:
    """Build a large synthetic corpus of procedures, examples, and prior cases."""
    core = _core_records()
    rows = max(int(rows), len(core))
    conn = connect()
    try:
        version_row = conn.execute(
            "SELECT value FROM metadata WHERE key='seed_version'"
        ).fetchone()
        version = version_row[0] if version_row else None

        if version != SEED_VERSION:
            conn.execute("DELETE FROM corpus")
            conn.executemany(
                "INSERT INTO corpus(task,kind,title,body,tags) VALUES (?,?,?,?,?)", core
            )

            rng = random.Random(29)
            batch: list[tuple[str, str, str, str, str]] = []
            for i in range(rows - len(core)):
                spec = rng.choice(TASK_SPECS)
                source = rng.choice(SOURCES)
                variant = rng.choice([
                    "The employee supplied enough information to apply the procedure directly.",
                    "The prior assistant stopped and requested required fields rather than guessing.",
                    "The prior assistant used the reference record to resolve an organization-specific rule.",
                    "The case contained ambiguous evidence, so the prior assistant separated facts from uncertainty.",
                    "The result followed the standard output pattern and preserved missing information explicitly.",
                ])
                body = (
                    f"Synthetic prior case for task '{spec['name']}' derived from a {source}. "
                    f"{variant}\n"
                    f"Representative employee request: {spec['example_user']}\n"
                    f"Representative successful pattern: {spec['example_answer']}\n"
                    f"Case reference: {i + 1}."
                )
                batch.append((
                    spec["name"],
                    "prior_case",
                    f"Prior case {i + 1}: {spec['title']}",
                    body,
                    f"prior-case {spec['keywords']}",
                ))
                if len(batch) >= 1000:
                    conn.executemany(
                        "INSERT INTO corpus(task,kind,title,body,tags) VALUES (?,?,?,?,?)", batch
                    )
                    batch.clear()
            if batch:
                conn.executemany(
                    "INSERT INTO corpus(task,kind,title,body,tags) VALUES (?,?,?,?,?)", batch
                )

            conn.execute("INSERT INTO corpus_fts(corpus_fts) VALUES('rebuild')")
            conn.execute(
                "INSERT INTO metadata(key,value) VALUES('seed_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (SEED_VERSION,),
            )
            conn.commit()

        final_count = conn.execute("SELECT COUNT(*) FROM corpus").fetchone()[0]
        return {
            "database": str(DB_PATH),
            "corpus_rows": final_count,
            "tasks": len(TASK_SPECS),
            "seed_version": SEED_VERSION,
        }
    finally:
        conn.close()

def _fts_query(text: str) -> str:
    tokens = [
        "".join(ch for ch in token if ch.isalnum() or ch in "_-.")
        for token in text.split()
    ]
    tokens = [t for t in tokens if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in tokens[:16]) or '"help"'

def search_corpus(query: str, limit: int = 8) -> dict[str, Any]:
    """Search procedures, references, examples, and past cases."""
    limit = max(1, min(int(limit), 12))
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT c.id, c.task, c.kind, c.title,
                   snippet(corpus_fts, 3, '[', ']', ' … ', 38) AS excerpt
            FROM corpus_fts
            JOIN corpus c ON c.id=corpus_fts.rowid
            WHERE corpus_fts MATCH ?
            ORDER BY
                CASE c.kind
                    WHEN 'procedure' THEN 0
                    WHEN 'reference' THEN 1
                    WHEN 'worked_example' THEN 2
                    ELSE 3
                END,
                bm25(corpus_fts)
            LIMIT ?
            """,
            (_fts_query(query), limit),
        ).fetchall()
        return {"results": [dict(r) for r in rows]}
    finally:
        conn.close()

def get_corpus_record(record_id: int) -> dict[str, Any]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id,task,kind,title,body,tags FROM corpus WHERE id=?",
            (int(record_id),),
        ).fetchone()
        return {"record": dict(row) if row else None}
    finally:
        conn.close()

def get_task_context(task_name: str, example_limit: int = 3) -> dict[str, Any]:
    """Retrieve the procedural bundle for one known task."""
    example_limit = max(0, min(int(example_limit), 5))
    conn = connect()
    try:
        authoritative = conn.execute(
            """
            SELECT id,task,kind,title,body
            FROM corpus
            WHERE task=? AND kind IN ('procedure','reference','worked_example')
            ORDER BY CASE kind
                WHEN 'procedure' THEN 0
                WHEN 'reference' THEN 1
                ELSE 2 END
            """,
            (str(task_name),),
        ).fetchall()
        prior = conn.execute(
            """
            SELECT id,task,kind,title,body
            FROM corpus
            WHERE task=? AND kind='prior_case'
            ORDER BY id
            LIMIT ?
            """,
            (str(task_name), example_limit),
        ).fetchall()
        if not authoritative and not prior:
            return {"task": task_name, "records": [], "error": "task not found"}
        return {
            "task": task_name,
            "records": [dict(r) for r in [*authoritative, *prior]],
        }
    finally:
        conn.close()

def list_tasks() -> dict[str, Any]:
    return {
        "tasks": [
            {
                "name": spec["name"],
                "title": spec["title"],
                "description": spec["description"],
                "required_inputs": spec["required"],
            }
            for spec in TASK_SPECS
        ]
    }

TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "search_corpus": search_corpus,
    "get_corpus_record": get_corpus_record,
    "get_task_context": get_task_context,
    "list_tasks": list_tasks,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_corpus",
            "description": "Search the internal procedural-memory corpus for a task, procedure, reference, or similar prior case.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 12},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_corpus_record",
            "description": "Read one complete corpus record returned by search_corpus.",
            "parameters": {
                "type": "object",
                "properties": {"record_id": {"type": "integer"}},
                "required": ["record_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_task_context",
            "description": "Load the procedure, reference, worked example, and a few prior cases for a named task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_name": {"type": "string"},
                    "example_limit": {"type": "integer", "minimum": 0, "maximum": 5},
                },
                "required": ["task_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List the tasks represented in the internal corpus.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

SYSTEM_PROMPT = """You are CommonTasks, a small language model running entirely inside an organization's network.
There is no internet and no external-model fallback.

Your power comes from an internal procedural-memory corpus. It contains organization-specific procedures,
reference rules, worked examples, and synthetic prior-agent cases. You are not trained on these tasks.
You retrieve the relevant corpus at inference time and apply it to the employee's new details.

For substantive employee requests:
1. Search the corpus before answering.
2. Identify the best matching task.
3. Load that task with get_task_context.
4. Follow the retrieved procedure and reference rules.
5. Use worked examples as patterns only; never copy case-specific facts from an old example.
6. Employee/case-specific facts must come from the current conversation. If required inputs are missing, ask for them.
7. Never pretend to access the public internet or an external frontier model.
8. Never invent approvals, measurements, dates, identities, outcomes, or actions that were not provided.
9. For medical, legal, regulatory, security, or other high-stakes material, provide structured analysis/checklist support
   from the retrieved corpus but do not make the final authorized decision, diagnose, prescribe, or give legal sign-off.

Answer naturally. Do not explain the retrieval machinery unless the employee asks how CommonTasks works.
"""

def intranet_chat(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Call an OpenAI-compatible model server reachable only on the local network."""
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_SCHEMAS,
        "tool_choice": "auto",
        "temperature": 0.1,
    }).encode("utf-8")
    request = urllib.request.Request(
        MODEL_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MODEL_API_KEY}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"Intranet model API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach intranet model server at {MODEL_API_URL}. "
            "Start your local/on-prem OpenAI-compatible server or set COMMONTASKS_API_URL."
        ) from exc

def run_agent(user_prompt: str, max_steps: int = 10, verbose: bool = True) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    for step in range(max_steps):
        response = intranet_chat(messages)
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError(f"Intranet model returned no choices: {response}")
        raw = choices[0].get("message") or {}
        tool_calls = raw.get("tool_calls") or []
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": raw.get("content"),
        }
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        if not tool_calls:
            return (raw.get("content") or "").strip()

        for call in tool_calls:
            fn = call.get("function") or {}
            name = fn.get("name")
            raw_args = fn.get("arguments") or "{}"
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
            except json.JSONDecodeError:
                args = {}
            if name not in TOOLS:
                result = {"ok": False, "error": f"unknown tool: {name}"}
            else:
                try:
                    result = TOOLS[name](**args)
                except Exception as exc:
                    result = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            if verbose:
                print(f"[tool {step + 1}] {name}({json.dumps(args, ensure_ascii=False)})")
                print(json.dumps(result, indent=2, ensure_ascii=False)[:5000])
            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id"),
                "content": json.dumps(result, ensure_ascii=False),
            })

    return "Stopped after reaching the tool-call limit."

def deterministic_demo() -> None:
    """Show the corpus/retrieval path without needing a model server."""
    print(json.dumps(list_tasks(), indent=2)[:9000])
    print(json.dumps(search_corpus("analyze intelligence report claims sources contradictions", 6), indent=2))
    print(json.dumps(get_task_context("incident_severity_triage", 1), indent=2))

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Offline/intranet SLM + large procedural-memory corpus"
    )
    parser.add_argument("prompt", nargs="*", help="Employee request or case details")
    parser.add_argument("--seed", type=int, default=50_000)
    parser.add_argument("--db-only", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--list-tasks", action="store_true")
    args = parser.parse_args()

    info = seed_database(args.seed)
    print(
        f"Ready: {info['corpus_rows']:,} corpus records across "
        f"{info['tasks']} tasks in {info['database']}"
    )

    if args.list_tasks:
        for task in list_tasks()["tasks"]:
            print(f"- {task['name']}: {task['description']}")
        return 0

    if args.db_only:
        deterministic_demo()
        return 0

    prompt = " ".join(args.prompt).strip() or input("Ask CommonTasks: ").strip()
    if not prompt:
        return 0
    print(run_agent(prompt, verbose=not args.quiet))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())