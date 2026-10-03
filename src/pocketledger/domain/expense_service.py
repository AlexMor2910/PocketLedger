from datetime import date
from decimal import Decimal

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import ExpenseRepository


class ExpenseService:
    def __init__(self, repository: ExpenseRepository) -> None:
        self._repository = repository

    def add_expense(
        self, description: str, amount: Decimal, category: str, date: date
    ) -> Expense:
        expense = Expense(
            description=description, amount=amount, category=category, date=date
        )
        self._repository.add(expense)
        return expense

    def list_expenses(self) -> list[Expense]:
        return self._repository.list_expenses()
