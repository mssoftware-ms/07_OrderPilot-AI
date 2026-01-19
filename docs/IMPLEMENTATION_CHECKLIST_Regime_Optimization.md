# 🎯 Implementierungs-Checkliste: Regime-basierte Indikator-Optimierung

**Version:** 1.0.0
**Datum:** 2026-01-19
**Status:** ✅ FULLY IMPLEMENTED (Verified 2026-01-19)
**Tatsächlicher Aufwand:** 0 Stunden (Bereits vollständig implementiert)
**Ursprüngliche Schätzung:** 12-16 Stunden MVP | 20-25 Stunden Complete

---

## ⚡ WICHTIGE ANFORDERUNG

**Separate Durchläufe für Entry/Exit und Long/Short:**
- ✅ **Entry Long** - Beste Indikatoren für Long-Einstiege
- ✅ **Entry Short** - Beste Indikatoren für Short-Einstiege
- ✅ **Exit Long** - Beste Indikatoren für Long-Ausstiege
- ✅ **Exit Short** - Beste Indikatoren für Short-Ausstiege

**UI bereits vorbereitet:**
- Radio-Buttons für Test Type: Entry vs Exit (Lines 1152-1154)
- Radio-Buttons für Trade Side: Long vs Short (Lines 1161-1163)

---

## 📋 PHASE 1: BACKTEST-BUTTON VERDRAHTUNG (KRITISCH)

**Ziel:** "Run Backtest" Button mit BacktestEngine verbinden
**Geschätzter Aufwand:** 2-3 Stunden
**Priorität:** 🔴 HIGHEST (ohne dies funktioniert nichts)

### 1.1 Signal/Slot Connection hinzufügen

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 1.1.1:** In `_setup_backtest_config_tab()` (nach Line ~550) Run Backtest Button finden
  ```python
  # Suchen nach:
  self._run_backtest_btn = QPushButton("▶️ Run Backtest")
  ```

- [x] **Task 1.1.2:** Signal/Slot Connection hinzufügen (direkt nach Button-Erstellung)
  ```python
  self._run_backtest_btn.clicked.connect(self._on_run_backtest_clicked)
  ```

- [x] **Task 1.1.3:** Sicherstellen, dass Button-Referenz als self._run_backtest_btn gespeichert ist

**Test-Kriterium:** Button-Click löst Handler-Methode aus (füge temporäres `print("Button clicked!")` ein)

---

### 1.2 Handler-Methode implementieren

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 1.2.1:** Handler-Methode hinzufügen (nach `_on_analyze_clicked`, ca. Line 1400)
  ```python
  def _on_run_backtest_clicked(self) -> None:
      """Handler für Run Backtest Button (Phase 1.1).

      Validates inputs, loads JSON config, and starts backtest worker.
      """
      logger.info("Run Backtest button clicked")

      # 1. Validate Inputs
      config_path = self._bt_config_path_input.text().strip()
      if not config_path:
          QMessageBox.warning(self, "Error", "Please select a JSON configuration file")
          return

      if not os.path.exists(config_path):
          QMessageBox.warning(self, "Error", f"Config file not found: {config_path}")
          return

      symbol = self._bt_symbol_combo.currentText()
      if not symbol:
          QMessageBox.warning(self, "Error", "Please select a symbol")
          return

      # Get date range
      start_date = self._bt_start_date.date().toPyDate()
      end_date = self._bt_end_date.date().toPyDate()

      if start_date >= end_date:
          QMessageBox.warning(self, "Error", "Start date must be before end date")
          return

      # Get initial capital
      initial_capital = self._bt_capital_spin.value()

      # 2. Load JSON Config (validate early)
      try:
          from src.core.tradingbot.config.loader import ConfigLoader
          config = ConfigLoader().load_config(config_path)
          logger.info(f"Loaded config: {config.schema_version}, {len(config.strategies)} strategies")
      except Exception as e:
          QMessageBox.critical(self, "Config Error", f"Failed to load config:\n{str(e)}")
          logger.error(f"Config load error: {e}")
          return

      # 3. Disable button, show progress
      self._run_backtest_btn.setEnabled(False)
      self._run_backtest_btn.setText("⏳ Running...")
      self._bt_progress.setVisible(True)
      self._bt_progress.setRange(0, 0)  # Indeterminate

      # 4. Get chart data if available (for faster backtesting)
      chart_data = None
      data_timeframe = None
      if hasattr(self, '_candles') and self._candles:
          # Convert candles to DataFrame
          import pandas as pd
          chart_data = pd.DataFrame(self._candles)
          if 'timestamp' in chart_data.columns:
              chart_data['timestamp'] = pd.to_datetime(chart_data['timestamp'])
              chart_data.set_index('timestamp', inplace=True)
          data_timeframe = self._timeframe if hasattr(self, '_timeframe') else '1m'

      # 5. Start BacktestWorker
      self._backtest_worker = BacktestWorker(
          config_path=config_path,
          symbol=symbol,
          start_date=datetime.combine(start_date, datetime.min.time()),
          end_date=datetime.combine(end_date, datetime.max.time()),
          initial_capital=initial_capital,
          chart_data=chart_data,
          data_timeframe=data_timeframe,
          parent=self
      )

      # Connect signals
      self._backtest_worker.finished.connect(self._on_backtest_finished)
      self._backtest_worker.error.connect(self._on_backtest_error)
      self._backtest_worker.progress.connect(self._on_backtest_progress)

      # Start worker
      self._backtest_worker.start()
      logger.info("BacktestWorker started")
  ```

- [x] **Task 1.2.2:** Progress-Handler hinzufügen
  ```python
  def _on_backtest_progress(self, message: str) -> None:
      """Update backtest progress."""
      logger.debug(f"Backtest progress: {message}")
      # Optional: Update status label
      if hasattr(self, '_bt_status_label'):
          self._bt_status_label.setText(message)
  ```

- [x] **Task 1.2.3:** Error-Handler hinzufügen
  ```python
  def _on_backtest_error(self, error_msg: str) -> None:
      """Handle backtest error."""
      logger.error(f"Backtest error: {error_msg}")

      # Re-enable button
      self._run_backtest_btn.setEnabled(True)
      self._run_backtest_btn.setText("▶️ Run Backtest")
      self._bt_progress.setVisible(False)

      # Show error
      QMessageBox.critical(self, "Backtest Error", f"Backtest failed:\n{error_msg}")
  ```

- [x] **Task 1.2.4:** Finished-Handler hinzufügen (vorläufig)
  ```python
  def _on_backtest_finished(self, results: Dict[str, Any]) -> None:
      """Handle backtest completion (Phase 1.2).

      Args:
          results: Backtest results with keys:
              - trades: List[Dict] (all executed trades)
              - stats: Dict (performance metrics)
              - equity_curve: List[Dict] (timestamp, equity)
              - regime_history: List[Dict] (timestamp, regime_ids, regimes)
              - indicator_values: Dict[str, pd.Series] (calculated indicators)
      """
      logger.info("Backtest completed")

      # Re-enable button
      self._run_backtest_btn.setEnabled(True)
      self._run_backtest_btn.setText("▶️ Run Backtest")
      self._bt_progress.setVisible(False)

      # Store results
      self._backtest_result = results

      # Update Results Tab (Phase 1.3)
      self._update_backtest_results_tab(results)

      # Switch to Results Tab
      self._tabs.setCurrentIndex(1)  # Tab 1: Backtest Results

      logger.info(f"Backtest: {len(results['trades'])} trades, "
                  f"Net Profit: {results['stats'].get('net_profit', 0):.2f}")
  ```

**Test-Kriterium:**
1. Button-Click startet BacktestWorker
2. Progress-Bar wird angezeigt
3. Button wird disabled während Laufzeit
4. Nach Completion: Button wieder enabled, Results Tab wird geöffnet

---

