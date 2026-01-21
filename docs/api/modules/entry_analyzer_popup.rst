Entry Analyzer Popup
====================

.. automodule:: src.ui.dialogs.entry_analyzer_popup
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``EntryAnalyzerPopup`` is a comprehensive dialog for analyzing trading entries and strategies:

* **Backtest Setup**: JSON config selection, date range, capital settings
* **Visible Range Analysis**: Entry analysis for current chart view
* **Backtest Results**: Performance metrics, trade list, equity curve
* **AI Copilot**: LLM-powered entry recommendations and insights
* **Validation**: Walk-forward validation for out-of-sample testing

Key Features
------------

**Multi-Tab Interface:**
   5 tabs for different analysis workflows (Setup, Analysis, Results, AI, Validation).

**Background Processing:**
   QThread workers for non-blocking analysis (backtest, AI copilot, validation).

**JSON-Based Backtesting:**
   Integrates with BacktestEngine for regime-based strategy testing.

**AI Integration:**
   Async LLM analysis for entry quality assessment and recommendations.

**Comprehensive Results:**
   Performance stats, trade breakdown, regime transitions, equity curve.

Usage Example
-------------

.. code-block:: python

    from src.ui.dialogs.entry_analyzer_popup import EntryAnalyzerPopup
    from PyQt6.QtWidgets import QApplication
    import pandas as pd

    # 1. Create Qt application
    app = QApplication([])

    # 2. Prepare chart data
    chart_data = pd.DataFrame({
        'timestamp': [...],
        'open': [...],
        'high': [...],
        'low': [...],
        'close': [...],
        'volume': [...]
    })

    # 3. Create Entry Analyzer popup
    popup = EntryAnalyzerPopup(
        candles=chart_data,
        symbol='BTCUSD',
        timeframe='1h'
    )

    # 4. Show popup
    popup.show()

    # 5. Run application
    app.exec()

Classes
-------

.. autoclass:: src.ui.dialogs.entry_analyzer_popup.EntryAnalyzerPopup
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Worker Classes
--------------

CopilotWorker
~~~~~~~~~~~~~

.. autoclass:: src.ui.dialogs.entry_analyzer_popup.CopilotWorker
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Background worker for AI Copilot analysis.

**Signals:**

.. code-block:: python

    finished = pyqtSignal(object)  # CopilotResponse
    error = pyqtSignal(str)

**Example:**

.. code-block:: python

    worker = CopilotWorker(
        analysis=analysis_result,
        symbol='BTCUSD',
        timeframe='1h',
        validation=validation_result
    )

    worker.finished.connect(lambda response: print(f"AI says: {response.recommendation}"))
    worker.error.connect(lambda err: print(f"Error: {err}"))

    worker.start()

ValidationWorker
~~~~~~~~~~~~~~~~

.. autoclass:: src.ui.dialogs.entry_analyzer_popup.ValidationWorker
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Background worker for walk-forward validation.

**Signals:**

.. code-block:: python

    finished = pyqtSignal(object)  # ValidationResult
    error = pyqtSignal(str)

**Example:**

.. code-block:: python

    worker = ValidationWorker(
        analysis=analysis_result,
        candles=chart_data
    )

    worker.finished.connect(lambda result: print(f"OOS Sharpe: {result.oos_sharpe:.2f}"))
    worker.error.connect(lambda err: print(f"Validation failed: {err}"))

    worker.start()

BacktestWorker
~~~~~~~~~~~~~~

.. autoclass:: src.ui.dialogs.entry_analyzer_popup.BacktestWorker
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Background worker for full history backtesting.

**Signals:**

.. code-block:: python

    finished = pyqtSignal(object)  # Dict[str, Any] stats
    error = pyqtSignal(str)
    progress = pyqtSignal(str)  # Progress message

**Example:**

.. code-block:: python

    worker = BacktestWorker(
        config_path='strategy.json',
        symbol='BTCUSD',
        start_date=datetime(2024, 1, 1),
        end_date=datetime(2024, 12, 31),
        initial_capital=10000.0,
        chart_data=df,
        data_timeframe='1h'
    )

    worker.progress.connect(lambda msg: print(f"[{datetime.now()}] {msg}"))
    worker.finished.connect(lambda stats: print(f"Sharpe: {stats['sharpe']:.2f}"))
    worker.error.connect(lambda err: print(f"Backtest failed: {err}"))

    worker.start()

