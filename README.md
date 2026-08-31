# Text2SQL Workspace

**Multi-user LLM Data Query Service**

Text2SQL Workspace is a public, independently reproducible Python/FastAPI backend project for multi-user natural-language data queries.

The service does not treat LLM-generated SQL as trusted output. A request moves through explicit generation, validation and read-only execution boundaries, while each user's workspace, query history and results remain isolated from other users.

## Verified in the current MVP slice

The current implementation has CI-backed coverage for:

- synthetic signed bearer-token identity for two demo users
- workspace create/list/read APIs with server-side ownership resolution
- cross-user workspace and query access denial
- persistent query history and retry attempts without overwriting prior attempts
- replaceable `Text2SqlModel` interface with deterministic fixture model
- natural-language question -> candidate SQL -> SQLGlot policy validation -> read-only query execution
- single-statement, SELECT-only and table-allowlist policy
- separate synthetic commerce analytics database
- bounded result rows and SQLite read-only/query-only execution
- explicit generation, validation and execution failure states
- proof that unsafe generated SQL is rejected before the executor is invoked

The demo-token endpoint is intentionally **not production authentication**. It exists to make authenticated identity and authorization/isolation behavior reproducible in CI. Production identity-provider integration is outside the current evidence boundary.

## What this project is intended to prove

- multi-user backend design with explicit workspace ownership
- Python/FastAPI API design and service-layer boundaries
- LLM integration behind a replaceable model interface
- server-side validation of generated SQL before database execution
- read-only and resource-bounded query execution
- explicit failure classification across generation, validation and execution
- reproducible query history and retry relationships
- deterministic automated tests that do not require an external paid LLM

## Core flow

```text
Authenticated user
  -> owned Workspace
  -> Natural-language question
  -> Text2SQL model
  -> SQL policy validation
  -> Read-only execution
  -> Result
  -> Query / attempt history
```

A generated SQL string is not considered a successful request by itself.

```text
generation success
!= validation success
!= execution success
!= result correctness
```

Result correctness evaluation is the next major capability; it is not yet claimed as implemented.

## Current API surface

```text
POST /api/v1/auth/demo-token
POST /api/v1/workspaces
GET  /api/v1/workspaces
GET  /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/queries
GET  /api/v1/workspaces/{workspace_id}/queries
GET  /api/v1/workspaces/{workspace_id}/queries/{query_id}
POST /api/v1/workspaces/{workspace_id}/queries/{query_id}/retry
```

## Current synthetic questions

The deterministic model exists for reproducible CI and currently includes examples such as:

- `월별 주문 건수`
- `카테고리별 매출`
- `테이블 삭제 테스트` — intentionally returns unsafe SQL so the validation boundary can be tested

An external LLM adapter will be added only after the deterministic service and evaluation gates are stable.

## Security and disclosure boundary

This repository uses only synthetic or public data and independently designed code.

It does not contain company-owned source code, database schemas, SQL, prompts, customer identifiers, internal URLs, credentials or datasets.

SQLite is currently used for deterministic public CI. PostgreSQL and Docker-based runtime verification remain planned and will not be claimed until implemented and tested.

See [`CURRENT_STATE.md`](CURRENT_STATE.md), [`TASKS.md`](TASKS.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md) for the exact evidence boundary and remaining work.
