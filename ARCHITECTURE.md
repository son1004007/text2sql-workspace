# Architecture

## System boundary

Text2SQL Workspace is a multi-user backend service. The model proposes SQL, but the server owns authorization, validation, execution policy and persisted service state.

```text
Client
  -> FastAPI
      -> Authentication / current user
      -> Workspace authorization
      -> Query application service
          -> Text2SQL model interface
          -> SQL policy validator
          -> Read-only query executor
          -> Result evaluator
      -> metadata state
      -> analytics database
```

The bounded Docker runtime separates service state from analytics query authority:

```text
FastAPI
  |- metadata state -> application-owned volume
  `- generated SQL  -> analytics_reader -> PostgreSQL
```

The analytics reader is not the database owner and does not have write privileges.

## Primary entities

### User

Represents an authenticated service user.

### Workspace

Owned by one user in the current MVP. Queries belong to a workspace and authorization is resolved from the authenticated user rather than trusting a request-provided identifier.

### Query

Stores the natural-language request and the lifecycle of Text2SQL attempts.

The implemented attempt flow covers:

```text
RECEIVED
  -> GENERATED
  -> VALIDATED
  -> EXECUTED
  -> SUCCEEDED
```

Failure states are explicit:

```text
GENERATION_FAILED
VALIDATION_FAILED
EXECUTION_FAILED
```

Evaluation is run as a separate deterministic gate over explicit fixtures rather than being required for every interactive query.

### QueryAttempt

A retry is a new attempt linked to the previous attempt. Previous SQL, result and failure information are not overwritten.

## Trust boundaries

### Model output

Model output is untrusted input.

Generated SQL must not reach the analytics database before server-side validation.

### Workspace ownership

A request-provided workspace or query identifier never proves authorization. Ownership is resolved server-side from the authenticated user. The current E2E proves one demo user cannot retrieve another user's workspace.

### Application SQL policy

The SQLGlot-based validator enforces the current application policy:

- exactly one statement
- query/SELECT only
- explicit table allowlist
- no DDL or DML

This prevents unsafe model output from being sent to the executor.

### Database execution

Database privilege is a second boundary rather than a substitute for application validation.

The PostgreSQL runtime uses a dedicated analytics reader role with:

- `SELECT` privilege on the synthetic analytics tables
- no table write privilege
- default read-only transactions
- explicit read-only transaction in the executor
- bounded statement timeout
- bounded returned rows through an outer query limit

Docker E2E directly verifies `SELECT` succeeds and an `INSERT` attempt fails for the same analytics reader.

### Runtime network exposure

The bounded Compose environment publishes only the FastAPI service to host loopback:

```text
127.0.0.1:18000 -> FastAPI
```

PostgreSQL remains on the Compose network and has no host-published port.

This is local runtime evidence, not a claim about an Internet-facing production perimeter.

## Query executor boundary

Application code depends on a query-executor interface.

```text
QueryExecutor
  |- SqliteReadOnlyQueryExecutor   # fast deterministic tests/local fallback
  `- PostgresReadOnlyQueryExecutor # Docker/PostgreSQL runtime evidence
```

The SQLite adapter and PostgreSQL adapter share the same validated-query boundary but provide different evidence:

- SQLite keeps the unit/integration path fast and deterministic.
- PostgreSQL proves database privilege, transaction and engine-compatibility behavior in the bounded Docker runtime.

## Model boundary

Application code depends on an interface rather than one provider.

```text
Text2SqlModel
  -> FixtureModel       # deterministic CI
  -> ExternalLlmModel   # optional bounded real-model verification
```

Core CI must pass without an API key or external model service.

## Evaluation boundary

Evaluation distinguishes these outcomes:

1. generation: a candidate was produced
2. validation: candidate satisfied execution policy
3. execution: database returned a result
4. correctness: result matched the expected semantic result for an evaluation fixture

SQL string equality is not the primary correctness criterion because different valid SQL can return the same expected result.

The evaluator also normalizes numeric comparison across SQLite numeric values and PostgreSQL `NUMERIC`/`Decimal` values.

## Synthetic domain

The public fixture uses an independently designed commerce-style dataset:

- customers
- products
- orders
- order_items

No company-owned schema, query, prompt or data is reproduced.

## Runtime verification layers

```text
pytest
  -> service behavior and failure boundaries

Docker/PostgreSQL E2E
  -> container startup
  -> API health
  -> multi-user isolation
  -> validated Text2SQL execution
  -> result-based evaluation
  -> network exposure checks
  -> database read/write privilege checks
```

A runtime claim is considered verified only when the corresponding executable gate passes.

## Non-goals for the current MVP

- production-scale tenancy
- production identity-provider integration
- arbitrary customer database connections
- write SQL
- long-running analytical workloads
- vector database or RAG without a demonstrated need
- Redis/Kafka/Kubernetes added only for technology breadth
- production secret-management claims
- production SLA, concurrency or large-user claims without runtime evidence
