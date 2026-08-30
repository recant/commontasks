#!/usr/bin/env python3
"""CommonTasks: local SLM + large local database + safe actions demo.

This demo keeps company data in SQLite and gives a local Qwen3.5-4B model
small, explicit tools to search the database and update fake support tickets.
The model never receives the whole database; it asks for only the rows it needs.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

DB_PATH = Path(os.environ.get("COMMONTASKS_DB", "commontasks.db"))
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/chat")
MODEL = os.environ.get("COMMONTASKS_MODEL", "qwen3.5:4b")


SCHEMA = """
PRAGMA journal_mode=WAL;
CREATE TABLE IF NOT EXISTS knowledge (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    tags TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS tickets (
    id INTEGER PRIMARY KEY,
    employee TEXT NOT NULL,
    issue TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'open',
    note TEXT NOT NULL DEFAULT ''
);
CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
    title, body, tags, content='knowledge', content_rowid='id'
);
"""

RUNBOOKS = [
    (
        "Staging AUTH_TOKEN_MISMATCH after secret rotation",
        "If staging workers report AUTH_TOKEN_MISMATCH immediately after a secret rotation: "
        "(1) verify the deployment is healthy, (2) compare the worker SECRET_VERSION with the "
        "current Vault version, (3) if they differ, refresh the worker secret, (4) restart only "
        "the affected staging worker, (5) run /health/auth. Close the ticket only if the health "
        "check passes. Never apply this runbook to production without escalation.",
        "auth staging vault secret token worker",
    ),
    (
        "VPN certificate expired",
        "For an expired employee VPN certificate: confirm device ownership, revoke the old cert, "
        "issue a replacement certificate, ask the employee to reconnect, and verify a successful "
        "VPN session before closing the ticket.",
        "vpn certificate network remote-access",
    ),
    (
        "CI cache corruption",
        "For deterministic CI failures that disappear on a clean runner, invalidate the repository "
        "build cache, retry the failed job once, and attach the new run ID to the ticket. If the "
        "retry fails with the same error, leave the ticket open for engineering.",
        "ci build cache github actions",
    ),
]

FILLER_TOPICS = [
    "database connection pooling", "laptop disk encryption", "expense reimbursement",
    "service account rotation", "DNS troubleshooting", "on-call handoff", "package registry",
    "SSO enrollment", "container registry", "staging deployment", "printer setup",
    "incident severity", "data retention", "access review", "monitoring alert",
]


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    return conn


def seed_database(rows: int = 50_000) -> dict[str, Any]:
    """Create a sizable fake knowledge base plus demo support tickets."""
    if rows < len(RUNBOOKS):
        rows = len(RUNBOOKS)
    conn = connect()
    try:
        count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        if count == 0:
            conn.executemany(
                "INSERT INTO knowledge(title, body, tags) VALUES (?, ?, ?)", RUNBOOKS
            )
            rng = random.Random(7)
            batch = []
            for i in range(rows - len(RUNBOOKS)):
                topic = rng.choice(FILLER_TOPICS)
                batch.append((
                    f"Internal note {i + 1}: {topic}",
                    f"Synthetic internal documentation for {topic}. Reference record {i + 1}. "
                    "This filler record exists to make the retrieval demo operate over a larger "
                    "local corpus instead of placing all company information in the model context.",
                    topic.replace(" ", ","),
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

        ticket_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
        if ticket_count == 0:
            conn.executemany(
                "INSERT INTO tickets(id, employee, issue, status) VALUES (?, ?, ?, 'open')",
                [
                    (1001, "Alex", "Staging worker fails with AUTH_TOKEN_MISMATCH after this morning's secret rotation"),
                    (1002, "Morgan", "VPN says my certificate expired"),
                    (1003, "Jamie", "CI test job only fails on cached runners"),
                ],
            )
        conn.commit()
        final_count = conn.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        return {"database": str(DB_PATH), "knowledge_rows": final_count, "tickets": 3}
    finally:
        conn.close()


def _fts_query(text: str) -> str:
    tokens = ["".join(ch for ch in token if ch.isalnum() or ch in "_-.") for token in text.split()]
    tokens = [t for t in tokens if len(t) > 2]
    return " OR ".join(f'"{t}"' for t in tokens[:12]) or '"help"'


def search_knowledge(query: str, limit: int = 5) -> dict[str, Any]:
    """Search local organizational knowledge without exposing the whole DB to the model."""
    limit = max(1, min(int(limit), 10))
    conn = connect()
    try:
        rows = conn.execute(
            """
            SELECT k.id, k.title, snippet(knowledge_fts, 1, '[', ']', ' … ', 24) AS excerpt, k.tags
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


def get_ticket(ticket_id: int) -> dict[str, Any]:
    conn = connect()
    try:
        row = conn.execute(
            "SELECT id, employee, issue, status, note FROM tickets WHERE id = ?", (int(ticket_id),)
        ).fetchone()
        return {"ticket": dict(row) if row else None}
    finally:
        conn.close()