Tab Workflows
-------------

Backtest Setup Tab
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Workflow 1: JSON Config Selection and Backtest Execution

    # 1. Select JSON strategy config
    popup.json_file_input.setText('strategy.json')

    # 2. Set date range
    popup.start_date_edit.setDate(QDate(2024, 1, 1))
    popup.end_date_edit.setDate(QDate(2024, 12, 31))

    # 3. Set capital
    popup.capital_spin.setValue(10000.0)

    # 4. Select symbol (auto-filled from chart)
    popup.symbol_combo.setCurrentText('BTCUSD')

    # 5. Click "Run Backtest" button
    # → Starts BacktestWorker in background
    # → Shows progress bar with status updates
    # → Switches to Results tab when complete

**JSON Config Selection:**

.. code-block:: python

    def _on_browse_json_clicked(self):
        # Open file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Strategy JSON Config",
            "03_JSON/Trading_Bot/",
            "JSON Files (*.json)"
        )

        if file_path:
            # Validate JSON structure
            try:
                with open(file_path, 'r') as f:
                    config_data = json.load(f)

                # Check required fields
                required = ['indicators', 'regimes', 'strategies', 'routing']
                if all(field in config_data for field in required):
                    self.json_file_input.setText(file_path)
                    self._load_config_preview(config_data)
                else:
                    QMessageBox.warning(self, "Invalid Config", "Missing required fields")

            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load config: {e}")

Visible Range Analysis Tab
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Workflow 2: Analyze Current Chart View

    # 1. Switch to "Visible Range Analysis" tab
    popup.tab_widget.setCurrentIndex(1)

    # 2. Click "🔄 Analyze Visible Range" button
    # → Extracts visible candles from chart
    # → Runs entry analysis on visible data
    # → Displays results in table

    # 3. Review entry signals
    # → Entry time, price, score, regime, confidence
    # → Filter by score threshold
    # → Sort by entry quality

    # 4. Click "📍 Draw on Chart" button
    # → Draws entry markers on chart
    # → Color-coded by score (green=high, yellow=medium, red=low)

**Entry Analysis Display:**

.. code-block:: python

    def _display_analysis_results(self, analysis):
        # Populate entry table
        self.entry_table.setRowCount(len(analysis.entries))

        for row, entry in enumerate(analysis.entries):
            # Entry time
            time_item = QTableWidgetItem(entry.timestamp.strftime('%Y-%m-%d %H:%M'))
            self.entry_table.setItem(row, 0, time_item)

            # Entry price
            price_item = QTableWidgetItem(f"{entry.price:.2f}")
            self.entry_table.setItem(row, 1, price_item)

            # Entry score (color-coded)
            score_item = QTableWidgetItem(f"{entry.score:.2f}")
            if entry.score >= 0.7:
                score_item.setBackground(QBrush(QColor('#26a69a')))  # Green
            elif entry.score >= 0.5:
                score_item.setBackground(QBrush(QColor('#ffa726')))  # Orange
            else:
                score_item.setBackground(QBrush(QColor('#ef5350')))  # Red
            self.entry_table.setItem(row, 2, score_item)

            # Regime
            regime_item = QTableWidgetItem(entry.regime)
            self.entry_table.setItem(row, 3, regime_item)

            # Confidence
            confidence_item = QTableWidgetItem(f"{entry.confidence:.2%}")
            self.entry_table.setItem(row, 4, confidence_item)

Backtest Results Tab
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # Workflow 3: Review Backtest Performance

    # 1. After backtest completes, switch to Results tab
    popup.tab_widget.setCurrentIndex(2)

    # 2. Review performance metrics
    # → Net Profit, Win Rate, Profit Factor
    # → Sharpe Ratio, Max Drawdown, Total Trades

    # 3. Analyze trade breakdown
    # → List of all trades with entry/exit details
    # → Profit/loss per trade
    # → Regime at entry

    # 4. View regime transitions
    # → Timeline of regime changes during backtest
    # → Correlation with performance

    # 5. Export results
    # → Click "📄 Generate Report" button
    # → Save detailed report to PDF/HTML

**Performance Metrics Display:**

