# PocketLedger

An educational personal expense-tracking project for learning Python and working
with Codex through small, reviewable software-engineering stages. The eventual
desktop application will use PySide6 and SQLite.

Stage 1 established the scaffold and placeholder entry point. Stage 2 adds an
immutable expense model and an in-memory service for adding and listing expenses,
with domain tests. Stage 3 adds interchangeable in-memory and SQLite repositories.
There is no UI or application database wiring; the entry point remains a placeholder.

## Development environment

`environment.yml` defines the `PocketLedger` Conda environment with Python 3.12
and pytest. For a new environment, run from the project root:

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

## Run the placeholder and tests

From the project root in the activated PowerShell terminal:

```powershell
$env:PYTHONPATH = (Resolve-Path .\src).Path
python -m pocketledger
python -m pytest
```

The app prints `PocketLedger scaffold` and exits successfully. The test launches
the module with the same Python interpreter and checks its exit code and output.
Set `PYTHONPATH` again in each new terminal session. This makes the `src` package
importable until packaging metadata is introduced in a later learning stage.

## Structure

- `src/pocketledger/app.py`: minimal startup function.
- `src/pocketledger/__main__.py`: module entry point.
- `src/pocketledger/ui/`: future PySide6 presentation code.
- `src/pocketledger/domain/expense.py`: immutable expense model and validation.
- `src/pocketledger/domain/expense_service.py`: add/list service with an injected repository.
- `src/pocketledger/domain/expense_repository.py`: storage protocol and duplicate-ID error.
- `src/pocketledger/persistence/`: in-memory and SQLite repository implementations.
- `tests/`: entry-point smoke test and domain tests.

`app.py` will coordinate the layers later. The UI package is empty.
`local-data/` is reserved and ignored by Git for future local databases and
exports; no stage so far creates it or any application data. Packaging metadata
and dependency locking are deferred to later stages.

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
protocol: `add(expense)` and `list_expenses()`. The service validates new expenses
before storage and returns them only after a successful addition. Repositories
return fresh lists in insertion order and reject duplicate IDs with
`DuplicateExpenseError`. In-memory repositories own separate collections; services
can share a repository intentionally. The domain imports no SQLite or storage adapter.

`SQLiteExpenseRepository(database_path)` owns its connection and creates the
`expenses` table if needed. The caller supplies a path with an existing parent
directory. Use it as a context manager or call `close()` explicitly. Successful
additions are committed; failed additions are rolled back. UUIDs, Decimal amounts,
and dates are stored as text and restored to their domain types, retaining identity
and exact decimal precision. Invalid rows fail visibly; only duplicate-ID database
errors are translated, and other database errors propagate.

SQLite tests use pytest's `tmp_path` files outside the project, including reopening
databases to verify persistence. The placeholder app does not create a database.
There are no migrations, ORM dependencies, or hardcoded application database paths.
