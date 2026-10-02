import subprocess
import sys


def test_placeholder_entrypoint():
    result = subprocess.run(
        [sys.executable, "-m", "pocketledger"],
        capture_output=True,
        text=True,
        timeout=10,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "PocketLedger scaffold"
