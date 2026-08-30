# Architecture

## System boundary

Text2SQL Workspace is a multi-user backend service. The LLM proposes SQL, but the server owns authorization, validation, execution policy and persisted state.

```text
Client
  -> FastAPI
      -> Authentication / current user
      -> Workspace authorization
      -> Query application service
          -> Context selector
          -> Text2SQL model interface
          -> SQL policy validator
          -> Read-only query executor
          -> Result evaluator
      -> PostgreSQL
```

## Primary entities

### User

Represents an authenticated service user.

### Workspace

Owned by one user in the initial MVP. All queries and evaluation records belong to a workspace.

### Query

Stores the natural-language request and the lifecycle of one Text2SQL attempt.

Proposed lifecycle:

```text
RECEIVED
  -> CONTEXT_READY
  -> GENERATED
  -> VALIDATED
  -> EXECUTED
  -> EVALUATED
  -> SUCCEEDED
```

Failure states are explicit:

```text
GENERATION_FAILED
VALIDATION_FAILED
EXECUTION_FAILED
EVALUATION_FAILED
```

### QueryAttempt

A retry is a new attempt linked to the original query. Previous SQL, result and failure information are not overwritten.

## Trust boundaries

### LLM output

LLM output is untrusted input.

Generated SQL must not reach the database before server-side validation.

### Workspace ownership

A request-provided workspace or query identifier never proves authorization. Ownership is resolved server-side from the authenticated user.

### Database execution

The execution credential is read-only. Application policy provides an additional boundary, not a replacement for database privilege restrictions.

Initial policy targets:

- one SQL statement only
- query statements only
- explicit schema/table allowlist
- no DDL or DML
- bounded returned rows
- bounded execution time
- deterministic error classification

## Model boundary

Application code depends on an interface rather than one provider.

```text
Text2SqlModel
  -> FixtureModel       # deterministic CI
  -> ExternalLlmModel   # optional bounded real-model verification
```

Core CI must pass without an API key or external model service.

## Evaluation boundary

Evaluation distinguishes at least these outcomes:

1. generation: a candidate was produced
2. validation: candidate satisfied execution policy
3. execution: database returned a result
4. correctness: result matched the expected semantic result for an evaluation fixture

SQL string equality is not the primary correctness criterion because different valid SQL can return the same expected result.

## Initial synthetic domain

The first public fixture will use a generic commerce-style dataset such as:

- customers
- products
- orders
- order_items

Names and relationships are independently designed for this repository.

## Non-goals for MVP

- production-scale tenancy
- arbitrary customer database connections
- write SQL
- long-running analytical workloads
- vector database or RAG without a demonstrated need
- Redis/Kafka/Kubernetes added only for technology breadth
- claims of production SLA or large-user scale without runtime evidence
