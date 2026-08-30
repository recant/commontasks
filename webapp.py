#!/usr/bin/env python3
"""Browser UI for the CommonTasks procedural-memory demo."""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from demo import list_tasks, seed_database
from liquid_agent import MODEL, run_agent

HOST = os.environ.get("COMMONTASKS_HOST", "127.0.0.1")
PORT = int(os.environ.get("COMMONTASKS_PORT", "8000"))
ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"


def build_prompt(message: str, history: list[dict[str, Any]]) -> str:
    """Include recent employee context while leaving task knowledge in the corpus."""
    recent = history[-12:]
    lines: list[str] = []
    for item in recent:
        role = str(item.get("role", "user")).strip().lower()
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role.upper()}: {content}")

    if not lines:
        return message
    return (
        "Continue this employee conversation. Case-specific facts must come from this conversation. "
        "Retrieve the relevant procedure, reference, and examples from the corpus before doing the task.\n\n"
        "Recent conversation:\n"
        + "\n".join(lines)
        + f"\nUSER: {message}"
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def _json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if self.path == "/api/health":
            self._json(200, {
                "ok": True,
                "model": MODEL,
                "inference": "OpenRouter",
                "tasks": len(list_tasks()["tasks"]),
            })
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()

    def do_POST(self) -> None:
        if self.path != "/api/chat":
            self._json(404, {"error": "not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 1_000_000:
                raise ValueError("invalid request size")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            message = str(payload.get("message", "")).strip()
            history = payload.get("history") or []
            if not message:
                raise ValueError("message is required")
            if not isinstance(history, list):
                raise ValueError("history must be a list")

            answer = run_agent(build_prompt(message, history), verbose=False)
            self._json(200, {"answer": answer, "model": MODEL})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {fmt % args}")


def main() -> None:
    info = seed_database(50_000)
    print(
        f"Ready: {info['corpus_rows']:,} procedural-memory records across "
        f"{info['tasks']} tasks in {info['database']}"
    )
    print(f"Hosted model: {MODEL} via OpenRouter")
    print(f"Open http://localhost:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
