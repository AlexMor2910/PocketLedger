from datetime import date
from decimal import Decimal
from uuid import uuid4

import pytest

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import ExpenseNotFoundError
from pocketledger.domain.expense_service import ExpenseService
from pocketledger.persistence.in_memory_expense_repository import InMemoryExpenseRepository


def make_service():
    return ExpenseService(InMemoryExpenseRepository())


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
    assert make_service().list_expenses() == []


def test_add_returns_and_stores_validated_expense():
    service = make_service()
    expense = add_expense(service, description="  Lunch  ", category="  Food  ")

    assert isinstance(expense, Expense)
    assert expense.description == "Lunch"
    assert expense.category == "Food"
    assert service.list_expenses() == [expense]


def test_multiple_expenses_have_distinct_ids_and_preserve_insertion_order():
    service = make_service()
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
    service = make_service()
    existing = add_expense(service)

    with pytest.raises(error):
        add_expense(service, **overrides)

    assert service.list_expenses() == [existing]


def test_listing_returns_a_copy():
    service = make_service()
    expense = add_expense(service)
    listed = service.list_expenses()
    listed.clear()

    assert service.list_expenses() == [expense]
    assert service.list_expenses() is not service.list_expenses()


def test_service_instances_have_separate_collections():
    first_service = make_service()
    second_service = make_service()
    add_expense(first_service)

    assert second_service.list_expenses() == []


def test_service_requires_repository():
    with pytest.raises(TypeError):
        ExpenseService()


def test_services_can_share_an_injected_repository():
    repository = InMemoryExpenseRepository()
    first = ExpenseService(repository)
    second = ExpenseService(repository)
    expense = add_expense(first)
    assert second.list_expenses() == [expense]


def test_repository_failure_propagates_from_service():
    class FailingRepository:
        def add(self, expense):
            raise RuntimeError("storage failed")

        def list_expenses(self):
            raise RuntimeError("storage failed")

    service = ExpenseService(FailingRepository())
    with pytest.raises(RuntimeError, match="storage failed"):
        add_expense(service)
    with pytest.raises(RuntimeError, match="storage failed"):
        service.list_expenses()


def test_deletion_delegates_uuid_to_repository():
    class RecordingRepository:
        def delete(self, expense_id):
            self.deleted_id = expense_id

    repository = RecordingRepository()
    expense_id = uuid4()
    assert ExpenseService(repository).delete_expense(expense_id) is None
    assert repository.deleted_id == expense_id


@pytest.mark.parametrize("error", [ExpenseNotFoundError("missing"), RuntimeError("failed")])
def test_deletion_errors_propagate(error):
    class FailingRepository:
        def delete(self, expense_id):
            raise error

    with pytest.raises(type(error), match=str(error)):
        ExpenseService(FailingRepository()).delete_expense(uuid4())
