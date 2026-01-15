"""
MarketContext Inspector Dialog - Zeigt MarketContext als JSON/Tree an.

Ermöglicht:
- Anzeige des vollständigen MarketContext
- Export als JSON
- Copy to Clipboard
- Refresh

Phase 1.5 der Bot-Integration.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QTabWidget,
    QWidget,
    QGroupBox,
    QFormLayout,
    QApplication,
    QFileDialog,
    QMessageBox,
    QTreeWidget,
    QTreeWidgetItem,
    QSplitter,
)

if TYPE_CHECKING:
    from src.core.trading_bot.market_context import MarketContext

logger = logging.getLogger(__name__)


class MarketContextInspector(QDialog):
    """
    Dialog zum Inspizieren des MarketContext.

    Zeigt:
    - Summary Tab mit Key-Infos
    - JSON Tab mit vollständigem JSON
    - Tree Tab mit hierarchischer Ansicht

    Usage:
        dialog = MarketContextInspector(context, parent=self)
        dialog.exec()

        # Oder mit Refresh-Callback:
        dialog = MarketContextInspector(
            context,
            refresh_callback=lambda: get_latest_context(),
            parent=self
        )
    """

    refresh_requested = pyqtSignal()

    def __init__(
        self,
        context: "MarketContext | None" = None,
        refresh_callback: callable | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._context = context
        self._refresh_callback = refresh_callback

        self._setup_ui()

        if context:
            self._update_display(context)

    def _setup_ui(self) -> None:
        """Initialisiert das UI."""
        self.setWindowTitle("MarketContext Inspector")
        self.setMinimumSize(700, 600)
        self.resize(800, 700)

        layout = QVBoxLayout(self)

        # Header mit Symbol/TF Info
        self._header_label = QLabel("No Context Loaded")
        self._header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self._header_label)

        # Tab Widget
        self._tabs = QTabWidget()
        layout.addWidget(self._tabs)

        # Summary Tab
        self._summary_tab = self._create_summary_tab()
        self._tabs.addTab(self._summary_tab, "Summary")

        # JSON Tab
        self._json_tab = self._create_json_tab()
        self._tabs.addTab(self._json_tab, "JSON")

        # Tree Tab
        self._tree_tab = self._create_tree_tab()
        self._tabs.addTab(self._tree_tab, "Tree View")

        # AI Prompt Tab
        self._prompt_tab = self._create_prompt_tab()
        self._tabs.addTab(self._prompt_tab, "AI Prompt Context")

        # Button Row
        button_layout = QHBoxLayout()

        self._refresh_btn = QPushButton("Refresh")
        self._refresh_btn.clicked.connect(self._on_refresh)
        button_layout.addWidget(self._refresh_btn)

        self._copy_btn = QPushButton("Copy JSON")
        self._copy_btn.clicked.connect(self._on_copy)
        button_layout.addWidget(self._copy_btn)

        self._export_btn = QPushButton("Export...")
        self._export_btn.clicked.connect(self._on_export)
        button_layout.addWidget(self._export_btn)

        button_layout.addStretch()

        self._close_btn = QPushButton("Close")
        self._close_btn.clicked.connect(self.close)
        button_layout.addWidget(self._close_btn)

        layout.addLayout(button_layout)

    def _create_summary_tab(self) -> QWidget:
        """Erstellt Summary Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Regime Group
        regime_group = QGroupBox("Regime & Trend")
        regime_layout = QFormLayout(regime_group)

        self._regime_label = QLabel("-")
        self._regime_confidence_label = QLabel("-")
        self._regime_reason_label = QLabel("-")
        self._regime_reason_label.setWordWrap(True)

        regime_layout.addRow("Regime:", self._regime_label)
        regime_layout.addRow("Confidence:", self._regime_confidence_label)
        regime_layout.addRow("Reason:", self._regime_reason_label)

        layout.addWidget(regime_group)

        # MTF Trends Group
        trends_group = QGroupBox("Multi-Timeframe Trends")
        trends_layout = QFormLayout(trends_group)

        self._trend_1d_label = QLabel("-")
        self._trend_4h_label = QLabel("-")
        self._trend_1h_label = QLabel("-")
        self._trend_5m_label = QLabel("-")
        self._mtf_alignment_label = QLabel("-")

        trends_layout.addRow("1D:", self._trend_1d_label)
        trends_layout.addRow("4H:", self._trend_4h_label)
        trends_layout.addRow("1H:", self._trend_1h_label)
        trends_layout.addRow("5M:", self._trend_5m_label)
        trends_layout.addRow("Alignment:", self._mtf_alignment_label)

        layout.addWidget(trends_group)

        # Levels Group
        levels_group = QGroupBox("Support/Resistance")
        levels_layout = QFormLayout(levels_group)

        self._support_label = QLabel("-")
        self._resistance_label = QLabel("-")
        self._dist_support_label = QLabel("-")
        self._dist_resistance_label = QLabel("-")

        levels_layout.addRow("Nearest Support:", self._support_label)
        levels_layout.addRow("Distance:", self._dist_support_label)
        levels_layout.addRow("Nearest Resistance:", self._resistance_label)
        levels_layout.addRow("Distance:", self._dist_resistance_label)

        layout.addWidget(levels_group)

        # Price & Volatility Group
        price_group = QGroupBox("Price & Volatility")
        price_layout = QFormLayout(price_group)

        self._price_label = QLabel("-")
        self._atr_label = QLabel("-")
        self._volatility_label = QLabel("-")

        price_layout.addRow("Current Price:", self._price_label)
        price_layout.addRow("ATR %:", self._atr_label)
        price_layout.addRow("Volatility State:", self._volatility_label)

        layout.addWidget(price_group)

        # Data Quality Group
        quality_group = QGroupBox("Data Quality")
        quality_layout = QFormLayout(quality_group)

        self._freshness_label = QLabel("-")
        self._issues_label = QLabel("-")
        self._issues_label.setWordWrap(True)

        quality_layout.addRow("Freshness:", self._freshness_label)
        quality_layout.addRow("Issues:", self._issues_label)

        layout.addWidget(quality_group)

        layout.addStretch()

        return widget

    def _create_json_tab(self) -> QWidget:
        """Erstellt JSON Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._json_edit = QTextEdit()
        self._json_edit.setReadOnly(True)
        self._json_edit.setFont(QFont("Consolas", 10))
        self._json_edit.setLineWrapMode(QTextEdit.LineWrapMode.NoWrap)

        layout.addWidget(self._json_edit)

        return widget

    def _create_tree_tab(self) -> QWidget:
        """Erstellt Tree View Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        self._tree_widget = QTreeWidget()
        self._tree_widget.setHeaderLabels(["Key", "Value", "Type"])
        self._tree_widget.setColumnWidth(0, 200)
        self._tree_widget.setColumnWidth(1, 300)

        layout.addWidget(self._tree_widget)

        return widget

    def _create_prompt_tab(self) -> QWidget:
        """Erstellt AI Prompt Context Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        info_label = QLabel(
            "This is the compact context that would be sent to an AI model.\n"
            "It contains only the essential information for analysis."
        )
        info_label.setStyleSheet("color: gray;")
        layout.addWidget(info_label)

        self._prompt_edit = QTextEdit()
        self._prompt_edit.setReadOnly(True)
        self._prompt_edit.setFont(QFont("Consolas", 10))

        layout.addWidget(self._prompt_edit)

        return widget

    def set_context(self, context: "MarketContext") -> None:
        """Setzt neuen Context und aktualisiert Anzeige."""
        self._context = context
        self._update_display(context)

    def _update_display(self, context: "MarketContext") -> None:
        """Aktualisiert alle Tabs mit Context-Daten."""
        # Header
        self._header_label.setText(
            f"{context.symbol} / {context.timeframe} - "
            f"Context ID: {context.context_id[:12]}..."
        )

        # Summary Tab
        self._update_summary(context)

        # JSON Tab
        json_str = context.to_json(indent=2)
        self._json_edit.setPlainText(json_str)

        # Tree Tab
        self._update_tree(context.to_dict())

        # Prompt Tab
        prompt_context = context.to_ai_prompt_context()
        prompt_str = json.dumps(prompt_context, indent=2, ensure_ascii=False)
        self._prompt_edit.setPlainText(prompt_str)

    def _update_summary(self, context: "MarketContext") -> None:
        """Aktualisiert Summary Tab."""
        # Regime
        regime_value = context.regime.value if hasattr(context.regime, "value") else str(context.regime)
        self._regime_label.setText(regime_value)
        self._regime_label.setStyleSheet(self._get_regime_style(regime_value))

        self._regime_confidence_label.setText(f"{context.regime_confidence:.0%}")
        self._regime_reason_label.setText(context.regime_reason or "-")

        # Trends
        def format_trend(trend) -> str:
            if trend is None:
                return "-"
            return trend.value if hasattr(trend, "value") else str(trend)

        def trend_style(trend) -> str:
            if trend is None:
                return ""
            val = trend.value if hasattr(trend, "value") else str(trend)
            if "BULLISH" in val:
                return "color: green; font-weight: bold;"
            elif "BEARISH" in val:
                return "color: red; font-weight: bold;"
            return ""

        self._trend_1d_label.setText(format_trend(context.trend_1d))
        self._trend_1d_label.setStyleSheet(trend_style(context.trend_1d))

        self._trend_4h_label.setText(format_trend(context.trend_4h))
        self._trend_4h_label.setStyleSheet(trend_style(context.trend_4h))

        self._trend_1h_label.setText(format_trend(context.trend_1h))
        self._trend_1h_label.setStyleSheet(trend_style(context.trend_1h))

        self._trend_5m_label.setText(format_trend(context.trend_5m))
        self._trend_5m_label.setStyleSheet(trend_style(context.trend_5m))

        alignment_text = f"{context.mtf_alignment_score:+.2f}"
        if context.mtf_aligned:
            alignment_text += " (ALIGNED)"
        self._mtf_alignment_label.setText(alignment_text)

        # Levels
        if context.nearest_support:
            self._support_label.setText(f"${context.nearest_support:,.2f}")
        else:
            self._support_label.setText("-")

        if context.nearest_resistance:
            self._resistance_label.setText(f"${context.nearest_resistance:,.2f}")
        else:
            self._resistance_label.setText("-")

        if context.distance_to_support_pct:
            self._dist_support_label.setText(f"{context.distance_to_support_pct:.2f}%")
        else:
            self._dist_support_label.setText("-")

        if context.distance_to_resistance_pct:
            self._dist_resistance_label.setText(f"{context.distance_to_resistance_pct:.2f}%")
        else:
            self._dist_resistance_label.setText("-")

        # Price & Volatility
        self._price_label.setText(f"${context.current_price:,.2f}")
        self._atr_label.setText(f"{context.atr_pct:.2f}%")
        self._volatility_label.setText(context.volatility_state)
        self._volatility_label.setStyleSheet(self._get_volatility_style(context.volatility_state))

        # Data Quality
        if context.data_fresh:
            freshness_text = f"Fresh ({context.data_freshness_seconds}s old)"
            freshness_style = "color: green;"
        else:
            freshness_text = f"Stale ({context.data_freshness_seconds}s old)"
            freshness_style = "color: red;"

        self._freshness_label.setText(freshness_text)
        self._freshness_label.setStyleSheet(freshness_style)

        if context.data_quality_issues:
            self._issues_label.setText("\n".join(context.data_quality_issues[:3]))
            self._issues_label.setStyleSheet("color: orange;")
        else:
            self._issues_label.setText("None")
            self._issues_label.setStyleSheet("color: green;")

    def _update_tree(self, data: dict, parent: QTreeWidgetItem | None = None) -> None:
        """Aktualisiert Tree Widget rekursiv."""
        if parent is None:
            self._tree_widget.clear()

        for key, value in data.items():
            if parent is None:
                item = QTreeWidgetItem(self._tree_widget)
            else:
                item = QTreeWidgetItem(parent)

            item.setText(0, str(key))

            if isinstance(value, dict):
                item.setText(1, "{...}")
                item.setText(2, "dict")
                self._update_tree(value, item)
            elif isinstance(value, list):
                item.setText(1, f"[{len(value)} items]")
                item.setText(2, "list")
                for i, v in enumerate(value[:10]):  # Limit to 10 items
                    if isinstance(v, dict):
                        child = QTreeWidgetItem(item)
                        child.setText(0, f"[{i}]")
                        child.setText(1, "{...}")
                        child.setText(2, "dict")
                        self._update_tree(v, child)
                    else:
                        child = QTreeWidgetItem(item)
                        child.setText(0, f"[{i}]")
                        child.setText(1, str(v)[:100])
                        child.setText(2, type(v).__name__)
            else:
                item.setText(1, str(value)[:200] if value is not None else "null")
                item.setText(2, type(value).__name__ if value is not None else "null")

    def _get_regime_style(self, regime: str) -> str:
        """Gibt Style für Regime zurück."""
        if "BULL" in regime:
            return "color: green; font-weight: bold;"
        elif "BEAR" in regime:
            return "color: red; font-weight: bold;"
        elif "CHOP" in regime or "RANGE" in regime:
            return "color: orange; font-weight: bold;"
        elif "EXPLOSIVE" in regime:
            return "color: purple; font-weight: bold;"
        return ""

    def _get_volatility_style(self, state: str) -> str:
        """Gibt Style für Volatility State zurück."""
        if state == "EXTREME":
            return "color: red; font-weight: bold;"
        elif state == "HIGH":
            return "color: orange;"
        elif state == "LOW":
            return "color: blue;"
        return ""

    def _on_refresh(self) -> None:
        """Handler für Refresh Button."""
        if self._refresh_callback:
            try:
                new_context = self._refresh_callback()
                if new_context:
                    self.set_context(new_context)
                    logger.debug("MarketContext refreshed")
            except Exception as e:
                logger.error(f"Failed to refresh context: {e}")
                QMessageBox.warning(self, "Refresh Failed", str(e))

        self.refresh_requested.emit()

    def _on_copy(self) -> None:
        """Kopiert JSON in Clipboard."""
        if self._context:
            json_str = self._context.to_json(indent=2)
            clipboard = QApplication.clipboard()
            clipboard.setText(json_str)
            logger.debug("MarketContext JSON copied to clipboard")

    def _on_export(self) -> None:
        """Exportiert Context als JSON-Datei."""
        if not self._context:
            return

        default_name = f"market_context_{self._context.symbol}_{self._context.timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath, _ = QFileDialog.getSaveFileName(
            self,
            "Export MarketContext",
            default_name,
            "JSON Files (*.json);;All Files (*)",
        )

        if filepath:
            try:
                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(self._context.to_json(indent=2))
                logger.info(f"MarketContext exported to {filepath}")
                QMessageBox.information(
                    self, "Export Successful", f"Context exported to:\n{filepath}"
                )
            except Exception as e:
                logger.error(f"Failed to export context: {e}")
                QMessageBox.critical(self, "Export Failed", str(e))


def show_context_inspector(
    context: "MarketContext",
    refresh_callback: callable | None = None,
    parent: QWidget | None = None,
) -> MarketContextInspector:
    """
    Convenience-Funktion zum Anzeigen des Inspectors.

    Usage:
        dialog = show_context_inspector(context, parent=self)
    """
    dialog = MarketContextInspector(context, refresh_callback, parent)
    dialog.show()
    return dialog
