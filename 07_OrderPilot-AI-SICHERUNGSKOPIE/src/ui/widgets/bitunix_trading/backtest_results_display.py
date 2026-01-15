"""
Backtest Results Display - Results Processing and Table Updates

Handles display of backtest results:
- Update KPI cards and tables
- Format metrics, trades, breakdown data
- Color coding for P&L visualization
- Regime/Setup performance breakdown

Module 3/5 of backtest_tab.py split (Lines 2219-2496)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import pyqtSlot, Qt
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import QLabel, QTableWidgetItem

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class BacktestResultsDisplay:
    """Verwaltet die Anzeige von Backtest-Ergebnissen.

    Verantwortlich für:
    - Aktualisierung der KPI Cards (P&L, Win Rate, PF, Max DD)
    - Aktualisierung der Metriken-Tabelle
    - Aktualisierung der Trades-Tabelle mit Farb-Coding
    - Aktualisierung der Breakdown-Tabelle (Regime/Setup Statistiken)
    - Aktualisierung der Batch-Ergebnisse Tabelle
    - Aktualisierung der Walk-Forward Ergebnisse Tabelle
    """

    def __init__(self, parent_widget: "QWidget"):
        """Initialisiert BacktestResultsDisplay.

        Args:
            parent_widget: Das BacktestTab Widget
        """
        self.parent = parent_widget

    @pyqtSlot(object)
    def on_backtest_finished(self, result) -> None:
        """Verarbeitet Backtest-Ergebnis und aktualisiert UI.

        Args:
            result: BacktestResult Objekt mit Metriken, Trades, Equity Curve
        """
        if result is None:
            return

        try:
            # Update KPI Cards
            metrics = result.metrics if hasattr(result, 'metrics') else None

            if metrics:
                # P&L
                pnl = result.total_pnl if hasattr(result, 'total_pnl') else 0
                pnl_color = "#4CAF50" if pnl >= 0 else "#f44336"
                self.parent.kpi_pnl.findChild(QLabel, "kpi_value").setText(f"${pnl:,.2f}")
                self.parent.kpi_pnl.findChild(QLabel, "kpi_value").setStyleSheet(
                    f"color: {pnl_color}; font-size: 18px; font-weight: bold;"
                )

                # Win Rate
                win_rate = metrics.win_rate * 100 if metrics.win_rate else 0
                self.parent.kpi_winrate.findChild(QLabel, "kpi_value").setText(f"{win_rate:.1f}%")

                # Profit Factor
                pf = metrics.profit_factor if metrics.profit_factor else 0
                self.parent.kpi_pf.findChild(QLabel, "kpi_value").setText(f"{pf:.2f}")

                # Max DD
                dd = metrics.max_drawdown_pct if metrics.max_drawdown_pct else 0
                self.parent.kpi_dd.findChild(QLabel, "kpi_value").setText(f"{dd:.1f}%")

                # Update Metrics Table
                self.update_metrics_table(metrics)

            # Update Trades Table
            if hasattr(result, 'trades') and result.trades:
                self.update_trades_table(result.trades)
                self.update_breakdown_table(result.trades)

            # Update Equity Curve Chart
            if self.parent.equity_chart and hasattr(result, 'equity_curve') and result.equity_curve:
                try:
                    self.parent.equity_chart.load_from_result(result)
                    self.parent._log(f"📈 Equity Curve geladen: {len(result.equity_curve)} Punkte")
                except Exception as eq_err:
                    logger.warning(f"Could not load equity chart: {eq_err}")

            # Switch to Results tab
            self.parent.sub_tabs.setCurrentIndex(2)  # Results Tab

            self.parent._log(f"📊 Ergebnisse geladen: {metrics.total_trades if metrics else 0} Trades")

        except Exception as e:
            logger.exception("Error updating results")
            self.parent._log(f"❌ Fehler beim Anzeigen: {e}")

    def update_metrics_table(self, metrics) -> None:
        """Aktualisiert die Metriken-Tabelle.

        Zeigt 9 Key-Metriken in 2 Spalten (Metrik, Wert):
        - Total Trades, Winning/Losing Trades
        - Win Rate, Profit Factor, Expectancy
        - Max Drawdown, Sharpe Ratio, Avg R-Multiple

        Args:
            metrics: BacktestMetrics Objekt mit allen Statistiken
        """
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

        self.parent.metrics_table.setRowCount(len(data))
        for row, (name, value) in enumerate(data):
            self.parent.metrics_table.setItem(row, 0, QTableWidgetItem(name))
            self.parent.metrics_table.setItem(row, 1, QTableWidgetItem(value))

    def update_trades_table(self, trades: list) -> None:
        """Aktualisiert die Trades-Tabelle.

        Zeigt alle Trades in 8 Spalten:
        - ID, Symbol, Side, Entry Price, Exit Price, Size
        - P&L (mit Farb-Coding: grün=Gewinn, rot=Verlust)
        - R-Multiple

        Args:
            trades: Liste von Trade Objekten
        """
        self.parent.trades_table.setRowCount(len(trades))

        for row, trade in enumerate(trades):
            self.parent.trades_table.setItem(row, 0, QTableWidgetItem(trade.id[:8] if trade.id else "—"))
            self.parent.trades_table.setItem(row, 1, QTableWidgetItem(trade.symbol))
            self.parent.trades_table.setItem(row, 2, QTableWidgetItem(trade.side.value.upper()))
            self.parent.trades_table.setItem(row, 3, QTableWidgetItem(f"${trade.entry_price:.2f}"))
            self.parent.trades_table.setItem(row, 4, QTableWidgetItem(
                f"${trade.exit_price:.2f}" if trade.exit_price else "—"
            ))
            self.parent.trades_table.setItem(row, 5, QTableWidgetItem(f"{trade.size:.4f}"))

            # P&L mit Farbe
            pnl = trade.realized_pnl
            pnl_item = QTableWidgetItem(f"${pnl:.2f}")
            pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
            self.parent.trades_table.setItem(row, 6, pnl_item)

            # R-Multiple
            r_mult = trade.r_multiple if hasattr(trade, 'r_multiple') else None
            self.parent.trades_table.setItem(row, 7, QTableWidgetItem(
                f"{r_mult:.2f}R" if r_mult else "—"
            ))

    def update_breakdown_table(self, trades: list) -> None:
        """Aktualisiert die Regime/Setup Breakdown Tabelle.

        Gruppiert Trades nach Regime/Setup und berechnet Statistiken:
        - Win Rate, Avg P&L, Profit Factor, Expectancy
        - Farb-Coding für Performance-Bewertung

        Zeigt 7 Spalten:
        - Regime/Setup, Trades, Win Rate, Avg P&L, PF, Expectancy, Anteil

        Args:
            trades: Liste von Trade Objekten
        """
        if not trades:
            self.parent.breakdown_table.setRowCount(0)
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
        self.parent.breakdown_table.setRowCount(len(breakdown))

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
            self.parent.breakdown_table.setItem(row, 0, QTableWidgetItem(regime))
            self.parent.breakdown_table.setItem(row, 1, QTableWidgetItem(str(num_trades)))

            # Win Rate mit Farb-Coding
            wr_item = QTableWidgetItem(f"{win_rate:.1f}%")
            wr_item.setForeground(QColor("#4CAF50" if win_rate >= 50 else "#FF9800" if win_rate >= 40 else "#f44336"))
            self.parent.breakdown_table.setItem(row, 2, wr_item)

            # Avg P&L mit Farb-Coding
            avg_item = QTableWidgetItem(f"${avg_pnl:.2f}")
            avg_item.setForeground(QColor("#4CAF50" if avg_pnl >= 0 else "#f44336"))
            self.parent.breakdown_table.setItem(row, 3, avg_item)

            # Profit Factor mit Farb-Coding
            pf_str = f"{pf:.2f}" if pf != float('inf') else "∞"
            pf_item = QTableWidgetItem(pf_str)
            pf_item.setForeground(QColor("#4CAF50" if pf >= 1.5 else "#FF9800" if pf >= 1 else "#f44336"))
            self.parent.breakdown_table.setItem(row, 4, pf_item)

            # Expectancy mit Farb-Coding
            exp_item = QTableWidgetItem(f"${expectancy:.2f}")
            exp_item.setForeground(QColor("#4CAF50" if expectancy >= 0 else "#f44336"))
            self.parent.breakdown_table.setItem(row, 5, exp_item)

            # Anteil
            self.parent.breakdown_table.setItem(row, 6, QTableWidgetItem(f"{share:.1f}%"))

    def update_batch_results_table(self, results: list) -> None:
        """Aktualisiert die Batch-Ergebnisse Tabelle.

        Zeigt Batch-Optimization-Ergebnisse mit 5 Spalten:
        - Rank/Run, Parameters (kurz), P&L, Expectancy, Max DD
        - Farb-Coding für Performance-Bewertung

        Args:
            results: Liste von BatchRunResult Objekten
        """
        self.parent.batch_results_table.setRowCount(len(results))

        for row, run in enumerate(results):
            # Rank/Run
            self.parent.batch_results_table.setItem(row, 0, QTableWidgetItem(f"#{row + 1}"))

            # Parameters (kurze Darstellung - erste 2 Parameter)
            params_str = ", ".join(f"{k}={v}" for k, v in list(run.parameters.items())[:2])
            if len(run.parameters) > 2:
                params_str += "..."
            self.parent.batch_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            if run.metrics:
                # P&L
                pnl = run.metrics.total_return_pct
                pnl_item = QTableWidgetItem(f"{pnl:.1f}%")
                pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
                self.parent.batch_results_table.setItem(row, 2, pnl_item)

                # Expectancy
                exp = run.metrics.expectancy if run.metrics.expectancy else 0
                self.parent.batch_results_table.setItem(row, 3, QTableWidgetItem(f"${exp:.2f}"))

                # Max DD mit Farb-Coding (rot >10%, orange 5-10%, grün <5%)
                dd = run.metrics.max_drawdown_pct
                dd_item = QTableWidgetItem(f"{dd:.1f}%")
                dd_item.setForeground(QColor("#f44336" if dd > 10 else "#FF9800" if dd > 5 else "#4CAF50"))
                self.parent.batch_results_table.setItem(row, 4, dd_item)
            else:
                # Error case
                error_item = QTableWidgetItem(run.error or "Fehler")
                error_item.setForeground(QColor("#f44336"))
                self.parent.batch_results_table.setItem(row, 2, error_item)

    def update_wf_results_table(self, fold_results: list) -> None:
        """Aktualisiert die Walk-Forward Ergebnisse Tabelle.

        Zeigt Walk-Forward-Analyse Fold-Ergebnisse mit 5 Spalten:
        - Fold Number, Parameters (optimiert), OOS P&L, OOS Expectancy, OOS Max DD
        - Farb-Coding für Performance-Bewertung

        Args:
            fold_results: Liste von FoldResult Objekten
        """
        self.parent.batch_results_table.setRowCount(len(fold_results))

        for row, fold in enumerate(fold_results):
            # Fold Number
            self.parent.batch_results_table.setItem(row, 0, QTableWidgetItem(f"Fold {fold.fold_number}"))

            # Parameters (optimierte)
            if fold.optimized_parameters:
                params_str = ", ".join(f"{k}={v}" for k, v in list(fold.optimized_parameters.items())[:2])
            else:
                params_str = "Standard"
            self.parent.batch_results_table.setItem(row, 1, QTableWidgetItem(params_str))

            # OOS (Out-of-Sample) Metrics
            if fold.oos_metrics:
                # OOS P&L
                pnl = fold.oos_metrics.total_return_pct
                pnl_item = QTableWidgetItem(f"{pnl:.1f}%")
                pnl_item.setForeground(QColor("#4CAF50" if pnl >= 0 else "#f44336"))
                self.parent.batch_results_table.setItem(row, 2, pnl_item)

                # OOS Expectancy
                exp = fold.oos_metrics.expectancy if fold.oos_metrics.expectancy else 0
                self.parent.batch_results_table.setItem(row, 3, QTableWidgetItem(f"${exp:.2f}"))

                # OOS Max DD mit Farb-Coding
                dd = fold.oos_metrics.max_drawdown_pct
                dd_item = QTableWidgetItem(f"{dd:.1f}%")
                dd_item.setForeground(QColor("#f44336" if dd > 10 else "#FF9800" if dd > 5 else "#4CAF50"))
                self.parent.batch_results_table.setItem(row, 4, dd_item)
            else:
                # Keine OOS-Daten verfügbar
                error_item = QTableWidgetItem("Keine OOS-Daten")
                error_item.setForeground(QColor("#888"))
                self.parent.batch_results_table.setItem(row, 2, error_item)