.. code-block:: python

    def _display_backtest_results(self, results):
        # Performance summary
        self.net_profit_label.setText(f"${results['net_profit']:,.2f}")
        self.win_rate_label.setText(f"{results['win_rate']:.2%}")
        self.profit_factor_label.setText(f"{results['profit_factor']:.2f}")
        self.sharpe_label.setText(f"{results['sharpe']:.2f}")
        self.max_dd_label.setText(f"{results['max_dd']:.2%}")
        self.total_trades_label.setText(f"{results['total_trades']}")

        # Color-code metrics
        if results['sharpe'] >= 2.0:
            self.sharpe_label.setStyleSheet("color: #26a69a; font-weight: bold;")
        elif results['sharpe'] >= 1.0:
            self.sharpe_label.setStyleSheet("color: #ffa726;")
        else:
            self.sharpe_label.setStyleSheet("color: #ef5350;")

        # Trade list
        self.trade_table.setRowCount(len(results['trades']))
        for row, trade in enumerate(results['trades']):
            # ... populate trade details

        # Equity curve chart (if matplotlib available)
        self._plot_equity_curve(results['equity_curve'])

AI Copilot Tab
~~~~~~~~~~~~~~

.. code-block:: python

    # Workflow 4: Get AI Insights

    # 1. Run analysis on Visible Range or Backtest
    # → Analysis results are stored internally

    # 2. Switch to "AI Copilot" tab
    popup.tab_widget.setCurrentIndex(3)

    # 3. Click "🤖 Get AI Analysis" button
    # → Starts CopilotWorker in background
    # → Shows loading spinner

    # 4. Review AI recommendations
    # → Entry quality assessment
    # → Pattern recognition insights
    # → Risk recommendations
    # → Strategy improvements

**AI Copilot Display:**

.. code-block:: python

    def _display_copilot_response(self, response):
        # Overall assessment
        self.assessment_text.setText(response.assessment)

        # Entry recommendations
        recommendations_html = "<ul>"
        for rec in response.recommendations:
            recommendations_html += f"<li>{rec}</li>"
        recommendations_html += "</ul>"
        self.recommendations_text.setHtml(recommendations_html)

        # Risk warnings
        if response.warnings:
            warnings_html = "<div style='color: #ef5350;'><b>⚠ Warnings:</b><ul>"
            for warning in response.warnings:
                warnings_html += f"<li>{warning}</li>"
            warnings_html += "</ul></div>"
            self.warnings_text.setHtml(warnings_html)

        # Suggested improvements
        improvements_html = "<ol>"
        for improvement in response.improvements:
            improvements_html += f"<li>{improvement}</li>"
        improvements_html += "</ol>"
        self.improvements_text.setHtml(improvements_html)

Validation Tab
~~~~~~~~~~~~~~

.. code-block:: python

    # Workflow 5: Walk-Forward Validation

    # 1. Run analysis on Visible Range
    # → Need historical data for validation

    # 2. Switch to "Validation" tab
    popup.tab_widget.setCurrentIndex(4)

    # 3. Configure validation settings
    popup.train_days_spin.setValue(180)  # Training period
    popup.test_days_spin.setValue(60)    # Testing period

    # 4. Click "🔍 Run Validation" button
    # → Starts ValidationWorker in background
    # → Performs walk-forward analysis

    # 5. Review results
    # → In-sample (IS) metrics
    # → Out-of-sample (OOS) metrics
    # → Degradation percentage
    # → Robustness gate pass/fail

**Validation Results Display:**

.. code-block:: python

    def _display_validation_results(self, result):
        # In-sample metrics
        self.is_sharpe_label.setText(f"{result.in_sample_sharpe:.2f}")
        self.is_win_rate_label.setText(f"{result.in_sample_win_rate:.2%}")

        # Out-of-sample metrics
        self.oos_sharpe_label.setText(f"{result.oos_sharpe:.2f}")
        self.oos_win_rate_label.setText(f"{result.oos_win_rate:.2%}")

        # Degradation
        degradation = (result.in_sample_sharpe - result.oos_sharpe) / result.in_sample_sharpe
        self.degradation_label.setText(f"{degradation:.2%}")

        # Color-code degradation
        if degradation <= 0.20:  # <20% degradation
            self.degradation_label.setStyleSheet("color: #26a69a;")
        elif degradation <= 0.30:  # 20-30% degradation
            self.degradation_label.setStyleSheet("color: #ffa726;")
        else:  # >30% degradation
            self.degradation_label.setStyleSheet("color: #ef5350;")

        # Robustness gate
        passes_gate = result.passes_robustness_gate
        self.robustness_label.setText("✅ PASS" if passes_gate else "❌ FAIL")
        self.robustness_label.setStyleSheet(
            "color: #26a69a;" if passes_gate else "color: #ef5350;"
        )

