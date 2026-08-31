from __future__ import annotations

from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError


@dataclass(frozen=True)
class SqlValidationResult:
    normalized_sql: str
    tables: tuple[str, ...]


class SqlPolicyViolation(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


class SqlPolicyValidator:
    def __init__(self, *, allowed_tables: set[str]):
        self.allowed_tables = frozenset(allowed_tables)

    def validate(self, sql: str) -> SqlValidationResult:
        try:
            statements = parse(sql, read="sqlite")
        except ParseError as exc:
            raise SqlPolicyViolation("SQL_PARSE_ERROR") from exc

        if len(statements) != 1:
            raise SqlPolicyViolation("MULTI_STATEMENT_NOT_ALLOWED")

        statement = statements[0]
        if not isinstance(statement, exp.Select):
            raise SqlPolicyViolation("READ_QUERY_ONLY")

        forbidden_types = (
            exp.Insert,
            exp.Update,
            exp.Delete,
            exp.Create,
            exp.Drop,
            exp.Alter,
        )
        if any(isinstance(node, forbidden_types) for node in statement.walk()):
            raise SqlPolicyViolation("WRITE_OR_DDL_NOT_ALLOWED")

        tables = tuple(sorted({table.name for table in statement.find_all(exp.Table)}))
        if not tables:
            raise SqlPolicyViolation("TABLE_REQUIRED")

        disallowed = [table for table in tables if table not in self.allowed_tables]
        if disallowed:
            raise SqlPolicyViolation("TABLE_NOT_ALLOWED")

        return SqlValidationResult(
            normalized_sql=statement.sql(dialect="sqlite"),
            tables=tables,
        )
