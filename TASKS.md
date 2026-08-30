# Tasks

## P0 - Repository bootstrap

- [x] add global control pointer and public disclosure boundary
- [x] define project scope
- [x] define architecture and trust boundaries
- [x] record current state
- [ ] add setup and dependency definition
- [ ] add minimal FastAPI application
- [ ] add CI

## P1 - Multi-user backend baseline

- [ ] synthetic user model / authentication boundary
- [ ] workspace model
- [ ] create/list/read workspace APIs
- [ ] server-side ownership resolution
- [ ] cross-user access denial tests
- [ ] query-history ownership boundary

## P2 - Text2SQL lifecycle

- [ ] `Text2SqlModel` interface
- [ ] deterministic fixture model for CI
- [ ] question -> candidate SQL flow
- [ ] explicit query/attempt lifecycle states
- [ ] generation failure classification
- [ ] retry relationship without overwriting prior attempts

## P3 - SQL policy and execution

- [ ] parse SQL as structured syntax rather than regex-only validation
- [ ] SELECT/query-only policy
- [ ] single-statement policy
- [ ] schema/table allowlist
- [ ] row-limit policy
- [ ] execution timeout
- [ ] read-only database credential
- [ ] validation failure classification
- [ ] execution failure classification
- [ ] prove unsafe SQL causes zero execution

## P4 - Evaluation

- [ ] synthetic evaluation dataset
- [ ] expected-result representation
- [ ] result-based correctness comparison
- [ ] distinguish generation/validation/execution/correctness metrics
- [ ] record evaluation evidence without overstating model quality

## P5 - Runtime and publication

- [ ] Docker-based local environment
- [ ] PostgreSQL synthetic fixture initialization
- [ ] deterministic integration/E2E suite
- [ ] public GitHub Actions verification
- [ ] optional bounded real-model E2E
- [ ] security/disclosure review
- [ ] portfolio integration only after implementation evidence exists

## Non-goals unless a demonstrated need appears

- Redis
- Kafka
- Kubernetes
- vector DB / RAG
- arbitrary production database connectors
- write SQL
- production SLA claims