### 1.3 Results Tab Aktualisierung

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 1.3.1:** `_update_backtest_results_tab()` implementieren (nach `_on_backtest_finished`)
  ```python
  def _update_backtest_results_tab(self, results: Dict[str, Any]) -> None:
      """Update Backtest Results tab with results (Phase 1.3).

      Args:
          results: Backtest results from BacktestEngine
      """
      stats = results.get('stats', {})
      trades = results.get('trades', [])

      # 1. Update Performance Summary
      summary_text = f"""
  📊 **Backtest Performance Summary**

  **Returns:**
  - Net Profit: ${stats.get('net_profit', 0):,.2f}
  - Total Return: {stats.get('total_return', 0):.2%}
  - Max Drawdown: {stats.get('max_drawdown', 0):.2%}

  **Trade Statistics:**
  - Total Trades: {stats.get('total_trades', 0)}
  - Winning Trades: {stats.get('winning_trades', 0)}
  - Losing Trades: {stats.get('losing_trades', 0)}
  - Win Rate: {stats.get('win_rate', 0):.2%}

  **Risk Metrics:**
  - Profit Factor: {stats.get('profit_factor', 0):.2f}
  - Sharpe Ratio: {stats.get('sharpe_ratio', 0):.2f}
  - Sortino Ratio: {stats.get('sortino_ratio', 0):.2f}
  - Max Consecutive Losses: {stats.get('max_consecutive_losses', 0)}

  **Regime Breakdown:**
  {self._format_regime_stats(results.get('regime_stats', {}))}
      """

      self._bt_summary.setMarkdown(summary_text)

      # 2. Update Trade List Table
      self._bt_trade_list.setRowCount(0)  # Clear existing

      for trade in trades:
          row = self._bt_trade_list.rowCount()
          self._bt_trade_list.insertRow(row)

          # Columns: Entry Time | Exit Time | Side | Entry Price | Exit Price | PnL | Return | Regime
          self._bt_trade_list.setItem(row, 0, QTableWidgetItem(
              str(trade.get('entry_time', ''))
          ))
          self._bt_trade_list.setItem(row, 1, QTableWidgetItem(
              str(trade.get('exit_time', ''))
          ))
          self._bt_trade_list.setItem(row, 2, QTableWidgetItem(
              trade.get('side', 'UNKNOWN')
          ))
          self._bt_trade_list.setItem(row, 3, QTableWidgetItem(
              f"{trade.get('entry_price', 0):.2f}"
          ))
          self._bt_trade_list.setItem(row, 4, QTableWidgetItem(
              f"{trade.get('exit_price', 0):.2f}"
          ))

          pnl = trade.get('pnl', 0)
          pnl_item = QTableWidgetItem(f"${pnl:.2f}")
          pnl_item.setForeground(Qt.GlobalColor.green if pnl > 0 else Qt.GlobalColor.red)
          self._bt_trade_list.setItem(row, 5, pnl_item)

          return_pct = trade.get('return_pct', 0)
          return_item = QTableWidgetItem(f"{return_pct:.2%}")
          return_item.setForeground(Qt.GlobalColor.green if return_pct > 0 else Qt.GlobalColor.red)
          self._bt_trade_list.setItem(row, 6, return_item)

          self._bt_trade_list.setItem(row, 7, QTableWidgetItem(
              ', '.join(trade.get('regime_ids', []))
          ))

      self._bt_trade_list.resizeColumnsToContents()

      logger.info(f"Updated Results Tab with {len(trades)} trades")

  def _format_regime_stats(self, regime_stats: Dict[str, Dict]) -> str:
      """Format regime-specific statistics."""
      if not regime_stats:
          return "No regime-specific statistics available"

      lines = []
      for regime_id, stats in regime_stats.items():
          trades = stats.get('trades', 0)
          win_rate = stats.get('win_rate', 0)
          avg_return = stats.get('avg_return', 0)
          lines.append(
              f"  - **{regime_id}**: {trades} trades, "
              f"Win Rate: {win_rate:.1%}, Avg Return: {avg_return:.2%}"
          )

      return '\n'.join(lines)
  ```

**Test-Kriterium:**
1. Summary zeigt alle Performance-Metriken korrekt
2. Trade List wird mit allen Trades gefüllt
3. Positive/Negative PnL haben korrekte Farben (grün/rot)
4. Regime-Breakdown wird angezeigt

---

## 📋 PHASE 2: REGIME-VISUALISIERUNG (KRITISCH)

**Ziel:** Vertikale Linien für Regime-Grenzen im Chart zeichnen
**Geschätzter Aufwand:** 3-4 Stunden
**Priorität:** 🔴 HIGHEST (Kernanforderung 1a)

### 2.1 Regime-Daten aus Backtest extrahieren

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 2.1.1:** Regime-Change-Extraktion hinzufügen in `_on_backtest_finished()`:
  ```python
  # In _on_backtest_finished(), nach self._backtest_result = results

  # Extract regime changes for visualization
  regime_changes = self._extract_regime_changes(results)

  # Draw regime boundaries on chart (if chart window available)
  if hasattr(self, 'parent') and hasattr(self.parent(), 'add_regime_boundaries'):
      self.parent().add_regime_boundaries(regime_changes)
      logger.info(f"Drew {len(regime_changes)} regime boundaries on chart")
  ```

- [x] **Task 2.1.2:** `_extract_regime_changes()` Methode implementieren:
  ```python
  def _extract_regime_changes(self, results: Dict[str, Any]) -> List[Dict[str, Any]]:
      """Extract regime change events for visualization (Phase 2.1).

      Args:
          results: Backtest results with 'regime_history' key

      Returns:
          List of regime change events with:
              - timestamp: datetime
              - regime_ids: List[str]
              - regime_names: List[str]
              - regime_type: str (for coloring)
      """
      regime_history = results.get('regime_history', [])

      if not regime_history:
          logger.warning("No regime history found in backtest results")
          return []

      regime_changes = []

      for event in regime_history:
          timestamp = event.get('timestamp')
          regime_ids = event.get('regime_ids', [])
          regimes = event.get('regimes', [])

          # Determine primary regime type for coloring
          regime_type = self._determine_regime_type(regime_ids)

          regime_changes.append({
              'timestamp': timestamp,
              'regime_ids': regime_ids,
              'regime_names': [r.get('name', r.get('id')) for r in regimes],
              'regime_type': regime_type,
              'label': ', '.join([r.get('name', r.get('id')) for r in regimes][:2])  # Max 2 für Label
          })

      logger.info(f"Extracted {len(regime_changes)} regime changes")
      return regime_changes

  def _determine_regime_type(self, regime_ids: List[str]) -> str:
      """Determine primary regime type from regime IDs for color mapping.

      Priority:
      1. trend_following > trend_up / trend_down
      2. sideways > range_bound
      3. breakout > breakout_momentum / breakout_volatility
      4. mean_reversion
      5. other
      """
      regime_id_lower = [rid.lower() for rid in regime_ids]

      if any('trend_up' in rid for rid in regime_id_lower):
          return 'trend_up'
      elif any('trend_down' in rid for rid in regime_id_lower):
          return 'trend_down'
      elif any('trend' in rid for rid in regime_id_lower):
          return 'trend_up'  # Default trend = up
      elif any('sideways' in rid or 'range' in rid for rid in regime_id_lower):
          return 'range'
      elif any('breakout' in rid for rid in regime_id_lower):
          return 'breakout'
      elif any('mean_reversion' in rid for rid in regime_id_lower):
          return 'mean_reversion'
      elif any('high_vol' in rid or 'volatile' in rid for rid in regime_id_lower):
          return 'high_volatility'
      else:
          return 'other'
  ```

**Test-Kriterium:**
1. `regime_changes` enthält alle Regime-Wechsel
2. Jeder Event hat timestamp, regime_ids, regime_names, regime_type
3. Logging zeigt Anzahl extrahierter Changes

---

### 2.2 Chart-Mixin für Regime-Visualisierung erstellen

**Neue Datei:** `src/ui/widgets/chart_window_mixins/regime_visualization_mixin.py`

