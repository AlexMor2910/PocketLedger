import sqlite3
from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import QTimer

from pocketledger import gui
from pocketledger.persistence.sqlite_expense_repository import SQLiteExpenseRepository


def test_gui_launcher_persists_addition_and_deletion_across_runs(tmp_path, monkeypatch, qapplication):
    monkeypatch.chdir(tmp_path)
    instances = []
    checks = []

    class DrivenWindow(gui.ExpenseWindow):
        def __init__(self, service):
            super().__init__(service)
            instances.append(self)
            QTimer.singleShot(0, self.exercise)

        def exercise(self):
            try:
                if len(instances) == 1:
                    self.description_input.setText("Lunch")
                    self.amount_input.setText("1.2300")
                    self.category_input.setText("Food")
                    self.date_input.setText("2024-02-29")
                    self.add_expense()
                    checks.append(self.table.rowCount() == 1)
                else:
                    checks.append(self.table.item(0, 3).text() == "1.2300")
                    self.table.selectRow(0)
                    self.delete_expense()
                    checks.append(self.table.rowCount() == 0)
            except Exception:
                checks.append(False)
            finally:
                self.close()

    monkeypatch.setattr(gui, "ExpenseWindow", DrivenWindow)
    assert gui.main() == 0
    path = tmp_path / "local-data" / "pocketledger.sqlite"
    with SQLiteExpenseRepository(path) as repository:
        expense, = repository.list_expenses()
        assert expense.amount.as_tuple() == Decimal("1.2300").as_tuple()
        assert expense.date == date(2024, 2, 29)
    assert gui.main() == 0
    assert all(checks) and len(checks) == 3
    with SQLiteExpenseRepository(path) as repository:
        assert repository.list_expenses() == []


@pytest.mark.parametrize("fail_construction", [False, True])
def test_gui_repository_is_closed_on_exit_or_startup_failure(tmp_path, monkeypatch, qapplication, fail_construction):
    monkeypatch.chdir(tmp_path)
    repositories = []

    class TrackingRepository(SQLiteExpenseRepository):
        def __init__(self, path):
            super().__init__(path)
            repositories.append(self)

    class ClosingWindow(gui.ExpenseWindow):
        def __init__(self, service):
            if fail_construction:
                raise RuntimeError("startup failed")
            super().__init__(service)
            QTimer.singleShot(0, self.close)

    monkeypatch.setattr(gui, "SQLiteExpenseRepository", TrackingRepository)
    monkeypatch.setattr(gui, "ExpenseWindow", ClosingWindow)
    if fail_construction:
        with pytest.raises(RuntimeError, match="startup failed"):
            gui.main()
    else:
        assert gui.main() == 0
    with pytest.raises(sqlite3.ProgrammingError):
        repositories[0].list_expenses()
