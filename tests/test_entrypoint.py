import subprocess
import sys


def test_interactive_entrypoint_persists_and_lists_expenses(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "pocketledger"],
        capture_output=True,
        text=True,
        timeout=10,
        cwd=tmp_path,
        input="1\nLunch\n12.345\nFood\n2024-02-29\n4\n",
    )

    assert result.returncode == 0, result.stderr
    assert "PocketLedger" in result.stdout
    assert "1. Add expense" in result.stdout
    assert "2. List expenses" in result.stdout
    assert "3. Delete expense" in result.stdout
    assert "4. Exit" in result.stdout
    assert "Expense added." in result.stdout
    assert result.stdout.rstrip().endswith("Goodbye.")
    assert (tmp_path / "local-data" / "pocketledger.sqlite").is_file()

    reopened = subprocess.run(
        [sys.executable, "-m", "pocketledger"],
        capture_output=True, text=True, timeout=10, cwd=tmp_path, input="2\n4\n",
    )
    assert reopened.returncode == 0, reopened.stderr
    assert "2024-02-29 | Lunch | Food | 12.345" in reopened.stdout
    assert reopened.stdout.rstrip().endswith("Goodbye.")
