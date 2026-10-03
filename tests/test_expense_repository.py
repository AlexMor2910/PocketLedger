from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import DuplicateExpenseError, ExpenseRepository
from pocketledger.domain.expense_repository import ExpenseNotFoundError
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


def test_delete_preserves_remaining_order_and_allows_more_additions(repository):
    first, middle, last = make_expense(), make_expense(), make_expense()
    for expense in (first, middle, last):
        repository.add(expense)
    assert repository.delete(middle.id) is None
    assert repository.list_expenses() == [first, last]
    additional = make_expense()
    repository.add(additional)
    assert repository.list_expenses() == [first, last, additional]


def test_unknown_delete_leaves_collection_unchanged_and_repository_usable(repository):
    existing = make_expense()
    repository.add(existing)
    with pytest.raises(ExpenseNotFoundError):
        repository.delete(uuid4())
    assert repository.list_expenses() == [existing]
    repository.delete(existing.id)
    assert repository.list_expenses() == []
    with pytest.raises(ExpenseNotFoundError):
        repository.delete(existing.id)
    assert repository.list_expenses() == []
