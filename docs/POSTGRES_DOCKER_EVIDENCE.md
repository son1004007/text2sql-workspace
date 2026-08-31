# PostgreSQL / Docker Runtime Evidence

## Scope

This document records bounded runtime evidence for the public synthetic `Text2SQL Workspace` implementation.

The evidence applies to the repository-owned Docker Compose environment and deterministic fixture model. It does not represent production deployment, production authentication, external-LLM quality, load capacity or SLA evidence.

## Runtime under test

```text
host loopback
  -> FastAPI container
      -> application metadata volume
      -> dedicated analytics_reader
          -> PostgreSQL 17 container
```

The PostgreSQL service is not published to a host port.

## Executable gate

Run:

```bash
python scripts/docker_e2e.py
```

CI executes the same script in a dedicated `docker-postgres-e2e` job, separate from the Python test job.

The script starts from clean synthetic volumes and tears the runtime down after verification.

## Verified boundaries

| Boundary | Executable evidence |
| --- | --- |
| API health | `/health` returns the expected healthy response after Compose startup |
| multi-user identity | independent demo identities are issued for two synthetic users |
| workspace isolation | one user cannot fetch the other user's workspace |
| safe Text2SQL flow | natural-language fixture -> candidate SQL -> validation -> PostgreSQL -> expected result |
| unsafe generated SQL | destructive fixture is rejected by application policy before analytics execution |
| result evaluation | the two bounded deterministic cases pass generation, validation, execution and correctness on PostgreSQL |
| application host exposure | Compose publishes FastAPI only to `127.0.0.1:18000` |
| PostgreSQL host exposure | PostgreSQL has no concrete host-published port |
| database read privilege | `analytics_reader` can `SELECT` from the synthetic analytics tables |
| database write privilege | direct `INSERT` as `analytics_reader` fails |
| cleanup | containers and synthetic volumes are removed after the run |

## Defense in depth

Generated SQL is constrained at two different layers.

### Application layer

- SQLGlot parsing
- single statement
- SELECT/query only
- table allowlist
- bounded outer result limit

### PostgreSQL layer

- dedicated analytics reader role
- table `SELECT` grants only
- role default transaction read-only
- executor explicitly opens a read-only transaction
- bounded statement timeout

The database privilege test is intentionally direct. It bypasses the application validator and attempts a write using the same reader identity used by the FastAPI analytics executor. The write must fail for the runtime gate to pass.

## Engine-compatibility finding

The first PostgreSQL E2E exposed an assumption that SQLite did not reveal: the initial synthetic money column type caused an aggregate rounding expression to behave differently on PostgreSQL.

The public synthetic schema was changed to model money as `NUMERIC(12, 2)`, and result comparison was extended to handle PostgreSQL `Decimal` values consistently. The deterministic PostgreSQL evaluation then passed.

This is retained as evidence for why the project separates fast deterministic tests from an actual PostgreSQL runtime gate.

## Compose exposure finding

On the GitHub-hosted Compose runtime, an exposed-but-unpublished container port can be reported by `docker compose port` as `:0`. The E2E therefore treats only a concrete host port as publication and also relies on the Compose configuration/runtime state that leaves PostgreSQL without a host binding.

## Current evidence limits

Not verified by this gate:

- production identity provider integration
- production secret storage/rotation
- Internet-facing deployment
- external or real LLM behavior
- statistically meaningful Text2SQL model quality
- arbitrary schemas or customer databases
- concurrent-user/load behavior
- production availability or SLA

Those claims must remain absent until separate executable evidence exists.