def add_ticket_note(ticket_id: int, note: str) -> dict[str, Any]:
    conn = connect()
    try:
        exists = conn.execute("SELECT 1 FROM tickets WHERE id = ?", (int(ticket_id),)).fetchone()
        if not exists:
            return {"ok": False, "error": "ticket not found"}
        conn.execute("UPDATE tickets SET note = ? WHERE id = ?", (str(note)[:2000], int(ticket_id)))
        conn.commit()
        return {"ok": True, "ticket_id": int(ticket_id), "note": str(note)[:2000]}
    finally:
        conn.close()


def set_ticket_status(ticket_id: int, status: str) -> dict[str, Any]:
    """Allow only benign demo-state transitions on the fake ticket database."""
    allowed = {"open", "in_progress", "resolved", "escalated"}
    if status not in allowed:
        return {"ok": False, "error": f"status must be one of {sorted(allowed)}"}
    conn = connect()
    try:
        exists = conn.execute("SELECT 1 FROM tickets WHERE id = ?", (int(ticket_id),)).fetchone()
        if not exists:
            return {"ok": False, "error": "ticket not found"}
        conn.execute("UPDATE tickets SET status = ? WHERE id = ?", (status, int(ticket_id)))
        conn.commit()
        return {"ok": True, "ticket_id": int(ticket_id), "status": status}
    finally:
        conn.close()


TOOLS: dict[str, Callable[..., dict[str, Any]]] = {
    "search_knowledge": search_knowledge,
    "get_knowledge_record": get_knowledge_record,
    "get_ticket": get_ticket,
    "add_ticket_note": add_ticket_note,
    "set_ticket_status": set_ticket_status,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "Search the local company knowledge database for relevant policies, runbooks, or past solutions.",
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
            "description": "Read one full knowledge record after finding its id with search_knowledge.",
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
            "name": "get_ticket",
            "description": "Read a fake employee support ticket.",
            "parameters": {
                "type": "object",
                "properties": {"ticket_id": {"type": "integer"}},
                "required": ["ticket_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add_ticket_note",
            "description": "Add a note to a fake support ticket after consulting relevant knowledge.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer"},
                    "note": {"type": "string"},
                },
                "required": ["ticket_id", "note"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_ticket_status",
            "description": "Change a fake ticket status. Valid values: open, in_progress, resolved, escalated.",
            "parameters": {
                "type": "object",
                "properties": {
                    "ticket_id": {"type": "integer"},
                    "status": {"type": "string", "enum": ["open", "in_progress", "resolved", "escalated"]},
                },
                "required": ["ticket_id", "status"],
            },
        },
    },
]

SYSTEM_PROMPT = """You are CommonTasks, a private local employee-support agent.
You have a large local database but cannot see it directly. Use tools to retrieve only what you need.
For ticket requests: read the ticket, search organizational knowledge, inspect the relevant full record,
then add a concise note and choose a status. Do not claim you performed real infrastructure actions;
this demo only changes the fake ticket database. If a runbook requires a real-world verification you
cannot perform, mark the ticket in_progress or escalated rather than resolved. Keep the final answer short.
"""


def ollama_chat(messages: list[dict[str, Any]]) -> dict[str, Any]:
    payload = json.dumps({
        "model": MODEL,
        "messages": messages,
        "tools": TOOL_SCHEMAS,
        "stream": False,
        "options": {"temperature": 0.1},
    }).encode("utf-8")
    request = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.load(response)
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Could not reach Ollama at {OLLAMA_URL}. Start Ollama and run: ollama pull {MODEL}"
        ) from exc


def run_agent(user_prompt: str, max_steps: int = 10, verbose: bool = True) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for step in range(max_steps):
        response = ollama_chat(messages)
        message = response.get("message", {})
        messages.append(message)
        tool_calls = message.get("tool_calls") or []

        if not tool_calls:
            return (message.get("content") or "").strip()

        for call in tool_calls:
            fn = call.get("function", {})
            name = fn.get("name")
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                args = json.loads(args)
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
                "tool_name": name,
                "content": json.dumps(result, ensure_ascii=False),
            })

    return "Stopped after reaching the tool-call limit."


def deterministic_demo(ticket_id: int = 1001) -> None:
    """Exercise the database/tool layer without requiring Ollama."""
    print(json.dumps(get_ticket(ticket_id), indent=2))
    hits = search_knowledge("AUTH_TOKEN_MISMATCH staging secret rotation", 3)
    print(json.dumps(hits, indent=2))
    if hits["results"]:
        record = get_knowledge_record(hits["results"][0]["id"])
        print(json.dumps(record, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Local SLM + large local DB + actions demo")
    parser.add_argument("prompt", nargs="*", help="Employee request for the local agent")
    parser.add_argument("--seed", type=int, default=50_000, help="Number of fake knowledge records")
    parser.add_argument("--db-only", action="store_true", help="Test retrieval without starting an SLM")
    parser.add_argument("--quiet", action="store_true", help="Hide individual tool calls")
    args = parser.parse_args()

    info = seed_database(args.seed)
    print(f"Ready: {info['knowledge_rows']:,} local knowledge records in {info['database']}")

    if args.db_only:
        deterministic_demo()
        return 0

    prompt = " ".join(args.prompt).strip() or "Handle ticket 1001 using the company knowledge base."
    try:
        answer = run_agent(prompt, verbose=not args.quiet)
    except RuntimeError as exc:
        print(exc, file=sys.stderr)
        return 2
    print("\n[agent]\n" + answer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
