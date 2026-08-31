from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.analytics import (
    QueryExecutor,
    QueryResult,
    SqliteReadOnlyQueryExecutor,
    initialize_synthetic_analytics_db,
)
from app.config import Settings
from app.main import create_app


class CountingExecutor:
    def __init__(self, delegate: QueryExecutor):
        self.delegate = delegate
        self.execution_count = 0

    def execute(self, sql: str) -> QueryResult:
        self.execution_count += 1
        return self.delegate.execute(sql)


@pytest.fixture
def app_client(tmp_path: Path):
    analytics_path = tmp_path / "analytics.db"
    initialize_synthetic_analytics_db(analytics_path)
    executor = CountingExecutor(
        SqliteReadOnlyQueryExecutor(
            database_path=analytics_path,
            max_result_rows=100,
            timeout_seconds=1.0,
        )
    )
    settings = Settings(
        metadata_database_url="sqlite+pysqlite:///:memory:",
        analytics_database_path=analytics_path,
        auth_secret="test-secret",
        access_token_ttl_seconds=3600,
        max_result_rows=100,
        query_timeout_seconds=1.0,
    )
    app = create_app(settings=settings, executor=executor)
    with TestClient(app) as client:
        yield client, executor


def token_headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo-token", json={"username": username})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
