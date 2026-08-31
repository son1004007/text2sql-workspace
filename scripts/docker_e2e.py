from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "http://127.0.0.1:18000"
READER_PASSWORD = os.getenv("ANALYTICS_READER_PASSWORD", "local-reader-only")


def compose(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", "compose", *args],
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def request_json(
    method: str,
    path: str,
    *,
    token: str | None = None,
    body: dict[str, Any] | None = None,
    expected_status: int = 200,
) -> dict[str, Any] | list[Any]:
    payload = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(BASE_URL + path, data=payload, headers=headers, method=method)
    try:
        with urlopen(request, timeout=5) as response:
            if response.status != expected_status:
                raise AssertionError(
                    f"{method} {path}: expected {expected_status}, got {response.status}"
                )
            raw = response.read()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        if exc.code == expected_status:
            raw = exc.read()
            return json.loads(raw) if raw else {}
        raise


def wait_for_health() -> None:
    deadline = time.monotonic() + 90
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            payload = request_json("GET", "/health")
            if payload == {"status": "UP"}:
                return
        except (HTTPError, URLError, ConnectionError) as exc:
            last_error = exc
        time.sleep(1)
    raise RuntimeError(f"application health check did not pass: {last_error}")


def issue_token(username: str) -> str:
    payload = request_json(
        "POST",
        "/api/v1/auth/demo-token",
        body={"username": username},
    )
    assert isinstance(payload, dict)
    return str(payload["access_token"])


def verify_api_flow() -> None:
    alice = issue_token("alice")
    bob = issue_token("bob")

    workspace = request_json(
        "POST",
        "/api/v1/workspaces",
        token=alice,
        body={"name": "Docker PostgreSQL E2E"},
        expected_status=201,
    )
    assert isinstance(workspace, dict)
    workspace_id = str(workspace["id"])

    safe_query = request_json(
        "POST",
        f"/api/v1/workspaces/{workspace_id}/queries",
        token=alice,
        body={"question": "월별 주문 건수"},
        expected_status=201,
    )
    assert isinstance(safe_query, dict)
    attempt = safe_query["attempts"][-1]
    assert attempt["status"] == "SUCCEEDED"
    assert attempt["result"]["columns"] == ["order_month", "order_count"]
    assert attempt["result"]["rows"] == [["2026-01", 2], ["2026-02", 1]]

    request_json(
        "GET",
        f"/api/v1/workspaces/{workspace_id}",
        token=bob,
        expected_status=404,
    )

    unsafe_query = request_json(
        "POST",
        f"/api/v1/workspaces/{workspace_id}/queries",
        token=alice,
        body={"question": "테이블 삭제 테스트"},
        expected_status=201,
    )
    assert isinstance(unsafe_query, dict)
    unsafe_attempt = unsafe_query["attempts"][-1]
    assert unsafe_attempt["status"] == "VALIDATION_FAILED"

    evaluation = request_json(
        "POST",
        "/api/v1/evaluations/run",
        token=alice,
    )
    assert isinstance(evaluation, dict)
    assert evaluation["total"] == 2
    assert evaluation["generation_success"] == 2
    assert evaluation["validation_success"] == 2
    assert evaluation["execution_success"] == 2
    assert evaluation["correctness_success"] == 2


def verify_runtime_boundaries() -> None:
    app_port = compose("port", "app", "8000").stdout.strip()
    assert app_port == "127.0.0.1:18000", app_port

    postgres_port = compose("port", "postgres", "5432", check=False)
    assert postgres_port.returncode != 0 or not postgres_port.stdout.strip(), postgres_port.stdout

    read = compose(
        "exec",
        "-T",
        "-e",
        f"PGPASSWORD={READER_PASSWORD}",
        "postgres",
        "psql",
        "-h",
        "127.0.0.1",
        "-U",
        "analytics_reader",
        "-d",
        "analytics",
        "-Atqc",
        "SELECT COUNT(*) FROM orders",
    )
    assert read.stdout.strip() == "3", read.stdout

    write = compose(
        "exec",
        "-T",
        "-e",
        f"PGPASSWORD={READER_PASSWORD}",
        "postgres",
        "psql",
        "-h",
        "127.0.0.1",
        "-U",
        "analytics_reader",
        "-d",
        "analytics",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        "INSERT INTO customers(id, name) VALUES (999, 'blocked')",
        check=False,
    )
    assert write.returncode != 0, "analytics_reader unexpectedly obtained write access"


def main() -> int:
    compose("down", "-v", "--remove-orphans", check=False)
    try:
        up = compose("up", "-d", "--build")
        print(up.stdout)
        wait_for_health()
        verify_api_flow()
        verify_runtime_boundaries()
        print("Docker PostgreSQL E2E: PASS")
        return 0
    except Exception:
        print("Docker PostgreSQL E2E: FAIL", file=sys.stderr)
        print(compose("ps", check=False).stdout, file=sys.stderr)
        print(compose("logs", "--no-color", check=False).stdout, file=sys.stderr)
        raise
    finally:
        compose("down", "-v", "--remove-orphans", check=False)


if __name__ == "__main__":
    raise SystemExit(main())