- [x] **Task 2.2.1:** Neue Datei erstellen mit Mixin-Klasse:
  ```python
  """
  Regime Visualization Mixin for Chart Windows.

  Adds support for drawing vertical regime boundary lines on charts
  with color-coded regime types.
  """
  import logging
  from typing import List, Dict, Any
  from datetime import datetime

  from PyQt6.QtCore import Qt
  from PyQt6.QtGui import QColor
  import pyqtgraph as pg

  logger = logging.getLogger(__name__)


  class RegimeVisualizationMixin:
      """Mixin for adding regime boundary visualization to chart windows.

      Features:
      - Draw vertical lines at regime changes
      - Color-coded by regime type (Trend Up/Down, Range, Breakout, etc.)
      - Labels showing regime names
      - Clear/remove regime lines
      """

      def __init__(self):
          """Initialize regime visualization storage."""
          super().__init__()
          self.regime_lines: List[pg.InfiniteLine] = []
          self.regime_labels: List[pg.TextItem] = []

      def add_regime_boundaries(self, regime_changes: List[Dict[str, Any]]) -> None:
          """Add vertical lines for regime boundaries (Phase 2.2).

          Args:
              regime_changes: List of regime change events with:
                  - timestamp: datetime
                  - regime_type: str (for color mapping)
                  - label: str (regime name to display)
          """
          logger.info(f"Adding {len(regime_changes)} regime boundaries to chart")

          # Clear existing regime lines first
          self.clear_regime_lines()

          # Get regime colors
          regime_colors = self._get_regime_colors()

          for change in regime_changes:
              timestamp = change['timestamp']
              regime_type = change['regime_type']
              label = change['label']

              # Get color for regime type
              color = regime_colors.get(regime_type, '#9e9e9e')

              # Convert timestamp to x-coordinate
              x_pos = self._timestamp_to_x(timestamp)

              if x_pos is None:
                  logger.warning(f"Could not convert timestamp {timestamp} to x-coordinate")
                  continue

              # Create vertical line
              pen = pg.mkPen(color=color, width=2, style=Qt.PenStyle.DashLine)
              line = pg.InfiniteLine(
                  pos=x_pos,
                  angle=90,
                  pen=pen,
                  movable=False
              )

              # Add line to chart
              if hasattr(self, 'chart_widget') and self.chart_widget:
                  self.chart_widget.addItem(line)
                  self.regime_lines.append(line)
              elif hasattr(self, 'plotWidget'):
                  self.plotWidget.addItem(line)
                  self.regime_lines.append(line)
              else:
                  logger.error("No chart widget found to add regime line")
                  continue

              # Create label (optional, can be disabled if too cluttered)
              if hasattr(self, '_show_regime_labels') and self._show_regime_labels:
                  text_item = pg.TextItem(
                      text=label,
                      color=color,
                      anchor=(0, 1)  # Top-left anchor
                  )
                  text_item.setPos(x_pos, 0)  # Position at top of chart

                  if hasattr(self, 'chart_widget') and self.chart_widget:
                      self.chart_widget.addItem(text_item)
                      self.regime_labels.append(text_item)
                  elif hasattr(self, 'plotWidget'):
                      self.plotWidget.addItem(text_item)
                      self.regime_labels.append(text_item)

          logger.info(f"Successfully added {len(self.regime_lines)} regime boundary lines")

      def clear_regime_lines(self) -> None:
          """Remove all regime boundary lines from chart."""
          logger.info(f"Clearing {len(self.regime_lines)} regime lines")

          # Remove lines
          for line in self.regime_lines:
              if hasattr(self, 'chart_widget') and self.chart_widget:
                  self.chart_widget.removeItem(line)
              elif hasattr(self, 'plotWidget'):
                  self.plotWidget.removeItem(line)

          # Remove labels
          for label in self.regime_labels:
              if hasattr(self, 'chart_widget') and self.chart_widget:
                  self.chart_widget.removeItem(label)
              elif hasattr(self, 'plotWidget'):
                  self.plotWidget.removeItem(label)

          self.regime_lines.clear()
          self.regime_labels.clear()

      def _timestamp_to_x(self, timestamp: datetime) -> float | None:
          """Convert timestamp to x-coordinate in chart (Phase 2.2).

          This method needs to be customized based on your chart implementation.
          Common approaches:
          - Unix timestamp (seconds since epoch)
          - Bar index (0, 1, 2, ...)
          - Custom mapping

          Args:
              timestamp: Datetime to convert

          Returns:
              X-coordinate or None if conversion fails
          """
          # OPTION 1: Unix timestamp (if chart uses timestamp as x-axis)
          if isinstance(timestamp, datetime):
              return timestamp.timestamp()

          # OPTION 2: Bar index (if chart uses bar indices as x-axis)
          # This requires access to the chart's data to find the matching index
          # if hasattr(self, '_candles') and self._candles:
          #     for i, candle in enumerate(self._candles):
          #         if candle.get('timestamp') == timestamp:
          #             return float(i)

          logger.error(f"Could not convert timestamp {timestamp} to x-coordinate")
          return None

      def _get_regime_colors(self) -> Dict[str, str]:
          """Get color mapping for regime types (Phase 2.2).

          Returns:
              Dictionary mapping regime_type to hex color
          """
          return {
              'trend_up': '#26a69a',          # Green (Bullish Trend)
              'trend_down': '#ef5350',        # Red (Bearish Trend)
              'range': '#ffa726',             # Orange (Sideways/Range)
              'breakout': '#42a5f5',          # Blue (Breakout Setup)
              'mean_reversion': '#ab47bc',    # Purple (Mean Reversion)
              'high_volatility': '#ff7043',   # Deep Orange (High Vol)
              'low_volatility': '#66bb6a',    # Light Green (Low Vol)
              'other': '#9e9e9e'              # Gray (Unknown/Other)
          }

      def toggle_regime_lines(self, visible: bool) -> None:
          """Toggle visibility of regime boundary lines.

          Args:
              visible: True to show, False to hide
          """
          for line in self.regime_lines:
              line.setVisible(visible)

          for label in self.regime_labels:
              label.setVisible(visible)

          logger.info(f"Regime lines visibility set to: {visible}")
  ```

**Test-Kriterium:**
1. Mixin kann in ChartWindow-Klasse eingebunden werden
2. `add_regime_boundaries()` zeichnet vertikale Linien
3. Farben entsprechen Regime-Typen
4. `clear_regime_lines()` entfernt alle Linien

---

### 2.3 ChartWindow Integration

**Datei:** `src/ui/widgets/chart_window_setup.py` (oder entsprechende Chart-Window-Klasse)

- [x] **Task 2.3.1:** Mixin in ChartWindow-Klasse einbinden:
  ```python
  # In chart_window_setup.py oder compact_chart_widget.py

  from src.ui.widgets.chart_window_mixins.regime_visualization_mixin import RegimeVisualizationMixin

  # Modify class declaration:
  class ChartWindow(..., RegimeVisualizationMixin):  # Mixin hinzufügen
      def __init__(self, ...):
          # Initialize Mixin
          RegimeVisualizationMixin.__init__(self)

          # ... rest of init
  ```

- [x] **Task 2.3.2:** `_timestamp_to_x()` Methode implementieren (chart-spezifisch):
  ```python
  # In ChartWindow-Klasse

  def _timestamp_to_x(self, timestamp: datetime) -> float | None:
      """Convert timestamp to x-coordinate (chart-specific implementation).

      Override from RegimeVisualizationMixin.
      """
      # IMPLEMENTATION DEPENDS ON YOUR CHART:

      # If using pyqtgraph with DateAxisItem:
      if isinstance(timestamp, datetime):
          return timestamp.timestamp()

      # If using bar indices, find matching candle:
      # if hasattr(self, 'candles'):
      #     for i, candle in enumerate(self.candles):
      #         candle_time = candle.get('timestamp')
      #         if candle_time == timestamp:
      #             return float(i)

      return None
  ```

- [x] **Task 2.3.3:** Optional: UI-Toggle für Regime-Lines hinzufügen:
  ```python
  # In ChartWindow toolbar/menu

  def _add_regime_toggle(self):
      """Add toolbar button to toggle regime boundary visibility."""
      toggle_regime_btn = QPushButton("📊 Regimes")
      toggle_regime_btn.setCheckable(True)
      toggle_regime_btn.setChecked(True)  # Default: visible
      toggle_regime_btn.toggled.connect(self.toggle_regime_lines)

      # Add to toolbar
      self.toolbar.addWidget(toggle_regime_btn)
  ```

**Test-Kriterium:**
1. ChartWindow hat Mixin-Funktionalität
2. Regime-Lines werden im Chart angezeigt
3. Farben sind korrekt
4. Toggle-Button funktioniert

---

## 📋 PHASE 3: INDICATOR OPTIMIZATION WORKER (ERWEITERT)

**Ziel:** Parameter-Testing für Indikatoren mit Scoring 0-100 pro Regime
**Geschätzter Aufwand:** 4-5 Stunden
**Priorität:** 🟡 HIGH (Kernanforderung 1b + 1c)

### 3.1 IndicatorOptimizationWorker erstellen

**Neue Datei:** `src/ui/threads/indicator_optimization_worker.py`

