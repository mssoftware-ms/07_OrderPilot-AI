from __future__ import annotations


from PyQt6.QtWidgets import QTableWidgetItem

class BotDisplayMetricsMixin:
    """BotDisplayMetricsMixin extracted from BotDisplayManagerMixin."""
    def update_strategy_scores(self, scores: list[dict]) -> None:
        """Update strategy scores table.

        Args:
            scores: List of strategy score dicts
        """
        self.strategy_scores_table.setRowCount(len(scores))
        for row, score_data in enumerate(scores):
            self.strategy_scores_table.setItem(
                row, 0, QTableWidgetItem(score_data.get("name", "-"))
            )
            self.strategy_scores_table.setItem(
                row, 1, QTableWidgetItem(f"{score_data.get('score', 0):.2f}")
            )
            self.strategy_scores_table.setItem(
                row, 2, QTableWidgetItem(f"{score_data.get('profit_factor', 0):.2f}")
            )
            self.strategy_scores_table.setItem(
                row, 3, QTableWidgetItem(f"{score_data.get('win_rate', 0):.1%}")
            )
            self.strategy_scores_table.setItem(
                row, 4, QTableWidgetItem(f"{score_data.get('max_drawdown', 0):.1%}")
            )
    def update_walk_forward_results(self, results: dict) -> None:
        """Update walk-forward results display.

        Args:
            results: Walk-forward results dict
        """
        text = []
        if results:
            text.append(f"Training Window: {results.get('training_days', 'N/A')} days")
            text.append(f"Test Window: {results.get('test_days', 'N/A')} days")
            text.append(f"IS Profit Factor: {results.get('is_pf', 0):.2f}")
            text.append(f"OOS Profit Factor: {results.get('oos_pf', 0):.2f}")
            text.append(f"OOS Degradation: {results.get('degradation', 0):.1%}")
            text.append(f"Passed Gate: {'Yes' if results.get('passed', False) else 'No'}")
        self.wf_results_text.setText("\n".join(text))

    def update_strategy_indicators(self, strategy_name: str | None = None) -> None:
        """Issue #2: Update strategy indicators display.

        Extracts and displays indicators from the strategy catalog's entry_rules
        for the active strategy.

        Args:
            strategy_name: Name of the active strategy (e.g., "trend_following_conservative")
        """
        if not hasattr(self, 'strategy_indicators_label'):
            return

        if not strategy_name:
            self.strategy_indicators_label.setText("-")
            self.strategy_indicators_label.setStyleSheet("color: #888; font-size: 11px;")
            return

        # Get strategy from catalog
        try:
            from src.core.tradingbot.strategy_catalog import StrategyCatalog
            catalog = StrategyCatalog()
            strategy_def = catalog.get_strategy(strategy_name)

            if not strategy_def:
                self.strategy_indicators_label.setText(f"Strategy '{strategy_name}' not in catalog")
                self.strategy_indicators_label.setStyleSheet("color: #888; font-size: 11px;")
                return

            # Extract unique indicators from entry_rules
            indicators = set()
            for rule in strategy_def.entry_rules:
                if rule.indicator:
                    # Clean up indicator name (e.g., "rsi_14" -> "RSI", "macd_hist" -> "MACD")
                    ind_name = rule.indicator.upper()
                    # Remove suffixes like _14, _20, _HIST, _MOMENTUM
                    for suffix in ['_14', '_20', '_50', '_200', '_HIST', '_MOMENTUM', '_SPREAD', '_ALIGNMENT', '_PCT', '_RATIO']:
                        ind_name = ind_name.replace(suffix, '')
                    # Handle special cases
                    if 'BB' in ind_name:
                        ind_name = 'BB'
                    elif 'SMA' in ind_name or 'MA' in ind_name:
                        ind_name = 'SMA'
                    elif 'VOLUME' in ind_name:
                        ind_name = 'VOL'
                    elif 'DI' in ind_name and 'ADX' not in ind_name:
                        ind_name = 'DMI'
                    indicators.add(ind_name)

            if indicators:
                # Sort alphabetically for consistency
                sorted_indicators = sorted(indicators)
                self.strategy_indicators_label.setText(", ".join(sorted_indicators))
                self.strategy_indicators_label.setStyleSheet(
                    "color: #26a69a; font-size: 11px; font-weight: bold;"
                )
            else:
                self.strategy_indicators_label.setText("No indicators defined")
                self.strategy_indicators_label.setStyleSheet("color: #888; font-size: 11px;")

        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to get strategy indicators: {e}")
            self.strategy_indicators_label.setText("-")
            self.strategy_indicators_label.setStyleSheet("color: #888; font-size: 11px;")
