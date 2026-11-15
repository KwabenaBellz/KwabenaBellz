# Agent Execution Guard — reproducible engineering demonstration

This is a new, independent, synthetic Python work sample demonstrating reliable AI-agent side effects. It uses no customer records, JPL data, private Sovereign source code, API keys, live email accounts or paid services.

## How to run

Python 3.10+ with no third-party dependencies.

Run: python -m unittest discover -v
Run: python demo.py

The second command writes sample_trace.json showing:
1. Human approval required before effect.
2. A deliberate transient 503 failure and bounded retry.
3. Receipt verification after successful provider action.
4. Restart recovery from a durable SQLite action journal.
5. Suppression of duplicate job execution.
6. Explicit refusal of changed payload with an existing idempotency key.

IMPORTANT: This fake provider honors an idempotency key. Real APIs might not. A crash between an external action and saving its receipt can leave an ambiguous result. Do not promise exactly-once execution without provider-level idempotency or a reconciliation protocol.

## Buyer application

Work sample for a fixed-scope, paid repair of existing Python/agent automations. A reasonable experimental quote is USD 350-500 after examining the real integration, with buyer-approved scope, milestones and acceptance criteria. This is a proposed quote, not a verified market price.

Acceptance criteria for a real pilot: reproduce one specific failure; implement retries/approval/idempotency as supported; verify actual external results safely; produce independent tests, rollback instructions, and an audit report.

This work sample does not prove an external customer deployment or commercial revenue. Ownership of any existing production Sovereign/JPL source must be separately established before distribution.