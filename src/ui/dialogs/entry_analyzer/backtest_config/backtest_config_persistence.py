"""Backtest Config Persistence - JSON I/O and table operations.

Extracted from entry_analyzer_backtest_config.py (lines 228-639)
Handles config file loading/saving and table data management.

Components:
- Config file resolution and loading
- Table population from JSON
- Table editing and dirty tracking
- Config building from table data
- Save operations (save and save-as)

Date: 2026-01-31 (Task 3.2.1 - Patch 2)
LOC: ~420
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QMessageBox,
    QTableWidgetItem,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestConfigPersistenceMixin:
    """Config file I/O and table data management.

    Provides:
    - Config file resolution and loading
    - Table population with v2 regime config data
    - Cell editing and dirty flag tracking
    - Config extraction from table
    - Save and save-as operations

    Attributes (defined in parent class):
        _regime_config: dict | None - Loaded regime config
        _regime_config_path: Path | None - Current config path
        _regime_config_dirty: bool - Unsaved changes flag
        _regime_config_table: QTableWidget - Config table (52 columns)
        _regime_config_path_label: QLabel - Path display
        _regime_config_save_btn: QPushButton - Save button
        _regime_config_save_as_btn: QPushButton - Save as button
        _symbol: str - Trading symbol
        _timeframe: str - Chart timeframe
    """

    # ==================== Config File Operations ====================

    def _default_regime_config_path(self) -> Path:
        """Default JSON config path for Entry Analyzer regime detection."""
        return Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")

    def _resolve_readable_regime_config(self) -> Path:
        """Find a readable regime config within the repo; no copies into 03_JSON."""

        rel = self._default_regime_config_path()  # 03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json
        repo_root = Path(__file__).resolve().parents[4]
        template = repo_root / "03_JSON/Entry_Analyzer/Regime/JSON Template/v2_schema_reference.json"
        candidates = [rel, repo_root / rel, template]

        for p in candidates:
            try:
                if p.exists():
                    # Quick readability probe
                    with p.open("r", encoding="utf-8") as f:
                        _ = f.read(1)
                    return p
            except OSError as exc:
                logger.warning("Cannot open regime config %s: %s", p, exc)
                continue

        # Last resort: create a temporary minimal config (outside 03_JSON)
        import tempfile

        tmp = Path(tempfile.gettempdir()) / "entry_analyzer_regime_tmp.json"
        try:
            tmp.write_text(
                '{"schema_version":"2.0.0","indicators":[],"regimes":[],"strategies":[]}',
                encoding="utf-8",
            )
            logger.info("Using temporary minimal regime config at %s", tmp)
        except OSError as exc:
            logger.error("Failed to create temporary regime config: %s", exc)
        return tmp

    def _load_default_regime_config(self) -> None:
        """Load the default regime config from the Entry Analyzer directory."""
        resolved_path = self._resolve_readable_regime_config()
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._load_regime_config(resolved_path, show_error=False)
            return
        except OSError as exc:
            logger.error("Cannot open resolved regime config %s: %s", resolved_path, exc)

        # If still failing, show path in orange
        self._regime_config_path_label.setText(str(resolved_path))
        self._regime_config_path_label.setStyleSheet("color: #f59e0b;")

    def _on_load_regime_config_clicked(self) -> None:
        """Load regime config from JSON file and populate table."""
        base_dir = Path("03_JSON/Entry_Analyzer/Regime")
        base_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Load Regime Config", str(base_dir), "JSON Files (*.json)"
        )
        if not file_path:
            return

        self._load_regime_config(Path(file_path))

    def _load_regime_config(self, config_path: Path, show_error: bool = True) -> None:
        """Load regime config and update UI state.

        Supports both v1.0 (Trading Bot format) and v2.0 (Entry Analyzer format).
        """
        from src.core.tradingbot.config.regime_loader_v2 import (
            RegimeConfigLoaderV2,
            RegimeConfigLoadError,
        )

        loader = RegimeConfigLoaderV2()
        try:
            config = loader.load_config(config_path)
        except RegimeConfigLoadError as e:
            logger.error(f"Failed to load regime config: {e}")
            if show_error:
                QMessageBox.critical(
                    self, "Regime Config Error", f"Failed to load regime config:\n\n{e}"
                )
            return

        self._regime_config = config
        self._regime_config_path = config_path

        # Build path display with optimization score if available
        path_text = str(config_path)
        if "optimization_results" in config and config["optimization_results"]:
            applied = [r for r in config["optimization_results"] if r.get('applied', False)]
            result = applied[-1] if applied else config["optimization_results"][0]
            score = result.get('score', 0)
            path_text = f"{config_path.name}  |  Score: {score:.1f}"

        self._regime_config_path_label.setText(path_text)
        self._regime_config_path_label.setStyleSheet("color: #10b981;")
        self._populate_regime_config_table(config)

    # ==================== Table Population ====================

    def _populate_regime_config_table(self, config: dict) -> None:
        """Populate the regime config table with indicators and regimes.

        Uses wide 52-column format: Type, ID, then [P1 Name, P1 Val, P1 Min, P1 Max, P1 Step] x 10.
        Each parameter/threshold gets 5 columns for editing.
        """
        # Block signals while populating to avoid triggering dirty flag
        self._regime_config_table.blockSignals(True)
        self._regime_config_table.setSortingEnabled(False)
        self._regime_config_table.setRowCount(0)

        # Get applied result from optimization_results (v2.0 format)
        indicators = []
        regimes = []

        if "optimization_results" in config and config["optimization_results"]:
            applied = [r for r in config["optimization_results"] if r.get('applied', False)]
            result = applied[-1] if applied else config["optimization_results"][0]
            indicators = result.get('indicators', [])
            regimes = result.get('regimes', [])

        def create_item(text: str, editable: bool = False, center: bool = False) -> QTableWidgetItem:
            """Create a table item with optional editability."""
            item = QTableWidgetItem(str(text) if text is not None else "")
            if center:
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not editable:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            return item

        # Populate indicators
        for indicator in indicators:
            row = self._regime_config_table.rowCount()
            self._regime_config_table.insertRow(row)

            # Column 0: Type (read-only)
            self._regime_config_table.setItem(row, 0, create_item("Indicator", center=True))

            # Column 1: ID (read-only)
            indicator_name = indicator.get('name', '?')
            self._regime_config_table.setItem(row, 1, create_item(indicator_name))

            # Populate up to 10 parameters (columns 2-51)
            params = indicator.get('params', [])
            for i, param in enumerate(params[:10]):
                base_col = 2 + (i * 5)  # P1 starts at col 2, P2 at col 7, etc.

                param_name = param.get('name', '')
                param_value = param.get('value', '')
                param_range = param.get('range', {})
                range_min = param_range.get('min', '')
                range_max = param_range.get('max', '')
                range_step = param_range.get('step', '')

                # P Name (read-only)
                self._regime_config_table.setItem(row, base_col, create_item(param_name))
                # P Val (editable)
                self._regime_config_table.setItem(row, base_col + 1, create_item(param_value, editable=True, center=True))
                # P Min (editable)
                self._regime_config_table.setItem(row, base_col + 2, create_item(range_min, editable=True, center=True))
                # P Max (editable)
                self._regime_config_table.setItem(row, base_col + 3, create_item(range_max, editable=True, center=True))
                # P Step (editable)
                self._regime_config_table.setItem(row, base_col + 4, create_item(range_step, editable=True, center=True))

        # Populate regimes
        for regime in regimes:
            row = self._regime_config_table.rowCount()
            self._regime_config_table.insertRow(row)

            # Column 0: Type (read-only)
            self._regime_config_table.setItem(row, 0, create_item("Regime", center=True))

            # Column 1: ID (read-only, color-coded)
            regime_id = regime.get('id', '?')
            id_item = create_item(regime_id)
            if "BULL" in regime_id.upper():
                id_item.setForeground(Qt.GlobalColor.darkGreen)
            elif "BEAR" in regime_id.upper():
                id_item.setForeground(Qt.GlobalColor.darkRed)
            elif "SIDEWAYS" in regime_id.upper() or "CHOP" in regime_id.upper():
                id_item.setForeground(Qt.GlobalColor.darkYellow)
            self._regime_config_table.setItem(row, 1, id_item)

            # Populate thresholds as parameters (columns 2-51)
            thresholds = regime.get('thresholds', [])
            for i, thresh in enumerate(thresholds[:10]):
                base_col = 2 + (i * 5)

                thresh_name = thresh.get('name', '')
                thresh_value = thresh.get('value', '')
                thresh_range = thresh.get('range', {})
                range_min = thresh_range.get('min', '')
                range_max = thresh_range.get('max', '')
                range_step = thresh_range.get('step', '')

                # P Name (read-only - threshold name)
                self._regime_config_table.setItem(row, base_col, create_item(thresh_name))
                # P Val (editable)
                self._regime_config_table.setItem(row, base_col + 1, create_item(thresh_value, editable=True, center=True))
                # P Min (editable)
                self._regime_config_table.setItem(row, base_col + 2, create_item(range_min, editable=True, center=True))
                # P Max (editable)
                self._regime_config_table.setItem(row, base_col + 3, create_item(range_max, editable=True, center=True))
                # P Step (editable)
                self._regime_config_table.setItem(row, base_col + 4, create_item(range_step, editable=True, center=True))

        # Re-enable sorting and signals
        self._regime_config_table.setSortingEnabled(True)
        self._regime_config_table.resizeColumnsToContents()
        self._regime_config_table.blockSignals(False)

        # Enable save buttons now that config is loaded
        self._regime_config_save_btn.setEnabled(True)
        self._regime_config_save_as_btn.setEnabled(True)
        self._regime_config_dirty = False

    # ==================== Table Edit Handlers ====================

    def _on_regime_config_cell_changed(self, row: int, col: int) -> None:
        """Handle cell edit in regime config table - mark as dirty."""
        # Only editable columns are Val, Min, Max, Step (columns 3,4,5,6 then 8,9,10,11 etc.)
        if col >= 2:
            col_in_group = (col - 2) % 5
            if col_in_group in (1, 2, 3, 4):  # Val, Min, Max, Step
                self._regime_config_dirty = True
                # Update path label to show unsaved changes
                if hasattr(self, '_regime_config_path') and self._regime_config_path:
                    current_text = self._regime_config_path_label.text()
                    if not current_text.endswith("*"):
                        self._regime_config_path_label.setText(current_text + " *")
                        self._regime_config_path_label.setStyleSheet("color: #f59e0b;")  # Orange for unsaved

    def _build_config_from_table(self) -> dict:
        """Build regime config dict from current table values.

        Returns:
            Updated config dict with values from table.
        """
        if not self._regime_config:
            return {}

        # Deep copy original config
        import copy
        config = copy.deepcopy(self._regime_config)

        # Get optimization_results reference
        if "optimization_results" not in config or not config["optimization_results"]:
            return config

        applied = [r for r in config["optimization_results"] if r.get('applied', False)]
        result = applied[-1] if applied else config["optimization_results"][0]

        indicators = result.get('indicators', [])
        regimes = result.get('regimes', [])

        # Map rows to indicators/regimes
        ind_idx = 0
        reg_idx = 0

        for row in range(self._regime_config_table.rowCount()):
            type_item = self._regime_config_table.item(row, 0)
            if not type_item:
                continue

            row_type = type_item.text()

            if row_type == "Indicator" and ind_idx < len(indicators):
                params = indicators[ind_idx].get('params', [])
                for i, param in enumerate(params[:10]):
                    base_col = 2 + (i * 5)
                    # Read Val, Min, Max, Step from table
                    val_item = self._regime_config_table.item(row, base_col + 1)
                    min_item = self._regime_config_table.item(row, base_col + 2)
                    max_item = self._regime_config_table.item(row, base_col + 3)
                    step_item = self._regime_config_table.item(row, base_col + 4)

                    if val_item and val_item.text():
                        param['value'] = self._parse_number(val_item.text())
                    if min_item and min_item.text():
                        if 'range' not in param:
                            param['range'] = {}
                        param['range']['min'] = self._parse_number(min_item.text())
                    if max_item and max_item.text():
                        if 'range' not in param:
                            param['range'] = {}
                        param['range']['max'] = self._parse_number(max_item.text())
                    if step_item and step_item.text():
                        if 'range' not in param:
                            param['range'] = {}
                        param['range']['step'] = self._parse_number(step_item.text())

                ind_idx += 1

            elif row_type == "Regime" and reg_idx < len(regimes):
                thresholds = regimes[reg_idx].get('thresholds', [])
                for i, thresh in enumerate(thresholds[:10]):
                    base_col = 2 + (i * 5)
                    val_item = self._regime_config_table.item(row, base_col + 1)
                    min_item = self._regime_config_table.item(row, base_col + 2)
                    max_item = self._regime_config_table.item(row, base_col + 3)
                    step_item = self._regime_config_table.item(row, base_col + 4)

                    if val_item and val_item.text():
                        thresh['value'] = self._parse_number(val_item.text())
                    if min_item and min_item.text():
                        if 'range' not in thresh:
                            thresh['range'] = {}
                        thresh['range']['min'] = self._parse_number(min_item.text())
                    if max_item and max_item.text():
                        if 'range' not in thresh:
                            thresh['range'] = {}
                        thresh['range']['max'] = self._parse_number(max_item.text())
                    if step_item and step_item.text():
                        if 'range' not in thresh:
                            thresh['range'] = {}
                        thresh['range']['step'] = self._parse_number(step_item.text())

                reg_idx += 1

        return config

    def _parse_number(self, text: str) -> int | float:
        """Parse string to int or float."""
        try:
            if '.' in text:
                return float(text)
            return int(text)
        except ValueError:
            return 0

    # ==================== Save Operations ====================

    def _on_save_regime_config(self) -> None:
        """Save changes to current regime config file."""
        if not self._regime_config_path:
            self._on_save_regime_config_as()
            return

        try:
            config = self._build_config_from_table()
            with open(self._regime_config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

            self._regime_config = config
            self._regime_config_dirty = False

            # Update path label
            path_text = str(self._regime_config_path.name)
            if "optimization_results" in config and config["optimization_results"]:
                applied = [r for r in config["optimization_results"] if r.get('applied', False)]
                result = applied[-1] if applied else config["optimization_results"][0]
                score = result.get('score', 0)
                path_text = f"{self._regime_config_path.name}  |  Score: {score:.1f}"

            self._regime_config_path_label.setText(path_text)
            self._regime_config_path_label.setStyleSheet("color: #10b981;")

            logger.info(f"Regime config saved to {self._regime_config_path}")

        except Exception as e:
            logger.error(f"Failed to save regime config: {e}")
            QMessageBox.critical(self, "Save Error", f"Failed to save config:\n\n{e}")

    def _on_save_regime_config_as(self) -> None:
        """Save regime config to a new file."""
        base_dir = Path("03_JSON/Entry_Analyzer/Regime")
        base_dir.mkdir(parents=True, exist_ok=True)

        # Suggest filename
        from datetime import datetime
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        symbol = getattr(self, '_symbol', 'UNKNOWN').replace('/', '')
        timeframe = getattr(self, '_timeframe', '5m')
        suggested = f"{timestamp}_regime_config_{symbol}_{timeframe}.json"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save Regime Config As", str(base_dir / suggested), "JSON Files (*.json)"
        )
        if not file_path:
            return

        self._regime_config_path = Path(file_path)
        self._on_save_regime_config()

    def _check_unsaved_changes(self) -> bool:
        """Check for unsaved changes and prompt user.

        Returns:
            True if OK to proceed, False if cancelled.
        """
        if not self._regime_config_dirty:
            return True

        reply = QMessageBox.question(
            self,
            "Unsaved Changes",
            "The regime config has unsaved changes.\n\n"
            "Do you want to save before continuing?",
            QMessageBox.StandardButton.Save |
            QMessageBox.StandardButton.Discard |
            QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Save
        )

        if reply == QMessageBox.StandardButton.Save:
            self._on_save_regime_config()
            return True
        elif reply == QMessageBox.StandardButton.Discard:
            return True
        else:  # Cancel
            return False