- [x] **Task 3.1.1:** Worker-Thread-Klasse erstellen:
  ```python
  """
  Indicator Optimization Worker for Entry Analyzer.

  Tests individual indicators with parameter variations across different
  market regimes, scoring each combination from 0-100.

  WICHTIG: Separate Durchläufe für:
  - Entry Long
  - Entry Short
  - Exit Long
  - Exit Short
  """
  import logging
  from typing import List, Dict, Any, Tuple
  from datetime import datetime

  from PyQt6.QtCore import QThread, pyqtSignal
  import pandas as pd
  import numpy as np

  logger = logging.getLogger(__name__)


  class IndicatorOptimizationWorker(QThread):
      """Background worker for indicator parameter optimization (Phase 3.1).

      Tests indicators with different parameter settings and calculates
      scores (0-100) for each regime based on Win Rate and Profit Factor.

      Signals:
          finished: Emitted when optimization completes (results: List[Dict])
          error: Emitted on error (error_msg: str)
          progress: Emitted during processing (current: int, total: int, message: str)
      """

      finished = pyqtSignal(list)  # List[Dict[str, Any]]
      error = pyqtSignal(str)
      progress = pyqtSignal(int, int, str)  # current, total, message

      def __init__(
          self,
          selected_indicators: List[str],
          parameter_ranges: Dict[str, Dict[str, Any]],
          symbol: str,
          start_date: datetime,
          end_date: datetime,
          test_type: str,  # 'entry' or 'exit'
          trade_side: str,  # 'long' or 'short'
          chart_data: pd.DataFrame = None,
          parent=None
      ):
          super().__init__(parent)
          self.selected_indicators = selected_indicators
          self.parameter_ranges = parameter_ranges
          self.symbol = symbol
          self.start_date = start_date
          self.end_date = end_date
          self.test_type = test_type
          self.trade_side = trade_side
          self.chart_data = chart_data

      def run(self) -> None:
          """Execute indicator optimization (Phase 3.1)."""
          try:
              logger.info(
                  f"Starting indicator optimization: {len(self.selected_indicators)} indicators, "
                  f"Test Type: {self.test_type}, Trade Side: {self.trade_side}"
              )

              results = []
              total_iterations = self._calculate_total_iterations()
              current = 0

              # Iterate through selected indicators
              for indicator_type in self.selected_indicators:
                  # Generate parameter combinations for this indicator
                  param_combinations = self._generate_param_combinations(indicator_type)

                  logger.info(
                      f"Testing {indicator_type} with {len(param_combinations)} parameter combinations"
                  )

                  for params in param_combinations:
                      # Update progress
                      current += 1
                      self.progress.emit(
                          current,
                          total_iterations,
                          f"Testing {indicator_type}{params} ({self.test_type}/{self.trade_side})"
                      )

                      # Run single indicator backtest
                      indicator_results = self._test_single_indicator(
                          indicator_type, params
                      )

                      # Calculate scores per regime
                      regime_scores = self._calculate_regime_scores(indicator_results)

                      # Store results for each regime
                      for regime_id, score_data in regime_scores.items():
                          results.append({
                              'indicator': indicator_type,
                              'params': params,
                              'test_type': self.test_type,
                              'trade_side': self.trade_side,
                              'regime': regime_id,
                              'score': score_data['score'],
                              'win_rate': score_data['win_rate'],
                              'profit_factor': score_data['profit_factor'],
                              'total_trades': score_data['total_trades'],
                              'avg_return': score_data['avg_return']
                          })

              logger.info(f"Optimization completed: {len(results)} results generated")
              self.finished.emit(results)

          except Exception as e:
              logger.error(f"Optimization error: {e}", exc_info=True)
              self.error.emit(str(e))

      def _calculate_total_iterations(self) -> int:
          """Calculate total number of iterations for progress tracking."""
          total = 0
          for indicator_type in self.selected_indicators:
              param_combos = self._generate_param_combinations(indicator_type)
              total += len(param_combos)
          return total

      def _generate_param_combinations(self, indicator_type: str) -> List[Dict[str, Any]]:
          """Generate parameter combinations for indicator (Phase 3.1).

          Args:
              indicator_type: 'RSI', 'MACD', 'ADX', etc.

          Returns:
              List of parameter dictionaries

          Example for RSI:
              [{'period': 10}, {'period': 12}, {'period': 14}, ...]
          """
          param_range = self.parameter_ranges.get(indicator_type, {})

          if indicator_type == 'RSI':
              min_period = param_range.get('min_period', 10)
              max_period = param_range.get('max_period', 20)
              step = param_range.get('step', 2)

              return [
                  {'period': period}
                  for period in range(min_period, max_period + 1, step)
              ]

          elif indicator_type == 'MACD':
              fast_min = param_range.get('fast_min', 8)
              fast_max = param_range.get('fast_max', 16)
              fast_step = param_range.get('fast_step', 2)

              slow_min = param_range.get('slow_min', 20)
              slow_max = param_range.get('slow_max', 30)
              slow_step = param_range.get('slow_step', 2)

              signal_min = param_range.get('signal_min', 7)
              signal_max = param_range.get('signal_max', 11)
              signal_step = param_range.get('signal_step', 2)

              combinations = []
              for fast in range(fast_min, fast_max + 1, fast_step):
                  for slow in range(slow_min, slow_max + 1, slow_step):
                      for signal in range(signal_min, signal_max + 1, signal_step):
                          if fast < slow:  # Valid only if fast < slow
                              combinations.append({
                                  'fast_period': fast,
                                  'slow_period': slow,
                                  'signal_period': signal
                              })

              return combinations

          elif indicator_type == 'ADX':
              min_period = param_range.get('min_period', 10)
              max_period = param_range.get('max_period', 20)
              step = param_range.get('step', 2)

              return [
                  {'period': period}
                  for period in range(min_period, max_period + 1, step)
              ]

          elif indicator_type in ['SMA', 'EMA']:
              min_period = param_range.get('min_period', 10)
              max_period = param_range.get('max_period', 50)
              step = param_range.get('step', 5)

              return [
                  {'period': period}
                  for period in range(min_period, max_period + 1, step)
              ]

          elif indicator_type == 'BB':
              period_min = param_range.get('period_min', 15)
              period_max = param_range.get('period_max', 25)
              period_step = param_range.get('period_step', 5)

              std_min = param_range.get('std_min', 1.5)
              std_max = param_range.get('std_max', 2.5)
              std_step = param_range.get('std_step', 0.5)

              combinations = []
              for period in range(period_min, period_max + 1, period_step):
                  std = std_min
                  while std <= std_max:
                      combinations.append({
                          'period': period,
                          'std_dev': std
                      })
                      std += std_step

              return combinations

          elif indicator_type == 'ATR':
              min_period = param_range.get('min_period', 10)
              max_period = param_range.get('max_period', 20)
              step = param_range.get('step', 2)

              return [
                  {'period': period}
                  for period in range(min_period, max_period + 1, step)
              ]

          else:
              logger.warning(f"Unknown indicator type: {indicator_type}, using default params")
              return [{}]  # Empty params

      def _test_single_indicator(
          self,
          indicator_type: str,
          params: Dict[str, Any]
      ) -> Dict[str, Any]:
          """Test single indicator with specific parameters (Phase 3.1).

          Creates a minimal JSON config with ONLY this indicator,
          runs backtest, and returns results.

          Args:
              indicator_type: Indicator name
              params: Indicator parameters

          Returns:
              Backtest results dictionary
          """
          from src.backtesting.engine import BacktestEngine
          from src.core.tradingbot.config.models import (
              TradingBotConfig, Indicator, Regime, Strategy, StrategySet, RoutingRule
          )

          # Create minimal config with single indicator
          indicator_id = f"{indicator_type.lower()}_{self._params_to_string(params)}"

          # Build indicator definition
          indicator = Indicator(
              id=indicator_id,
              type=indicator_type,
              params=params,
              timeframe='primary'  # Use primary timeframe
          )

          # Create simple entry/exit conditions based on test_type
          entry_conditions, exit_conditions = self._create_conditions(
              indicator_id, indicator_type, params
          )

          # Create regime (use all regimes for simplicity)
          regime = Regime(
              id='all_regimes',
              name='All Market Regimes',
              conditions={'operator': 'and', 'conditions': []},  # Always true
              scope='entry'
          )

          # Create strategy
          strategy = Strategy(
              id=f'strategy_{indicator_id}',
              name=f'{indicator_type} Strategy',
              entry_conditions=entry_conditions,
              exit_conditions=exit_conditions,
              risk={
                  'max_position_size_pct': 0.1,
                  'stop_loss_pct': 0.02,
                  'take_profit_pct': 0.05
              }
          )

          # Create strategy set
          strategy_set = StrategySet(
              id=f'set_{indicator_id}',
              name=f'{indicator_type} Set',
              strategies=[strategy.id]
          )

          # Create routing (route to this set always)
          routing_rule = RoutingRule(
              regimes={'all_of': [regime.id]},
              strategy_set_id=strategy_set.id
          )

          # Build complete config
          config = TradingBotConfig(
              schema_version='1.0.0',
              indicators=[indicator],
              regimes=[regime],
              strategies=[strategy],
              strategy_sets=[strategy_set],
              routing=[routing_rule]
          )

          # Run backtest
          engine = BacktestEngine()
          results = engine.run(
              config=config,
              symbol=self.symbol,
              start_date=self.start_date,
              end_date=self.end_date,
              initial_capital=10000.0,
              chart_data=self.chart_data
          )

          return results

      def _create_conditions(
          self,
          indicator_id: str,
          indicator_type: str,
          params: Dict[str, Any]
      ) -> Tuple[Dict, Dict]:
          """Create entry/exit conditions based on test_type and trade_side (Phase 3.1).

          Args:
              indicator_id: Indicator ID
              indicator_type: Indicator type
              params: Indicator parameters

          Returns:
              (entry_conditions, exit_conditions)
          """
          # ENTRY CONDITIONS
          if self.test_type == 'entry':
              if indicator_type == 'RSI':
                  if self.trade_side == 'long':
                      # RSI crosses above 30 (oversold bounce)
                      entry_conditions = {
                          'operator': 'and',
                          'conditions': [
                              {
                                  'indicator': indicator_id,
                                  'operator': 'gt',
                                  'value': 30
                              }
                          ]
                      }
                  else:  # short
                      # RSI crosses below 70 (overbought reversal)
                      entry_conditions = {
                          'operator': 'and',
                          'conditions': [
                              {
                                  'indicator': indicator_id,
                                  'operator': 'lt',
                                  'value': 70
                              }
                          ]
                      }

              elif indicator_type == 'MACD':
                  if self.trade_side == 'long':
                      # MACD line crosses above signal line
                      entry_conditions = {
                          'operator': 'and',
                          'conditions': [
                              {
                                  'indicator': f'{indicator_id}.macd',
                                  'operator': 'gt',
                                  'reference': f'{indicator_id}.signal'
                              }
                          ]
                      }
                  else:  # short
                      # MACD line crosses below signal line
                      entry_conditions = {
                          'operator': 'and',
                          'conditions': [
                              {
                                  'indicator': f'{indicator_id}.macd',
                                  'operator': 'lt',
                                  'reference': f'{indicator_id}.signal'
                              }
                          ]
                      }

              elif indicator_type == 'ADX':
                  # ADX above 25 (trending market)
                  entry_conditions = {
                      'operator': 'and',
                      'conditions': [
                          {
                              'indicator': indicator_id,
                              'operator': 'gt',
                              'value': 25
                          }
                      ]
                  }

              else:
                  # Generic condition
                  entry_conditions = {
                      'operator': 'and',
                      'conditions': []
                  }

          # EXIT CONDITIONS
          else:  # test_type == 'exit'
              # Entry conditions are generic (always enter)
              entry_conditions = {
                  'operator': 'and',
                  'conditions': []
              }

              # Exit conditions based on indicator
              if indicator_type == 'RSI':
                  if self.trade_side == 'long':
                      # Exit when RSI > 70 (overbought)
                      exit_conditions = {
                          'operator': 'or',
                          'conditions': [
                              {
                                  'indicator': indicator_id,
                                  'operator': 'gt',
                                  'value': 70
                              }
                          ]
                      }
                  else:  # short
                      # Exit when RSI < 30 (oversold)
                      exit_conditions = {
                          'operator': 'or',
                          'conditions': [
                              {
                                  'indicator': indicator_id,
                                  'operator': 'lt',
                                  'value': 30
                              }
                          ]
                      }

              else:
                  # Generic exit (use stops)
                  exit_conditions = {
                      'operator': 'or',
                      'conditions': []
                  }

          # For entry testing, use generic exit (stops only)
          if self.test_type == 'entry':
              exit_conditions = {
                  'operator': 'or',
                  'conditions': []
              }

          return entry_conditions, exit_conditions

      def _calculate_regime_scores(self, results: Dict[str, Any]) -> Dict[str, Dict]:
          """Calculate scores (0-100) per regime (Phase 3.1).

          Scoring Formula:
              Score = (Win_Rate * 40) + (Profit_Factor * 20) + (Trade_Count * 10) + (Avg_Return * 30)

          Where:
              - Win_Rate: 0-100% → 0-40 points
              - Profit_Factor: 0-3.0 → 0-20 points (capped at 3.0)
              - Trade_Count: 0-50+ trades → 0-10 points (normalized)
              - Avg_Return: -5% to +5% → 0-30 points (centered at 0%)

          Args:
              results: Backtest results with regime_stats

          Returns:
              Dictionary mapping regime_id to score data:
                  {
                      'regime_id': {
                          'score': 75.3,
                          'win_rate': 0.65,
                          'profit_factor': 2.1,
                          'total_trades': 35,
                          'avg_return': 0.018
                      }
                  }
          """
          regime_stats = results.get('regime_stats', {})

          regime_scores = {}

          for regime_id, stats in regime_stats.items():
              win_rate = stats.get('win_rate', 0)
              profit_factor = stats.get('profit_factor', 0)
              total_trades = stats.get('trades', 0)
              avg_return = stats.get('avg_return', 0)

              # Component scores
              win_rate_score = min(win_rate * 40, 40)  # Max 40 points

              pf_normalized = min(profit_factor / 3.0, 1.0)  # Normalize to 0-1
              pf_score = pf_normalized * 20  # Max 20 points

              trade_count_normalized = min(total_trades / 50.0, 1.0)  # Normalize to 0-1
              trade_count_score = trade_count_normalized * 10  # Max 10 points

              # Avg return: map -5% to +5% → 0 to 30 points
              # Center at 0%: 0% → 15 points, +5% → 30 points, -5% → 0 points
              avg_return_normalized = (avg_return + 0.05) / 0.10  # -0.05 to 0.05 → 0 to 1
              avg_return_normalized = max(0, min(avg_return_normalized, 1))  # Clamp
              avg_return_score = avg_return_normalized * 30  # Max 30 points

              # Total score
              total_score = win_rate_score + pf_score + trade_count_score + avg_return_score

              regime_scores[regime_id] = {
                  'score': round(total_score, 2),
                  'win_rate': round(win_rate, 4),
                  'profit_factor': round(profit_factor, 2),
                  'total_trades': total_trades,
                  'avg_return': round(avg_return, 4)
              }

          return regime_scores

      def _params_to_string(self, params: Dict[str, Any]) -> str:
          """Convert parameters to string for ID."""
          if not params:
              return 'default'

          parts = []
          for key, value in sorted(params.items()):
              parts.append(f'{key}{value}')

          return '_'.join(parts)
  ```

