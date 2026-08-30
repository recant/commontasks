#!/usr/bin/env python3
"""Hosted Liquid AI agent for the Secret Agent demo.

The procedural-memory corpus stays in local SQLite. For the public demo, model
inference prefers Liquid AI's small model through OpenRouter. If Liquid is
unavailable or rate-limited, OpenRouter automatically falls back to its free
model router while preserving tool-calling requirements.
"""

from __future__ import annotations

import argparse
import json
import os
import urllib.error
import urllib.request
from typing import Any

from demo import TOOLS, TOOL_SCHEMAS, deterministic_demo, list_tasks, seed_database

PRODUCT_NAME = "Secret Agent"
MODEL_API_URL = os.environ.get(
    "COMMONTASKS_API_URL", "https://openrouter.ai/api/v1/chat/completions"
)
MODEL_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.environ.get(
    "COMMONTASKS_API_KEY", ""
)
MODEL = os.environ.get("COMMONTASKS_MODEL", "liquid/lfm-2.5-2.6b:free")
FALLBACK_MODEL = os.environ.get("COMMONTASKS_FALLBACK_MODEL", "openrouter/free")

SYSTEM_PROMPT = """You are Secret Agent, a small language model that performs recurring organizational tasks by reading a procedural-memory corpus at inference time.

The corpus contains organization-specific procedures, reference rules, worked examples, and synthetic prior-agent cases. You were not trained or fine-tuned on these organizational tasks. Retrieve the relevant corpus material and apply it to the employee's new details.

For substantive employee requests:
1. Search the corpus before answering.
2. Identify the best matching task.
3. Load that task with get_task_context.
4. Follow the retrieved procedure and reference rules.
5. Use worked examples as patterns only; never copy case-specific facts from an old example.
6. Employee/case-specific facts must come from the current conversation. If required inputs are missing, ask for them.
7. Do not use generic model knowledge to invent organization-specific policy or procedure.
8. Never invent approvals, measurements, dates, identities, outcomes, or actions that were not provided.
9. For medical, legal, regulatory, security, or other high-stakes material, provide structured analysis/checklist support from the retrieved corpus but do not make the final authorized decision, diagnose, prescribe, or give legal sign-off.

Answer naturally. Do not explain the retrieval machinery unless the employee asks how Secret Agent works.
"""


def hosted_chat(messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Call OpenRouter, preferring Liquid and falling back to another free tool-capable model."""
    if not MODEL_API_KEY:
        raise RuntimeError(
            "Missing API key. Set OPENROUTER_API_KEY before starting Secret Agent."
        )

    models = [MODEL]
    if FALLBACK_MODEL and FALLBACK_MODEL != MODEL:
        models.append(FALLBACK_MODEL)

    payload = json.dumps(
        {
            "models": models,
            "messages": messages,
            "tools": TOOL_SCHEMAS,
            "tool_choice": "auto",
            "temperature": 0.1,
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        MODEL_API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {MODEL_API_KEY}",
            "HTTP-Referer": "https://github.com/recant/commontasks",
            "X-OpenRouter-Title": PRODUCT_NAME,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")[:2000]
        if exc.code == 429:
            raise RuntimeError(
                "All configured free model routes are temporarily busy. Please retry shortly."
            ) from exc
        raise RuntimeError(f"OpenRouter returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach OpenRouter: {exc}") from exc


def run_agent(user_prompt: str, max_steps: int = 8, verbose: bool = True) -> str:
    """Run the procedural-memory retrieval loop using hosted inference."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]

    for step in range(max_steps):
        response = hosted_chat(messages)
        choices = response.get("choices") or []
        if not choices:
            raise RuntimeError(f"OpenRouter returned no choices: {response}")

        if verbose:
            served_model = response.get("model")
            if served_model:
                print(f"[model {step + 1}] {served_model}")

        raw_message = choices[0].get("message") or {}
        tool_calls = raw_message.get("tool_calls") or []
        assistant_message: dict[str, Any] = {
            "role": "assistant",
            "content": raw_message.get("content"),
        }
        if tool_calls:
            assistant_message["tool_calls"] = tool_calls
        messages.append(assistant_message)

        if not tool_calls:
            return (raw_message.get("content") or "").strip()

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

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.get("id"),
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    return "Stopped after reaching the tool-call limit."


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Secret Agent procedural-memory demo with Liquid + free fallback via OpenRouter"
    )
    parser.add_argument("prompt", nargs="*", help="Task plus the current case details")
    parser.add_argument("--seed", type=int, default=50_000)
    parser.add_argument("--db-only", action="store_true")
    parser.add_argument("--list-tasks", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    info = seed_database(args.seed)
    print(
        f"Ready: {info['corpus_rows']:,} procedural-memory records across "
        f"{info['tasks']} tasks in {info['database']}"
    )
    print(f"Preferred model: {MODEL} via OpenRouter")
    print(f"Fallback model: {FALLBACK_MODEL}")

    if args.list_tasks:
        print(json.dumps(list_tasks(), indent=2, ensure_ascii=False))
        return 0
    if args.db_only:
        deterministic_demo()
        return 0

    prompt = " ".join(args.prompt).strip() or input("Ask Secret Agent: ").strip()
    if not prompt:
        return 0
    print(run_agent(prompt, verbose=not args.quiet))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
