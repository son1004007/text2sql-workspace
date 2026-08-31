# Setup

## Requirements

### Fast local tests

- Python 3.12+
- `pip`

### Full PostgreSQL runtime verification

- Docker Engine
- Docker Compose v2

An external LLM or model API key is not required for either path.

## Local Python setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

Windows PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Run fast tests

```bash
python -m pytest
```

These tests use isolated temporary metadata and SQLite analytics fixtures where appropriate. They verify application behavior without requiring Docker or a remote service.

## Run the API without Docker

```bash
python -m uvicorn app.main:app --reload
```

Then check:

```text
GET /health
```

Expected response:

```json
{"status":"UP"}
```

Without `TEXT2SQL_ANALYTICS_DATABASE_URL`, the application uses the deterministic SQLite analytics adapter.

## Run the PostgreSQL Docker runtime

Build and start the bounded local runtime:

```bash
docker compose up -d --build
```

The API is available only on the host loopback boundary:

```text
http://127.0.0.1:18000
```

PostgreSQL is available to the application through the Compose network but is not published to a host port.

Stop the services:

```bash
docker compose down
```

Remove services and synthetic persistent data:

```bash
docker compose down -v
```

The Compose file contains explicit local-only demo credential defaults so the synthetic environment is reproducible. They are not suitable examples for production secret management. Override them with environment variables when experimenting locally rather than reusing them outside this isolated demo.

## Run the complete Docker/PostgreSQL E2E

```bash
python scripts/docker_e2e.py
```

The E2E script:

1. removes any prior synthetic Compose state
2. builds the FastAPI image
3. starts PostgreSQL and the application
4. waits for health
5. verifies multi-user isolation
6. executes a safe Text2SQL query against PostgreSQL
7. verifies unsafe generated SQL is rejected
8. executes the deterministic evaluation set
9. verifies application and database host-exposure boundaries
10. verifies the analytics reader can `SELECT`
11. verifies the analytics reader cannot `INSERT`
12. removes containers and volumes

CI runs this as a separate job from the Python test suite.

## Runtime configuration

Relevant environment variables include:

```text
TEXT2SQL_METADATA_DATABASE_URL
TEXT2SQL_ANALYTICS_DATABASE_URL
TEXT2SQL_AUTH_SECRET
TEXT2SQL_ACCESS_TOKEN_TTL_SECONDS
TEXT2SQL_MAX_RESULT_ROWS
TEXT2SQL_QUERY_TIMEOUT_SECONDS
```

`TEXT2SQL_ANALYTICS_DATABASE_URL` selects the PostgreSQL analytics executor. If it is absent, the SQLite adapter is used.

## Dependency policy

Core CI remains deterministic and does not require an external model API key. Real-model verification, if added, will be a separate bounded gate and will not replace the deterministic test and PostgreSQL runtime gates.
