from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
import json
import math
from pathlib import Path
from typing import Iterable

from app.analytics import QueryExecutionError, QueryExecutor, QueryResult
from app.sql_policy import SqlPolicyValidator, SqlPolicyViolation
from app.text2sql import Text2SqlGenerationError, Text2SqlModel


DEFAULT_FIXTURE_PATH = Path(__file__).resolve().parent.parent / "evaluation" / "fixtures.json"


@dataclass(frozen=True)
class EvaluationCase:
    id: str
    question: str
    expected_columns: tuple[str, ...]
    expected_rows: tuple[tuple[object, ...], ...]
    ordered: bool = True


@dataclass(frozen=True)
class EvaluationCaseResult:
    case_id: str
    question: str
    generation_success: bool
    validation_success: bool
    execution_success: bool
    correctness_success: bool
    failure_code: str | None
    candidate_sql: str | None


@dataclass(frozen=True)
class EvaluationSummary:
    total: int
    generation_success: int
    validation_success: int
    execution_success: int
    correctness_success: int
    cases: tuple[EvaluationCaseResult, ...]


def load_evaluation_cases(path: Path = DEFAULT_FIXTURE_PATH) -> tuple[EvaluationCase, ...]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return tuple(
        EvaluationCase(
            id=str(item["id"]),
            question=str(item["question"]),
            expected_columns=tuple(str(column) for column in item["expected_columns"]),
            expected_rows=tuple(tuple(row) for row in item["expected_rows"]),
            ordered=bool(item.get("ordered", True)),
        )
        for item in raw
    )


class EvaluationRunner:
    def __init__(
        self,
        *,
        model: Text2SqlModel,
        validator: SqlPolicyValidator,
        executor: QueryExecutor,
        cases: Iterable[EvaluationCase] | None = None,
    ):
        self.model = model
        self.validator = validator
        self.executor = executor
        self.cases = tuple(cases if cases is not None else load_evaluation_cases())

    def run(self) -> EvaluationSummary:
        results = tuple(self._run_case(case) for case in self.cases)
        return EvaluationSummary(
            total=len(results),
            generation_success=sum(result.generation_success for result in results),
            validation_success=sum(result.validation_success for result in results),
            execution_success=sum(result.execution_success for result in results),
            correctness_success=sum(result.correctness_success for result in results),
            cases=results,
        )

    def _run_case(self, case: EvaluationCase) -> EvaluationCaseResult:
        try:
            generated = self.model.generate(question=case.question)
        except Text2SqlGenerationError as exc:
            return self._failed(case, failure_code=str(exc))

        try:
            validation = self.validator.validate(generated.sql)
        except SqlPolicyViolation as exc:
            return self._failed(
                case,
                generation_success=True,
                failure_code=exc.code,
                candidate_sql=generated.sql,
            )

        try:
            actual = self.executor.execute(validation.normalized_sql)
        except QueryExecutionError as exc:
            return self._failed(
                case,
                generation_success=True,
                validation_success=True,
                failure_code=str(exc),
                candidate_sql=generated.sql,
            )

        correct = result_matches(case, actual)
        return EvaluationCaseResult(
            case_id=case.id,
            question=case.question,
            generation_success=True,
            validation_success=True,
            execution_success=True,
            correctness_success=correct,
            failure_code=None if correct else "RESULT_MISMATCH",
            candidate_sql=generated.sql,
        )

    @staticmethod
    def _failed(
        case: EvaluationCase,
        *,
        generation_success: bool = False,
        validation_success: bool = False,
        execution_success: bool = False,
        failure_code: str,
        candidate_sql: str | None = None,
    ) -> EvaluationCaseResult:
        return EvaluationCaseResult(
            case_id=case.id,
            question=case.question,
            generation_success=generation_success,
            validation_success=validation_success,
            execution_success=execution_success,
            correctness_success=False,
            failure_code=failure_code,
            candidate_sql=candidate_sql,
        )


def result_matches(case: EvaluationCase, actual: QueryResult) -> bool:
    if actual.columns != case.expected_columns:
        return False

    expected_rows = case.expected_rows
    actual_rows = actual.rows
    if not case.ordered:
        expected_rows = tuple(sorted(expected_rows, key=repr))
        actual_rows = tuple(sorted(actual_rows, key=repr))

    if len(expected_rows) != len(actual_rows):
        return False

    return all(
        _row_matches(expected, observed)
        for expected, observed in zip(expected_rows, actual_rows, strict=True)
    )


def _row_matches(expected: tuple[object, ...], actual: tuple[object, ...]) -> bool:
    if len(expected) != len(actual):
        return False
    return all(_value_matches(left, right) for left, right in zip(expected, actual, strict=True))


def _value_matches(expected: object, actual: object) -> bool:
    numeric_types = (int, float, Decimal)
    if isinstance(expected, numeric_types) and isinstance(actual, numeric_types):
        return math.isclose(float(expected), float(actual), rel_tol=1e-9, abs_tol=1e-9)
    return expected == actual
