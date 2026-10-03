from dataclasses import FrozenInstanceError
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

import pytest

from pocketledger.domain.expense import Expense


def make_expense(**overrides):
    fields = {
        "description": "  Lunch  ",
        "amount": Decimal("12.345"),
        "category": "  Food  ",
        "date": date(2024, 2, 29),
    }
    fields.update(overrides)
    return Expense(**fields)


def test_valid_expense_normalizes_text_and_retains_amount_and_date():
    expense = make_expense()

    assert isinstance(expense.id, UUID)
    assert expense.description == "Lunch"
    assert expense.amount == Decimal("12.345")
    assert expense.category == "Food"
    assert expense.date == date(2024, 2, 29)


def test_ids_are_generated_automatically_and_are_distinct():
    assert make_expense().id != make_expense().id
    with pytest.raises(TypeError):
        make_expense(id=UUID(int=0))


@pytest.mark.parametrize("field", ["description", "category"])
@pytest.mark.parametrize("value", ["", " ", "\t\n"])
def test_blank_text_is_rejected(field, value):
    with pytest.raises(ValueError):
        make_expense(**{field: value})


@pytest.mark.parametrize("field", ["description", "category"])
@pytest.mark.parametrize("value", [None, 123, b"Food"])
def test_non_string_text_is_rejected(field, value):
    with pytest.raises(TypeError):
        make_expense(**{field: value})


@pytest.mark.parametrize("amount", ["0", "-0", "-1", "NaN", "sNaN", "Infinity", "-Infinity"])
def test_non_positive_or_non_finite_amount_is_rejected(amount):
    with pytest.raises(ValueError):
        make_expense(amount=Decimal(amount))


@pytest.mark.parametrize("amount", [1.25, 1, True, "1.25", None])
def test_non_decimal_amount_is_rejected(amount):
    with pytest.raises(TypeError):
        make_expense(amount=amount)


def test_positive_amount_has_no_two_decimal_place_restriction():
    assert make_expense(amount=Decimal("0.0001")).amount == Decimal("0.0001")


@pytest.mark.parametrize("value", ["2024-02-29", None, 123, datetime(2024, 2, 29, 12)])
def test_unsupported_date_type_is_rejected(value):
    with pytest.raises(TypeError):
        make_expense(date=value)


def test_future_date_is_allowed():
    future_date = date(9999, 12, 31)
    assert make_expense(date=future_date).date == future_date


@pytest.mark.parametrize("field", ["id", "description", "amount", "category", "date"])
def test_expense_fields_are_immutable(field):
    expense = make_expense()
    with pytest.raises(FrozenInstanceError):
        setattr(expense, field, getattr(expense, field))


def test_restore_preserves_identity_and_validates_and_normalizes_fields():
    original = make_expense()
    restored = Expense.restore(
        id=original.id, description="  Lunch  ", amount=original.amount,
        category="  Food  ", date=original.date,
    )
    assert restored == original
    with pytest.raises(FrozenInstanceError):
        restored.id = UUID(int=0)


@pytest.mark.parametrize(
    "overrides, error",
    [
        ({"id": "not-a-uuid"}, TypeError),
        ({"description": " "}, ValueError),
        ({"category": " "}, ValueError),
        ({"amount": Decimal("NaN")}, ValueError),
        ({"amount": Decimal("0")}, ValueError),
        ({"amount": 1.25}, TypeError),
        ({"date": datetime(2024, 2, 29)}, TypeError),
    ],
)
def test_restore_rejects_invalid_fields(overrides, error):
    original = make_expense()
    fields = {
        "id": original.id, "description": original.description,
        "amount": original.amount, "category": original.category, "date": original.date,
    }
    fields.update(overrides)
    with pytest.raises(error):
        Expense.restore(**fields)
