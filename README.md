# PocketLedger

An educational personal expense-tracking project for learning Python and working
with Codex through small, reviewable software-engineering stages. The eventual
desktop application will use PySide6 and SQLite.

Stage 1 provides only a package scaffold, a placeholder entry point, and one
pytest smoke test. It contains no UI, database, or expense-tracking functionality.

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
- `src/pocketledger/domain/`: future business logic, independent of Qt and SQLite.
- `src/pocketledger/persistence/`: future SQLite data access.
- `tests/`: smoke test.

`app.py` will coordinate the layers later. The three layer packages are empty.
`local-data/` is reserved and ignored by Git for future local databases and
exports; Stage 1 does not create it or any application data. Packaging metadata
and dependency locking are deferred to later stages.
