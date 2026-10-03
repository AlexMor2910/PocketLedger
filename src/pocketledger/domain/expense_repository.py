from typing import Protocol
from uuid import UUID

from pocketledger.domain.expense import Expense


class DuplicateExpenseError(Exception):
    """An expense with this identifier is already stored."""


class ExpenseNotFoundError(Exception):
    """No stored expense has the requested identifier."""


class ExpenseRepository(Protocol):
    def add(self, expense: Expense) -> None:
        """Store an expense, raising DuplicateExpenseError for an existing ID."""
        ...

    def list_expenses(self) -> list[Expense]:
        """Return a fresh list of expenses in insertion order."""
        ...

    def delete(self, expense_id: UUID) -> None:
        """Delete by UUID; raise ExpenseNotFoundError without changes if absent."""
        ...
