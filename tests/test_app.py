import sqlite3

import pytest

from pocketledger import app
from pocketledger.persistence.sqlite_expense_repository import SQLiteExpenseRepository


def test_application_creates_local_directory_and_persists_across_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter(["1", "Lunch", "1.2300", "Food", "2024-02-29", "4"])
    assert app.main(input_fn=lambda prompt: next(answers), output_fn=lambda line: None) == 0
    path = tmp_path / "local-data" / "pocketledger.sqlite"
    assert path.is_file()
    output = []
    answers = iter(["2", "4"])
    assert app.main(input_fn=lambda prompt: next(answers), output_fn=output.append) == 0
    assert "2024-02-29 | Lunch | Food | 1.2300" in output
    with SQLiteExpenseRepository(path) as repository:
        assert len(repository.list_expenses()) == 1


@pytest.mark.parametrize("exit_mode", ["menu", "eof", "interrupt", "unexpected"])
def test_application_closes_repository_on_all_exit_paths(tmp_path, monkeypatch, exit_mode):
    instances = []

    class TrackingRepository(SQLiteExpenseRepository):
        def __init__(self, path):
            super().__init__(path)
            instances.append(self)

    monkeypatch.setattr(app, "SQLiteExpenseRepository", TrackingRepository)
    monkeypatch.chdir(tmp_path)

    def read(prompt):
        if exit_mode == "menu":
            return "4"
        if exit_mode == "eof":
            raise EOFError
        if exit_mode == "interrupt":
            raise KeyboardInterrupt
        raise RuntimeError("unexpected failure")

    if exit_mode == "unexpected":
        with pytest.raises(RuntimeError, match="unexpected failure"):
            app.main(input_fn=read, output_fn=lambda line: None)
    else:
        assert app.main(input_fn=read, output_fn=lambda line: None) == 0
    with pytest.raises(sqlite3.ProgrammingError):
        instances[0].list_expenses()


def test_expense_added_in_one_run_can_be_deleted_in_later_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    answers = iter(["1", "Lunch", "1.2300", "Food", "2024-02-29", "4"])
    assert app.main(input_fn=lambda prompt: next(answers), output_fn=lambda line: None) == 0
    output = []
    answers = iter(["3", "1", "4"])
    assert app.main(input_fn=lambda prompt: next(answers), output_fn=output.append) == 0
    assert "Expense deleted." in output
    output = []
    answers = iter(["2", "4"])
    assert app.main(input_fn=lambda prompt: next(answers), output_fn=output.append) == 0
    assert "No expenses yet." in output
    with SQLiteExpenseRepository(tmp_path / "local-data" / "pocketledger.sqlite") as repository:
        assert repository.list_expenses() == []
