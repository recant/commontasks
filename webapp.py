#!/usr/bin/env python3
"""Browser UI for CommonTasks.

Run:
    export OPENROUTER_API_KEY="..."
    python3 webapp.py
Then open:
    http://localhost:8000

The browser and synthetic company database are local; model inference is hosted
through OpenRouter using Liquid AI's free LFM2.5-2.6B endpoint by default.
"""

from __future__ import annotations

import json
import os
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from liquid_agent import MODEL, run_agent, seed_database

HOST = os.environ.get("COMMONTASKS_HOST", "127.0.0.1")
PORT = int(os.environ.get("COMMONTASKS_PORT", "8000"))
ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "web"


def build_prompt(message: str, history: list[dict[str, Any]]) -> str:
    """Give the hosted agent enough recent context to collect workflow details conversationally."""
    recent = history[-10:]
    lines = []
    for item in recent:
        role = str(item.get("role", "user")).strip().lower()
        content = str(item.get("content", "")).strip()
        if content:
            lines.append(f"{role.upper()}: {content}")

    if lines:
        return (
            "Continue this employee conversation. Use company-brain tools for company-specific facts and "
            "workflow procedures. Employee-specific details must come from the conversation, never from guesses.\n\n"
            "Recent conversation:\n"
            + "\n".join(lines)
            + f"\nUSER: {message}"
        )
    return message


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
            self._json(200, {"ok": True, "model": MODEL, "inference": "hosted"})
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

            prompt = build_prompt(message, history)
            answer = run_agent(prompt, verbose=False)
            self._json(200, {"answer": answer, "model": MODEL})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        print(f"[web] {self.address_string()} - {fmt % args}")


def main() -> None:
    info = seed_database(50_000)
    print(f"Ready: {info['knowledge_rows']:,} company-brain records in {info['database']}")
    print(f"Hosted model: {MODEL}")
    print(f"Open http://localhost:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
