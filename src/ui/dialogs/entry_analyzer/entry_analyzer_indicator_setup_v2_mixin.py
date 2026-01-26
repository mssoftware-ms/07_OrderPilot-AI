"""Entry Analyzer - Indicator Setup V2 Mixin (Rebuilt for Indicator Sets).

Handles Indicator Setup for Stage 2 (Indicators only, ohne Regime):
- JSON-Import einer reinen Indikatorliste (v2 Schema angelehnt an Regime-Template)
- Signal-Typ Auswahl (Entry/Exit Long/Short) – alle vorgewählt
- Dynamische Parameter-Range-Tabelle (bis 10 Parameter/Indikator, Name/Value/Min/Max/Step)
- Keine Regime-Auswahl, keine alten Checkbox-Listen
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
    QFileDialog,
    QMessageBox,
)

from src.core.tradingbot.config.validator import SchemaValidator, ValidationError
from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class IndicatorSetupV2Mixin:
    """Stage 2: Indicator Setup UI (neu, ohne Regime)."""

    # Attributes injected by parent
    _ind_v2_signal_types: dict[str, QCheckBox]
    _ind_v2_params_table: QTableWidget
    _ind_v2_indicator_config: dict | None
    _ind_v2_indicator_config_path: Path | None

    def _setup_indicator_setup_v2_tab(self, tab: QWidget) -> None:
        """Setup Indicator Setup V2 tab (Indicators only)."""
        layout = QVBoxLayout(tab)

        header = QLabel("Indicator Setup (Long/Short Entry & Exit)")
        header.setStyleSheet("font-size: 14pt; font-weight: bold;")
        layout.addWidget(header)

        desc = QLabel(
            "Lade eine Indikator-JSON (v2) mit einer reinen Indikatorliste. "
            "Lege für jeden Parameter Min/Max/Step fest (bis zu 10 Parameter/Indikator). "
            "Signal-Typen sind standardmäßig aktiv."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; padding: 4px;")
        layout.addWidget(desc)

        # ===== Signal Type Selection Group =====
        signal_group = QGroupBox("Signal Types to Optimize")
        signal_layout = QHBoxLayout(signal_group)

        self._ind_v2_signal_types = {
            "entry_long": QCheckBox("Entry Long"),
            "entry_short": QCheckBox("Entry Short"),
            "exit_long": QCheckBox("Exit Long"),
            "exit_short": QCheckBox("Exit Short"),
        }
        for cb in self._ind_v2_signal_types.values():
            cb.setChecked(True)  # Vorgabe: alle aktiv
            signal_layout.addWidget(cb)
        signal_layout.addStretch()
        layout.addWidget(signal_group)

        # ===== Indicator Parameter Optimization Ranges (Regime-Style 52 Col) =====
        params_group = QGroupBox("Indicator Parameter Optimization Ranges")
        params_layout = QVBoxLayout(params_group)

        self._ind_v2_params_table = QTableWidget()
        self._ind_v2_params_table.setColumnCount(52)
        headers = ["Indicator", "Type"]
        for i in range(1, 11):
            headers.extend(
                [
                    f"Param{i} Name",
                    f"Param{i} Value",
                    f"Param{i} Min",
                    f"Param{i} Max",
                    f"Param{i} Step",
                ]
            )
        self._ind_v2_params_table.setHorizontalHeaderLabels(headers)

        header_view = self._ind_v2_params_table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        for col in range(2, 52):
            header_view.setSectionResizeMode(col, QHeaderView.ResizeMode.Interactive)
        self._ind_v2_params_table.setAlternatingRowColors(True)

        params_layout.addWidget(self._ind_v2_params_table)
        params_group.setLayout(params_layout)
        layout.addWidget(params_group, stretch=2)

        # ===== Buttons =====
        btn_layout = QHBoxLayout()

        self._ind_v2_import_btn = QPushButton(get_icon("folder_open"), "Load Indicator Config (JSON)")
        self._ind_v2_import_btn.clicked.connect(self._on_indicator_v2_import)
        btn_layout.addWidget(self._ind_v2_import_btn)

        reload_btn = QPushButton(get_icon("refresh"), "Reload")
        reload_btn.clicked.connect(self._populate_indicator_setup_table)
        btn_layout.addWidget(reload_btn)

        btn_layout.addStretch()

        self._ind_v2_apply_btn = QPushButton(get_icon("check_circle"), "Apply & Continue")
        self._ind_v2_apply_btn.setProperty("class", "success")
        self._ind_v2_apply_btn.clicked.connect(self._on_indicator_v2_apply)
        btn_layout.addWidget(self._ind_v2_apply_btn)

        layout.addLayout(btn_layout)

        # State
        self._ind_v2_indicator_config = None
        self._ind_v2_indicator_config_path = None

        layout.addStretch()

    # ------------------------------------------------------------------ UI Actions
    def _on_indicator_v2_import(self) -> None:
        """Import indicator config JSON (Indicators only)."""
        project_root = Path(__file__).parents[4]
        default_dir = project_root / "03_JSON" / "Trading_Indicatorsets"
        default_dir.mkdir(parents=True, exist_ok=True)

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Indicator Config (v2)",
            str(default_dir),
            "JSON Files (*.json);;All Files (*)",
        )
        if not file_path:
            return

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Load failed", f"Could not load JSON:\n{e}")
            logger.error("Indicator config load failed", exc_info=True)
            return

        # Validate against indicator_sets schema
        try:
            validator = SchemaValidator()
            validator.validate_data(config, schema_name="indicator_sets")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Schema validation failed",
                f"Indicator config is invalid:\n{e}",
            )
            logger.error("Indicator config schema validation failed", exc_info=True)
            return

        self._ind_v2_indicator_config = config
        self._ind_v2_indicator_config_path = Path(file_path)
        self._populate_indicator_setup_table()

    def _on_indicator_v2_apply(self) -> None:
        """Validate config and keep ranges ready for optimization."""
        if not self._ind_v2_indicator_config:
            QMessageBox.warning(
                self, "No config", "Please load an Indicator Config JSON before continuing."
            )
            return

        param_ranges = self._get_indicator_param_ranges()
        if not param_ranges:
            QMessageBox.warning(
                self,
                "No parameters",
                "No parameter ranges found. Please fill the table.",
            )
            return

        QMessageBox.information(
            self,
            "Indicator Setup",
            "Indicator parameters recorded. Continue with Optimization tab.",
        )

    # ------------------------------------------------------------------ Helpers
    def _populate_indicator_setup_table(self) -> None:
        """Populate parameter table from loaded indicator config."""
        table = self._ind_v2_params_table
        table.setRowCount(0)

        if not self._ind_v2_indicator_config:
            return

        indicators = self._ind_v2_indicator_config.get("indicators") or []
        if not indicators and "optimization_results" in self._ind_v2_indicator_config:
            # allow Regime-like v2 structure
            opt = self._ind_v2_indicator_config.get("optimization_results", [])
            if opt:
                indicators = opt[0].get("indicators", [])

        for row_idx, indicator in enumerate(indicators):
            table.insertRow(row_idx)
            name = indicator.get("name") or indicator.get("id") or indicator.get("indicator") or "UNKNOWN"
            ind_type = indicator.get("type") or indicator.get("category") or ""

            table.setItem(row_idx, 0, QTableWidgetItem(str(name)))
            table.setItem(row_idx, 1, QTableWidgetItem(str(ind_type)))

            params = indicator.get("params") or []
            # cap to 10
            params = params[:10]
            for i, param in enumerate(params, start=1):
                base_col = 2 + (i - 1) * 5
                table.setItem(row_idx, base_col, QTableWidgetItem(str(param.get("name", ""))))
                table.setItem(
                    row_idx, base_col + 1, QTableWidgetItem(str(param.get("value", "")))
                )
                rng = param.get("range", {})
                table.setItem(
                    row_idx, base_col + 2, QTableWidgetItem(str(rng.get("min", "")))
                )
                table.setItem(
                    row_idx, base_col + 3, QTableWidgetItem(str(rng.get("max", "")))
                )
                table.setItem(
                    row_idx, base_col + 4, QTableWidgetItem(str(rng.get("step", "")))
                )

    def _get_indicator_param_ranges(self) -> dict:
        """Read parameter ranges from table -> dict structure for worker."""
        ranges: dict[str, dict] = {}
        table = self._ind_v2_params_table
        rows = table.rowCount()
        for row in range(rows):
            ind_name_item = table.item(row, 0)
            if not ind_name_item:
                continue
            ind_name = ind_name_item.text().strip()
            if not ind_name:
                continue
            ranges[ind_name] = {}

            for i in range(1, 11):
                base_col = 2 + (i - 1) * 5
                name_item = table.item(row, base_col)
                if not name_item:
                    continue
                param_name = name_item.text().strip()
                if not param_name:
                    continue

                def _num(item):
                    try:
                        return float(item.text())
                    except Exception:
                        return None

                val_item = table.item(row, base_col + 1)
                min_item = table.item(row, base_col + 2)
                max_item = table.item(row, base_col + 3)
                step_item = table.item(row, base_col + 4)

                ranges[ind_name][param_name] = {
                    "value": _num(val_item) if val_item else None,
                    "min": _num(min_item) if min_item else None,
                    "max": _num(max_item) if max_item else None,
                    "step": _num(step_item) if step_item else None,
                }

        # Remove empty indicators
        ranges = {k: v for k, v in ranges.items() if v}
        return ranges
