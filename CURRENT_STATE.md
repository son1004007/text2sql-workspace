# Current State

- date: 2026-08-31
- phase: multi-user Text2SQL vertical slice
- public repository: yes
- implementation status: P1/P2 implemented, P3 partial
- verification status: GitHub Actions test suite passing on the feature branch; final merge gate pending latest branch run

## Confirmed decisions

- project name: `Text2SQL Workspace`
- positioning: `Multi-user LLM Data Query Service`
- primary stack direction: Python / FastAPI / PostgreSQL
- deterministic public CI currently uses SQLite; PostgreSQL runtime evidence is still pending
- multi-user workspace isolation is a first-class requirement
- LLM output is treated as untrusted input
- SQL must pass server-side policy validation before execution
- database execution is read-only and resource-bounded
- generation, validation, execution and correctness are separate outcomes
- core automated tests must not require a paid or external LLM
- company code, schema, SQL, prompts and data are excluded from this repository

## Implemented and tested

### Multi-user boundary

- synthetic signed bearer tokens for `alice` and `bob`
- persistent users and owned workspaces
- create/list/read workspace APIs
- server-side ownership resolution
- cross-user workspace access returns `404`
- query history is scoped through the owned workspace and is not visible cross-user

The demo-token endpoint is a reproducible authentication fixture, not a production identity-provider implementation.

### Text2SQL lifecycle

- `Text2SqlModel` interface
- deterministic fixture model
- natural-language question -> candidate SQL flow
- persistent query and query-attempt records
- explicit generation/validation/execution failure states
- retry creates a linked new attempt and preserves the previous attempt

### SQL policy and execution

- SQLGlot structured parsing
- exactly one statement
- SELECT/query-only policy
- analytics table allowlist
- separate synthetic commerce analytics database
- SQLite read-only connection plus `PRAGMA query_only`
- bounded returned rows
- progress-handler execution timeout boundary
- unsafe fixture output (`DELETE`) is proven to cause zero executor calls

## Not yet claimed

- production authentication or external IdP integration
- PostgreSQL read-only role/credential runtime verification
- Docker deployment
- result-based correctness evaluation dataset and metrics
- external/real LLM E2E
- production concurrency, load, SLA or large-user operation

## Next gate

1. add deterministic execution-failure coverage
2. add result-based evaluation fixtures and correctness classification
3. move synthetic analytics runtime to PostgreSQL with a dedicated read-only role
4. add Docker Compose and bounded integration E2E
5. only then add an optional external LLM adapter and bounded real-model evaluation
