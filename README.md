# Text2SQL Workspace

**Multi-user LLM Data Query Service**

Text2SQL Workspace is a public, independently reproducible Python/FastAPI backend project for multi-user natural-language data queries.

The service does not treat LLM-generated SQL as trusted output. A request moves through explicit generation, validation, read-only execution and evaluation boundaries, while each user's workspace, query history and results remain isolated from other users.

## What this project is intended to prove

- multi-user backend design with explicit workspace ownership
- Python/FastAPI API design and service-layer boundaries
- LLM integration behind a replaceable model interface
- server-side validation of generated SQL before database execution
- read-only and resource-bounded query execution
- explicit failure classification across generation, validation, execution and evaluation
- reproducible query history and retry relationships
- deterministic automated tests that do not require an external paid LLM

## Core flow

```text
User
  -> Workspace
  -> Natural-language question
  -> Context selection
  -> Text2SQL model
  -> SQL validation
  -> Read-only execution
  -> Result / evaluation
  -> Query history
```

A generated SQL string is not considered a successful request by itself.

```text
generation success
!= validation success
!= execution success
!= result correctness
```

## Initial MVP

1. user authentication
2. workspace creation and ownership checks
3. query creation and history
4. replaceable Text2SQL model adapter
5. SELECT-only SQL validation
6. allow-listed schema/table boundary
7. single-statement enforcement
8. row-limit and execution-time boundary
9. read-only database access
10. explicit request states and failure reasons
11. deterministic evaluation fixtures
12. authorization, unsafe-SQL and model-failure E2E tests
13. Docker-based local execution
14. CI verification

## Security and disclosure boundary

This repository uses only synthetic or public data and independently designed code.

It does not contain company-owned source code, database schemas, SQL, prompts, customer identifiers, internal URLs, credentials or datasets.

## Planned status

The repository has just been initialized. Implementation status is tracked in [`CURRENT_STATE.md`](CURRENT_STATE.md) and [`TASKS.md`](TASKS.md).
