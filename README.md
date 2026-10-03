# PocketLedger

An educational personal expense-tracking project for learning Python and working
with Codex through small, reviewable software-engineering stages. The eventual
desktop application uses PySide6 and SQLite, alongside a terminal interface.

Stage 1 established the scaffold and placeholder entry point. Stage 2 adds an
immutable expense model and an in-memory service for adding and listing expenses,
with domain tests. Stage 3 adds interchangeable in-memory and SQLite repositories.
Stage 4 adds a terminal menu and wires the service to a local SQLite database.
Stage 5 adds deletion by UUID through both repository implementations.
Stage 6 adds a simple PySide6 desktop interface while preserving the CLI.

## Development environment

`environment.yml` defines the `PocketLedger` Conda environment with Python 3.12,
pytest, and PySide6. For a new environment, run from the project root:

```powershell
conda env create -f environment.yml
```

If the environment already exists, synchronize it when needed:

```powershell
conda env update -n PocketLedger -f environment.yml
```

Activate it and verify the interpreter:

```powershell
conda activate PocketLedger
python -c "import sys; print(sys.executable)"
```

The interpreter should be inside `anaconda3\envs\PocketLedger` (or your own
Conda installation's equivalent). Select the same interpreter in PyCharm.

## Run PocketLedger

From the project root in the activated PowerShell terminal:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m pocketledger
```

Set `PYTHONPATH` again in each new terminal session. This makes the `src` package
importable until packaging metadata is introduced in a later learning stage.

To launch the GUI instead, from the same activated environment and project root:

```powershell
python -m pocketledger.gui
```

If upgrading an existing environment, run the `conda env update` command above to
install PySide6 before launching the GUI or running the GUI tests. The CLI launcher
does not import PySide6. Both interfaces use the same database when launched from
the same working directory.

The GUI provides description, amount, category, and date fields plus **Add expense**.
Enter dates as `YYYY-MM-DD`; amounts use Decimal without automatic rounding.
Validation errors appear below the buttons and retain form input. Successful additions
reset the text fields, reset the date to today, and refresh the table. The read-only
table shows expenses in insertion order. Select a row and click **Delete selected
expense** to delete it by its internal UUID. No selection or an expense disappearing
produces a message. Closing the window closes the database connection.

The menu offers **1. Add expense**, **2. List expenses**, **3. Delete expense**,
and **4. Exit**. Adding asks for
description, decimal amount (e.g. `12.50`), category, and a valid date in exactly
`YYYY-MM-DD` format (e.g. `2026-10-02`). Invalid input displays an error and returns
to the menu. Listing shows date, description, category, and amount in insertion
order without rounding amounts. Future dates remain allowed. Exit, EOF, or Ctrl+C
closes the application and its database connection.

Deleting shows the current expenses as a numbered list in insertion order. Enter
the number of the expense to delete; the CLI resolves that selection to its UUID
and calls the service. UUIDs are not displayed or entered by the user. Invalid
selections or an empty list show a message and return to the menu. If the expense
has disappeared since listing, nothing is deleted and a not-found message is shown.
Successful deletion prints `Expense deleted.` and persists across application runs.

Run from the project root to use `local-data/pocketledger.sqlite`. The application
creates this directory and database on startup; expenses persist across runs.
The path is relative to the working directory, so launching elsewhere creates a
separate `local-data/` there. The project's entire `local-data/` directory is ignored
by Git. Editing expenses is outside this stage.

## Run tests

From the project root with Conda activated and `PYTHONPATH` set as above:

```powershell
python -m pytest
```

Tests use injected input/output functions rather than human input. SQLite and
application tests use temporary directories and do not write to project local data.
GUI tests use one session-scoped `QApplication`, real PySide6 widgets, and programmatic
button clicks. The `qapplication` fixture sets `QT_QPA_PLATFORM=offscreen` before
creating the application, so no visible desktop or manual clicking is required.
Normal GUI launches do not set this variable. No additional GUI testing library is needed.

## Structure

- `src/pocketledger/app.py`: creates the data directory and wires repository, service, and CLI.
- `src/pocketledger/__main__.py`: module entry point.
- `src/pocketledger/ui/cli.py`: terminal menu, input conversion, and expense display.
- `src/pocketledger/gui.py`: separate GUI launcher and SQLite wiring.
- `src/pocketledger/ui/gui.py`: standard-widget form, expense table, and feedback.
- `src/pocketledger/domain/expense.py`: immutable expense model and validation.
- `src/pocketledger/domain/expense_service.py`: add/list/delete service with an injected repository.
- `src/pocketledger/domain/expense_repository.py`: storage protocol and shared repository errors.
- `src/pocketledger/persistence/`: in-memory and SQLite repository implementations.
- `tests/`: domain, repository, CLI, GUI, application, and module entry-point tests.

Application flow: `app.py` constructs `SQLiteExpenseRepository`, injects it into
`ExpenseService`, and passes the service into `ExpenseCLI`. The CLI converts text
into Decimal and date values, then calls the service. The service creates validated
domain expenses and delegates storage to the repository. The CLI imports no SQLite,
and the domain imports neither UI nor repository implementations. The app owns the
repository lifetime through a context manager. Packaging metadata and dependency
locking are deferred to later stages.

The GUI launcher constructs the same repository and service, then passes the service
to `ExpenseWindow`: GUI -> ExpenseService -> ExpenseRepository -> SQLite implementation.
Widgets perform no SQL and create no repositories. A snapshot of displayed expenses
maps the selected row to a UUID; row numbers never reach the service or repository.
The launcher keeps the repository context open through Qt's event loop and closes it
on exit or startup failure. Domain and persistence code import no Qt or UI modules.

## Domain rules

Expenses generate their own UUIDs. Description and category must be strings;
surrounding whitespace is trimmed, blank values are rejected, and case is preserved.
Amounts must be finite, positive `decimal.Decimal` values; floats are rejected and
decimal precision is unrestricted. Dates must be `datetime.date` objects, excluding
`datetime.datetime`; future dates are allowed. Unsupported types raise `TypeError`,
and invalid values raise `ValueError`.

Expenses cannot be edited. Normal construction generates an ID; `Expense.restore(...)`
accepts an existing UUID and reuses the same validation rules.

## Repository boundary

`ExpenseService(repository)` requires an object implementing the `ExpenseRepository`
protocol: `add(expense)`, `list_expenses()`, and `delete(expense_id: UUID)`. The service validates new expenses
before storage and returns them only after a successful addition. Repositories
return fresh lists in insertion order and reject duplicate IDs with
`DuplicateExpenseError`. In-memory repositories own separate collections; services
can share a repository intentionally. The domain imports no SQLite or storage adapter.

The service's `delete_expense(expense_id)` delegates directly to the repository.
Both repositories delete by UUID, preserve remaining insertion order, and raise
`ExpenseNotFoundError` if the ID is absent, leaving stored expenses unchanged.
The numbered selection exists only in the CLI; it is never passed into storage.

`SQLiteExpenseRepository(database_path)` owns its connection and creates the
`expenses` table if needed. The caller supplies a path with an existing parent
directory. Use it as a context manager or call `close()` explicitly. Successful
additions and deletions are committed; failed operations are rolled back. UUIDs, Decimal amounts,
and dates are stored as text and restored to their domain types, retaining identity
and exact decimal precision. Invalid rows fail visibly; only duplicate-ID database
errors are translated, and other database errors propagate.

SQLite tests use pytest's `tmp_path` files outside the project, including reopening
databases to verify persistence. The repository itself still requires a caller-supplied
path; only `app.py` chooses the application's local database location. There are no
migrations or ORM dependencies.
