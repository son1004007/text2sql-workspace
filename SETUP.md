# Setup

## Requirements

- Python 3.12+
- `pip`

The initial bootstrap does not require PostgreSQL or an external LLM. Those dependencies are introduced only when the corresponding implementation gates are added.

## Local setup

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

## Run tests

```bash
python -m pytest
```

## Run the API

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

## Dependency policy

Core CI must remain deterministic and must not require an external model API key. Real-model verification, when added, will be a separate bounded gate.
