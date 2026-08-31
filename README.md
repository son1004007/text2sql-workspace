# Text2SQL Workspace

**Multi-user LLM Data Query Service**

Text2SQL Workspace is a public, independently reproducible Python/FastAPI backend project for multi-user natural-language data queries.

The service does not treat model-generated SQL as trusted output. A request moves through explicit generation, validation, read-only execution and result-evaluation boundaries, while each user's workspace, query history and results remain isolated from other users.

## Verified in the current MVP

The current implementation has CI-backed coverage for:

- synthetic signed bearer-token identity for two demo users
- workspace create/list/read APIs with server-side ownership resolution
- cross-user workspace and query access denial
- persistent query history and retry attempts without overwriting prior attempts
- replaceable `Text2SqlModel` interface with deterministic fixture model
- natural-language question -> candidate SQL -> SQLGlot policy validation -> read-only query execution
- single-statement, SELECT-only and table-allowlist application policy
- explicit generation, validation and execution failure states
- proof that unsafe generated SQL is rejected before the executor is invoked
- result-based evaluation that separately counts generation, validation, execution and correctness
- deterministic SQLite tests for fast application-level verification
- Docker Compose runtime backed by PostgreSQL 17 and synthetic commerce data
- dedicated PostgreSQL analytics reader credential separated from application metadata state
- database-level read-only transactions and bounded statement execution
- direct runtime proof that the analytics reader can `SELECT` and cannot `INSERT`
- bounded network exposure: the application is published on loopback while PostgreSQL has no host-published port

The demo-token endpoint is intentionally **not production authentication**. It exists to make authenticated identity and authorization/isolation behavior reproducible in CI. Production identity-provider integration is outside the current evidence boundary.

## What this project is intended to prove

- multi-user backend design with explicit workspace ownership
- Python/FastAPI API design and service-layer boundaries
- LLM integration behind a replaceable model interface
- server-side validation of generated SQL before database execution
- defense in depth through both application SQL policy and database read-only privilege
- read-only and resource-bounded query execution
- explicit failure classification across generation, validation and execution
- reproducible query history and retry relationships
- result-based Text2SQL evaluation instead of SQL-string equality
- deterministic automated tests that do not require an external paid LLM
- runtime verification across FastAPI, PostgreSQL and Docker boundaries

## Core flow

```text
Authenticated user
  -> owned Workspace
  -> Natural-language question
  -> Text2SQL model
  -> SQL policy validation
  -> read-only analytics credential
  -> PostgreSQL query
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

The evaluation runner compares the actual columns and rows against explicit expected results. This allows different but semantically equivalent SQL to pass correctness, while SQL that executes successfully but returns the wrong answer fails correctness.

## Runtime separation

The bounded Docker runtime deliberately separates service state from analytics execution authority.

```text
FastAPI
  |- metadata state -> application-owned SQLite volume
  `- generated query -> PostgreSQL analytics_reader
                         |- SELECT: allowed
                         `- write: denied by DB privilege/read-only transaction
```

The PostgreSQL service is reachable only inside the Compose network. The demo API is published to `127.0.0.1:18000`; the PostgreSQL port is not published to the host.

## Current API surface

```text
POST /api/v1/auth/demo-token
POST /api/v1/evaluations/run
POST /api/v1/workspaces
GET  /api/v1/workspaces
GET  /api/v1/workspaces/{workspace_id}
POST /api/v1/workspaces/{workspace_id}/queries
GET  /api/v1/workspaces/{workspace_id}/queries
GET  /api/v1/workspaces/{workspace_id}/queries/{query_id}
POST /api/v1/workspaces/{workspace_id}/queries/{query_id}/retry
```

## Deterministic evaluation evidence

The current synthetic evaluation set contains two intentionally small cases:

- monthly order count
- sales by category

With the deterministic fixture model, the current bounded evaluation is:

```text
total cases:          2
generation success:   2
validation success:   2
execution success:    2
correctness success:  2
```

The same bounded evaluation is exercised against the PostgreSQL Docker runtime. This is a **system/evaluation-pipeline verification fixture**, not a claim that an external LLM has 100% Text2SQL accuracy. See [`docs/EVALUATION_EVIDENCE.md`](docs/EVALUATION_EVIDENCE.md).

## Docker/PostgreSQL verification

Run the full bounded runtime verification with:

```bash
python scripts/docker_e2e.py
```

The script creates a clean Compose environment, verifies the API and database boundaries, and removes containers and volumes afterward. CI runs the same E2E as a separate job from the Python test suite.

Verified runtime scenarios include:

1. application health
2. two-user authentication fixture
3. successful Text2SQL query against PostgreSQL
4. cross-user workspace denial
5. unsafe generated SQL rejected by application policy
6. result-based evaluation against PostgreSQL
7. loopback-only application host binding
8. no host-published PostgreSQL port
9. analytics reader `SELECT` succeeds
10. analytics reader write attempt fails

See [`docs/POSTGRES_DOCKER_EVIDENCE.md`](docs/POSTGRES_DOCKER_EVIDENCE.md) for the evidence boundary.

## Current synthetic questions

The deterministic model exists for reproducible CI and currently includes examples such as:

- `월별 주문 건수`
- `카테고리별 매출`
- `테이블 삭제 테스트` — intentionally returns unsafe SQL so the validation boundary can be tested

An external LLM adapter remains optional and will be added only as a separate bounded verification path. Core CI does not require an external model or API key.

## Security and disclosure boundary

This repository uses only synthetic or public data and independently designed code.

It does not contain company-owned source code, database schemas, SQL, prompts, customer identifiers, internal URLs, credentials or datasets.

The Docker Compose credential defaults are explicitly local demo values for an isolated synthetic environment. They are not production credential examples. Production authentication, production secret management, external/real LLM E2E, concurrency/load characterization and SLA claims remain outside the verified boundary.

See [`CURRENT_STATE.md`](CURRENT_STATE.md), [`TASKS.md`](TASKS.md) and [`ARCHITECTURE.md`](ARCHITECTURE.md) for the exact evidence boundary and remaining work.
