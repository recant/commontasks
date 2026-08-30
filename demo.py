#!/usr/bin/env python3
"""CommonTasks: hosted small model + large private company brain + workflows.

The model is hosted on Groq rather than running on the employee device. Company
knowledge stays in SQLite. The model sees only small search results and explicit
workflow tools, never the entire knowledge base.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

DB_PATH = Path(os.environ.get("COMMONTASKS_DB", "commontasks.db"))
MODEL_API_URL = os.environ.get(
    "COMMONTASKS_API_URL", "https://api.groq.com/openai/v1/chat/completions"
)
MODEL_API_KEY = os.environ.get("GROQ_API_KEY") or os.environ.get("COMMONTASKS_API_KEY", "")
MODEL = os.environ.get("COMMONTASKS_MODEL", "llama-3.1-8b-instant")
SEED_VERSION = "company-brain-v2"

SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title, body, tags, content='knowledge', content_rowid='id'
);
CREATE TABLE IF NOT EXISTS workflow_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_name TEXT NOT NULL,
    details_json TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

# These are the high-signal records the model should usually retrieve. They are
# synthetic examples of the kind of recurring knowledge a GBrain-like ingestion
# layer could derive from Slack, docs, handbooks, FAQs, and past internal answers.
CORE_KNOWLEDGE = [
    (
        "FAQ: Paid time off and vacation",
        "Employees have 20 days of flexible PTO per calendar year plus company holidays. "
        "For 1-2 consecutive days, notify your manager in advance and add the time to the team calendar. "
        "For 3 or more consecutive workdays, request manager approval at least 2 weeks ahead when practical. "
        "Unused PTO does not roll over in this synthetic demo company.",
        "gbrain faq hr pto vacation time-off holidays manager",
    ),
    (
        "FAQ: Expense reimbursement",
        "Business expenses should be submitted within 30 days. A receipt is required for expenses of $25 or more. "
        "Every submission needs merchant, transaction date, amount and currency, business purpose, cost center, "
        "and receipt status. Reimbursements are normally included in the next payroll cycle after approval.",
        "gbrain faq finance expense reimbursement receipt cost-center payroll",
    ),
    (
        "Workflow: Submit an expense reimbursement",
        "Use workflow expense_reimbursement. Required employee-provided fields: merchant, transaction_date, "
        "amount, currency, business_purpose, cost_center, receipt_available. Never guess a missing field. "
        "If receipt_available is false and amount is at least $25, explain that Finance will require a receipt "
        "before approval. A completed submission enters pending_finance_review.",
        "gbrain workflow finance expense reimbursement receipt submit common-task",
    ),
    (
        "FAQ: Software and SaaS access",
        "Standard collaboration apps may be requested for a concrete business need. Access is least-privilege. "
        "The request must identify the application, business reason, and manager. Privileged/admin access also "
        "requires the requested duration. Security-sensitive systems may require an additional owner approval.",
        "gbrain faq it software access saas permissions figma github notion salesforce",
    ),
    (
        "Workflow: Request software access",
        "Use workflow software_access. Required employee-provided fields: application, business_reason, manager. "
        "Optional fields: access_level and duration. Never infer the employee's manager or business reason. "
        "Standard requests enter pending_manager_approval; privileged requests may require security review.",
        "gbrain workflow it software access request permissions figma github notion common-task",
    ),
    (
        "FAQ: New laptop or replacement laptop",
        "IT replaces devices that are failing, unsafe, lost, or materially blocking work. Employees should provide "
        "their current device type, the problem, work impact, and current location. Lost devices should be reported "
        "to Security immediately. Normal replacement requests are reviewed by IT and may require manager approval.",
        "gbrain faq it laptop computer replacement device hardware",
    ),
    (
        "Workflow: Request a laptop replacement",
        "Use workflow laptop_replacement. Required employee-provided fields: current_device, issue, work_impact, "
        "location. Never invent serial numbers, office location, or damage details. Completed requests enter "
        "pending_it_review.",
        "gbrain workflow it laptop replacement hardware common-task",
    ),
    (
        "FAQ: Business travel",
        "Book normal business travel through the company travel portal. Economy airfare is standard for flights "
        "under 6 hours. Trips expected to exceed the team budget or requiring an exception should be approved before "
        "booking. Employees should retain receipts for reimbursable out-of-pocket costs.",
        "gbrain faq finance travel airfare hotel booking expense",
    ),
    (
        "Workflow: Request a travel exception",
        "Use workflow travel_exception. Required employee-provided fields: destination, start_date, end_date, "
        "estimated_cost, exception_reason, manager. Completed requests enter pending_manager_approval. "
        "Do not invent itinerary or pricing.",
        "gbrain workflow travel exception finance manager common-task",
    ),
    (
        "FAQ: Health insurance and benefits",
        "New employees have 30 days from their start date to make benefit elections in the benefits portal. "
        "A qualifying life event can reopen enrollment. Questions involving a specific claim or medical situation "
        "should be directed to the benefits administrator rather than answered from general company policy.",
        "gbrain faq hr benefits health insurance enrollment",
    ),
    (
        "FAQ: Payroll, direct deposit, and address changes",
        "Employees can update direct deposit and home address in the payroll portal. Changes submitted at least "
        "5 business days before payroll are normally reflected in the next cycle. Payroll discrepancies should be "
        "reported to People Ops with the affected pay date and a description of the discrepancy.",
        "gbrain faq hr payroll direct-deposit address people-ops",
    ),
    (
        "FAQ: Password reset and account security",
        "Use the identity portal for routine password resets. If you suspect phishing, credential theft, an unknown "
        "MFA prompt, or a lost device, contact Security immediately and do not approve unexpected MFA requests.",
        "gbrain faq security password reset mfa phishing account",
    ),
    (
        "FAQ: Vendor and contractor onboarding",
        "New vendors require an internal owner, business purpose, expected annual spend, and disclosure of whether "
        "the vendor will access company or customer data. Legal review is required for non-standard contracts; "
        "Security review is required when a vendor handles sensitive data.",
        "gbrain faq procurement vendor contractor onboarding legal security",
    ),
    (
        "Workflow: Start vendor onboarding",
        "Use workflow vendor_onboarding. Required employee-provided fields: vendor_name, business_purpose, owner, "
        "expected_annual_spend, data_access, contract_status. Never infer whether a vendor handles sensitive data. "
        "Completed requests enter pending_procurement_review.",
        "gbrain workflow procurement vendor onboarding legal security common-task",
    ),
    (
        "FAQ: Remote-work equipment stipend",
        "Employees may expense up to $500 per calendar year for approved remote-work equipment such as a monitor, "
        "keyboard, webcam, or ergonomic accessories. The normal expense reimbursement rules still apply.",
        "gbrain faq hr finance remote-work stipend equipment",
    ),
    (
        "FAQ: Parental leave",
        "The synthetic company provides 16 weeks of paid parental leave for birth, adoption, or foster placement. "
        "Employees should contact People Ops to coordinate timing and any jurisdiction-specific paperwork.",
        "gbrain faq hr parental leave family people-ops",
    ),
    (
        "FAQ: Office visitors and guests",
        "Employees may host business visitors during normal office hours. Register visitors with reception before "
        "arrival and escort them in badge-controlled areas. Never lend an employee badge to a guest.",
        "gbrain faq office visitor guest reception badge security",
    ),
]

BRAIN_TOPICS = [
    ("PTO", "People Ops regularly reminds teams to put planned PTO on the team calendar and notify managers early."),
    ("expenses", "Finance regularly answers questions about receipts, cost centers, business purpose, and reimbursement timing."),
    ("software access", "IT access requests should state the app, why it is needed, and the approving manager."),
    ("laptops", "IT triage notes commonly distinguish cosmetic issues from problems that materially block work."),
    ("travel", "Finance reminders emphasize pre-approval for exceptions and keeping receipts for out-of-pocket costs."),
    ("benefits", "People Ops points employees to the benefits portal for elections and the administrator for claim-specific issues."),
    ("security", "Security reminders tell employees to report suspicious MFA prompts, phishing, and lost devices immediately."),
    ("vendors", "Procurement threads repeatedly ask for vendor owner, spend, contract status, and data-access details."),
    ("payroll", "People Ops commonly asks for the affected pay date when investigating a payroll discrepancy."),
    ("office access", "Workplace posts remind employees not to lend badges and to register visitors in advance."),
]

WORKFLOW_DEFS: dict[str, dict[str, Any]] = {
    "software_access": {
        "required": ["application", "business_reason", "manager"],
        "status": "pending_manager_approval",
    },
    "expense_reimbursement": {
        "required": [
            "merchant", "transaction_date", "amount", "currency",
            "business_purpose", "cost_center", "receipt_available",
        ],
        "status": "pending_finance_review",
    },
    "laptop_replacement": {
        "required": ["current_device", "issue", "work_impact", "location"],
        "status": "pending_it_review",
    },
    "travel_exception": {
        "required": ["destination", "start_date", "end_date", "estimated_cost", "exception_reason", "manager"],
        "status": "pending_manager_approval",
    },
    "vendor_onboarding": {
        "required": ["vendor_name", "business_purpose", "owner", "expected_annual_spend", "data_access", "contract_status"],
        "status": "pending_procurement_review",
    },
}


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def seed_database(rows: int = 50_000) -> dict[str, Any]:
    """Build a synthetic GBrain-derived company corpus plus workflow state."""
    rows = max(rows, len(CORE_KNOWLEDGE))
    conn = connect()
    try:
        version_row = conn.execute(
            "SELECT value FROM metadata WHERE key = 'seed_version'"
        ).fetchone()
        version = version_row[0] if version_row else None

        if version != SEED_VERSION:
            conn.execute("DELETE FROM knowledge")
            conn.execute("DELETE FROM workflow_runs")
            conn.executemany(
                "INSERT INTO knowledge(title, body, tags) VALUES (?, ?, ?)", CORE_KNOWLEDGE
            )

            rng = random.Random(11)
            batch: list[tuple[str, str, str]] = []
            for i in range(rows - len(CORE_KNOWLEDGE)):
                topic, snippet = rng.choice(BRAIN_TOPICS)
                channel = rng.choice(["Slack", "handbook", "wiki", "FAQ", "team note"])
                batch.append((
                    f"GBrain snapshot {i + 1}: {topic}",
                    f"Synthetic {channel} material summarized by the company-brain ingestion layer. {snippet} "
                    f"Snapshot reference {i + 1}.",
                    f"gbrain {channel.lower().replace(' ', '-')} {topic.lower().replace(' ', '-')}",
                ))
                if len(batch) >= 1000:
                    conn.executemany(
                        "INSERT INTO knowledge(title, body, tags) VALUES (?, ?, ?)", batch
                    )
                    batch.clear()
            if batch:
                conn.executemany(
                    "INSERT INTO knowledge(title, body, tags) VALUES (?, ?, ?)", batch
                )

            conn.execute("INSERT INTO knowledge_fts(knowledge_fts) VALUES('rebuild')")
            conn.execute(
                "INSERT INTO metadata(key, value) VALUES('seed_version', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (SEED_VERSION,),
            )
            conn.commit()

        final_count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        workflow_count = conn.execute("SELECT COUNT(*) FROM workflow_runs").fetchone()[0]
        return {
            "database": str(DB_PATH),
            "knowledge_rows": final_count,
            "workflow_runs": workflow_count,
            "seed_version": SEED_VERSION,
        }
    finally:
        conn.close()


def _fts_query(text: str) -> str:
    tokens = ["".join(ch for ch in token if ch.isalnum() or ch in "_-.") for token in text.split()]
    tokens = [t for t in tokens if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in tokens[:12]) or '"help"'


def search_knowledge(query: str, limit: int = 5) -> dict[str, Any]:
    """Search the private company brain without exposing the whole database."""
    limit = max(1, min(int(limit), 10))
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT k.id, k.title,
                   snippet(knowledge_fts, 1, '[', ']', ' … ', 32) AS excerpt,
                   k.tags
            FROM knowledge_fts
            JOIN knowledge k ON k.id = knowledge_fts.rowid
            WHERE knowledge_fts MATCH ?
            ORDER BY bm25(knowledge_fts)
            LIMIT ?
            """,
            (_fts_query(query), limit),
        ).fetchall()
        return {"results": [dict(r) for r in rows]}
    finally:
        conn.close()


