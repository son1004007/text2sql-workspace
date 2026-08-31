from __future__ import annotations

from fastapi.testclient import TestClient


def _headers(client: TestClient, username: str) -> dict[str, str]:
    response = client.post("/api/v1/auth/demo-token", json={"username": username})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _workspace(client: TestClient, username: str, name: str = "demo") -> tuple[str, dict[str, str]]:
    headers = _headers(client, username)
    response = client.post("/api/v1/workspaces", json={"name": name}, headers=headers)
    assert response.status_code == 201
    return response.json()["id"], headers


def test_workspace_requires_authentication(app_client) -> None:
    client, _ = app_client

    response = client.get("/api/v1/workspaces")

    assert response.status_code == 401


def test_workspace_isolation_hides_other_users_resources(app_client) -> None:
    client, _ = app_client
    workspace_id, alice_headers = _workspace(client, "alice", "alice-space")
    bob_headers = _headers(client, "bob")

    assert client.get(f"/api/v1/workspaces/{workspace_id}", headers=alice_headers).status_code == 200
    assert client.get(f"/api/v1/workspaces/{workspace_id}", headers=bob_headers).status_code == 404
    assert client.get("/api/v1/workspaces", headers=bob_headers).json() == []


def test_safe_question_executes_and_persists_history(app_client) -> None:
    client, executor = app_client
    workspace_id, headers = _workspace(client, "alice")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/queries",
        json={"question": "월별 주문 건수"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["question"] == "월별 주문 건수"
    assert len(body["attempts"]) == 1
    attempt = body["attempts"][0]
    assert attempt["status"] == "SUCCEEDED"
    assert attempt["failure_code"] is None
    assert attempt["result"] == {
        "columns": ["order_month", "order_count"],
        "rows": [["2026-01", 2], ["2026-02", 1]],
    }
    assert executor.execution_count == 1

    history = client.get(
        f"/api/v1/workspaces/{workspace_id}/queries",
        headers=headers,
    )
    assert history.status_code == 200
    assert [item["id"] for item in history.json()] == [body["id"]]


def test_unsafe_model_output_is_blocked_before_execution(app_client) -> None:
    client, executor = app_client
    workspace_id, headers = _workspace(client, "alice")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/queries",
        json={"question": "테이블 삭제 테스트"},
        headers=headers,
    )

    assert response.status_code == 201
    attempt = response.json()["attempts"][0]
    assert attempt["status"] == "VALIDATION_FAILED"
    assert attempt["failure_code"] == "READ_QUERY_ONLY"
    assert attempt["candidate_sql"] == "DELETE FROM orders"
    assert attempt["result"] is None
    assert executor.execution_count == 0


def test_generation_failure_is_recorded_without_database_execution(app_client) -> None:
    client, executor = app_client
    workspace_id, headers = _workspace(client, "alice")

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/queries",
        json={"question": "등록되지 않은 질문"},
        headers=headers,
    )

    assert response.status_code == 201
    attempt = response.json()["attempts"][0]
    assert attempt["status"] == "GENERATION_FAILED"
    assert attempt["failure_code"] == "NO_FIXTURE_FOR_QUESTION"
    assert executor.execution_count == 0


def test_query_history_is_not_visible_cross_user(app_client) -> None:
    client, _ = app_client
    workspace_id, alice_headers = _workspace(client, "alice")
    created = client.post(
        f"/api/v1/workspaces/{workspace_id}/queries",
        json={"question": "월별 주문 건수"},
        headers=alice_headers,
    ).json()
    bob_headers = _headers(client, "bob")

    response = client.get(
        f"/api/v1/workspaces/{workspace_id}/queries/{created['id']}",
        headers=bob_headers,
    )

    assert response.status_code == 404


def test_retry_creates_new_attempt_without_overwriting_previous_one(app_client) -> None:
    client, executor = app_client
    workspace_id, headers = _workspace(client, "alice")
    created = client.post(
        f"/api/v1/workspaces/{workspace_id}/queries",
        json={"question": "월별 주문 건수"},
        headers=headers,
    ).json()
    first = created["attempts"][0]

    response = client.post(
        f"/api/v1/workspaces/{workspace_id}/queries/{created['id']}/retry",
        headers=headers,
    )

    assert response.status_code == 200
    attempts = response.json()["attempts"]
    assert len(attempts) == 2
    assert attempts[0]["id"] == first["id"]
    assert attempts[1]["attempt_number"] == 2
    assert attempts[1]["retry_of_attempt_id"] == first["id"]
    assert attempts[0]["status"] == "SUCCEEDED"
    assert attempts[1]["status"] == "SUCCEEDED"
    assert executor.execution_count == 2
