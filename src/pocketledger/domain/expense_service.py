from datetime import date
from decimal import Decimal

from pocketledger.domain.expense import Expense


class ExpenseService:
    def __init__(self) -> None:
        self._expenses: list[Expense] = []

    def add_expense(
        self, description: str, amount: Decimal, category: str, date: date
    ) -> Expense:
        expense = Expense(
            description=description, amount=amount, category=category, date=date
        )
        self._expenses.append(expense)
        return expense

    def list_expenses(self) -> list[Expense]:
        return self._expenses.copy()