def get_knowledge_record(record_id: int) -> dict[str, Any]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id, title, body, tags FROM knowledge WHERE id = ?", (int(record_id),)
        ).fetchone()
        return {"record": dict(row) if row else None}
    finally:
        conn.close()


def submit_workflow(workflow_name: str, details: dict[str, Any]) -> dict[str, Any]:
    """Validate user-supplied fields and create a synthetic workflow run."""
    spec = WORKFLOW_DEFS.get(str(workflow_name))
    if not spec:
        return {"ok": False, "error": "unknown workflow", "available": sorted(WORKFLOW_DEFS)}
    if not isinstance(details, dict):
        return {"ok": False, "error": "details must be an object"}

    cleaned = {str(k): v for k, v in details.items() if v is not None and str(v).strip() != ""}
    missing = [field for field in spec["required"] if field not in cleaned]
    if missing:
        return {
            "ok": False,
            "workflow_name": workflow_name,
            "missing_fields": missing,
            "message": "Ask the employee for these details. Do not guess them.",
        }

    # A deterministic policy check outside the model.
    if workflow_name == "expense_reimbursement":
        try:
            amount = float(cleaned["amount"])
        except (TypeError, ValueError):
            return {"ok": False, "error": "amount must be numeric"}
        receipt = cleaned["receipt_available"]
        has_receipt = receipt if isinstance(receipt, bool) else str(receipt).strip().lower() in {"true", "yes", "1"}
        if amount >= 25 and not has_receipt:
            return {
                "ok": False,
                "workflow_name": workflow_name,
                "policy_block": "A receipt is required for expenses of $25 or more.",
            }

    created_at = datetime.now(timezone.utc).isoformat()
    conn = connect()
    try:
        cursor = conn.execute(
            "INSERT INTO workflow_runs(workflow_name, details_json, status, created_at) VALUES (?, ?, ?, ?)",
            (workflow_name, json.dumps(cleaned, ensure_ascii=False), spec["status"], created_at),
        )
        conn.commit()
        return {
            "ok": True,
            "run_id": cursor.lastrowid,
            "workflow_name": workflow_name,
            "status": spec["status"],
            "details": cleaned,
        }
    finally:
        conn.close()


