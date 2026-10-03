import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from pocketledger.domain.expense_service import ExpenseService
from pocketledger.persistence.sqlite_expense_repository import SQLiteExpenseRepository
from pocketledger.ui.gui import ExpenseWindow


def main() -> int:
    application = QApplication.instance() or QApplication([sys.argv[0]])
    data_directory = Path.cwd() / "local-data"
    data_directory.mkdir(parents=True, exist_ok=True)
    with SQLiteExpenseRepository(data_directory / "pocketledger.sqlite") as repository:
        window = ExpenseWindow(ExpenseService(repository))
        try:
            window.show()
            return application.exec()
        finally:
            window.close()
            window.deleteLater()
            application.processEvents()


if __name__ == "__main__":
    raise SystemExit(main())
