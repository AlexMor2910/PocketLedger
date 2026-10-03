import re
from collections.abc import Callable
from datetime import date
from decimal import Decimal, InvalidOperation

from pocketledger.domain.expense_service import ExpenseService
from pocketledger.domain.expense_repository import ExpenseNotFoundError


class ExpenseCLI:
    def __init__(
        self,
        service: ExpenseService,
        *,
        input_fn: Callable[[str], str] = input,
        output_fn: Callable[[str], None] = print,
    ) -> None:
        self._service = service
        self._input = input_fn
        self._output = output_fn

    def run(self) -> None:
        try:
            while True:
                self._output(
                    "\nPocketLedger\n1. Add expense\n2. List expenses\n3. Delete expense\n4. Exit"
                )
                choice = self._input("Choose an option: ").strip()
                if choice == "1":
                    self._add_expense()
                elif choice == "2":
                    self._list_expenses()
                elif choice == "3":
                    self._delete_expense()
                elif choice == "4":
                    break
                else:
                    self._output("Choose 1, 2, 3, or 4.")
        except (EOFError, KeyboardInterrupt):
            self._output("")
        self._output("Goodbye.")

    def _add_expense(self) -> None:
        description = self._input("Description: ")
        amount_text = self._input("Amount (e.g. 12.50): ")
        category = self._input("Category: ")
        date_text = self._input("Date (YYYY-MM-DD): ").strip()

        try:
            amount = Decimal(amount_text)
        except InvalidOperation:
            self._output("Error: enter a decimal amount, such as 12.50.")
            return

        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", date_text):
                raise ValueError
            expense_date = date.fromisoformat(date_text)
        except ValueError:
            self._output("Error: enter a valid date in YYYY-MM-DD format.")
            return

        try:
            self._service.add_expense(
                description=description, amount=amount, category=category, date=expense_date
            )
        except (ValueError, TypeError) as error:
            self._output(f"Error: {error}.")
            return
        self._output("Expense added.")

    def _list_expenses(self) -> None:
        expenses = self._service.list_expenses()
        if not expenses:
            self._output("No expenses yet.")
            return
        self._output("Date | Description | Category | Amount")
        for expense in expenses:
            self._output(
                f"{expense.date.isoformat()} | {expense.description} | "
                f"{expense.category} | {expense.amount}"
            )

    def _delete_expense(self) -> None:
        expenses = self._service.list_expenses()
        if not expenses:
            self._output("No expenses to delete.")
            return
        for number, expense in enumerate(expenses, start=1):
            self._output(
                f"{number}. {expense.date.isoformat()} | {expense.description} | "
                f"{expense.category} | {expense.amount}"
            )
        try:
            selection = int(self._input("Expense number to delete: "))
            if not 1 <= selection <= len(expenses):
                raise ValueError
        except ValueError:
            self._output(f"Error: choose a number from 1 to {len(expenses)}.")
            return
        try:
            self._service.delete_expense(expenses[selection - 1].id)
        except ExpenseNotFoundError:
            self._output("Expense no longer exists. Nothing was deleted.")
            return
        self._output("Expense deleted.")
