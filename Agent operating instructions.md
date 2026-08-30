# Agent Layer

The agent layer defines how the small language model interacts with Clarion Health's organizational memory.

The SLM is responsible for understanding the employee's request and composing the final response. Deterministic retrieval functions are responsible for finding evidence from the knowledge graph.

## Architecture

Employee question
→ intent and entity extraction
→ skill selection
→ deterministic graph retrieval
→ evidence validation
→ confidence decision
→ SLM answer composition
→ citations

The SLM must never write SQL or directly query raw database tables.

## Files

| File | Purpose |
|---|---|
| `decision_policy.md` | Overall agent behavior and decision rules |
| `skill_policy.yaml` | Machine readable source of truth for the 12 atomic skills |
| `classification_examples.json` | Examples for intent and entity classification |
| `response_examples.md` | Gold standard response patterns |

## Atomic skills

1. recall
2. timeline
3. person
4. decision
5. follow_up
6. change
7. frequency
8. consensus
9. contradiction
10. evidence
11. routing
12. gap

## Design principle

The system makes the small model more capable by giving it structured organizational memory and reliable retrieval tools. The model handles language at the edges; deterministic code handles retrieval and evidence checks.
