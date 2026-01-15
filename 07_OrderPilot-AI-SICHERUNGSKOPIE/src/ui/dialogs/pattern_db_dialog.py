"""Pattern Database Management Dialog."""

from __future__ import annotations

from PyQt6.QtWidgets import QDialog

from .pattern_db_build_mixin import PatternDbBuildMixin
from .pattern_db_docker_mixin import PatternDbDockerMixin
from .pattern_db_lifecycle_mixin import PatternDbLifecycleMixin
from .pattern_db_log_mixin import PatternDbLogMixin
from .pattern_db_search_mixin import PatternDbSearchMixin
from .pattern_db_settings_mixin import PatternDbSettingsMixin
from .pattern_db_tabs_mixin import PatternDbTabsMixin
from .pattern_db_ui_mixin import PatternDbUIMixin
from .pattern_db_worker import DatabaseBuildWorker


class PatternDatabaseDialog(
    PatternDbTabsMixin,
    PatternDbUIMixin,
    PatternDbDockerMixin,
    PatternDbBuildMixin,
    PatternDbLogMixin,
    PatternDbSearchMixin,
    PatternDbLifecycleMixin,
    PatternDbSettingsMixin,
    QDialog,
):
    """Dialog for managing the pattern database."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Pattern Database Manager")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)

        self._settings = QSettings("OrderPilot", "TradingApp")
        self._build_worker: Optional[DatabaseBuildWorker] = None
        self._pending_crypto_symbols: list[str] = []
        self._pending_timeframes: list[str] = []
        self._pending_days_back: int = 0
        self._progress_total_tasks: int = 0
        self._progress_offset: int = 0
        self._current_worker_total: int = 0
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._update_docker_status)

        self._setup_ui()
        self._load_initial_state()

        # Start status timer
        self._status_timer.start(5000)
