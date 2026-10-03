from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest

from pocketledger.domain.expense_service import ExpenseService
from pocketledger.persistence.in_memory_expense_repository import InMemoryExpenseRepository
from pocketledger.ui.gui import ExpenseWindow


@pytest.fixture
def service():
    return ExpenseService(InMemoryExpenseRepository())


@pytest.fixture
def window(qapplication, service):
    window = ExpenseWindow(service)
    yield window
    window.close()
    window.deleteLater()
    qapplication.processEvents()


def fill_form(window, description="Lunch", amount="1.2300", category="Food", date_text="2024-02-29"):
    window.description_input.setText(description)
    window.amount_input.setText(amount)
    window.category_input.setText(category)
    window.date_input.setText(date_text)


def rows(window):
    return [
        [window.table.item(row, column).text() for column in range(4)]
        for row in range(window.table.rowCount())
    ]


def test_window_title_and_empty_table(window):
    assert window.windowTitle() == "PocketLedger"
    assert window.table.columnCount() == 4
    assert window.table.rowCount() == 0
    assert [window.table.horizontalHeaderItem(column).text() for column in range(4)] == [
        "Date", "Description", "Category", "Amount"
    ]


def test_initial_display_preserves_order_precision_and_hides_uuid(qapplication, service):
    first = service.add_expense("First", Decimal("1.2300"), "Food", date(2030, 1, 1))
    second = service.add_expense("Second", Decimal("0.0001"), "Other", date(2020, 1, 1))
    window = ExpenseWindow(service)
    try:
        assert rows(window) == [
            ["2030-01-01", "First", "Food", "1.2300"],
            ["2020-01-01", "Second", "Other", "0.0001"],
        ]
        assert str(first.id) not in str(rows(window))
        assert str(second.id) not in str(rows(window))
        assert not window.table.isSortingEnabled()
    finally:
        window.close()
        window.deleteLater()


def test_add_button_calls_service_refreshes_and_resets_form(window, service):
    fill_form(window, description="  Lunch  ", category="  Food  ")
    QTest.mouseClick(window.add_button, Qt.MouseButton.LeftButton)
    expense, = service.list_expenses()
    assert expense.description == "Lunch"
    assert expense.amount.as_tuple() == Decimal("1.2300").as_tuple()
    assert expense.date == date(2024, 2, 29)
    assert rows(window) == [["2024-02-29", "Lunch", "Food", "1.2300"]]
    assert window.feedback.text() == "Expense added."
    assert window.description_input.text() == ""
    assert window.amount_input.text() == ""
    assert window.category_input.text() == ""
    assert window.date_input.text() == date.today().isoformat()


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"amount": "oops"}, "decimal"),
        ({"amount": ""}, "decimal"),
        ({"amount": "0"}, "greater than zero"),
        ({"amount": "-1"}, "greater than zero"),
        ({"amount": "NaN"}, "finite"),
        ({"amount": "Infinity"}, "finite"),
        ({"date_text": "2024-02-30"}, "YYYY-MM-DD"),
        ({"date_text": "20240229"}, "YYYY-MM-DD"),
        ({"date_text": "2024-W09-4"}, "YYYY-MM-DD"),
        ({"description": " "}, "description"),
        ({"category": " "}, "category"),
    ],
)
def test_input_and_domain_errors_are_displayed_and_recovery_works(window, service, overrides, message):
    fill_form(window, **overrides)
    window.add_expense()
    assert message in window.feedback.text()
    assert window.table.rowCount() == 0
    assert service.list_expenses() == []
    assert window.description_input.text() == overrides.get("description", "Lunch")
    fill_form(window)
    window.add_expense()
    assert window.table.rowCount() == 1


def test_delete_selected_row_maps_to_uuid_and_refreshes(window, service):
    first = service.add_expense("First", Decimal("1"), "Food", date(2024, 1, 1))
    second = service.add_expense("Second", Decimal("2"), "Food", date(2024, 1, 1))
    window.refresh_expenses()
    window.table.selectRow(1)
    assert window.selected_expense_id() == second.id
    QTest.mouseClick(window.delete_button, Qt.MouseButton.LeftButton)
    assert service.list_expenses() == [first]
    assert rows(window) == [["2024-01-01", "First", "Food", "1"]]
    assert window.feedback.text() == "Expense deleted."
    assert window.selected_expense_id() is None


def test_delete_without_selection_is_handled(window):
    window.delete_expense()
    assert window.feedback.text() == "Select an expense to delete."


def test_disappearing_expense_is_handled_and_table_refreshed(window, service):
    expense = service.add_expense("Lunch", Decimal("1"), "Food", date(2024, 1, 1))
    window.refresh_expenses()
    window.table.selectRow(0)
    service.delete_expense(expense.id)
    window.delete_expense()
    assert "no longer exists" in window.feedback.text()
    assert window.table.rowCount() == 0


def test_gui_passes_typed_values_and_selected_uuid_to_service(qapplication):
    expense = ExpenseService(InMemoryExpenseRepository()).add_expense(
        "Lunch", Decimal("1.2300"), "Food", date(2024, 2, 29)
    )

    class RecordingService:
        def list_expenses(self):
            return [expense]

        def add_expense(self, **fields):
            self.fields = fields

        def delete_expense(self, expense_id):
            self.deleted_id = expense_id

    service = RecordingService()
    window = ExpenseWindow(service)
    try:
        fill_form(window)
        window.add_expense()
        assert service.fields == {
            "description": "Lunch", "amount": Decimal("1.2300"),
            "category": "Food", "date": date(2024, 2, 29),
        }
        window.table.selectRow(0)
        window.delete_expense()
        assert service.deleted_id == expense.id
    finally:
        window.close()
        window.deleteLater()