Common Patterns
---------------

**Pattern 1: Quick Backtest Workflow**

.. code-block:: python

    # Load popup with pre-configured settings
    popup = EntryAnalyzerPopup(
        candles=chart_data,
        symbol='BTCUSD',
        timeframe='1h',
        auto_load_config='strategy.json'
    )

    # Connect to result signal
    popup.backtest_finished.connect(
        lambda results: print(f"Sharpe: {results['sharpe']:.2f}")
    )

    # Auto-run backtest on show
    popup.show()
    popup.run_backtest_automatically()

**Pattern 2: AI-Assisted Strategy Development**

.. code-block:: python

    # 1. Analyze visible range
    popup.analyze_visible_range()

    # 2. Get AI recommendations
    popup.run_ai_copilot()

    # 3. Wait for AI response
    def on_ai_response(response):
        # Apply AI suggestions to config
        if "increase RSI period to 21" in response.improvements:
            update_config_parameter('rsi_period', 21)

        # Re-run backtest with improvements
        popup.run_backtest()

    popup.copilot_finished.connect(on_ai_response)

**Pattern 3: Validation-Driven Optimization**

.. code-block:: python

    # Iterate through parameter combinations
    for rsi_period in [10, 14, 18, 21]:
        # Update config
        config['indicators'][0]['params']['period'] = rsi_period

        # Run backtest
        backtest_results = popup.run_backtest_sync(config)

        # Validate with walk-forward
        validation_results = popup.run_validation_sync()

        # Check if passes robustness
        if validation_results.passes_robustness_gate:
            print(f"✅ RSI {rsi_period}: OOS Sharpe = {validation_results.oos_sharpe:.2f}")
        else:
            print(f"❌ RSI {rsi_period}: Failed robustness gate")

Best Practices
--------------

**1. Always Use Walk-Forward Validation:**

.. code-block:: python

    # ✅ Good: Validate after backtest
    backtest_results = popup.run_backtest()
    validation_results = popup.run_validation()

    if validation_results.passes_robustness_gate:
        print("Strategy is robust")
    else:
        print("Strategy overfitted - adjust parameters")

    # ❌ Bad: Trust backtest alone
    backtest_results = popup.run_backtest()
    if backtest_results['sharpe'] > 2.0:
        deploy_strategy()  # May be overfitted!

**2. Use AI Copilot for Insights, Not Blind Trust:**

.. code-block:: python

    # ✅ Good: Use AI as assistant
    ai_response = popup.get_ai_analysis()

    # Review recommendations
    for recommendation in ai_response.recommendations:
        print(f"AI suggests: {recommendation}")
        # Human decides whether to implement

    # ❌ Bad: Blindly apply AI suggestions
    ai_response = popup.get_ai_analysis()
    for improvement in ai_response.improvements:
        apply_improvement(improvement)  # No human review!

**3. Set Realistic Date Ranges:**

.. code-block:: python

    # ✅ Good: Use sufficient historical data
    popup.set_date_range(
        start=datetime(2023, 1, 1),  # 2 years of data
        end=datetime(2024, 12, 31)
    )

    # ❌ Bad: Too little data
    popup.set_date_range(
        start=datetime(2024, 11, 1),  # Only 2 months
        end=datetime(2024, 12, 31)
    )  # Not enough for validation!

**4. Monitor Background Workers:**

.. code-block:: python

    # ✅ Good: Handle worker errors
    worker = BacktestWorker(...)
    worker.error.connect(lambda err: QMessageBox.critical(popup, "Error", err))
    worker.finished.connect(popup._on_backtest_finished)
    worker.start()

    # ❌ Bad: No error handling
    worker = BacktestWorker(...)
    worker.start()  # If it fails, no feedback!

See Also
--------

* :doc:`backtest_engine` - BacktestEngine used for backtesting
* :doc:`strategy_evaluator` - Walk-forward validation implementation
* :doc:`strategy_generator` - AI-powered strategy generation (AI Copilot backend)
* :doc:`config_loader` - JSON config loading and validation
