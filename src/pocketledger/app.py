from collections.abc import Callable
from pathlib import Path

from pocketledger.domain.expense_service import ExpenseService
from pocketledger.persistence.sqlite_expense_repository import SQLiteExpenseRepository
from pocketledger.ui.cli import ExpenseCLI


def main(
    *,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], None] = print,
) -> int:
    data_directory = Path.cwd() / "local-data"
    data_directory.mkdir(parents=True, exist_ok=True)
    with SQLiteExpenseRepository(data_directory / "pocketledger.sqlite") as repository:
        service = ExpenseService(repository)
        ExpenseCLI(service, input_fn=input_fn, output_fn=output_fn).run()
    return 0
