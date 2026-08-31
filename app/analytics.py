from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time
from typing import Protocol

import psycopg


@dataclass(frozen=True)
class QueryResult:
    columns: tuple[str, ...]
    rows: tuple[tuple[object, ...], ...]


class QueryExecutionError(RuntimeError):
    pass


class QueryExecutor(Protocol):
    def execute(self, sql: str) -> QueryResult:
        ...


def initialize_synthetic_analytics_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    try:
        connection.executescript(
            """
            PRAGMA foreign_keys = ON;

            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                customer_id INTEGER NOT NULL REFERENCES customers(id),
                order_month TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY,
                order_id INTEGER NOT NULL REFERENCES orders(id),
                product_id INTEGER NOT NULL REFERENCES products(id),
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL
            );
            """
        )

        count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        if count == 0:
            connection.executemany(
                "INSERT INTO customers(id, name) VALUES (?, ?)",
                [(1, "Acme"), (2, "Bravo")],
            )
            connection.executemany(
                "INSERT INTO products(id, name, category) VALUES (?, ?, ?)",
                [
                    (1, "Notebook", "office"),
                    (2, "Monitor", "electronics"),
                    (3, "Keyboard", "electronics"),
                ],
            )
            connection.executemany(
                "INSERT INTO orders(id, customer_id, order_month) VALUES (?, ?, ?)",
                [
                    (1, 1, "2026-01"),
                    (2, 2, "2026-01"),
                    (3, 1, "2026-02"),
                ],
            )
            connection.executemany(
                """
                INSERT INTO order_items(id, order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?, ?)
                """,
                [
                    (1, 1, 1, 2, 5.0),
                    (2, 1, 2, 1, 200.0),
                    (3, 2, 3, 2, 80.0),
                    (4, 3, 2, 2, 200.0),
                ],
            )
        connection.commit()
    finally:
        connection.close()


class SqliteReadOnlyQueryExecutor:
    def __init__(
        self,
        *,
        database_path: Path,
        max_result_rows: int,
        timeout_seconds: float,
    ):
        self.database_path = database_path
        self.max_result_rows = max_result_rows
        self.timeout_seconds = timeout_seconds

    def execute(self, sql: str) -> QueryResult:
        started_at = time.monotonic()
        connection = sqlite3.connect(
            f"file:{self.database_path.resolve()}?mode=ro",
            uri=True,
        )
        try:
            connection.execute("PRAGMA query_only = ON")

            def abort_if_timed_out() -> int:
                return int(time.monotonic() - started_at > self.timeout_seconds)

            connection.set_progress_handler(abort_if_timed_out, 1000)
            bounded_sql = f"SELECT * FROM ({sql.rstrip(';')}) AS bounded_query LIMIT ?"
            cursor = connection.execute(bounded_sql, (self.max_result_rows,))
            columns = tuple(description[0] for description in cursor.description or ())
            rows = tuple(tuple(row) for row in cursor.fetchall())
            return QueryResult(columns=columns, rows=rows)
        except sqlite3.DatabaseError as exc:
            raise QueryExecutionError(type(exc).__name__) from exc
        finally:
            connection.close()


class PostgresReadOnlyQueryExecutor:
    def __init__(
        self,
        *,
        dsn: str,
        max_result_rows: int,
        timeout_seconds: float,
    ):
        self.dsn = dsn
        self.max_result_rows = max_result_rows
        self.timeout_seconds = timeout_seconds

    def execute(self, sql: str) -> QueryResult:
        timeout_ms = max(1, int(self.timeout_seconds * 1000))
        bounded_sql = f"SELECT * FROM ({sql.rstrip(';')}) AS bounded_query LIMIT %s"

        try:
            with psycopg.connect(self.dsn) as connection:
                with connection.transaction():
                    connection.execute("SET TRANSACTION READ ONLY")
                    connection.execute(
                        "SELECT set_config('statement_timeout', %s, true)",
                        (f"{timeout_ms}ms",),
                    )
                    cursor = connection.execute(bounded_sql, (self.max_result_rows,))
                    columns = tuple(
                        description.name for description in cursor.description or ()
                    )
                    rows = tuple(tuple(row) for row in cursor.fetchall())
                    return QueryResult(columns=columns, rows=rows)
        except psycopg.Error as exc:
            raise QueryExecutionError(type(exc).__name__) from exc
