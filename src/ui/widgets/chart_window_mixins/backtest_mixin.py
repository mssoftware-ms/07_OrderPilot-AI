"""Backtest Mixin for ChartWindow.

Contains backtest execution, visualization, and optimization methods.
"""

import json
import logging
from datetime import datetime
from decimal import Decimal

import pandas as pd
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QProgressDialog, QTableWidgetItem

logger = logging.getLogger(__name__)


class BacktestMixin:
    """Mixin providing backtest functionality for ChartWindow."""

    def _apply_strategy(self):
        """Apply selected strategy to chart - simple visualization without backtrader."""
        from src.core.indicators.engine import IndicatorConfig, IndicatorEngine, IndicatorType

        strategy_name = self.strategy_combo.currentText()
        logger.info(f"Applying strategy: {strategy_name} to chart {self.symbol}")

        try:
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
                QMessageBox.warning(self, "No Data", "Please load chart data first.")
                return

            chart_data = self.chart_widget.data.copy()
            logger.info(f"Analyzing {len(chart_data)} bars with strategy: {strategy_name}")

            # Get strategy parameters from UI
            stop_loss_pct = self.stop_loss.value() / 100
            take_profit_pct = self.take_profit.value() / 100

            # Calculate indicators based on strategy type
            indicator_engine = IndicatorEngine()
            signals = []

            # Normalize strategy name for matching (case-insensitive)
            strategy_lower = strategy_name.lower()
            detected_type = "Unknown"

            # Detect strategy type from name
            if "bollinger" in strategy_lower or "bb" in strategy_lower or "mean reversion" in strategy_lower:
                detected_type = "Bollinger Bands"
                logger.info(f"🎯 Detected Bollinger/Mean Reversion strategy")
                signals = self._generate_bollinger_signals(chart_data, indicator_engine, period=20)
            elif "rsi" in strategy_lower and "macd" in strategy_lower:
                detected_type = "RSI+MACD Combo"
                logger.info(f"🎯 Detected RSI+MACD combo strategy")
                # Combo: Use RSI signals (can be extended to combine both)
                signals = self._generate_rsi_signals(chart_data, indicator_engine, period=14)
            elif "rsi" in strategy_lower:
                detected_type = "RSI"
                logger.info(f"🎯 Detected RSI strategy")
                signals = self._generate_rsi_signals(chart_data, indicator_engine, period=14)
            elif "macd" in strategy_lower:
                detected_type = "MACD"
                logger.info(f"🎯 Detected MACD strategy")
                signals = self._generate_macd_signals(
                    chart_data, indicator_engine,
                    fast=self.fast_period.value(),
                    slow=self.slow_period.value(),
                    signal=self.signal_period.value()
                )
            elif "sma" in strategy_lower or "moving average" in strategy_lower or "crossover" in strategy_lower:
                detected_type = "SMA Crossover"
                logger.info(f"🎯 Detected Moving Average/Crossover strategy")
                signals = self._generate_ma_signals(
                    chart_data, indicator_engine,
                    fast=self.fast_period.value(),
                    slow=self.slow_period.value()
                )
            elif "momentum" in strategy_lower:
                detected_type = "Momentum (MACD)"
                logger.info(f"🎯 Detected Momentum strategy - using MACD")
                signals = self._generate_macd_signals(chart_data, indicator_engine, 12, 26, 9)
            elif "breakout" in strategy_lower or "volatility" in strategy_lower:
                detected_type = "Breakout (Bollinger)"
                logger.info(f"🎯 Detected Breakout/Volatility strategy - using Bollinger")
                signals = self._generate_bollinger_signals(chart_data, indicator_engine, period=20)
            else:
                # Default: Use MACD
                detected_type = "Default (MACD)"
                logger.info(f"⚠️ No specific strategy detected, using default MACD")
                signals = self._generate_macd_signals(chart_data, indicator_engine, 12, 26, 9)

            logger.info(f"📊 Strategy type: {detected_type} | Generated {len(signals)} signals")

            if not signals:
                QMessageBox.information(self, "No Signals", "No trading signals found with this strategy.")
                return

            # Simulate trades with SL/TP
            trades = self._simulate_trades(chart_data, signals, stop_loss_pct, take_profit_pct)

            # Clear existing markers
            if hasattr(self.chart_widget, '_execute_js'):
                self.chart_widget._execute_js("window.chartAPI.clearMarkers();")

            # Draw markers on chart
            self._draw_strategy_markers(trades)

            # Calculate statistics
            stats = self._calculate_trade_stats(trades)

            # Show results
            msg = (f"{detected_type}: {len(trades)} trades | "
                   f"Wins: {stats['wins']} | Losses: {stats['losses']} | "
                   f"Win Rate: {stats['win_rate']:.1f}%")
            logger.info(msg)

            if hasattr(self.chart_widget, 'market_status_label'):
                color = "#28a745" if stats['win_rate'] >= 50 else "#dc3545"
                self.chart_widget.market_status_label.setText(msg)
                self.chart_widget.market_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

            # Update results tab
            self._display_strategy_results(stats, strategy_name)

            # AI Analysis if enabled
            if hasattr(self, 'enable_ai_analysis') and self.enable_ai_analysis.isChecked():
                strategy_params = {
                    'stop_loss_pct': stop_loss_pct * 100,
                    'take_profit_pct': take_profit_pct * 100,
                    'position_size_pct': self.position_size.value() if hasattr(self, 'position_size') else 10
                }
                # Run AI analysis asynchronously
                self._run_ai_strategy_analysis(
                    strategy_name, detected_type, self.symbol,
                    trades, stats, strategy_params
                )

        except Exception as e:
            logger.error(f"Failed to apply strategy: {e}", exc_info=True)
            QMessageBox.warning(self, "Strategy Error", f"Failed to apply strategy:\n{e}")

    def _generate_macd_signals(self, data, engine, fast, slow, signal):
        """Generate buy/sell signals from MACD crossover."""
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        config = IndicatorConfig(
            indicator_type=IndicatorType.MACD,
            params={'fast': fast, 'slow': slow, 'signal': signal}
        )
        result = engine.calculate(data, config)

        signals = []
        macd_col = [c for c in result.values.columns if 'MACD_' in c and 'MACDh' not in c and 'MACDs' not in c][0]
        signal_col = [c for c in result.values.columns if 'MACDs' in c][0]

        macd = result.values[macd_col]
        signal_line = result.values[signal_col]

        for i in range(1, len(macd)):
            if pd.isna(macd.iloc[i]) or pd.isna(signal_line.iloc[i]):
                continue
            if pd.isna(macd.iloc[i-1]) or pd.isna(signal_line.iloc[i-1]):
                continue

            # MACD crosses above signal line = BUY
            if macd.iloc[i-1] < signal_line.iloc[i-1] and macd.iloc[i] > signal_line.iloc[i]:
                signals.append({
                    'time': data.index[i],
                    'type': 'BUY',
                    'price': float(data['close'].iloc[i])
                })
            # MACD crosses below signal line = SELL
            elif macd.iloc[i-1] > signal_line.iloc[i-1] and macd.iloc[i] < signal_line.iloc[i]:
                signals.append({
                    'time': data.index[i],
                    'type': 'SELL',
                    'price': float(data['close'].iloc[i])
                })

        logger.info(f"MACD signals generated: {len(signals)}")
        return signals

    def _generate_rsi_signals(self, data, engine, period):
        """Generate buy/sell signals from RSI overbought/oversold."""
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        config = IndicatorConfig(indicator_type=IndicatorType.RSI, params={'period': period})
        result = engine.calculate(data, config)
        rsi = result.values

        signals = []
        oversold = 30
        overbought = 70

        for i in range(1, len(rsi)):
            if pd.isna(rsi.iloc[i]) or pd.isna(rsi.iloc[i-1]):
                continue

            # RSI crosses above oversold = BUY
            if rsi.iloc[i-1] < oversold and rsi.iloc[i] >= oversold:
                signals.append({
                    'time': data.index[i],
                    'type': 'BUY',
                    'price': float(data['close'].iloc[i])
                })
            # RSI crosses below overbought = SELL
            elif rsi.iloc[i-1] > overbought and rsi.iloc[i] <= overbought:
                signals.append({
                    'time': data.index[i],
                    'type': 'SELL',
                    'price': float(data['close'].iloc[i])
                })

        logger.info(f"RSI signals generated: {len(signals)}")
        return signals

    def _generate_bollinger_signals(self, data, engine, period):
        """Generate buy/sell signals from Bollinger Bands."""
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        config = IndicatorConfig(indicator_type=IndicatorType.BB, params={'period': period, 'std': 2})
        result = engine.calculate(data, config)

        lower_col = [c for c in result.values.columns if 'BBL' in c][0]
        upper_col = [c for c in result.values.columns if 'BBU' in c][0]

        lower = result.values[lower_col]
        upper = result.values[upper_col]

        signals = []
        for i in range(1, len(data)):
            if pd.isna(lower.iloc[i]) or pd.isna(upper.iloc[i]):
                continue

            close = data['close'].iloc[i]
            prev_close = data['close'].iloc[i-1]

            # Price crosses below lower band = BUY (mean reversion)
            if prev_close >= lower.iloc[i-1] and close < lower.iloc[i]:
                signals.append({
                    'time': data.index[i],
                    'type': 'BUY',
                    'price': float(close)
                })
            # Price crosses above upper band = SELL
            elif prev_close <= upper.iloc[i-1] and close > upper.iloc[i]:
                signals.append({
                    'time': data.index[i],
                    'type': 'SELL',
                    'price': float(close)
                })

        logger.info(f"Bollinger signals generated: {len(signals)}")
        return signals

    def _generate_ma_signals(self, data, engine, fast, slow):
        """Generate buy/sell signals from Moving Average crossover."""
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        fast_config = IndicatorConfig(indicator_type=IndicatorType.SMA, params={'period': fast})
        slow_config = IndicatorConfig(indicator_type=IndicatorType.SMA, params={'period': slow})

        fast_ma = engine.calculate(data, fast_config).values
        slow_ma = engine.calculate(data, slow_config).values

        signals = []
        for i in range(1, len(fast_ma)):
            if pd.isna(fast_ma.iloc[i]) or pd.isna(slow_ma.iloc[i]):
                continue
            if pd.isna(fast_ma.iloc[i-1]) or pd.isna(slow_ma.iloc[i-1]):
                continue

            # Fast MA crosses above slow MA = BUY
            if fast_ma.iloc[i-1] < slow_ma.iloc[i-1] and fast_ma.iloc[i] > slow_ma.iloc[i]:
                signals.append({
                    'time': data.index[i],
                    'type': 'BUY',
                    'price': float(data['close'].iloc[i])
                })
            # Fast MA crosses below slow MA = SELL
            elif fast_ma.iloc[i-1] > slow_ma.iloc[i-1] and fast_ma.iloc[i] < slow_ma.iloc[i]:
                signals.append({
                    'time': data.index[i],
                    'type': 'SELL',
                    'price': float(data['close'].iloc[i])
                })

        logger.info(f"MA crossover signals generated: {len(signals)}")
        return signals

    def _simulate_trades(self, data, signals, stop_loss_pct, take_profit_pct):
        """Simulate trades with stop loss and take profit."""
        trades = []
        position = None

        for signal in signals:
            signal_time = signal['time']
            signal_idx = data.index.get_loc(signal_time)

            if signal['type'] == 'BUY' and position is None:
                # Open long position
                entry_price = signal['price']
                stop_loss = entry_price * (1 - stop_loss_pct)
                take_profit = entry_price * (1 + take_profit_pct)

                position = {
                    'entry_time': signal_time,
                    'entry_price': entry_price,
                    'stop_loss': stop_loss,
                    'take_profit': take_profit,
                    'type': 'LONG'
                }

            elif signal['type'] == 'SELL' and position is not None:
                # Close position on sell signal
                exit_price = signal['price']
                pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100

                trades.append({
                    **position,
                    'exit_time': signal_time,
                    'exit_price': exit_price,
                    'exit_reason': 'SIGNAL',
                    'pnl_pct': pnl_pct,
                    'is_winner': pnl_pct > 0
                })
                position = None

            # Check SL/TP for open position
            if position is not None:
                # Look at subsequent bars
                for j in range(signal_idx + 1, len(data)):
                    bar = data.iloc[j]
                    bar_time = data.index[j]

                    # Check stop loss
                    if bar['low'] <= position['stop_loss']:
                        exit_price = position['stop_loss']
                        pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                        trades.append({
                            **position,
                            'exit_time': bar_time,
                            'exit_price': exit_price,
                            'exit_reason': 'STOP_LOSS',
                            'pnl_pct': pnl_pct,
                            'is_winner': False
                        })
                        position = None
                        break

                    # Check take profit
                    if bar['high'] >= position['take_profit']:
                        exit_price = position['take_profit']
                        pnl_pct = (exit_price - position['entry_price']) / position['entry_price'] * 100
                        trades.append({
                            **position,
                            'exit_time': bar_time,
                            'exit_price': exit_price,
                            'exit_reason': 'TAKE_PROFIT',
                            'pnl_pct': pnl_pct,
                            'is_winner': True
                        })
                        position = None
                        break

                    # Check if next signal would be reached
                    next_signals = [s for s in signals if s['time'] > signal_time]
                    if next_signals and bar_time >= next_signals[0]['time']:
                        break

        logger.info(f"Simulated {len(trades)} trades")
        return trades

    def _draw_strategy_markers(self, trades):
        """Draw entry, exit, SL, and TP markers on chart."""
        markers = []

        for i, trade in enumerate(trades):
            entry_time = int(trade['entry_time'].timestamp())
            trade_num = i + 1

            # Entry marker (green arrow up for buy)
            markers.append({
                'time': entry_time,
                'position': 'belowBar',
                'color': '#26a69a',
                'shape': 'arrowUp',
                'text': f"#{trade_num} BUY @ {trade['entry_price']:.2f}"
            })

            # Exit marker with detailed info
            if 'exit_time' in trade:
                exit_time = int(trade['exit_time'].timestamp())
                exit_reason = trade['exit_reason']
                pnl = trade['pnl_pct']
                is_winner = trade['is_winner']

                # Different colors and shapes based on exit reason
                if exit_reason == 'STOP_LOSS':
                    exit_color = '#ef5350'  # Red
                    exit_shape = 'arrowDown'
                    exit_label = f"#{trade_num} SL"
                elif exit_reason == 'TAKE_PROFIT':
                    exit_color = '#26a69a'  # Green
                    exit_shape = 'arrowDown'
                    exit_label = f"#{trade_num} TP"
                else:  # SIGNAL
                    exit_color = '#26a69a' if is_winner else '#ef5350'
                    exit_shape = 'circle'
                    exit_label = f"#{trade_num} SELL"

                exit_text = f"{exit_label} @ {trade['exit_price']:.2f} ({pnl:+.1f}%)"

                markers.append({
                    'time': exit_time,
                    'position': 'aboveBar',
                    'color': exit_color,
                    'shape': exit_shape,
                    'text': exit_text
                })

        if hasattr(self.chart_widget, '_execute_js'):
            markers_json = json.dumps(markers)
            self.chart_widget._execute_js(f"window.chartAPI.addTradeMarkers({markers_json});")
            logger.info(f"Drew {len(markers)} markers on chart")

    def _clear_strategy_markers(self):
        """Clear all strategy markers from chart."""
        if hasattr(self.chart_widget, '_execute_js'):
            self.chart_widget._execute_js("window.chartAPI.clearMarkers();")
            logger.info("Cleared strategy markers from chart")

            # Clear results display
            if hasattr(self, 'results_summary'):
                self.results_summary.setText("Strategy markers cleared.\nSelect a strategy and click 'Apply Strategy to Chart'.")

            if hasattr(self.chart_widget, 'market_status_label'):
                self.chart_widget.market_status_label.setText("Markers cleared")
                self.chart_widget.market_status_label.setStyleSheet("color: #888; font-weight: normal;")

    def _run_ai_strategy_analysis(self, strategy_name, detected_type, symbol, trades, stats, strategy_params):
        """Run AI analysis on strategy trades asynchronously."""
        import asyncio
        import os

        # Check for API keys
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not api_key:
            logger.warning("No AI API key found - skipping AI analysis")
            if hasattr(self, 'results_summary'):
                current_text = self.results_summary.text()
                self.results_summary.setText(
                    current_text + "\n\n⚠️ AI Analysis unavailable - no API key configured"
                )
            return

        # Update UI to show AI is working
        if hasattr(self.chart_widget, 'market_status_label'):
            self.chart_widget.market_status_label.setText("🤖 AI analyzing strategy...")
            self.chart_widget.market_status_label.setStyleSheet("color: #FFA500; font-weight: bold;")

        async def run_analysis():
            try:
                from src.ai import get_ai_service
                service = await get_ai_service()

                analysis = await service.analyze_strategy_trades(
                    strategy_name=f"{strategy_name} ({detected_type})",
                    symbol=symbol,
                    trades=trades,
                    stats=stats,
                    strategy_params=strategy_params
                )

                # Store for potential optimization
                self._last_ai_analysis = analysis

                return analysis

            except Exception as e:
                logger.error(f"AI analysis failed: {e}", exc_info=True)
                return None

        def on_analysis_complete(future):
            try:
                analysis = future.result()
                if analysis:
                    self._display_ai_analysis(analysis, stats)
                else:
                    if hasattr(self, 'results_summary'):
                        current_text = self.results_summary.text()
                        self.results_summary.setText(
                            current_text + "\n\n❌ AI Analysis failed - check logs"
                        )
            except Exception as e:
                logger.error(f"Error displaying AI analysis: {e}")

        # Run async task
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                future = asyncio.ensure_future(run_analysis())
                future.add_done_callback(on_analysis_complete)
            else:
                result = asyncio.run(run_analysis())
                if result:
                    self._display_ai_analysis(result, stats)
        except Exception as e:
            logger.error(f"Failed to start AI analysis: {e}")

    def _display_ai_analysis(self, analysis, stats):
        """Display AI analysis results in the Results tab."""
        if hasattr(self.chart_widget, 'market_status_label'):
            self.chart_widget.market_status_label.setText(
                f"🤖 AI Rating: {analysis.strategy_rating:.1f}/10 | {analysis.win_rate_assessment}"
            )
            color = "#28a745" if analysis.strategy_rating >= 6 else "#dc3545"
            self.chart_widget.market_status_label.setStyleSheet(f"color: {color}; font-weight: bold;")

        if hasattr(self, 'results_summary'):
            ai_text = f"""
═══════════════════════════════════════
🤖 AI STRATEGY ANALYSIS
═══════════════════════════════════════

📊 OVERALL ASSESSMENT
Rating: {analysis.strategy_rating:.1f}/10
{analysis.overall_assessment}

✅ WINNING PATTERNS
{chr(10).join('• ' + p for p in analysis.winning_patterns[:5])}

❌ LOSING PATTERNS
{chr(10).join('• ' + p for p in analysis.losing_patterns[:5])}

📈 BEST ENTRY CONDITIONS
{analysis.best_entry_conditions}

📉 WORST ENTRY CONDITIONS
{analysis.worst_entry_conditions}

🔧 PARAMETER SUGGESTIONS
{chr(10).join(f'• {k}: {v}' for k, v in analysis.parameter_suggestions.items())}

⏱️ TIMING IMPROVEMENTS
{chr(10).join('• ' + t for t in analysis.timing_improvements[:3])}

🛡️ RISK MANAGEMENT TIPS
{chr(10).join('• ' + t for t in analysis.risk_management_tips[:3])}

🎯 OPTIMIZED STRATEGY
{chr(10).join(f'• {k}: {v}' for k, v in analysis.optimized_strategy.items())}
Expected: {analysis.expected_improvement}

🌍 MARKET FIT
Best for: {analysis.market_conditions_fit}
Timeframes: {', '.join(analysis.recommended_timeframes)}
Avoid: {', '.join(analysis.avoid_conditions[:3])}
"""
            current_text = self.results_summary.text()
            self.results_summary.setText(current_text + ai_text)

        logger.info(f"AI analysis displayed - Rating: {analysis.strategy_rating}/10")

    def _calculate_trade_stats(self, trades):
        """Calculate win/loss statistics."""
        if not trades:
            return {'wins': 0, 'losses': 0, 'win_rate': 0, 'avg_pnl': 0, 'total_pnl': 0}

        wins = sum(1 for t in trades if t['is_winner'])
        losses = len(trades) - wins
        win_rate = (wins / len(trades)) * 100 if trades else 0

        pnls = [t['pnl_pct'] for t in trades]
        avg_pnl = sum(pnls) / len(pnls) if pnls else 0
        total_pnl = sum(pnls)

        return {
            'wins': wins,
            'losses': losses,
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'total_pnl': total_pnl,
            'trades': trades
        }

    def _display_strategy_results(self, stats, strategy_name):
        """Display strategy results in Results tab."""
        summary = (
            f"Strategy: {strategy_name}\n"
            f"Symbol: {self.symbol}\n\n"
            f"Total Trades: {stats['wins'] + stats['losses']}\n"
            f"Winning Trades: {stats['wins']}\n"
            f"Losing Trades: {stats['losses']}\n"
            f"Win Rate: {stats['win_rate']:.1f}%\n\n"
            f"Average P&L: {stats['avg_pnl']:+.2f}%\n"
            f"Total P&L: {stats['total_pnl']:+.2f}%"
        )

        if hasattr(self, 'results_summary'):
            self.results_summary.setText(summary)

        # Update metrics table
        if hasattr(self, 'metrics_table') and 'trades' in stats:
            metrics_data = [
                ("Total Trades", str(stats['wins'] + stats['losses'])),
                ("Winning Trades", str(stats['wins'])),
                ("Losing Trades", str(stats['losses'])),
                ("Win Rate", f"{stats['win_rate']:.1f}%"),
                ("Average P&L", f"{stats['avg_pnl']:+.2f}%"),
                ("Total P&L", f"{stats['total_pnl']:+.2f}%"),
            ]

            # Add trade breakdown
            for i, trade in enumerate(stats['trades'][:10]):  # Show first 10 trades
                result = "✓ Win" if trade['is_winner'] else "✗ Loss"
                metrics_data.append((
                    f"Trade {i+1}",
                    f"{result}: {trade['pnl_pct']:+.2f}% ({trade['exit_reason']})"
                ))

            self.metrics_table.setRowCount(len(metrics_data))
            for i, (metric, value) in enumerate(metrics_data):
                self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
                self.metrics_table.setItem(i, 1, QTableWidgetItem(value))

    def _run_backtest(self):
        """Run backtest with chart data.

        Note: For simple strategy visualization, use 'Apply Strategy to Chart' instead.
        This backtest uses the full Backtrader engine for more detailed analysis.
        """
        import asyncio
        from src.core.backtesting.backtrader_integration import (
            BacktestConfig, BacktestEngine
        )
        from src.core.market_data.history_provider import Timeframe

        logger.info(f"Starting backtest for {self.symbol}")

        try:
            if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
                QMessageBox.warning(
                    self, "No Chart Data",
                    "Please load chart data first before running a backtest!"
                )
                return

            chart_data = self.chart_widget.data.copy()
            logger.info(f"Using chart data: {len(chart_data)} bars")

            progress = QProgressDialog(
                f"Running backtest on {len(chart_data)} bars...",
                "Cancel", 0, 0, self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Running Backtest")
            progress.show()

            start_date = self.backtest_start_date.date().toPyDate()
            end_date = self.backtest_end_date.date().toPyDate()
            start_datetime = datetime.combine(start_date, datetime.min.time())
            end_datetime = datetime.combine(end_date, datetime.max.time())

            # Make timezone-aware if chart data is timezone-aware
            if chart_data.index.tz is not None:
                import pytz
                start_datetime = pytz.UTC.localize(start_datetime)
                end_datetime = pytz.UTC.localize(end_datetime)

            mask = (chart_data.index >= start_datetime) & (chart_data.index <= end_datetime)
            backtest_data = chart_data[mask]

            if backtest_data.empty:
                progress.close()
                QMessageBox.warning(
                    self, "No Data in Date Range",
                    f"No chart data found between {start_date} and {end_date}."
                )
                return

            initial_cash = Decimal(str(self.initial_capital.value()))
            strategy_config = self._create_strategy_config_from_ui()

            backtest_config = BacktestConfig(
                start_date=start_datetime,
                end_date=end_datetime,
                initial_cash=initial_cash,
                commission=0.001,
                slippage=0.0005,
                timeframe=Timeframe.DAY,
                symbols=[self.symbol],
                strategies=[strategy_config]
            )

            # Create backtest engine
            engine = BacktestEngine(history_manager=self.history_manager)

            # Run backtest asynchronously
            async def run_async_backtest():
                return await engine.run_backtest(backtest_config)

            try:
                # Get or create event loop
                try:
                    loop = asyncio.get_running_loop()
                    # If we're in an async context, create task
                    future = asyncio.ensure_future(run_async_backtest())
                    result = loop.run_until_complete(future)
                except RuntimeError:
                    # No running loop, create new one
                    result = asyncio.run(run_async_backtest())

            except Exception as backtest_error:
                progress.close()
                logger.error(f"Backtest execution error: {backtest_error}", exc_info=True)
                QMessageBox.critical(
                    self, "Backtest Failed",
                    f"Backtest execution failed:\n\n{str(backtest_error)}"
                )
                return

            progress.close()

            if not result:
                QMessageBox.warning(self, "Backtest Failed", "No backtest result returned.")
                return

            logger.info(f"Backtest completed: {result.metrics.total_trades} trades")

            self._display_backtest_results(result)
            self._add_trade_markers_to_chart(result)
            self.panel_tabs.setCurrentWidget(self.results_tab)

            if not self.dock_widget.isVisible():
                self.dock_widget.setVisible(True)
                if hasattr(self.chart_widget, 'toggle_panel_button'):
                    self.chart_widget.toggle_panel_button.setChecked(True)
                    self._update_toggle_button_text()

        except ImportError as e:
            logger.error(f"Backtrader not available: {e}")
            QMessageBox.warning(
                self, "Backtrader Not Installed",
                "The full backtest engine requires Backtrader.\n\n"
                "Use 'Apply Strategy to Chart' for simple strategy visualization,\n"
                "or install backtrader: pip install backtrader"
            )
        except Exception as e:
            logger.error(f"Backtest execution failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Backtest Error", f"Failed to run backtest:\n{str(e)}")

    def _create_strategy_config_from_ui(self) -> 'StrategyConfig':
        """Create StrategyConfig from current UI parameters."""
        from src.core.strategy.engine import StrategyConfig, StrategyType
        from src.core.indicators.engine import IndicatorConfig, IndicatorType

        strategy_name = self.strategy_combo.currentText()

        strategy_type_map = {
            "MACD Crossover": StrategyType.TREND_FOLLOWING,
            "RSI Mean Reversion": StrategyType.MEAN_REVERSION,
            "Bollinger Bands": StrategyType.MEAN_REVERSION,
            "Moving Average": StrategyType.TREND_FOLLOWING,
            "Custom Strategy": StrategyType.CUSTOM
        }
        strategy_type = strategy_type_map.get(strategy_name, StrategyType.CUSTOM)

        parameters = {
            "fast_period": self.fast_period.value(),
            "slow_period": self.slow_period.value(),
            "signal_period": self.signal_period.value()
        }

        risk_params = {
            "stop_loss_pct": self.stop_loss.value(),
            "take_profit_pct": self.take_profit.value(),
            "position_size_pct": self.position_size.value()
        }

        indicators = []
        if "MACD" in strategy_name:
            indicators.append(
                IndicatorConfig(
                    indicator_type=IndicatorType.MACD,
                    params={
                        "fast": parameters["fast_period"],
                        "slow": parameters["slow_period"],
                        "signal": parameters["signal_period"]
                    }
                )
            )
        elif "RSI" in strategy_name:
            indicators.append(
                IndicatorConfig(indicator_type=IndicatorType.RSI, params={"period": 14})
            )
        elif "Bollinger" in strategy_name:
            indicators.append(
                IndicatorConfig(
                    indicator_type=IndicatorType.BB,
                    params={"period": 20, "std": 2}
                )
            )
        elif "Moving Average" in strategy_name:
            indicators.extend([
                IndicatorConfig(indicator_type=IndicatorType.SMA, params={"period": parameters["fast_period"]}),
                IndicatorConfig(indicator_type=IndicatorType.SMA, params={"period": parameters["slow_period"]})
            ])

        ai_validation = self.enable_ai_analysis.isChecked()

        return StrategyConfig(
            name=strategy_name,
            strategy_type=strategy_type,
            symbols=[self.symbol],
            parameters=parameters,
            risk_params=risk_params,
            indicators=indicators,
            enabled=True,
            ai_validation=ai_validation
        )

    def _display_backtest_results(self, result: 'BacktestResult'):
        """Display backtest results in Results tab."""
        from src.core.models.backtest_models import BacktestResult

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid result type: {type(result)}")
            return

        summary_text = (
            f"Backtest Completed: {result.symbol}\n"
            f"Period: {result.start.strftime('%Y-%m-%d')} to {result.end.strftime('%Y-%m-%d')}\n"
            f"Strategy: {result.strategy_name or 'Unknown'}\n"
            f"Total P&L: €{result.total_pnl:,.2f} ({result.total_pnl_pct:+.2f}%)"
        )
        self.results_summary.setText(summary_text)

        metrics = result.metrics
        metrics_data = [
            ("Total Return", f"{result.total_pnl_pct:+.2f}%"),
            ("Annual Return", f"{metrics.annual_return_pct:+.2f}%" if metrics.annual_return_pct else "N/A"),
            ("Net Profit", f"€{result.total_pnl:,.2f}"),
            ("Final Capital", f"€{result.final_capital:,.2f}"),
            ("", ""),
            ("Total Trades", str(metrics.total_trades)),
            ("Winning Trades", f"{metrics.winning_trades} ({metrics.win_rate:.1%})"),
            ("Losing Trades", f"{metrics.losing_trades}"),
            ("Win Rate", f"{metrics.win_rate:.2%}"),
            ("", ""),
            ("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%"),
            ("Sharpe Ratio", f"{metrics.sharpe_ratio:.3f}" if metrics.sharpe_ratio else "N/A"),
            ("Sortino Ratio", f"{metrics.sortino_ratio:.3f}" if metrics.sortino_ratio else "N/A"),
            ("Profit Factor", f"{metrics.profit_factor:.2f}"),
            ("", ""),
            ("Average Win", f"€{metrics.avg_win:,.2f}"),
            ("Average Loss", f"€{metrics.avg_loss:,.2f}"),
            ("Largest Win", f"€{metrics.largest_win:,.2f}"),
            ("Largest Loss", f"€{metrics.largest_loss:,.2f}"),
            ("Expectancy", f"€{metrics.expectancy:,.2f}" if metrics.expectancy else "N/A"),
            ("", ""),
            ("Max Consecutive Wins", str(metrics.max_consecutive_wins)),
            ("Max Consecutive Losses", str(metrics.max_consecutive_losses)),
        ]

        self.metrics_table.setRowCount(len(metrics_data))
        for i, (metric, value) in enumerate(metrics_data):
            self.metrics_table.setItem(i, 0, QTableWidgetItem(metric))
            self.metrics_table.setItem(i, 1, QTableWidgetItem(value))

        self.metrics_table.horizontalHeader().setStretchLastSection(True)
        self.metrics_table.resizeColumnToContents(0)

        logger.info("Backtest results displayed in Results tab")

    def _add_trade_markers_to_chart(self, result: 'BacktestResult'):
        """Add Entry/Exit markers to chart."""
        from src.core.models.backtest_models import BacktestResult, TradeSide

        if not isinstance(result, BacktestResult):
            logger.error(f"Invalid result type: {type(result)}")
            return

        show_entries = self.show_entry_markers.isChecked()
        show_exits = self.show_exit_markers.isChecked()

        logger.info(f"Adding trade markers to chart: {len(result.trades)} trades")

        markers = []

        for trade in result.trades:
            if show_entries:
                entry_time = int(trade.entry_time.timestamp())
                entry_marker = {
                    "time": entry_time,
                    "position": "belowBar" if trade.side == TradeSide.LONG else "aboveBar",
                    "color": "#26a69a" if trade.side == TradeSide.LONG else "#ef5350",
                    "shape": "arrowUp" if trade.side == TradeSide.LONG else "arrowDown",
                    "text": f"{'BUY' if trade.side == TradeSide.LONG else 'SELL'} @ €{trade.entry_price:.2f}"
                }
                markers.append(entry_marker)

            if show_exits and trade.exit_time and trade.exit_price:
                exit_time = int(trade.exit_time.timestamp())
                exit_marker = {
                    "time": exit_time,
                    "position": "aboveBar" if trade.side == TradeSide.LONG else "belowBar",
                    "color": "#26a69a" if trade.is_winner else "#ef5350",
                    "shape": "circle",
                    "text": f"EXIT @ €{trade.exit_price:.2f} ({trade.realized_pnl_pct:+.2f}%)"
                }
                markers.append(exit_marker)

        if hasattr(self.chart_widget, '_execute_js'):
            markers_json = json.dumps(markers)
            js_code = f"window.chartAPI.addTradeMarkers({markers_json});"
            self.chart_widget._execute_js(js_code)
            logger.info(f"Added {len(markers)} trade markers to chart")
        else:
            logger.warning("Chart widget doesn't have _execute_js method")

    def _start_optimization(self):
        """Start parameter optimization."""
        from src.core.backtesting.optimization import (
            ParameterOptimizer, ParameterRange, OptimizerConfig
        )

        logger.info(f"Starting parameter optimization for {self.symbol}")

        if not hasattr(self.chart_widget, 'data') or self.chart_widget.data is None or self.chart_widget.data.empty:
            QMessageBox.warning(
                self, "No Chart Data",
                "Please load chart data first before running optimization!"
            )
            return

        try:
            progress = QProgressDialog(
                "Running parameter optimization...",
                "Cancel", 0, 0, self
            )
            progress.setWindowModality(Qt.WindowModality.WindowModal)
            progress.setWindowTitle("Parameter Optimization")
            progress.show()

            parameter_ranges = [
                ParameterRange(
                    name="fast_period",
                    values=list(range(self.opt_fast_min.value(), self.opt_fast_max.value() + 1, 2))
                ),
                ParameterRange(
                    name="slow_period",
                    values=list(range(self.opt_slow_min.value(), self.opt_slow_max.value() + 1, 5))
                )
            ]

            metric_name = self.opt_metric.currentText()
            metric_map = {
                "Sharpe Ratio": "sharpe_ratio",
                "Total Return": "total_return_pct",
                "Profit Factor": "profit_factor",
                "Win Rate": "win_rate"
            }
            primary_metric = metric_map.get(metric_name, "sharpe_ratio")

            config = OptimizerConfig(
                max_workers=2,
                timeout_per_test=60,
                primary_metric=primary_metric,
                use_ai_guidance=self.use_ai_guidance.isChecked()
            )

            progress.close()

            QMessageBox.information(
                self, "Optimization Setup",
                f"Parameter Optimization configured:\n\n"
                f"Fast Period: {self.opt_fast_min.value()}-{self.opt_fast_max.value()}\n"
                f"Slow Period: {self.opt_slow_min.value()}-{self.opt_slow_max.value()}\n"
                f"Metric: {metric_name}\n"
                f"Max Iterations: {self.max_iterations.value()}\n"
                f"AI Guidance: {'Yes' if self.use_ai_guidance.isChecked() else 'No'}"
            )

            logger.info("Optimization setup complete")

        except Exception as e:
            logger.error(f"Optimization setup failed: {e}", exc_info=True)
            QMessageBox.critical(self, "Optimization Error", f"Failed to set up optimization:\n{str(e)}")