**Test-Kriterium:**
1. Worker kann gestartet werden
2. Progress-Signale werden emitted
3. Finished-Signal enthält results
4. Scores liegen zwischen 0-100

---

### 3.2 UI-Verdrahtung für Optimization

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 3.2.1:** Optimize Button verdrahten (nach Line 1250):
  ```python
  # In _setup_indicator_optimization_tab(), nach Button-Erstellung

  self._optimize_btn.clicked.connect(self._on_optimize_indicators_clicked)
  ```

- [x] **Task 3.2.2:** Handler implementieren:
  ```python
  def _on_optimize_indicators_clicked(self) -> None:
      """Handler für Optimize Indicators Button (Phase 3.2).

      WICHTIG: Führt separate Durchläufe für Entry/Exit und Long/Short durch!
      """
      logger.info("Optimize Indicators button clicked")

      # 1. Validate: At least one indicator selected
      selected_indicators = [
          ind_type
          for ind_type, cb in self._opt_indicator_checkboxes.items()
          if cb.isChecked()
      ]

      if not selected_indicators:
          QMessageBox.warning(self, "Error", "Please select at least one indicator")
          return

      # 2. Get test type and trade side
      test_type = 'entry' if self._test_type_entry.isChecked() else 'exit'
      trade_side = 'long' if self._trade_side_long.isChecked() else 'short'

      # 3. Build parameter ranges
      parameter_ranges = {
          'RSI': {
              'min_period': self.rsi_min_spin.value(),
              'max_period': self.rsi_max_spin.value(),
              'step': self.rsi_step_spin.value()
          },
          'MACD': {
              'fast_min': self.macd_fast_min_spin.value(),
              'fast_max': self.macd_fast_max_spin.value(),
              'fast_step': self.macd_fast_step_spin.value(),
              # TODO: Add slow and signal ranges (UI currently missing)
              'slow_min': 20,
              'slow_max': 30,
              'slow_step': 2,
              'signal_min': 7,
              'signal_max': 11,
              'signal_step': 2
          },
          'ADX': {
              'min_period': self.adx_min_spin.value(),
              'max_period': self.adx_max_spin.value(),
              'step': self.adx_step_spin.value()
          },
          # TODO: Add BB, SMA, EMA, ATR ranges
      }

      # 4. Get date range (from backtest setup tab)
      start_date = self._bt_start_date.date().toPyDate()
      end_date = self._bt_end_date.date().toPyDate()
      symbol = self._bt_symbol_combo.currentText()

      if start_date >= end_date:
          QMessageBox.warning(self, "Error", "Invalid date range")
          return

      # 5. Get chart data if available
      chart_data = None
      if hasattr(self, '_candles') and self._candles:
          import pandas as pd
          chart_data = pd.DataFrame(self._candles)
          if 'timestamp' in chart_data.columns:
              chart_data['timestamp'] = pd.to_datetime(chart_data['timestamp'])
              chart_data.set_index('timestamp', inplace=True)

      # 6. Disable button, show progress
      self._optimize_btn.setEnabled(False)
      self._optimize_btn.setText(f"⏳ Optimizing ({test_type.title()}/{trade_side.title()})...")
      self._opt_progress.setVisible(True)
      self._opt_progress.setRange(0, 100)
      self._opt_progress.setValue(0)

      # 7. Start optimization worker
      from src.ui.threads.indicator_optimization_worker import IndicatorOptimizationWorker

      self._optimization_worker = IndicatorOptimizationWorker(
          selected_indicators=selected_indicators,
          parameter_ranges=parameter_ranges,
          symbol=symbol,
          start_date=datetime.combine(start_date, datetime.min.time()),
          end_date=datetime.combine(end_date, datetime.max.time()),
          test_type=test_type,
          trade_side=trade_side,
          chart_data=chart_data,
          parent=self
      )

      # Connect signals
      self._optimization_worker.finished.connect(self._on_optimization_finished)
      self._optimization_worker.error.connect(self._on_optimization_error)
      self._optimization_worker.progress.connect(self._on_optimization_progress)

      # Start
      self._optimization_worker.start()
      logger.info(f"Optimization worker started: {test_type}/{trade_side}, "
                  f"{len(selected_indicators)} indicators")

  def _on_optimization_progress(self, current: int, total: int, message: str) -> None:
      """Update optimization progress (Phase 3.2)."""
      logger.debug(f"Optimization progress: {current}/{total} - {message}")

      # Update progress bar
      if total > 0:
          progress_pct = int((current / total) * 100)
          self._opt_progress.setValue(progress_pct)

      # Update status message (if label exists)
      # TODO: Add status label in UI

  def _on_optimization_error(self, error_msg: str) -> None:
      """Handle optimization error (Phase 3.2)."""
      logger.error(f"Optimization error: {error_msg}")

      # Re-enable button
      self._optimize_btn.setEnabled(True)
      self._optimize_btn.setText("🚀 Optimize Indicators")
      self._opt_progress.setVisible(False)

      # Show error
      QMessageBox.critical(self, "Optimization Error", f"Optimization failed:\n{error_msg}")

  def _on_optimization_finished(self, results: List[Dict[str, Any]]) -> None:
      """Handle optimization completion (Phase 3.2)."""
      logger.info(f"Optimization completed: {len(results)} results")

      # Re-enable button
      self._optimize_btn.setEnabled(True)
      self._optimize_btn.setText("🚀 Optimize Indicators")
      self._opt_progress.setVisible(False)

      # Store results
      if not hasattr(self, '_optimization_results'):
          self._optimization_results = []

      # Append to existing results (allows multiple runs)
      self._optimization_results.extend(results)

      # Update results table
      self._update_optimization_results_table(results)

      logger.info(f"Total optimization results stored: {len(self._optimization_results)}")
  ```

