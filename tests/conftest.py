import os

import pytest


@pytest.fixture(scope="session")
def qapplication():
    # Configure Qt before creating QApplication; normal launchers never set this.
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    from PySide6.QtWidgets import QApplication

    application = QApplication.instance() or QApplication([])
    yield application
    application.processEvents()
