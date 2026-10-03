from datetime import date
from decimal import Decimal

import pytest

from pocketledger.domain.expense_service import ExpenseService
from pocketledger.domain.expense_repository import ExpenseNotFoundError
from pocketledger.persistence.in_memory_expense_repository import InMemoryExpenseRepository
from pocketledger.ui.cli import ExpenseCLI


def run_cli(answers, service):
    answers = iter(answers)
    output = []
    ExpenseCLI(service, input_fn=lambda prompt: next(answers), output_fn=output.append).run()
    return output


def make_service():
    return ExpenseService(InMemoryExpenseRepository())


def test_add_valid_expense_and_exit():
    service = make_service()
    output = run_cli(["1", "  Lunch  ", "12.345", "  Food  ", "2024-02-29", "4"], service)
    expense, = service.list_expenses()
    assert expense.description == "Lunch"
    assert expense.amount == Decimal("12.345")
    assert expense.category == "Food"
    assert expense.date == date(2024, 2, 29)
    assert "Expense added." in output
    assert output[-1] == "Goodbye."


@pytest.mark.parametrize(
    "fields, message",
    [
        (["Lunch", "oops", "Food", "2024-02-29"], "decimal"),
        (["Lunch", "1", "Food", "2024-02-30"], "YYYY-MM-DD"),
        (["Lunch", "1", "Food", "20240229"], "YYYY-MM-DD"),
        (["Lunch", "1", "Food", "2024-W09-4"], "YYYY-MM-DD"),
        (["Lunch", "1", "Food", "29/02/2024"], "YYYY-MM-DD"),
        ([" ", "1", "Food", "2024-02-29"], "description"),
        (["Lunch", "1", " ", "2024-02-29"], "category"),
        (["Lunch", "0", "Food", "2024-02-29"], "greater than zero"),
        (["Lunch", "-1", "Food", "2024-02-29"], "greater than zero"),
        (["Lunch", "NaN", "Food", "2024-02-29"], "finite"),
        (["Lunch", "Infinity", "Food", "2024-02-29"], "finite"),
    ],
)
def test_invalid_input_returns_to_menu_and_allows_valid_addition(fields, message):
    service = make_service()
    output = run_cli(
        ["1", *fields, "1", "Valid", "2", "Food", "2024-01-01", "4"], service
    )
    assert any(line.startswith("Error:") and message in line for line in output)
    assert [expense.description for expense in service.list_expenses()] == ["Valid"]
    assert output[-1] == "Goodbye."


def test_list_shows_fields_in_insertion_order_without_ids_or_rounding():
    service = make_service()
    first = service.add_expense("First", Decimal("1.2300"), "Food", date(2030, 1, 1))
    second = service.add_expense("Second", Decimal("0.0001"), "Other", date(2020, 1, 1))
    text = "\n".join(run_cli(["2", "4"], service))
    assert "Date | Description | Category | Amount" in text
    assert "2030-01-01 | First | Food | 1.2300" in text
    assert "2020-01-01 | Second | Other | 0.0001" in text
    assert text.index("First") < text.index("Second")
    assert str(first.id) not in text
    assert str(second.id) not in text


def test_empty_list_and_invalid_menu_choice():
    output = run_cli(["oops", "2", "4"], make_service())
    assert "Choose 1, 2, 3, or 4." in output
    assert "No expenses yet." in output


def test_exit_does_not_call_service():
    class UnusedService:
        def add_expense(self, **fields):
            pytest.fail("Exit must not add expenses")

        def list_expenses(self):
            pytest.fail("Exit must not list expenses")

    assert run_cli(["4"], UnusedService())[-1] == "Goodbye."


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
@pytest.mark.parametrize("partial_answers", [[], ["1", "Lunch"]])
def test_input_interruption_exits_without_partial_expense(interruption, partial_answers):
    service = make_service()
    answers = iter(partial_answers)
    output = []

    def read(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise interruption

    ExpenseCLI(service, input_fn=read, output_fn=output.append).run()
    assert output[-1] == "Goodbye."
    assert service.list_expenses() == []


def test_ui_passes_converted_values_to_service():
    class RecordingService:
        def add_expense(self, **fields):
            self.fields = fields

    service = RecordingService()
    run_cli(["1", "Lunch", "1.234", "Food", "2024-02-29", "4"], service)
    assert service.fields == {
        "description": "Lunch", "amount": Decimal("1.234"),
        "category": "Food", "date": date(2024, 2, 29),
    }


def test_numbered_deletion_uses_selected_uuid_and_subsequent_listing_reflects_delete():
    service = make_service()
    first = service.add_expense("First", Decimal("1.2300"), "Food", date(2030, 1, 1))
    second = service.add_expense("Second", Decimal("2"), "Other", date(2020, 1, 1))
    output = run_cli(["3", "2", "2", "4"], service)
    assert "1. 2030-01-01 | First | Food | 1.2300" in output
    assert "2. 2020-01-01 | Second | Other | 2" in output
    assert "Expense deleted." in output
    after_delete = output[output.index("Expense deleted.") + 1:]
    assert "2030-01-01 | First | Food | 1.2300" in after_delete
    assert not any("Second" in line for line in after_delete)
    assert service.list_expenses() == [first]
    assert all(str(expense.id) not in "\n".join(output) for expense in (first, second))


@pytest.mark.parametrize("selection", ["oops", "", "1.5", "0", "-1", "2"])
def test_invalid_delete_selection_returns_to_menu_without_changes(selection):
    service = make_service()
    expense = service.add_expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1))
    output = run_cli(["3", selection, "2", "4"], service)
    assert "Error: choose a number from 1 to 1." in output
    assert "2024-01-01 | Lunch | Food | 1" in output
    assert service.list_expenses() == [expense]
    assert output[-1] == "Goodbye."


def test_delete_empty_list_returns_without_asking_for_selection():
    output = run_cli(["3", "4"], make_service())
    assert "No expenses to delete." in output
    assert output[-1] == "Goodbye."


def test_disappearing_expense_is_handled_and_uuid_is_passed_to_service():
    expense = make_service().add_expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1))

    class DisappearingService:
        def list_expenses(self):
            return [expense]

        def delete_expense(self, expense_id):
            assert expense_id == expense.id
            raise ExpenseNotFoundError("missing")

    output = run_cli(["3", "1", "4"], DisappearingService())
    assert "Expense no longer exists. Nothing was deleted." in output
    assert "Expense deleted." not in output


@pytest.mark.parametrize("interruption", [EOFError, KeyboardInterrupt])
def test_interruption_at_delete_selection_leaves_expense_intact(interruption):
    service = make_service()
    expense = service.add_expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1))
    output = []
    answers = iter(["3"])

    def read(prompt):
        try:
            return next(answers)
        except StopIteration:
            raise interruption

    ExpenseCLI(service, input_fn=read, output_fn=output.append).run()
    assert output[-1] == "Goodbye."
    assert service.list_expenses() == [expense]
