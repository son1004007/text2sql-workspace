from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from app.analytics import QueryExecutionError
from app.config import Settings
from app.main import create_app


class FailingExecutor:
    def execute(self, sql: str):
        raise QueryExecutionError("SIMULATED_ANALYTICS_FAILURE")


def test_execution_failure_is_persisted_as_domain_state(tmp_path: Path) -> None:
    settings = Settings(
        metadata_database_url="sqlite+pysqlite:///:memory:",
        analytics_database_path=tmp_path / "unused.db",
        auth_secret="test-secret",
    )
    app = create_app(settings=settings, executor=FailingExecutor())

    with TestClient(app) as client:
        token = client.post(
            "/api/v1/auth/demo-token", json={"username": "alice"}
        ).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        workspace_id = client.post(
            "/api/v1/workspaces",
            json={"name": "failure-test"},
            headers=headers,
        ).json()["id"]

        response = client.post(
            f"/api/v1/workspaces/{workspace_id}/queries",
            json={"question": "월별 주문 건수"},
            headers=headers,
        )

    assert response.status_code == 201
    attempt = response.json()["attempts"][0]
    assert attempt["status"] == "EXECUTION_FAILED"
    assert attempt["failure_code"] == "SIMULATED_ANALYTICS_FAILURE"
    assert attempt["result"] is None
