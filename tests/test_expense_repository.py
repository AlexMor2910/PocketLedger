from datetime import date
from decimal import Decimal

import pytest

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import DuplicateExpenseError, ExpenseRepository
from pocketledger.persistence.in_memory_expense_repository import InMemoryExpenseRepository
from pocketledger.persistence.sqlite_expense_repository import SQLiteExpenseRepository


@pytest.fixture(params=["memory", "sqlite"])
def repository(request, tmp_path):
    if request.param == "memory":
        yield InMemoryExpenseRepository()
    else:
        with SQLiteExpenseRepository(tmp_path / "expenses.sqlite") as repository:
            yield repository


def make_expense():
    return Expense("Lunch", Decimal("12.345"), "Food", date(2024, 2, 29))


def test_repository_starts_empty(repository: ExpenseRepository):
    assert repository.list_expenses() == []


def test_repository_adds_expenses_in_insertion_order(repository: ExpenseRepository):
    first = make_expense()
    second = make_expense()
    assert repository.add(first) is None
    repository.add(second)
    assert first.id != second.id
    assert repository.list_expenses() == [first, second]


def test_repository_returns_fresh_lists(repository: ExpenseRepository):
    expense = make_expense()
    repository.add(expense)
    listed = repository.list_expenses()
    listed.clear()
    assert repository.list_expenses() == [expense]
    assert repository.list_expenses() is not repository.list_expenses()


def test_duplicate_id_is_rejected_without_changing_existing_expense(repository):
    expense = make_expense()
    repository.add(expense)
    duplicate = Expense.restore(
        id=expense.id, description="Different", amount=Decimal("99"),
        category="Other", date=date(2030, 1, 1),
    )
    with pytest.raises(DuplicateExpenseError):
        repository.add(duplicate)
    assert repository.list_expenses() == [expense]
    next_expense = make_expense()
    repository.add(next_expense)
    assert repository.list_expenses() == [expense, next_expense]
