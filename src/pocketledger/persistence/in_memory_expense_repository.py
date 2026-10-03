from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import DuplicateExpenseError


class InMemoryExpenseRepository:
    def __init__(self) -> None:
        self._expenses: list[Expense] = []

    def add(self, expense: Expense) -> None:
        if any(existing.id == expense.id for existing in self._expenses):
            raise DuplicateExpenseError(f"Expense {expense.id} already exists")
        self._expenses.append(expense)

    def list_expenses(self) -> list[Expense]:
        return self._expenses.copy()
