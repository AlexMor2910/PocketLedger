import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import DuplicateExpenseError


class SQLiteExpenseRepository:
    def __init__(self, database_path: str | Path) -> None:
        self._connection = sqlite3.connect(database_path, autocommit=False)
        try:
            with self._connection:
                self._connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS expenses (
                        insertion_order INTEGER PRIMARY KEY,
                        id TEXT NOT NULL UNIQUE,
                        description TEXT NOT NULL,
                        amount TEXT NOT NULL,
                        category TEXT NOT NULL,
                        expense_date TEXT NOT NULL
                    )
                    """
                )
        except Exception:
            self._connection.close()
            raise

    def add(self, expense: Expense) -> None:
        try:
            with self._connection:
                self._connection.execute(
                    """
                    INSERT INTO expenses (id, description, amount, category, expense_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        str(expense.id), expense.description, str(expense.amount),
                        expense.category, expense.date.isoformat(),
                    ),
                )
        except sqlite3.IntegrityError as error:
            if (
                error.sqlite_errorcode == sqlite3.SQLITE_CONSTRAINT_UNIQUE
                and str(error) == "UNIQUE constraint failed: expenses.id"
            ):
                raise DuplicateExpenseError(f"Expense {expense.id} already exists") from error
            raise

    def list_expenses(self) -> list[Expense]:
        with self._connection:
            rows = self._connection.execute(
                """
                SELECT id, description, amount, category, expense_date
                FROM expenses ORDER BY insertion_order
                """
            ).fetchall()
        return [
            Expense.restore(
                id=UUID(row[0]), description=row[1], amount=Decimal(row[2]),
                category=row[3], date=date.fromisoformat(row[4]),
            )
            for row in rows
        ]

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> "SQLiteExpenseRepository":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
