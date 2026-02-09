from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def pytest_configure() -> None:
    """Configure environment for headless, CI-friendly test runs."""
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

    mpl_config = Path(os.environ.get("MPLCONFIGDIR", "/tmp/matplotlib"))
    mpl_config.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLCONFIGDIR", str(mpl_config))


def pytest_ignore_collect(collection_path: Path, config: Any) -> bool:
    """Skip UI tests by default unless RUN_UI_TESTS=1 is set."""
    run_ui = os.environ.get("RUN_UI_TESTS") == "1"
    if run_ui:
        return False
    return "tests/ui" in str(collection_path)
