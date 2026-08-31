import pytest

from app.sql_policy import SqlPolicyValidator, SqlPolicyViolation


@pytest.fixture
def validator() -> SqlPolicyValidator:
    return SqlPolicyValidator(
        allowed_tables={"customers", "products", "orders", "order_items"}
    )


def test_allows_single_select_from_allowed_table(validator: SqlPolicyValidator) -> None:
    result = validator.validate("SELECT id, order_month FROM orders")

    assert result.tables == ("orders",)
    assert result.normalized_sql.startswith("SELECT")


@pytest.mark.parametrize(
    ("sql", "code"),
    [
        ("DELETE FROM orders", "READ_QUERY_ONLY"),
        ("UPDATE orders SET order_month = 'x'", "READ_QUERY_ONLY"),
        ("SELECT * FROM orders; SELECT * FROM products", "MULTI_STATEMENT_NOT_ALLOWED"),
        ("SELECT * FROM sqlite_master", "TABLE_NOT_ALLOWED"),
        ("SELECT 1", "TABLE_REQUIRED"),
    ],
)
def test_rejects_unsafe_or_out_of_scope_sql(
    validator: SqlPolicyValidator, sql: str, code: str
) -> None:
    with pytest.raises(SqlPolicyViolation) as captured:
        validator.validate(sql)

    assert captured.value.code == code
