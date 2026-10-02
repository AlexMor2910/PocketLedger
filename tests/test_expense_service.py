from datetime import date
from decimal import Decimal

import pytest

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_service import ExpenseService


def add_expense(service, description="Lunch", **overrides):
    fields = {
        "description": description,
        "amount": Decimal("12.345"),
        "category": "Food",
        "date": date(2024, 2, 29),
    }
    fields.update(overrides)
    return service.add_expense(**fields)


def test_service_starts_empty():
    assert ExpenseService().list_expenses() == []


def test_add_returns_and_stores_validated_expense():
    service = ExpenseService()
    expense = add_expense(service, description="  Lunch  ", category="  Food  ")

    assert isinstance(expense, Expense)
    assert expense.description == "Lunch"
    assert expense.category == "Food"
    assert service.list_expenses() == [expense]


def test_multiple_expenses_have_distinct_ids_and_preserve_insertion_order():
    service = ExpenseService()
    first = add_expense(service)
    second = add_expense(service)

    assert first.id != second.id
    assert service.list_expenses() == [first, second]


@pytest.mark.parametrize(
    "overrides, error",
    [
        ({"description": " "}, ValueError),
        ({"category": " "}, ValueError),
        ({"amount": Decimal("0")}, ValueError),
        ({"amount": 1.25}, TypeError),
        ({"date": "2024-02-29"}, TypeError),
    ],
)
def test_invalid_addition_leaves_existing_collection_unchanged(overrides, error):
    service = ExpenseService()
    existing = add_expense(service)

    with pytest.raises(error):
        add_expense(service, **overrides)

    assert service.list_expenses() == [existing]


def test_listing_returns_a_copy():
    service = ExpenseService()
    expense = add_expense(service)
    listed = service.list_expenses()
    listed.clear()

    assert service.list_expenses() == [expense]
    assert service.list_expenses() is not service.list_expenses()


def test_service_instances_have_separate_collections():
    first_service = ExpenseService()
    second_service = ExpenseService()
    add_expense(first_service)

    assert second_service.list_expenses() == []