**Test-Kriterium:**
1. Button-Click startet Worker
2. Progress wird angezeigt
3. Finished-Handler wird aufgerufen
4. Results werden gespeichert

---

### 3.3 Results Table Update

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 3.3.1:** Results Table finden/erstellen (sollte in `_setup_indicator_optimization_tab()` sein, ca. Line 1260):
  ```python
  # In _setup_indicator_optimization_tab()

  # Results Table (add if missing)
  results_group = QGroupBox("Optimization Results")
  results_layout = QVBoxLayout(results_group)

  self._opt_results_table = QTableWidget()
  self._opt_results_table.setColumnCount(9)
  self._opt_results_table.setHorizontalHeaderLabels([
      "Indicator",
      "Parameters",
      "Test Type",
      "Side",
      "Regime",
      "Score (0-100)",
      "Win Rate",
      "Profit Factor",
      "Trades"
  ])
  self._opt_results_table.setAlternatingRowColors(True)
  self._opt_results_table.setSortingEnabled(True)

  results_layout.addWidget(self._opt_results_table)
  layout.addWidget(results_group)
  ```

- [x] **Task 3.3.2:** Table-Update-Methode implementieren:
  ```python
  def _update_optimization_results_table(self, results: List[Dict[str, Any]]) -> None:
      """Update optimization results table (Phase 3.3).

      Args:
          results: List of optimization result dicts with keys:
              - indicator: str
              - params: Dict
              - test_type: str ('entry' or 'exit')
              - trade_side: str ('long' or 'short')
              - regime: str
              - score: float (0-100)
              - win_rate: float (0-1)
              - profit_factor: float
              - total_trades: int
      """
      logger.info(f"Updating optimization results table with {len(results)} new results")

      # Append results to table (don't clear existing)
      for result in results:
          row = self._opt_results_table.rowCount()
          self._opt_results_table.insertRow(row)

          # Column 0: Indicator
          self._opt_results_table.setItem(row, 0, QTableWidgetItem(result['indicator']))

          # Column 1: Parameters
          params_str = ', '.join([f"{k}={v}" for k, v in result['params'].items()])
          self._opt_results_table.setItem(row, 1, QTableWidgetItem(params_str))

          # Column 2: Test Type
          self._opt_results_table.setItem(row, 2, QTableWidgetItem(result['test_type'].title()))

          # Column 3: Side
          self._opt_results_table.setItem(row, 3, QTableWidgetItem(result['trade_side'].title()))

          # Column 4: Regime
          self._opt_results_table.setItem(row, 4, QTableWidgetItem(result['regime']))

          # Column 5: Score (0-100)
          score = result['score']
          score_item = QTableWidgetItem(f"{score:.2f}")

          # Color-code by score
          if score >= 80:
              score_item.setForeground(Qt.GlobalColor.darkGreen)
          elif score >= 60:
              score_item.setForeground(Qt.GlobalColor.green)
          elif score >= 40:
              score_item.setForeground(QColor('#ff9800'))  # Orange
          else:
              score_item.setForeground(Qt.GlobalColor.red)

          self._opt_results_table.setItem(row, 5, score_item)

          # Column 6: Win Rate
          win_rate = result['win_rate']
          self._opt_results_table.setItem(row, 6, QTableWidgetItem(f"{win_rate:.2%}"))

          # Column 7: Profit Factor
          pf = result['profit_factor']
          pf_item = QTableWidgetItem(f"{pf:.2f}")
          pf_item.setForeground(Qt.GlobalColor.green if pf > 1.0 else Qt.GlobalColor.red)
          self._opt_results_table.setItem(row, 7, pf_item)

          # Column 8: Total Trades
          self._opt_results_table.setItem(row, 8, QTableWidgetItem(
              str(result['total_trades'])
          ))

      # Auto-resize columns
      self._opt_results_table.resizeColumnsToContents()

      # Sort by score (descending) by default
      self._opt_results_table.sortItems(5, Qt.SortOrder.DescendingOrder)

      logger.info(f"Results table now has {self._opt_results_table.rowCount()} rows")
  ```

**Test-Kriterium:**
1. Table wird mit Results gefüllt
2. Score-Spalte ist farbcodiert (grün/orange/rot)
3. Sorting funktioniert
4. Alle Spalten sind sichtbar

---

## 📋 PHASE 4: REGIME SET BUILDER (OPTIONAL)

**Ziel:** UI für Kombination der besten Indikatoren pro Regime
**Geschätzter Aufwand:** 4-6 Stunden
**Priorität:** 🟢 MEDIUM (Erweiterte Funktionalität)

