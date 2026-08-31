# Tasks

## P0 - Repository bootstrap

- [x] add global control pointer and public disclosure boundary
- [x] define project scope
- [x] define architecture and trust boundaries
- [x] record current state
- [x] add setup and dependency definition
- [x] add minimal FastAPI application
- [x] add CI

## P1 - Multi-user backend baseline

- [x] synthetic user model / authentication boundary
- [x] workspace model
- [x] create/list/read workspace APIs
- [x] server-side ownership resolution
- [x] cross-user access denial tests
- [x] query-history ownership boundary

## P2 - Text2SQL lifecycle

- [x] `Text2SqlModel` interface
- [x] deterministic fixture model for CI
- [x] question -> candidate SQL flow
- [x] explicit query/attempt lifecycle states
- [x] generation failure classification
- [x] retry relationship without overwriting prior attempts

## P3 - SQL policy and execution

- [x] parse SQL as structured syntax rather than regex-only validation
- [x] SELECT/query-only policy
- [x] single-statement policy
- [x] schema/table allowlist
- [x] row-limit policy
- [x] execution timeout boundary
- [ ] PostgreSQL read-only database role / credential
- [x] validation failure classification
- [ ] deterministic execution failure test
- [x] prove unsafe SQL causes zero execution

## P4 - Evaluation

- [ ] synthetic evaluation dataset
- [ ] expected-result representation
- [ ] result-based correctness comparison
- [ ] distinguish generation/validation/execution/correctness metrics
- [ ] record evaluation evidence without overstating model quality

## P5 - Runtime and publication

- [ ] Docker-based local environment
- [ ] PostgreSQL synthetic fixture initialization
- [x] deterministic integration/E2E suite for the current SQLite slice
- [x] public GitHub Actions verification
- [ ] optional bounded real-model E2E
- [ ] security/disclosure review before portfolio publication
- [ ] portfolio integration only after implementation evidence exists

## P6 - Production-like auth and concurrency evidence (later, only if useful)

- [ ] external identity-provider adapter or standards-based auth integration
- [ ] concurrent workspace/query isolation test
- [ ] connection-pool/resource-bound evidence

These are not required to call the current synthetic multi-user authorization boundary implemented.

## Non-goals unless a demonstrated need appears

- Redis
- Kafka
- Kubernetes
- vector DB / RAG
- arbitrary production database connectors
- write SQL
- production SLA claims
