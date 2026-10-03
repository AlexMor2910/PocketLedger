from typing import Protocol

from pocketledger.domain.expense import Expense


class DuplicateExpenseError(Exception):
    """An expense with this identifier is already stored."""


class ExpenseRepository(Protocol):
    def add(self, expense: Expense) -> None:
        """Store an expense, raising DuplicateExpenseError for an existing ID."""
        ...

    def list_expenses(self) -> list[Expense]:
        """Return a fresh list of expenses in insertion order."""
        ...