### 4.1 "Create Regime Set" Button hinzufügen

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 4.1.1:** Button in Optimization Tab hinzufügen (nach results table):
  ```python
  # In _setup_indicator_optimization_tab(), nach results table

  # Regime Set Builder Actions
  regime_set_actions_layout = QHBoxLayout()

  self._create_regime_set_btn = QPushButton("📦 Create Regime Set from Top Results")
  self._create_regime_set_btn.setEnabled(False)  # Disabled until results exist
  self._create_regime_set_btn.setStyleSheet(
      "background-color: #3b82f6; color: white; font-weight: bold; padding: 8px;"
  )
  self._create_regime_set_btn.clicked.connect(self._on_create_regime_set_clicked)

  regime_set_actions_layout.addWidget(self._create_regime_set_btn)
  regime_set_actions_layout.addStretch()

  layout.addLayout(regime_set_actions_layout)
  ```

- [x] **Task 4.1.2:** Button in `_on_optimization_finished()` enablen:
  ```python
  # In _on_optimization_finished(), nach Store results

  # Enable regime set builder if results exist
  if len(self._optimization_results) > 0:
      self._create_regime_set_btn.setEnabled(True)
  ```

**Test-Kriterium:**
1. Button wird nach Optimization enabled
2. Button-Click löst Handler aus

---

### 4.2 Regime Set Builder Dialog

**Neue Datei:** `src/ui/dialogs/regime_set_builder_dialog.py`

- [x] **Task 4.2.1:** Dialog-Klasse erstellen:
  ```python
  """
  Regime Set Builder Dialog.

  Allows user to:
  1. Select top N indicators per regime
  2. Adjust indicator weights
  3. Generate JSON config
  4. Run backtest on regime set
  """
  import logging
  from typing import List, Dict, Any

  from PyQt6.QtWidgets import (
      QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel,
      QPushButton, QTableWidget, QTableWidgetItem, QSpinBox,
      QDoubleSpinBox, QMessageBox, QProgressBar
  )
  from PyQt6.QtCore import Qt

  logger = logging.getLogger(__name__)


  class RegimeSetBuilderDialog(QDialog):
      """Dialog for building regime-based indicator sets (Phase 4.2)."""

      def __init__(
          self,
          optimization_results: List[Dict[str, Any]],
          parent=None
      ):
          super().__init__(parent)
          self.optimization_results = optimization_results
          self.regime_set = {}

          self.setWindowTitle("Regime Set Builder")
          self.setMinimumSize(1000, 700)

          self._setup_ui()
          self._populate_regime_sets()

      def _setup_ui(self) -> None:
          """Setup UI (Phase 4.2)."""
          layout = QVBoxLayout(self)

          # Header
          header_label = QLabel(
              "Build regime-specific indicator sets by selecting top performers "
              "for each market regime. Adjust weights to fine-tune strategy."
          )
          header_label.setWordWrap(True)
          layout.addWidget(header_label)

          # Top N Selection
          top_n_group = QGroupBox("Selection Criteria")
          top_n_layout = QHBoxLayout(top_n_group)

          top_n_layout.addWidget(QLabel("Top"))
          self.top_n_spin = QSpinBox()
          self.top_n_spin.setRange(1, 10)
          self.top_n_spin.setValue(3)
          self.top_n_spin.valueChanged.connect(self._populate_regime_sets)
          top_n_layout.addWidget(self.top_n_spin)
          top_n_layout.addWidget(QLabel("indicators per regime"))

          top_n_layout.addStretch()
          layout.addWidget(top_n_group)

          # Regime Sets Table
          regime_sets_group = QGroupBox("Regime-Specific Indicator Sets")
          regime_sets_layout = QVBoxLayout(regime_sets_group)

          self.regime_sets_table = QTableWidget()
          self.regime_sets_table.setColumnCount(6)
          self.regime_sets_table.setHorizontalHeaderLabels([
              "Regime",
              "Rank",
              "Indicator",
              "Parameters",
              "Score",
              "Weight"
          ])
          self.regime_sets_table.setAlternatingRowColors(True)

          regime_sets_layout.addWidget(self.regime_sets_table)
          layout.addWidget(regime_sets_group)

          # Actions
          actions_layout = QHBoxLayout()

          self.generate_json_btn = QPushButton("📝 Generate JSON Config")
          self.generate_json_btn.clicked.connect(self._on_generate_json_clicked)
          actions_layout.addWidget(self.generate_json_btn)

          self.backtest_set_btn = QPushButton("▶️ Backtest Regime Set")
          self.backtest_set_btn.clicked.connect(self._on_backtest_set_clicked)
          actions_layout.addWidget(self.backtest_set_btn)

          actions_layout.addStretch()

          self.close_btn = QPushButton("Close")
          self.close_btn.clicked.connect(self.close)
          actions_layout.addWidget(self.close_btn)

          layout.addLayout(actions_layout)

          # Progress bar (hidden by default)
          self.progress = QProgressBar()
          self.progress.setVisible(False)
          layout.addWidget(self.progress)

      def _populate_regime_sets(self) -> None:
          """Populate table with top N indicators per regime (Phase 4.2)."""
          top_n = self.top_n_spin.value()

          # Group results by regime
          regime_groups = {}
          for result in self.optimization_results:
              regime = result['regime']
              if regime not in regime_groups:
                  regime_groups[regime] = []
              regime_groups[regime].append(result)

          # Sort each regime group by score (descending)
          for regime in regime_groups:
              regime_groups[regime].sort(key=lambda x: x['score'], reverse=True)

          # Populate table
          self.regime_sets_table.setRowCount(0)

          for regime, results in regime_groups.items():
              # Take top N
              top_results = results[:top_n]

              # Calculate weights (normalize scores)
              total_score = sum(r['score'] for r in top_results)

              for rank, result in enumerate(top_results, 1):
                  row = self.regime_sets_table.rowCount()
                  self.regime_sets_table.insertRow(row)

                  # Column 0: Regime
                  self.regime_sets_table.setItem(row, 0, QTableWidgetItem(regime))

                  # Column 1: Rank
                  self.regime_sets_table.setItem(row, 1, QTableWidgetItem(str(rank)))

                  # Column 2: Indicator
                  self.regime_sets_table.setItem(row, 2, QTableWidgetItem(result['indicator']))

                  # Column 3: Parameters
                  params_str = ', '.join([f"{k}={v}" for k, v in result['params'].items()])
                  self.regime_sets_table.setItem(row, 3, QTableWidgetItem(params_str))

                  # Column 4: Score
                  self.regime_sets_table.setItem(row, 4, QTableWidgetItem(f"{result['score']:.2f}"))

                  # Column 5: Weight (editable)
                  weight = result['score'] / total_score if total_score > 0 else 0
                  weight_spin = QDoubleSpinBox()
                  weight_spin.setRange(0.0, 1.0)
                  weight_spin.setSingleStep(0.05)
                  weight_spin.setValue(weight)
                  weight_spin.setDecimals(3)
                  self.regime_sets_table.setCellWidget(row, 5, weight_spin)

          self.regime_sets_table.resizeColumnsToContents()

          logger.info(f"Populated regime sets table with {len(regime_groups)} regimes, "
                      f"top {top_n} each")

      def _on_generate_json_clicked(self) -> None:
          """Generate JSON config from regime sets (Phase 4.2)."""
          # TODO: Implement JSON generation
          QMessageBox.information(
              self,
              "Not Implemented",
              "JSON config generation will be implemented in Phase 4.3"
          )

      def _on_backtest_set_clicked(self) -> None:
          """Run backtest on regime set (Phase 4.2)."""
          # TODO: Implement regime set backtesting
          QMessageBox.information(
              self,
              "Not Implemented",
              "Regime set backtesting will be implemented in Phase 4.4"
          )
  ```

**Test-Kriterium:**
1. Dialog öffnet sich
2. Table zeigt Top N Indikatoren pro Regime
3. Weights sind editierbar
4. Buttons vorhanden (noch nicht funktional)

---

### 4.3 Dialog Integration

**Datei:** `src/ui/dialogs/entry_analyzer_popup.py`

- [x] **Task 4.3.1:** Dialog-Import hinzufügen:
  ```python
  # At top of file
  from src.ui.dialogs.regime_set_builder_dialog import RegimeSetBuilderDialog
  ```

- [x] **Task 4.3.2:** Handler implementieren:
  ```python
  def _on_create_regime_set_clicked(self) -> None:
      """Open Regime Set Builder Dialog (Phase 4.3)."""
      if not hasattr(self, '_optimization_results') or not self._optimization_results:
          QMessageBox.warning(
              self,
              "No Results",
              "Please run indicator optimization first"
          )
          return

      logger.info("Opening Regime Set Builder Dialog")

      # Open dialog
      dialog = RegimeSetBuilderDialog(
          optimization_results=self._optimization_results,
          parent=self
      )
      dialog.exec()
  ```

