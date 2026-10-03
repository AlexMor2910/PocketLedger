import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

import pytest

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_service import ExpenseService
from pocketledger.persistence.sqlite_expense_repository import SQLiteExpenseRepository


@pytest.mark.parametrize("amount", ["12345678901234567890.123456789", "1.2300", "1E-100"])
def test_exact_values_and_domain_types_survive_reopening(tmp_path, amount):
    path = tmp_path / "expenses.sqlite"
    expense = Expense("Café ' lunch", Decimal(amount), "Food", date(2024, 2, 29))
    future = Expense("Future", Decimal("2"), "Other", date(9999, 12, 31))
    with SQLiteExpenseRepository(path) as repository:
        repository.add(expense)
        repository.add(future)

    with SQLiteExpenseRepository(path) as reopened:
        restored, restored_future = reopened.list_expenses()
        assert [restored, restored_future] == [expense, future]
        assert isinstance(restored.id, UUID)
        assert isinstance(restored.amount, Decimal)
        assert type(restored.date) is date
        assert restored.amount.as_tuple() == expense.amount.as_tuple()

    with sqlite3.connect(path) as connection:
        row = connection.execute(
            "SELECT id, amount, expense_date FROM expenses ORDER BY insertion_order"
        ).fetchone()
        assert row == (str(expense.id), str(expense.amount), expense.date.isoformat())
        assert all(isinstance(value, str) for value in row)


def test_separate_database_files_are_isolated(tmp_path):
    with SQLiteExpenseRepository(tmp_path / "first.sqlite") as first:
        first.add(Expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1)))
        with SQLiteExpenseRepository(tmp_path / "second.sqlite") as second:
            assert second.list_expenses() == []


def test_service_additions_are_visible_to_another_repository_instance(tmp_path):
    path = tmp_path / "expenses.sqlite"
    with SQLiteExpenseRepository(path) as first, SQLiteExpenseRepository(path) as second:
        service = ExpenseService(first)
        expense = service.add_expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1))
        assert ExpenseService(second).list_expenses() == [expense]


@pytest.mark.parametrize(
    "column, value, error",
    [
        ("id", "bad-uuid", ValueError),
        ("amount", "bad-decimal", InvalidOperation),
        ("amount", "NaN", ValueError),
        ("amount", "0", ValueError),
        ("expense_date", "2024-02-30", ValueError),
        ("description", " ", ValueError),
        ("category", " ", ValueError),
    ],
)
def test_invalid_persisted_rows_fail_visibly(tmp_path, column, value, error):
    path = tmp_path / "expenses.sqlite"
    with SQLiteExpenseRepository(path) as repository:
        repository.add(Expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1)))
    with sqlite3.connect(path) as connection:
        # Column names come exclusively from the fixed test cases above.
        connection.execute(f"UPDATE expenses SET {column} = ?", (value,))
    with SQLiteExpenseRepository(path) as repository:
        with pytest.raises(error):
            repository.list_expenses()


def test_non_duplicate_integrity_error_propagates(tmp_path):
    path = tmp_path / "expenses.sqlite"
    with SQLiteExpenseRepository(path) as repository:
        with sqlite3.connect(path) as connection:
            connection.execute(
                "CREATE TRIGGER reject_expenses BEFORE INSERT ON expenses "
                "BEGIN SELECT RAISE(ABORT, 'blocked'); END"
            )
        with pytest.raises(sqlite3.IntegrityError, match="blocked"):
            repository.add(Expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1)))


def test_missing_parent_directory_error_propagates(tmp_path):
    with pytest.raises(sqlite3.OperationalError):
        SQLiteExpenseRepository(tmp_path / "missing" / "expenses.sqlite")


def test_close_and_context_manager_close_connection(tmp_path):
    repository = SQLiteExpenseRepository(tmp_path / "explicit.sqlite")
    repository.close()
    repository.close()
    with pytest.raises(sqlite3.ProgrammingError):
        repository.list_expenses()

    with SQLiteExpenseRepository(tmp_path / "context.sqlite") as repository:
        pass
    with pytest.raises(sqlite3.ProgrammingError):
        repository.list_expenses()


def test_context_manager_closes_connection_on_exception(tmp_path):
    with pytest.raises(RuntimeError):
        with SQLiteExpenseRepository(tmp_path / "exception.sqlite") as repository:
            raise RuntimeError("caller failed")
    with pytest.raises(sqlite3.ProgrammingError):
        repository.list_expenses()
