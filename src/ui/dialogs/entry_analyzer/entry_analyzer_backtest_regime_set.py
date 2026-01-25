"""Entry Analyzer - Regime Set Creation Mixin.

Extracted from entry_analyzer_backtest.py to keep files under 550 LOC.
Handles regime-based strategy set generation:
- Create regime set from optimization results
- Build regime set (group by regime, select top indicators)
- Generate JSON config with indicators, regimes, strategies, routing
- Generate regime conditions based on regime type
- Generate entry conditions from indicator combinations
- Backtest regime set

Date: 2026-01-21
LOC: ~375
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import QInputDialog, QMessageBox

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BacktestRegimeSetMixin:
    """Regime set creation functionality.

    Provides regime-based strategy generation with:
    - Group optimization results by regime
    - Select top N indicators per regime with weights
    - Generate complete JSON config (indicators, regimes, strategies, routing)
    - Regime condition generation (TREND_UP/DOWN, RANGE, HIGH_VOL)
    - Entry condition generation from indicators
    - Backtest regime set configuration

    Attributes (defined in parent class):
        _optimization_results: list - Optimization results from indicator optimization
        _bt_start_date: QDateEdit - Backtest start date
        _bt_end_date: QDateEdit - Backtest end date
        _bt_initial_capital: QDoubleSpinBox - Initial capital
        _bt_run_btn: QPushButton - Run backtest button
        _tabs: QTabWidget - Main tab widget
    """

    # Type hints for parent class attributes
    _optimization_results: list
    _bt_start_date: Any
    _bt_end_date: Any
    _bt_initial_capital: Any
    _bt_run_btn: Any
    _tabs: Any
    _symbol: str

    def _on_create_regime_set_clicked(self) -> None:
        """Create regime-based strategy set from optimization results.

        Original: entry_analyzer_backtest.py:784-871

        Workflow:
        1. Ask user for regime set name (with timestamp default)
        2. Ask for top N indicators per regime (1-10)
        3. Build regime set (group by regime, select top by score)
        4. Generate JSON config with all components
        5. Save config to 03_JSON/Trading_Bot/regime_sets/
        6. Offer to backtest the regime set immediately
        """
        if not hasattr(self, "_optimization_results") or not self._optimization_results:
            QMessageBox.warning(
                self, "No Optimization Results", "Please run indicator optimization first."
            )
            return

        # Ask user for regime set name
        regime_set_name, ok = QInputDialog.getText(
            self,
            "Create Regime Set",
            "Enter name for regime set:",
            text=f"RegimeSet_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        )

        if not ok or not regime_set_name:
            return

        # Ask for top N indicators per regime
        top_n, ok = QInputDialog.getInt(
            self, "Top Indicators", "Select top N indicators per regime:", value=3, min=1, max=10
        )

        if not ok:
            return

        logger.info(
            f"Creating regime set '{regime_set_name}' with top {top_n} indicators per regime"
        )

        try:
            # Build regime set
            regime_set = self._build_regime_set(self._optimization_results, top_n)

            # Generate JSON config
            config_dict = self._generate_regime_set_json(regime_set, regime_set_name)

            # Save config to file
            config_dir = Path("03_JSON/Trading_Bot/regime_sets")
            config_dir.mkdir(parents=True, exist_ok=True)

            config_path = config_dir / f"{regime_set_name}.json"
            with open(config_path, "w") as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Regime set config saved to: {config_path}")

            # Ask if user wants to backtest the regime set
            reply = QMessageBox.question(
                self,
                "Backtest Regime Set?",
                f"Regime set '{regime_set_name}' created successfully!\n"
                f"Config saved to: {config_path}\n\n"
                f"Do you want to run a backtest on this regime set now?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self._backtest_regime_set(config_path)

        except Exception as e:
            logger.error(f"Failed to create regime set: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Regime Set Error", f"Failed to create regime set:\n\n{str(e)}"
            )

    def _build_regime_set(self, results: list, top_n: int = 3) -> dict:
        """Build regime set from optimization results.

        Original: entry_analyzer_backtest.py:872-924

        Args:
            results: List of optimization result dictionaries
            top_n: Number of top indicators to select per regime

        Returns:
            Dictionary mapping regimes to their top indicators with weights
        """
        # Group results by regime
        regime_groups = {}

        for result in results:
            regime = result["regime"]
            if regime not in regime_groups:
                regime_groups[regime] = []
            regime_groups[regime].append(result)

        # Build regime set
        regime_set = {}

        for regime, regime_results in regime_groups.items():
            # Skip 'ALL' regime if present
            if regime == "ALL":
                continue

            # Sort by score (descending)
            sorted_results = sorted(regime_results, key=lambda x: x["score"], reverse=True)

            # Select top N
            top_indicators = sorted_results[:top_n]

            # Calculate weights (normalized scores)
            total_score = sum(ind["score"] for ind in top_indicators)

            weights = {}
            for ind in top_indicators:
                indicator_key = f"{ind['indicator']}_{str(ind['params'])}"
                weight = (
                    ind["score"] / total_score if total_score > 0 else 1.0 / len(top_indicators)
                )
                weights[indicator_key] = weight

            regime_set[regime] = {
                "indicators": top_indicators,
                "weights": weights,
                "avg_score": total_score / len(top_indicators) if top_indicators else 0.0,
            }

        logger.info(f"Built regime set with {len(regime_set)} regimes")

        return regime_set

    def _generate_regime_set_json(self, regime_set: dict, set_name: str) -> dict:
        """Generate JSON config from regime set.

        Original: entry_analyzer_backtest.py:926-1020

        Args:
            regime_set: Regime set dictionary
            set_name: Name for the regime set

        Returns:
            JSON config dictionary
        """
        config = {
            "schema_version": "1.0.0",
            "name": set_name,
            "description": f"Auto-generated regime set from optimization results at {datetime.now().isoformat()}",
            "indicators": [],
            "regimes": [],
            "strategies": [],
            "strategy_sets": [],
            "routing": [],
        }

        indicator_counter = 0
        strategy_counter = 0

        for regime_name, regime_data in regime_set.items():
            # Add regime definition
            regime_id = f"regime_{regime_name.lower().replace(' ', '_')}"

            config["regimes"].append(
                {
                    "id": regime_id,
                    "name": regime_name,
                    "description": f"Auto-generated regime definition for {regime_name}",
                    "conditions": self._generate_regime_conditions(regime_name),
                }
            )

            # Add indicators for this regime
            regime_indicators = []

            for ind_result in regime_data["indicators"]:
                indicator_counter += 1
                ind_id = f"ind_{indicator_counter}_{ind_result['indicator'].lower()}"

                config["indicators"].append(
                    {
                        "id": ind_id,
                        "type": ind_result["indicator"],
                        "timeframe": "1m",  # Default timeframe
                        "params": ind_result["params"],
                    }
                )

                regime_indicators.append(ind_id)

            # Add strategy for this regime
            strategy_counter += 1
            strategy_id = f"strategy_{strategy_counter}_{regime_name.lower().replace(' ', '_')}"

            config["strategies"].append(
                {
                    "id": strategy_id,
                    "name": f"{regime_name} Strategy",
                    "description": f"Auto-generated strategy for {regime_name} regime",
                    "entry_conditions": self._generate_entry_conditions(regime_indicators),
                    "exit_conditions": {
                        "type": "group",
                        "operator": "or",
                        "conditions": [
                            {"type": "stop_loss"},
                            {"type": "take_profit"},
                            {"type": "trailing_stop"},
                        ],
                    },
                    "risk": {
                        "position_size_pct": 2.0,
                        "stop_loss_pct": 2.0,
                        "take_profit_pct": 6.0,
                    },
                }
            )

            # Add strategy set
            set_id = f"set_{regime_name.lower().replace(' ', '_')}"

            config["strategy_sets"].append(
                {
                    "id": set_id,
                    "name": f"{regime_name} Set",
                    "strategies": [strategy_id],
                    "weights": {strategy_id: 1.0},
                }
            )

            # Add routing rule
            config["routing"].append(
                {"regimes": {"all_of": [regime_id]}, "strategy_set_id": set_id}
            )

        return config

    def _generate_regime_conditions(self, regime_name: str) -> dict:
        """Generate conditions for a regime based on its name.

        Original: entry_analyzer_backtest.py:1022-1070

        Args:
            regime_name: Name of the regime (e.g., 'TREND_UP', 'RANGE')

        Returns:
            Condition dictionary
        """
        # Simplified regime conditions
        # In production, these would be more sophisticated

        name_upper = regime_name.upper()

        # BULL / TREND_UP: Bullish trend
        if "BULL" in name_upper or "TREND_UP" in name_upper:
            return {
                "type": "group",
                "operator": "and",
                "conditions": [
                    {"type": "condition", "indicator": "adx", "operator": "gt", "value": 25},
                    {
                        "type": "condition",
                        "indicator": "sma_fast",
                        "operator": "gt",
                        "indicator2": "sma_slow",
                    },
                ],
            }
        # BEAR / TREND_DOWN: Bearish trend
        elif "BEAR" in name_upper or "TREND_DOWN" in name_upper:
            return {
                "type": "group",
                "operator": "and",
                "conditions": [
                    {"type": "condition", "indicator": "adx", "operator": "gt", "value": 25},
                    {
                        "type": "condition",
                        "indicator": "sma_fast",
                        "operator": "lt",
                        "indicator2": "sma_slow",
                    },
                ],
            }
        # SIDEWAYS / RANGE: Range-bound
        elif "SIDEWAYS" in name_upper or "RANGE" in name_upper:
            return {
                "type": "group",
                "operator": "and",
                "conditions": [
                    {"type": "condition", "indicator": "adx", "operator": "lt", "value": 25},
                    {"type": "condition", "indicator": "bb_width", "operator": "lt", "value": 0.05},
                ],
            }
        else:
            # Default condition
            return {"type": "condition", "indicator": "close", "operator": "gt", "value": 0}

    def _generate_entry_conditions(self, indicator_ids: list) -> dict:
        """Generate entry conditions using regime indicators.

        Original: entry_analyzer_backtest.py:1072-1124

        Args:
            indicator_ids: List of indicator IDs for this regime

        Returns:
            Entry conditions dictionary
        """
        # Generate combined entry conditions
        # In production, this would be more sophisticated

        conditions = []

        for ind_id in indicator_ids[:3]:  # Use top 3 indicators
            if "rsi" in ind_id.lower():
                conditions.append(
                    {
                        "type": "condition",
                        "indicator": ind_id,
                        "operator": "between",
                        "value": [30, 70],
                    }
                )
            elif "macd" in ind_id.lower():
                conditions.append(
                    {
                        "type": "condition",
                        "indicator": f"{ind_id}_histogram",
                        "operator": "gt",
                        "value": 0,
                    }
                )
            elif "adx" in ind_id.lower():
                conditions.append(
                    {"type": "condition", "indicator": ind_id, "operator": "gt", "value": 20}
                )

        if not conditions:
            # Fallback condition
            conditions.append(
                {"type": "condition", "indicator": "close", "operator": "gt", "value": 0}
            )

        return {"type": "group", "operator": "and", "conditions": conditions}