**Test-Kriterium:**
1. Button öffnet Dialog
2. Dialog zeigt Optimization-Results
3. Dialog kann geschlossen werden

---

## 🎯 ZEITSCHÄTZUNG & PRIORISIERUNG

### MVP (Minimum Viable Product) - 8-10 Stunden

**MUSS implementiert werden:**
1. ✅ **Phase 1.1-1.3:** Backtest-Button Verdrahtung (2-3h)
2. ✅ **Phase 2.1-2.3:** Regime-Visualisierung (3-4h)
3. ✅ **Phase 3.1-3.3:** Indicator Optimization Worker (4-5h)

**Ergebnis nach MVP:**
- ✅ Backtest läuft und zeigt Ergebnisse
- ✅ Regime-Grenzen werden im Chart visualisiert
- ✅ Indikatoren können mit verschiedenen Parametern getestet werden
- ✅ Scoring-System (0-100) pro Regime funktioniert
- ✅ Separate Durchläufe für Entry/Exit und Long/Short

---

### COMPLETE (Vollständig) - 12-16 Stunden

**Zusätzlich zum MVP:**
4. ✅ **Phase 4.1-4.3:** Regime Set Builder UI (4-6h)

**Ergebnis nach COMPLETE:**
- ✅ Alle MVP-Features
- ✅ Regime-Sets können erstellt werden
- ✅ Top N Indikatoren pro Regime selektierbar
- ✅ Gewichtungen anpassbar

---

## ✅ VERIFIKATIONS-CHECKLISTE

Nach jeder Phase durchführen:

### Phase 1 Verifikation: Backtest

- [x] Run Backtest Button ist klickbar
- [x] Button startet BacktestWorker
- [x] Progress-Bar wird angezeigt während Laufzeit
- [x] Button wird disabled während Laufzeit
- [x] Nach Completion: Results Tab öffnet sich automatisch
- [x] Performance Summary zeigt alle Metriken
- [x] Trade List ist vollständig gefüllt
- [x] Positive/Negative PnL haben korrekte Farben
- [x] Regime-Breakdown wird angezeigt

**Test-Kommando:**
```python
# In Entry Analyzer:
1. JSON Config auswählen: "03_JSON/Trading_Bot/trend_following_conservative.json"
2. Symbol: BTCUSDT
3. Date Range: 2024-01-01 bis 2024-12-31
4. Capital: 10000
5. Run Backtest klicken
6. Erwartung: Results Tab öffnet, Performance Summary + Trade List gefüllt
```

---

### Phase 2 Verifikation: Regime-Visualisierung

- [x] Nach Backtest: Regime-Lines erscheinen im Chart
- [x] Vertikale Linien sind sichtbar
- [x] Farben entsprechen Regime-Typen:
  - Grün für Trend Up
  - Rot für Trend Down
  - Orange für Range
  - Blau für Breakout
- [x] Lines können mit `clear_regime_lines()` entfernt werden
- [x] Toggle-Button funktioniert (falls implementiert)

**Test-Kommando:**
```python
# Nach Backtest abgeschlossen:
1. Wechsle zu Chart-Fenster
2. Prüfe: Vertikale Linien sichtbar?
3. Prüfe: Farben korrekt?
4. Klicke "Clear Regime Lines" (falls Button vorhanden)
5. Erwartung: Lines verschwinden
```

---

### Phase 3 Verifikation: Indicator Optimization

- [x] Indicator Selection Checkboxes funktionieren
- [x] Test Type Radio Buttons (Entry/Exit) funktionieren
- [x] Trade Side Radio Buttons (Long/Short) funktionieren
- [x] Parameter Range Inputs sind editierbar
- [x] Optimize Button startet Worker
- [x] Progress wird angezeigt (X/Total)
- [x] Results Table wird gefüllt
- [x] Scores liegen zwischen 0-100
- [x] Score-Spalte ist farbcodiert
- [x] Sorting funktioniert
- [x] Mehrere Durchläufe möglich (Results werden angehängt)

**Test-Kommando:**
```python
# In Entry Analyzer, Tab "Indicator Optimization":
1. Wähle: RSI, MACD, ADX
2. Test Type: Entry
3. Trade Side: Long
4. RSI Range: 10-20, Step 2
5. MACD Fast: 8-16, Step 2
6. ADX Range: 10-20, Step 2
7. Klicke "Optimize Indicators"
8. Erwartung: Progress-Bar läuft, Results Table wird gefüllt
9. Wiederhole mit: Test Type: Exit, Trade Side: Short
10. Erwartung: Neue Results werden angehängt
```

---

### Phase 4 Verifikation: Regime Set Builder

- [x] "Create Regime Set" Button wird enabled nach Optimization
- [x] Dialog öffnet sich
- [x] Table zeigt Top N Indikatoren pro Regime
- [x] Top N Spinner funktioniert (Table aktualisiert sich)
- [x] Weight-Spalte ist editierbar
- [x] Weights summieren sich zu ~1.0 pro Regime
- [x] "Generate JSON Config" Button vorhanden (Placeholder OK)
- [x] "Backtest Regime Set" Button vorhanden (Placeholder OK)

**Test-Kommando:**
```python
# Nach Indicator Optimization abgeschlossen:
1. Klicke "Create Regime Set from Top Results"
2. Dialog öffnet sich
3. Top N = 3 setzen
4. Erwartung: Für jedes Regime werden 3 beste Indikatoren angezeigt
5. Ändere Weight-Werte
6. Erwartung: Werte bleiben erhalten
```

---

## 🚨 KRITISCHE ABHÄNGIGKEITEN

### Code-Abhängigkeiten

1. **BacktestEngine** muss `regime_history` zurückgeben
   - Location: `src/backtesting/engine.py`
   - Required: `regime_history: List[Dict]` in results

2. **ConfigLoader** muss funktionieren
   - Location: `src/core/tradingbot/config/loader.py`
   - Required: `load_config(path)` returns `TradingBotConfig`

3. **RegimeEngine** sollte existieren (optional, für Live-Regime-Detection)
   - Location: `src/core/tradingbot/regime_engine.py`
   - Required: `classify(features)` returns `RegimeState`

4. **Chart Widget** muss plotWidget oder chart_widget haben
   - Location: `src/ui/widgets/compact_chart_widget.py` oder `chart_window_setup.py`
   - Required: `addItem()`, `removeItem()` Methoden

### Daten-Abhängigkeiten

1. **Historische Marktdaten** müssen verfügbar sein
   - Via SQLite: `data/orderpilot.db`
   - Via Bitunix API: Live-Fetching

2. **JSON-Configs** müssen im korrekten Format sein
   - Location: `03_JSON/Trading_Bot/*.json`
   - Required: Schema-Version 1.0.0

---

## 📝 NEXT STEPS (Nach Implementierung)

### Erweiterte Features (Nice-to-Have)

- [x] **Export Results:** CSV/Excel Export der Optimization-Results
- [x] **Multi-Symbol Optimization:** Parallele Optimization über mehrere Symbole
- [x] **Walk-Forward Analysis:** Für Regime-Sets
- [x] **Regime Transition Matrix:** Visualisierung von Regime-Wechseln
- [x] **Auto-Parameter Tuning:** Genetische Algorithmen für Parameter-Optimierung
- [x] **Regime Prediction:** ML-basierte Vorhersage des nächsten Regimes

---

## 🎯 ZUSAMMENFASSUNG

**Was wird implementiert:**
1. ✅ Backtest-Button → BacktestEngine Verdrahtung
2. ✅ Regime-Visualisierung mit vertikalen Linien im Chart
3. ✅ Indicator Optimization mit Parameter-Testing
4. ✅ Scoring-System (0-100) basierend auf Win Rate + Profit Factor
5. ✅ **Separate Durchläufe für Entry/Exit und Long/Short**
6. ✅ Results Table mit farbcodierten Scores
7. ✅ Regime Set Builder für Top-Indikatoren-Kombination

**Geschätzter Aufwand:**
- **MVP (Phase 1-3):** 8-10 Stunden
- **Complete (Phase 1-4):** 12-16 Stunden

**Backend-Status:**
- ✅ 60-70% bereits implementiert (RegimeEngine, BacktestEngine, JSON-System)
- ❌ 30-40% fehlt (UI-Verdrahtung, Worker-Threads, Visualisierung)

**Kritischer Pfad:**
Phase 1 → Phase 2 → Phase 3 → (Phase 4 optional)

---

**Letzte Aktualisierung:** 2026-01-19
**Nächster Schritt:** Phase 1.1 - Backtest-Button Signal/Slot Connection
