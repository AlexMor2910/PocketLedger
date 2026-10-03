import re
from datetime import date
from decimal import Decimal, InvalidOperation
from uuid import UUID

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from pocketledger.domain.expense_repository import ExpenseNotFoundError
from pocketledger.domain.expense_service import ExpenseService


class ExpenseWindow(QMainWindow):
    def __init__(self, service: ExpenseService) -> None:
        super().__init__()
        self._service = service
        self.setWindowTitle("PocketLedger")
        self.resize(760, 520)

        self.description_input = QLineEdit()
        self.amount_input = QLineEdit()
        self.amount_input.setPlaceholderText("12.50")
        self.category_input = QLineEdit()
        self.date_input = QLineEdit(date.today().isoformat())
        self.date_input.setPlaceholderText("YYYY-MM-DD")
        form = QFormLayout()
        form.addRow("Description", self.description_input)
        form.addRow("Amount", self.amount_input)
        form.addRow("Category", self.category_input)
        form.addRow("Date (YYYY-MM-DD)", self.date_input)

        self.add_button = QPushButton("Add expense")
        self.delete_button = QPushButton("Delete selected expense")
        self.add_button.clicked.connect(self.add_expense)
        self.delete_button.clicked.connect(self.delete_expense)
        actions = QHBoxLayout()
        actions.addWidget(self.add_button)
        actions.addWidget(self.delete_button)

        self.feedback = QLabel()
        self.feedback.setTextFormat(Qt.TextFormat.PlainText)
        self.feedback.setWordWrap(True)
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Date", "Description", "Category", "Amount"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setSortingEnabled(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addLayout(actions)
        layout.addWidget(self.feedback)
        layout.addWidget(self.table)
        central = QWidget()
        central.setLayout(layout)
        self.setCentralWidget(central)
        self.refresh_expenses()

    def read_form_values(self) -> tuple[str, Decimal, str, date]:
        try:
            amount = Decimal(self.amount_input.text())
        except InvalidOperation:
            raise ValueError("Enter a decimal amount, such as 12.50.") from None
        date_text = self.date_input.text().strip()
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_text):
                raise ValueError
            expense_date = date.fromisoformat(date_text)
        except ValueError:
            raise ValueError("Enter a valid date in YYYY-MM-DD format.") from None
        return self.description_input.text(), amount, self.category_input.text(), expense_date

    def add_expense(self) -> None:
        try:
            description, amount, category, expense_date = self.read_form_values()
            self._service.add_expense(
                description=description, amount=amount, category=category, date=expense_date
            )
        except (ValueError, TypeError) as error:
            self.feedback.setText(f"Error: {error}")
            return
        self.description_input.clear()
        self.amount_input.clear()
        self.category_input.clear()
        self.date_input.setText(date.today().isoformat())
        self.refresh_expenses()
        self.feedback.setText("Expense added.")

    def refresh_expenses(self) -> None:
        self._expenses = self._service.list_expenses()
        self.table.setRowCount(len(self._expenses))
        for row, expense in enumerate(self._expenses):
            values = (
                expense.date.isoformat(), expense.description, expense.category, str(expense.amount)
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
        self.table.clearSelection()

    def selected_expense_id(self) -> UUID | None:
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        return self._expenses[selected_rows[0].row()].id

    def delete_expense(self) -> None:
        expense_id = self.selected_expense_id()
        if expense_id is None:
            self.feedback.setText("Select an expense to delete.")
            return
        try:
            self._service.delete_expense(expense_id)
        except ExpenseNotFoundError:
            self.refresh_expenses()
            self.feedback.setText("Expense no longer exists. Nothing was deleted.")
            return
        self.refresh_expenses()
        self.feedback.setText("Expense deleted.")
