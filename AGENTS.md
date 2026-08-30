# AGENTS.md

## Global AI Control

Before substantive work, read `son1004007/ai-agent-workflow-playbook/CONTROL.md`, then this file and the current-state documents in this repository.

This repository is the source of truth for the public `Text2SQL Workspace` implementation, tests, architecture, verification state and backlog.

## Purpose

Build a public, independently reproducible multi-user LLM data-query service with Python/FastAPI.

Primary project statement:

> Text2SQL Workspace — Multi-user LLM Data Query Service

The project demonstrates backend engineering around user/workspace isolation, LLM-generated SQL validation, read-only execution, query history, failure classification and evaluation.

## Public / Confidentiality Boundary

This repository must be independently implemented with synthetic or public data.

Do not copy or reconstruct company-owned source code, database schemas, SQL, prompts, customer identifiers, internal URLs, credentials, datasets or other confidential artifacts.

Prior work may be used only as high-level evidence for the kinds of engineering problems encountered. Public implementation decisions must stand on their own.

## Engineering Priorities

1. multi-user authentication and workspace isolation
2. Text2SQL generation behind an explicit model interface
3. server-side SQL validation before execution
4. read-only database execution with bounded resource use
5. explicit generation / validation / execution / evaluation states
6. query history and reproducible retry relationships
7. deterministic CI without requiring a paid or external LLM
8. optional bounded real-model E2E only after deterministic gates pass

## Completion Rule

A feature is not complete because code exists. Required tests must pass and public claims must not exceed verified evidence.

Use synthetic data and cover normal, failure, authorization and boundary scenarios.

## Initial Read Order

1. `AGENTS.md`
2. `README.md`
3. `ARCHITECTURE.md`
4. `CURRENT_STATE.md`
5. `TASKS.md`
6. `SETUP.md`
