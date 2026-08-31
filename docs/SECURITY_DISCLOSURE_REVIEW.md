# Public Security / Disclosure Review

## Scope

This review covers the public repository contents and the PostgreSQL/Docker runtime changes before portfolio publication.

The purpose is to confirm that public evidence remains independently reproducible without exposing confidential work artifacts or presenting demo controls as production controls.

## Reviewed categories

The repository was reviewed for:

- company- or customer-specific source code
- non-public database schemas, SQL and prompts
- customer or employee identifiers
- internal hosts, URLs, addresses or environment details
- API keys, access tokens and private-key material
- real database credentials
- copied production datasets
- claims that exceed executable evidence

## Result

No confidential work artifact or real credential is intentionally present in the reviewed public implementation.

The project uses:

- independently designed Python/FastAPI code
- synthetic commerce schema and rows
- synthetic user identities
- deterministic model fixtures
- explicit local-only Compose credential defaults

The Compose defaults exist only so the disposable synthetic environment can start without external secret provisioning. They are documented as demo values and must not be represented as production secret-management practice.

## Security evidence currently supported

The repository has executable evidence for:

- server-side workspace ownership checks
- cross-user resource isolation in the synthetic two-user flow
- untrusted generated SQL validation before execution
- single-statement/query-only/table-allowlist policy
- database read-only privilege using a dedicated PostgreSQL analytics reader
- direct proof that the reader can query but cannot insert
- bounded statement execution and result rows
- loopback-only API publication in the bounded Compose runtime
- no host-published PostgreSQL port in that runtime
- non-root application container execution

## Explicitly not production claims

The repository does not claim evidence for:

- production authentication or identity-provider integration
- production authorization at organizational scale
- production secret storage, rotation or KMS integration
- Internet-facing perimeter security
- formal penetration testing
- production concurrency/load capacity
- availability/SLA guarantees
- external-model security or quality

## Publication rule

Portfolio language should describe only the boundaries above and should keep the following qualifiers visible when material:

- synthetic
- deterministic
- bounded
- local Docker/PostgreSQL runtime
- demo authentication fixture

Any future real-model or production-like evidence must be reviewed separately before expanding those claims.
