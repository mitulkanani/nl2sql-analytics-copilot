import pytest

from app.safety import SQLSafetyError, validate_sql


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM orders",
        "UPDATE orders SET status = 'cancelled'",
        "INSERT INTO orders VALUES (1, 1, '2024-01-01', 'completed', 10)",
        "DROP TABLE orders",
        "PRAGMA table_info(orders)",
        "ATTACH DATABASE '/tmp/x.db' AS x",
        "SELECT * INTO export FROM orders",
        "SELECT load_extension('evil') FROM orders",
    ],
)
def test_blocks_mutating_or_dangerous_sql(sql: str) -> None:
    with pytest.raises(SQLSafetyError):
        validate_sql(sql)


def test_blocks_multiple_statements() -> None:
    with pytest.raises(SQLSafetyError):
        validate_sql("SELECT * FROM orders; DELETE FROM orders")


def test_blocks_unknown_table() -> None:
    with pytest.raises(SQLSafetyError):
        validate_sql("SELECT * FROM users")


def test_blocks_comments() -> None:
    with pytest.raises(SQLSafetyError):
        validate_sql("SELECT * FROM orders -- show all")


def test_accepts_select_from_approved_tables() -> None:
    validated = validate_sql("SELECT status, COUNT(*) AS total FROM orders GROUP BY status")
    assert "orders" in validated.tables
