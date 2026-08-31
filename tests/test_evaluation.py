from __future__ import annotations

from pathlib import Path

from app.analytics import SqliteReadOnlyQueryExecutor, initialize_synthetic_analytics_db
from app.evaluation import EvaluationCase, EvaluationRunner
from app.sql_policy import SqlPolicyValidator
from app.text2sql import GeneratedSql


ALLOWED = {"customers", "products", "orders", "order_items"}


class EquivalentSqlModel:
    def generate(self, *, question: str) -> GeneratedSql:
        return GeneratedSql(
            sql=(
                "SELECT order_month, SUM(1) AS order_count "
                "FROM orders GROUP BY order_month ORDER BY order_month"
            ),
            model_name="equivalent-sql",
        )


class WrongButExecutableModel:
    def generate(self, *, question: str) -> GeneratedSql:
        return GeneratedSql(
            sql=(
                "SELECT order_month, COUNT(*) + 1 AS order_count "
                "FROM orders GROUP BY order_month ORDER BY order_month"
            ),
            model_name="wrong-result",
        )


def _runner(tmp_path: Path, model) -> EvaluationRunner:
    analytics_path = tmp_path / "analytics.db"
    initialize_synthetic_analytics_db(analytics_path)
    executor = SqliteReadOnlyQueryExecutor(
        database_path=analytics_path,
        max_result_rows=100,
        timeout_seconds=1.0,
    )
    return EvaluationRunner(
        model=model,
        validator=SqlPolicyValidator(allowed_tables=ALLOWED),
        executor=executor,
        cases=(
            EvaluationCase(
                id="monthly-order-count",
                question="월별 주문 건수",
                expected_columns=("order_month", "order_count"),
                expected_rows=(("2026-01", 2), ("2026-02", 1)),
                ordered=True,
            ),
        ),
    )


def test_equivalent_sql_is_correct_even_when_sql_text_differs(tmp_path: Path) -> None:
    summary = _runner(tmp_path, EquivalentSqlModel()).run()

    assert summary.total == 1
    assert summary.generation_success == 1
    assert summary.validation_success == 1
    assert summary.execution_success == 1
    assert summary.correctness_success == 1
    assert summary.cases[0].failure_code is None


def test_executable_sql_can_still_fail_correctness(tmp_path: Path) -> None:
    summary = _runner(tmp_path, WrongButExecutableModel()).run()

    assert summary.generation_success == 1
    assert summary.validation_success == 1
    assert summary.execution_success == 1
    assert summary.correctness_success == 0
    assert summary.cases[0].failure_code == "RESULT_MISMATCH"


def test_authenticated_evaluation_endpoint_reports_stage_metrics(app_client) -> None:
    client, _ = app_client
    token = client.post(
        "/api/v1/auth/demo-token", json={"username": "alice"}
    ).json()["access_token"]

    response = client.post(
        "/api/v1/evaluations/run",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["generation_success"] == 2
    assert body["validation_success"] == 2
    assert body["execution_success"] == 2
    assert body["correctness_success"] == 2
    assert {case["case_id"] for case in body["cases"]} == {
        "monthly-order-count",
        "sales-by-category",
    }


def test_evaluation_endpoint_requires_authentication(app_client) -> None:
    client, _ = app_client

    response = client.post("/api/v1/evaluations/run")

    assert response.status_code == 401
