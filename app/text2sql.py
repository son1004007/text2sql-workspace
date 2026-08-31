from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class Text2SqlGenerationError(RuntimeError):
    pass


@dataclass(frozen=True)
class GeneratedSql:
    sql: str
    model_name: str


class Text2SqlModel(Protocol):
    def generate(self, *, question: str) -> GeneratedSql:
        ...


class FixtureText2SqlModel:
    """Deterministic model used by CI and local development.

    It intentionally includes one unsafe output so the service can prove that
    model output never bypasses the SQL policy layer.
    """

    model_name = "fixture-text2sql-v1"

    _responses = {
        "월별 주문 건수": (
            "SELECT order_month, COUNT(*) AS order_count "
            "FROM orders GROUP BY order_month ORDER BY order_month"
        ),
        "카테고리별 매출": (
            "SELECT p.category, ROUND(SUM(oi.quantity * oi.unit_price), 2) AS sales "
            "FROM order_items oi JOIN products p ON p.id = oi.product_id "
            "GROUP BY p.category ORDER BY sales DESC"
        ),
        "테이블 삭제 테스트": "DELETE FROM orders",
    }

    def generate(self, *, question: str) -> GeneratedSql:
        normalized = " ".join(question.strip().split())
        sql = self._responses.get(normalized)
        if sql is None:
            raise Text2SqlGenerationError("NO_FIXTURE_FOR_QUESTION")
        return GeneratedSql(sql=sql, model_name=self.model_name)
