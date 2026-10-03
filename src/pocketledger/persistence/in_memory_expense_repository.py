from uuid import UUID

from pocketledger.domain.expense import Expense
from pocketledger.domain.expense_repository import DuplicateExpenseError, ExpenseNotFoundError


class InMemoryExpenseRepository:
    def __init__(self) -> None:
        self._expenses: list[Expense] = []

    def add(self, expense: Expense) -> None:
        if any(existing.id == expense.id for existing in self._expenses):
            raise DuplicateExpenseError(f"Expense {expense.id} already exists")
        self._expenses.append(expense)

    def list_expenses(self) -> list[Expense]:
        return self._expenses.copy()

    def delete(self, expense_id: UUID) -> None:
        for index, expense in enumerate(self._expenses):
            if expense.id == expense_id:
                del self._expenses[index]
                return
        raise ExpenseNotFoundError(f"Expense {expense_id} does not exist")
