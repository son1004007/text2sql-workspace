# Current State

- date: 2026-08-30
- phase: bootstrap
- public repository: yes
- implementation status: not yet implemented
- verification status: documentation-only bootstrap

## Confirmed decisions

- project name: `Text2SQL Workspace`
- positioning: `Multi-user LLM Data Query Service`
- primary stack direction: Python / FastAPI / PostgreSQL
- multi-user workspace isolation is a first-class requirement
- LLM output is treated as untrusted input
- SQL must pass server-side policy validation before execution
- database execution is read-only and resource-bounded
- generation, validation, execution and correctness are separate outcomes
- core automated tests must not require a paid or external LLM
- company code, schema, SQL, prompts and data are excluded from this repository

## Current evidence

Only project scope and architecture have been initialized. No implementation or test claim should be presented as complete yet.

## Next gate

Create the minimum executable service skeleton and tests for:

1. application health
2. authenticated user identity fixture
3. workspace ownership
4. cross-user workspace access denial
5. deterministic model adapter boundary

After that gate passes, implement SQL generation/validation/execution lifecycle.
