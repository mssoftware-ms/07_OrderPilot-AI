from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView, QSplitter,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BacktestTabUIResultsMixin:
    """UI creation and updates for Results tab"""

    def _create_results_tab(self) -> QWidget:
        """Erstellt Results Tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(8, 8, 8, 8)

        # --- KPI Cards ---
        kpi_layout = QHBoxLayout()

        self.kpi_pnl = self._create_kpi_card("💰 P&L", "—", "#4CAF50")
        kpi_layout.addWidget(self.kpi_pnl)

        self.kpi_winrate = self._create_kpi_card("🎯 Win Rate", "—", "#2196F3")
        kpi_layout.addWidget(self.kpi_winrate)

        self.kpi_pf = self._create_kpi_card("📊 Profit Factor", "—", "#FF9800")
        kpi_layout.addWidget(self.kpi_pf)

        self.kpi_dd = self._create_kpi_card("📉 Max DD", "—", "#f44336")
        kpi_layout.addWidget(self.kpi_dd)

        layout.addLayout(kpi_layout)

        # --- Equity Curve Chart ---
        equity_group = QGroupBox("📈 Equity Curve")
        equity_layout = QVBoxLayout(equity_group)

        try:
            from src.ui.widgets.equity_curve_widget import EquityCurveWidget
            self.equity_chart = EquityCurveWidget()
            self.equity_chart.setMinimumHeight(200)
            self.equity_chart.setMaximumHeight(300)
            equity_layout.addWidget(self.equity_chart)
        except ImportError as e:
            logger.warning(f"EquityCurveWidget not available: {e}")
            self.equity_chart = None
            placeholder = QLabel("Equity Chart nicht verfügbar")
            placeholder.setStyleSheet("color: #666;")
            equity_layout.addWidget(placeholder)

        layout.addWidget(equity_group)

        # --- Splitter für Metrics und Trades ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # --- Metrics Table ---
        metrics_widget = QWidget()
        metrics_layout_inner = QVBoxLayout(metrics_widget)
        metrics_layout_inner.setContentsMargins(0, 0, 0, 0)

        metrics_label = QLabel("📊 Detaillierte Metriken")
        metrics_label.setStyleSheet("font-weight: bold; color: #aaa;")
        metrics_layout_inner.addWidget(metrics_label)

        self.metrics_table = QTableWidget()
        self.metrics_table.setColumnCount(2)
        self.metrics_table.setHorizontalHeaderLabels(["Metrik", "Wert"])
        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.setMaximumHeight(180)
        metrics_layout_inner.addWidget(self.metrics_table)

        splitter.addWidget(metrics_widget)

        # --- Trades Table ---
        trades_widget = QWidget()
        trades_layout_inner = QVBoxLayout(trades_widget)
        trades_layout_inner.setContentsMargins(0, 0, 0, 0)

        trades_header = QHBoxLayout()
        trades_label = QLabel("📋 Trades")
        trades_label.setStyleSheet("font-weight: bold; color: #aaa;")
        trades_header.addWidget(trades_label)

        trades_header.addStretch()

        self.export_csv_btn = QPushButton("📄 Trades CSV")
        self.export_csv_btn.setMaximumWidth(80)
        self.export_csv_btn.clicked.connect(self._export_csv)
        trades_header.addWidget(self.export_csv_btn)

        self.export_equity_btn = QPushButton("📈 Equity CSV")
        self.export_equity_btn.setMaximumWidth(80)
        self.export_equity_btn.clicked.connect(self._export_equity_csv)
        trades_header.addWidget(self.export_equity_btn)

        self.export_json_btn = QPushButton("📋 JSON")
        self.export_json_btn.setMaximumWidth(60)
        self.export_json_btn.clicked.connect(self._export_json)
        trades_header.addWidget(self.export_json_btn)

        trades_layout_inner.addLayout(trades_header)

        self.trades_table = QTableWidget()
        self.trades_table.setColumnCount(8)
        self.trades_table.setHorizontalHeaderLabels([
            "ID", "Symbol", "Side", "Entry", "Exit", "Size", "P&L", "R-Mult"
        ])
        self.trades_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        trades_layout_inner.addWidget(self.trades_table)

        splitter.addWidget(trades_widget)

        # --- Regime/Setup Breakdown Table ---
        breakdown_widget = QWidget()
        breakdown_layout = QVBoxLayout(breakdown_widget)
        breakdown_layout.setContentsMargins(0, 0, 0, 0)

        breakdown_label = QLabel("🎯 Regime/Setup Breakdown")
        breakdown_label.setStyleSheet("font-weight: bold; color: #aaa;")
        breakdown_layout.addWidget(breakdown_label)

        self.breakdown_table = QTableWidget()
        self.breakdown_table.setColumnCount(7)
        self.breakdown_table.setHorizontalHeaderLabels([
            "Regime/Setup", "Trades", "Win Rate", "Avg P&L", "Profit Factor", "Expectancy", "Anteil"
        ])
        self.breakdown_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.breakdown_table.setMaximumHeight(150)
        breakdown_layout.addWidget(self.breakdown_table)

        splitter.addWidget(breakdown_widget)

        layout.addWidget(splitter)

        return widget
    def _update_metrics_table(self, metrics) -> None:
        """Aktualisiert die Metriken-Tabelle."""
        data = [
            ("Total Trades", str(metrics.total_trades)),
            ("Winning Trades", str(metrics.winning_trades)),
            ("Losing Trades", str(metrics.losing_trades)),
            ("Win Rate", f"{metrics.win_rate * 100:.1f}%"),
            ("Profit Factor", f"{metrics.profit_factor:.2f}"),
            ("Expectancy", f"${metrics.expectancy:.2f}" if metrics.expectancy else "—"),
            ("Max Drawdown", f"{metrics.max_drawdown_pct:.1f}%"),
            ("Sharpe Ratio", f"{metrics.sharpe_ratio:.2f}" if metrics.sharpe_ratio else "—"),
            ("Avg R-Multiple", f"{metrics.avg_r_multiple:.2f}" if metrics.avg_r_multiple else "—"),
        ]

        self.metrics_table.setRowCount(len(data))
        for row, (name, value) in enumerate(data):
            self.metrics_table.setItem(row, 0, QTableWidgetItem(name))
            self.metrics_table.setItem(row, 1, QTableWidgetItem(value))
    def _update_trades_table(self, trades: list) -> None:
        """Aktualisiert die Trades-Tabelle."""
        self.trades_table.setRowCount(len(trades))

        for row, trade in enumerate(trades):
            self.trades_table.setItem(row, 0, QTableWidgetItem(trade.id[:8] if trade.id else "—"))
            self.trades_table.setItem(row, 1, QTableWidgetItem(trade.symbol))
            self.trades_table.setItem(row, 2, QTableWidgetItem(trade.side.value.upper()))
            self.trades_table.setItem(row, 3, QTableWidgetItem(f"${trade.entry_price:.2f}"))
            self.trades_table.setItem(row, 4, QTableWidgetItem(
                f"${trade.exit_price:.2f}" if trade.exit_price else "—"
            ))
            self.trades_table.setItem(row, 5, QTableWidgetItem(f"{trade.size:.4f}"))

            # P&L mit Farbe
            pnl = trade.realized_pnl
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")
            pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
            self.trades_table.setItem(row, 6, pnl_item)

            # R-Multiple
            r_mult = trade.r_multiple if hasattr(trade, 'r_multiple') else None
            self.trades_table.setItem(row, 7, QTableWidgetItem(
                f"{r_mult:.2f}R" if r_mult else "—"
            ))
    def _update_breakdown_table(self, trades: list) -> None:
        """Aktualisiert die Regime/Setup Breakdown Tabelle.

        Gruppiert Trades nach Regime/Setup und berechnet Statistiken.

        Args:
            trades: Liste von Trade Objekten
        """
        if not trades:
            self.breakdown_table.setRowCount(0)
            return

        # Trades nach Regime/Setup gruppieren
        from collections import defaultdict

        breakdown = defaultdict(lambda: {
            "trades": [],
            "wins": 0,
            "losses": 0,
            "total_pnl": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
        })

        for trade in trades:
            # Bestimme Regime/Setup - verwende exit_reason oder regime falls vorhanden
            regime = "Unknown"
            if hasattr(trade, 'regime') and trade.regime:
                regime = trade.regime
            elif hasattr(trade, 'exit_reason') and trade.exit_reason:
                regime = trade.exit_reason
            elif hasattr(trade, 'setup_type') and trade.setup_type:
                regime = trade.setup_type
            elif hasattr(trade, 'side'):
                regime = f"{trade.side.value.upper()} Trade"

            pnl = trade.realized_pnl if hasattr(trade, 'realized_pnl') else 0

            breakdown[regime]["trades"].append(trade)
            breakdown[regime]["total_pnl"] += pnl

            if pnl >= 0:
                breakdown[regime]["wins"] += 1
                breakdown[regime]["gross_profit"] += pnl
            else:
                breakdown[regime]["losses"] += 1
                breakdown[regime]["gross_loss"] += abs(pnl)

        # Tabelle füllen
        total_trades = len(trades)
        self.breakdown_table.setRowCount(len(breakdown))

        for row, (regime, stats) in enumerate(sorted(breakdown.items(), key=lambda x: len(x[1]["trades"]), reverse=True)):
            num_trades = len(stats["trades"])
            wins = stats["wins"]
            losses = stats["losses"]
            total_pnl = stats["total_pnl"]
            gross_profit = stats["gross_profit"]
            gross_loss = stats["gross_loss"]

            # Win Rate
            win_rate = (wins / num_trades * 100) if num_trades > 0 else 0

            # Avg P&L
            avg_pnl = total_pnl / num_trades if num_trades > 0 else 0

            # Profit Factor
            pf = gross_profit / gross_loss if gross_loss > 0 else (float('inf') if gross_profit > 0 else 0)

            # Expectancy
            expectancy = avg_pnl

            # Anteil
            share = (num_trades / total_trades * 100) if total_trades > 0 else 0

            # Zeile setzen
            self.breakdown_table.setItem(row, 0, QTableWidgetItem(regime))
            self.breakdown_table.setItem(row, 1, QTableWidgetItem(str(num_trades)))

            wr_item = QTableWidgetItem(f"{win_rate:.1f}%")
            wr_item.setForeground(QColor("#4CAF50" if win_rate >= 50 else "#FF9800" if win_rate >= 40 else "#f44336"))
            self.breakdown_table.setItem(row, 2, wr_item)

            avg_item = QTableWidgetItem(f"${avg_pnl:.2f}")
            avg_item.setForeground(QColor("#4CAF50" if avg_pnl >= 0 else "#f44336"))
            self.breakdown_table.setItem(row, 3, avg_item)

            pf_str = f"{pf:.2f}" if pf != float('inf') else "∞"
            pf_item = QTableWidgetItem(pf_str)
            pf_item.setForeground(QColor("#4CAF50" if pf >= 1.5 else "#FF9800" if pf >= 1 else "#f44336"))
            self.breakdown_table.setItem(row, 4, pf_item)

            exp_item = QTableWidgetItem(f"${expectancy:.2f}")
            exp_item.setForeground(QColor("#4CAF50" if expectancy >= 0 else "#f44336"))
            self.breakdown_table.setItem(row, 5, exp_item)

            self.breakdown_table.setItem(row, 6, QTableWidgetItem(f"{share:.1f}%"))