def get_workflow_run(run_id: int) -> dict[str, Any]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id, workflow_name, details_json, status, created_at FROM workflow_runs WHERE id = ?",
            (int(run_id),),
        ).fetchone()
        if not row:
            return {"run": None}
        data = dict(row)
        data["details"] = json.loads(data.pop("details_json"))
        return {"run": data}
    finally:
        conn.close()


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "search_knowledge": search_knowledge,
    "get_knowledge_record": get_knowledge_record,
    "submit_workflow": submit_workflow,
    "get_workflow_run": get_workflow_run,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search the private company brain for policies, FAQs, procedures, or workflows relevant to an employee question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "limit": {"type": "integer", "minimum": 1, "maximum": 10},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_knowledge_record",
            "description": "Read one complete company-brain record after finding its id with search_knowledge.",
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
            "name": "submit_workflow",
            "description": "Submit a synthetic internal workflow only after the employee has supplied every required detail. Never invent missing details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_name": {
                        "type": "string",
                        "enum": sorted(WORKFLOW_DEFS),
                    },
                    "details": {"type": "object", "additionalProperties": True},
                },
                "required": ["workflow_name", "details"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_workflow_run",
            "description": "Read a previously submitted synthetic workflow run by its run id.",
            "parameters": {
                "type": "object",
                "properties": {"run_id": {"type": "integer"}},
                "required": ["run_id"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are CommonTasks, an employee assistant for recurring company questions and workflows.
The private company brain is derived from synthetic GBrain-like internal sources such as Slack, handbooks,
wikis, FAQs, and repeated past answers. You do not know company-specific policy unless you retrieve it.

For a company-specific question, search the company brain and read the most relevant full record before answering.
For a workflow request, first retrieve the workflow/procedure. Never invent employee-specific facts such as a
manager, amount, date, location, application, business reason, receipt status, or vendor details. If required
information is missing, ask the employee for exactly what is missing. Only call submit_workflow when the employee
clearly wants the action taken and all required information has actually been provided in the conversation.
If a deterministic tool rejects a request, explain the policy block rather than bypassing it.

Do not refer to hidden ticket IDs or pretend a situation exists unless the employee described it. Keep answers
concise and useful. When answering from company knowledge, state the policy or procedure directly rather than
explaining the retrieval machinery.
"""


def hosted_chat(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Call a hosted OpenAI-compatible chat-completions endpoint (Groq by default)."""
    if not MODEL_API_KEY:
        raise RuntimeError(
            "Missing API key. Set GROQ_API_KEY (or COMMONTASKS_API_KEY) before starting CommonTasks."
        )

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
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"Hosted model API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach hosted model API at {MODEL_API_URL}: {exc}") from exc


def run_agent(user_prompt: str, max_steps: int = 8, verbose: bool = True) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for step in range(max_steps):
        response = hosted_chat(messages)
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError(f"Hosted model returned no choices: {response}")
        message = choices[0].get("message") or {}
        messages.append(message)
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            return (message.get("content") or "").strip()

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
                print(json.dumps(result, indent=2, ensure_ascii=False)[:3000])

            messages.append({
                "role": "tool",
                "tool_call_id": call.get("id"),
                "content": json.dumps(result, ensure_ascii=False),
            })

    return "Stopped after reaching the tool-call limit."


def deterministic_demo() -> None:
    """Exercise retrieval and workflow validation without calling the hosted model."""
    print(json.dumps(search_knowledge("How do I get Figma access?", 5), indent=2))
    print(json.dumps(search_knowledge("expense reimbursement receipt", 5), indent=2))
    print(json.dumps(
        submit_workflow(
            "software_access",
            {
                "application": "Figma",
                "business_reason": "Edit product mockups for the launch",
            },
        ),
        indent=2,
    ))


def main() -> int:
    parser = argparse.ArgumentParser(description="Hosted SLM + private company brain + common workflows")
    parser.add_argument("prompt", nargs="*", help="Employee question or workflow request")
    parser.add_argument("--seed", type=int, default=50_000, help="Number of synthetic company-brain records")
    parser.add_argument("--db-only", action="store_true", help="Test retrieval/workflow validation without model API")
    parser.add_argument("--quiet", action="store_true", help="Hide individual tool calls")
    args = parser.parse_args()

    info = seed_database(args.seed)
    print(f"Ready: {info['knowledge_rows']:,} company-brain records in {info['database']}")

    if args.db_only:
        deterministic_demo()
        return 0

    prompt = " ".join(args.prompt).strip()
    if not prompt:
        prompt = input("Ask CommonTasks: ").strip()
    if not prompt:
        return 0
    print(run_agent(prompt, verbose=not args.quiet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
