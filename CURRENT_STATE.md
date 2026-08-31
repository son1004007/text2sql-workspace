# Current State

- date: 2026-08-31
- phase: publication-ready deterministic PostgreSQL evidence
- public repository: yes
- implementation status: P1-P4 implemented; bounded P5 Docker/PostgreSQL runtime implemented
- verification status: feature-branch GitHub Actions PASS for both Python tests and Docker/PostgreSQL E2E; public disclosure review completed

## Confirmed decisions

- project name: `Text2SQL Workspace`
- positioning: `Multi-user LLM Data Query Service`
- primary stack: Python / FastAPI / PostgreSQL
- fast deterministic application tests retain a SQLite analytics adapter
- bounded runtime verification uses PostgreSQL 17 through Docker Compose
- application metadata state and analytics query authority use separate storage/credential boundaries
- multi-user workspace isolation is a first-class requirement
- model output is treated as untrusted input
- SQL must pass server-side policy validation before execution
- PostgreSQL analytics execution uses a dedicated read-only role
- generation, validation, execution and correctness are separate outcomes
- core automated tests must not require a paid or external LLM
- company code, schema, SQL, prompts and data are excluded from this repository
- external real-model evaluation is optional and must not block publication of deterministic backend/runtime evidence

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
- SELECT/query-only application policy
- analytics table allowlist
- bounded returned rows
- execution timeout boundary
- unsafe fixture output (`DELETE`) is proven to cause zero executor calls
- deterministic executor failure is persisted as `EXECUTION_FAILED`
- SQLite read-only/query-only adapter remains available for fast deterministic tests
- PostgreSQL executor uses a dedicated analytics reader DSN
- PostgreSQL transactions are explicitly read-only
- PostgreSQL role is configured read-only and with a bounded statement timeout
- direct E2E proves the analytics reader can `SELECT`
- direct E2E proves the same reader cannot `INSERT`

### Result-based evaluation

- explicit synthetic evaluation dataset
- expected result stored as columns and rows
- generation / validation / execution / correctness counted separately
- correctness compares actual result semantics instead of SQL string equality
- semantically equivalent SQL with different text is proven to pass correctness
- policy-valid and executable SQL with the wrong result is proven to fail correctness
- PostgreSQL `NUMERIC` results are compared consistently with deterministic SQLite numeric results
- authenticated evaluation API is available at `POST /api/v1/evaluations/run`

Current bounded fixture:

```text
total cases:          2
generation success:   2
validation success:   2
execution success:    2
correctness success:  2
```

The same deterministic fixture is exercised against PostgreSQL in Docker E2E. This verifies the evaluation pipeline only. It is not an external-LLM accuracy claim.

### Docker / PostgreSQL runtime

- FastAPI runs as a non-root container user
- PostgreSQL 17 synthetic analytics runtime is initialized from repository-owned fixtures
- application metadata volume is separate from PostgreSQL analytics storage
- application connects to analytics using only the dedicated reader credential
- application host exposure is bounded to `127.0.0.1:18000`
- PostgreSQL has no host-published port
- Docker E2E starts from clean volumes and cleans them up after verification

## Verified runtime scenarios

The current automated gates verify normal, failure, authorization, evaluation and runtime-boundary behavior, including:

1. authentication required
2. cross-user workspace denial
3. cross-user query denial
4. successful natural-language -> SQL -> PostgreSQL result flow
5. persisted query history
6. generation failure with zero DB execution
7. unsafe SQL validation failure before DB execution
8. retry preserving the first attempt
9. deterministic analytics execution failure classification
10. direct SQL policy rejection cases
11. equivalent SQL result correctness
12. executable but semantically wrong SQL correctness failure
13. authenticated evaluation endpoint and per-stage metrics
14. PostgreSQL-backed deterministic evaluation
15. loopback-only API host binding in the bounded Compose runtime
16. no host-published PostgreSQL port
17. analytics reader `SELECT` succeeds
18. analytics reader write attempt fails

## Runtime findings resolved during verification

The Docker/PostgreSQL gate caught two assumptions that the SQLite-only path could not expose:

1. PostgreSQL rejected the initial money aggregation expression when synthetic money used `DOUBLE PRECISION`; the fixture was corrected to `NUMERIC(12, 2)` and the evaluator now handles `Decimal` values explicitly.
2. the GitHub-hosted Compose runtime represents an exposed-but-unpublished container port as `:0`; the E2E harness was corrected to treat only a concrete host port as exposure.

These fixes are retained as runtime portability evidence rather than hidden as test-only adjustments.

## Public disclosure review

The repository was reviewed before portfolio publication for confidential code/data, internal endpoints and real credential material. The implementation remains synthetic and independently designed. Local Compose credential defaults are explicitly demo-only and are not production secret-management evidence.

See [`docs/SECURITY_DISCLOSURE_REVIEW.md`](docs/SECURITY_DISCLOSURE_REVIEW.md).

## Not yet claimed

- production authentication or external IdP integration
- production secret management
- external/real LLM E2E
- statistically meaningful model-quality metrics
- arbitrary customer database connectors
- production concurrency, load, SLA or large-user operation

## Next gate

1. merge only after the final documentation head again passes both Python and Docker/PostgreSQL CI jobs
2. verify the same two jobs on `main`
3. integrate the bounded evidence into the engineering portfolio
4. add an external-model adapter later only if it contributes distinct evidence
