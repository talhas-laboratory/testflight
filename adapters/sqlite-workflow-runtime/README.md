# SQLite Workflow Runtime adapter

Durable, workspace-local storage for workflow run records and action idempotency results. It owns
SQLite schema and transaction behavior; workflow contracts remain provider-neutral. The database
is runtime state and must remain under ignored `.data/` storage.

The adapter uses insert-or-replace for phase transitions and insert-once for idempotency results.
An idempotency key can therefore replay a completed successful/partial action after process restart.
