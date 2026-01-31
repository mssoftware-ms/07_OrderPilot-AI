"""Regime Optimization - Rendering & Display Mixin.

Handles UI rendering and display updates.

Agent: CODER-013
Task: 3.1.3 - Split regime_optimization_mixin
File: 5/5 - Rendering (520 LOC target)
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QApplication,
    QMessageBox,
    QTableWidget,
    QTableWidgetItem,
)

logger = logging.getLogger(__name__)


class RegimeOptimizationRenderingMixin:
    """UI rendering and display updates.

    Handles:
        - Top results table updates
        - Current regime score calculation
        - Chart drawing for selected results
    """

    def _update_regime_opt_top5_table(self) -> None:
        """Update results table filtered by score > 50 (or best 10 if none).

        DYNAMIC column generation - NO hardcoded parameter names!
        Generates columns based on parameters in the first result.
        """
        from PyQt6.QtWidgets import QApplication

        # Filter results: all with score > 50, or best 10 if none
        results_to_show = [r for r in self._regime_opt_all_results if r.get("score", 0) > 50]

        if not results_to_show:
            # No results over 50, show best 10
            results_to_show = self._regime_opt_all_results[:10]
            logger.info(f"No results with score > 50, showing best {len(results_to_show)} results")
        else:
            logger.info(f"Showing {len(results_to_show)} results with score > 50")

        if not results_to_show:
            logger.warning("No results to display in top5 table")
            return

        # DYNAMIC COLUMN GENERATION: Get parameter names from first result
        first_result = results_to_show[0]
        params_dict = first_result.get("params", {})
        metrics_dict = first_result.get("metrics", {})

        # Sort parameter names for consistent column order
        param_names = sorted(params_dict.keys())

        # Build column headers: Rank, Total Score, [Dynamic Params], Trial #
        # Note: Score components (Sep, Coh, Fid, Bnd, Cov) removed - legacy scoring system
        headers = ["Rank", "Total"] + param_names + ["Trial #"]

        # Update table structure
        self._regime_opt_top5_table.setColumnCount(len(headers))
        self._regime_opt_top5_table.setHorizontalHeaderLabels(headers)

        # Configure header resize modes
        header = self._regime_opt_top5_table.horizontalHeader()
        for col in range(len(headers)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        logger.info(f"Dynamic table: {len(headers)} columns ({len(param_names)} parameters)")

        # Disable visual updates and sorting while updating for better performance
        self._regime_opt_top5_table.setUpdatesEnabled(False)
        self._regime_opt_top5_table.setSortingEnabled(False)
        self._regime_opt_top5_table.setRowCount(len(results_to_show))

        for row, result in enumerate(results_to_show):
            # Process events every 5 rows to keep spinner animation smooth
            if row > 0 and row % 5 == 0:
                QApplication.processEvents()
                # Update waiting dialog with progress
                if hasattr(self, "_waiting_dialog") and self._waiting_dialog and self._waiting_dialog.isVisible():
                    progress = int((row / len(results_to_show)) * 100)
                    self._waiting_dialog.set_status(f"Top-Ergebnisse: {row}/{len(results_to_show)} ({progress}%)")

            params = result.get("params", {})
            metrics = result.get("metrics", {})
            score = result.get("score", 0)
            trial_num = result.get("trial_number", row + 1)

            # Find original index in _regime_opt_all_results
            original_index = self._regime_opt_all_results.index(result) if result in self._regime_opt_all_results else row

            col = 0

            # Column 0: Rank (display rank, but store original index in UserRole)
            rank_item = QTableWidgetItem(str(row + 1))
            rank_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            rank_item.setData(Qt.ItemDataRole.UserRole, original_index)  # Store original index for correct retrieval
            self._regime_opt_top5_table.setItem(row, col, rank_item)
            col += 1

            # Column 1: Total Score
            score_item = QTableWidgetItem(f"{score:.1f}")
            score_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Color-code score
            if score >= 75:
                score_item.setForeground(Qt.GlobalColor.darkGreen)
            elif score >= 50:
                score_item.setForeground(Qt.GlobalColor.darkYellow)
            else:
                score_item.setForeground(Qt.GlobalColor.darkRed)
            self._regime_opt_top5_table.setItem(row, col, score_item)
            col += 1

            # Dynamic Parameter Columns
            for param_name in param_names:
                param_value = params.get(param_name, "--")
                # Format value based on type
                if isinstance(param_value, float):
                    value_str = f"{param_value:.2f}"
                else:
                    value_str = str(param_value)

                param_item = QTableWidgetItem(value_str)
                param_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._regime_opt_top5_table.setItem(row, col, param_item)
                col += 1

            # Last Column: Trial Number
            trial_item = QTableWidgetItem(str(trial_num))
            trial_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._regime_opt_top5_table.setItem(row, col, trial_item)

        # Re-enable visual updates and sorting
        self._regime_opt_top5_table.setUpdatesEnabled(True)
        self._regime_opt_top5_table.setSortingEnabled(True)

        # Final UI update
        QApplication.processEvents()

    @pyqtSlot()

    @pyqtSlot()
    def _on_calculate_current_regime_score(self) -> None:
        """Calculate and display score for currently active regime configuration."""
        from PyQt6.QtWidgets import QMessageBox

        # Check if we have chart data
        if not hasattr(self, "_candles") or len(self._candles) == 0:
            QMessageBox.warning(
                self,
                "No Data",
                "No chart data available. Please load chart first!"
            )
            return

        # Minimum 200 candles required for SMA(200) warmup period
        MIN_CANDLES_REQUIRED = 200
        candle_count = len(self._candles)
        if candle_count < MIN_CANDLES_REQUIRED:
            timeframe = getattr(self, "_current_timeframe", "5m")
            timeframe_minutes = self._timeframe_to_minutes(timeframe)
            required_hours = (timeframe_minutes * MIN_CANDLES_REQUIRED) / 60
            required_days = (timeframe_minutes * MIN_CANDLES_REQUIRED) / 1440

            if required_days >= 1:
                time_info = f"{required_days:.1f} Tage ({required_hours:.1f} Stunden)"
            else:
                time_info = f"{required_hours:.1f} Stunden"

            QMessageBox.warning(
                self,
                "Unzureichende Daten",
                f"Analyse kann nicht ausgeführt werden!\n\n"
                f"Mindestens {MIN_CANDLES_REQUIRED} Kerzen benötigt.\n"
                f"Aktuell vorhanden: {candle_count} Kerzen.\n\n"
                f"Bei {timeframe} Kerzen benötigen Sie mindestens:\n"
                f"• {time_info}\n\n"
                f"Bitte Zeitraum im Chart ändern."
            )
            return

        try:
            # Get current regime config from main app
            # This would typically come from the active trading bot config
            # For now, we'll use default values or load from a config file
            from src.core.regime_optimizer import (
                RegimeOptimizer,
                AllParamRanges,
                ADXParamRanges,
                RSIParamRanges,
                ATRParamRanges,
                ParamRange,
                RegimeParams,
            )
            import pandas as pd

            # Convert candles to DataFrame
            df = pd.DataFrame(self._candles)
            if "timestamp" in df.columns:
                df.set_index("timestamp", inplace=True)

            # Load ACTUAL params from JSON config (NO HARDCODED VALUES!)
            if not hasattr(self, "_regime_config") or self._regime_config is None:
                raise ValueError(
                    "No regime config loaded! Please load a JSON config in the 'Regime' tab first."
                )

            config = self._regime_config

            # Get optimized params from optimization_results if available
            optimized_params = {}
            opt_results = []
            if isinstance(config, dict):
                opt_results = config.get("optimization_results", [])
            elif hasattr(config, "optimization_results"):
                opt_results = config.optimization_results or []

            if opt_results:
                applied = [r for r in opt_results if r.get("applied", False)]
                if applied:
                    optimized_params = applied[-1].get("params", {})
                else:
                    optimized_params = opt_results[0].get("params", {})

            # Helper to get param value (optimized or base)
            def get_param(indicator_id: str, param_name: str, default: Any) -> Any:
                # Try optimized first
                opt_key = f"{indicator_id}.{param_name}"
                if opt_key in optimized_params:
                    return optimized_params[opt_key]

                # Also try underscore format (from optimizer)
                underscore_key = f"{indicator_id}_{param_name}"
                if underscore_key in optimized_params:
                    return optimized_params[underscore_key]

                # Fallback to indicators from config (dict or object)
                indicators = config.get("indicators", []) if isinstance(config, dict) else getattr(config, "indicators", [])

                # Also check optimization_results[0].indicators for v2 format
                if not indicators and isinstance(config, dict):
                    opt_results = config.get("optimization_results", [])
                    if opt_results:
                        indicators = opt_results[0].get("indicators", [])

                for ind in indicators:
                    ind_id = ind.get("id") or ind.get("name", "") if isinstance(ind, dict) else getattr(ind, "id", getattr(ind, "name", ""))
                    # Match by id or name (handle both v1 and v2 naming)
                    if ind_id.lower().replace("_", "") == indicator_id.lower().replace("_", "") or indicator_id.lower() in ind_id.lower():
                        if isinstance(ind, dict):
                            params = ind.get("params", {})
                            # v2 format: params is a list of {name, value}
                            if isinstance(params, list):
                                for p in params:
                                    if p.get("name") == param_name:
                                        return p.get("value", default)
                            else:
                                return params.get(param_name, default)
                        else:
                            return getattr(ind, "params", {}).get(param_name, default)

                return default

            # Helper for regime thresholds
            def get_regime_threshold(regime_id: str, threshold_name: str, default: Any) -> Any:
                opt_key = f"{regime_id}.{threshold_name}"
                if opt_key in optimized_params:
                    return optimized_params[opt_key]

                # Get regimes from config (dict or object)
                regimes = config.get("regimes", []) if isinstance(config, dict) else getattr(config, "regimes", [])

                # Also check optimization_results[0].regimes for v2 format
                if not regimes and isinstance(config, dict):
                    opt_results = config.get("optimization_results", [])
                    if opt_results:
                        regimes = opt_results[0].get("regimes", [])

                for regime in regimes:
                    r_id = regime.get("id", "") if isinstance(regime, dict) else getattr(regime, "id", "")
                    if r_id == regime_id:
                        if isinstance(regime, dict):
                            # v2 format: thresholds is a list of {name, value}
                            thresholds = regime.get("thresholds", [])
                            for t in thresholds:
                                if t.get("name") == threshold_name:
                                    return t.get("value", default)
                            # Also check direct keys for backwards compatibility
                            return regime.get(threshold_name, default)
                        else:
                            return getattr(regime, threshold_name, default)

                return default

            # Build current_params from JSON config (ADX/DI-based like original regime_engine)
            current_params = RegimeParams(
                adx_period=int(get_param("adx", "period", 14)),
                adx_trending_threshold=float(get_regime_threshold("BULL", "adx_min", 25.0)),
                adx_weak_threshold=float(get_regime_threshold("SIDEWAYS", "adx_max", 20.0)),
                di_diff_threshold=float(get_param("adx", "di_diff_threshold", 5.0)),
                rsi_period=int(get_param("rsi", "period", 14)),
                rsi_strong_bull=float(get_regime_threshold("BULL", "rsi_strong_bull", 55.0)),
                rsi_strong_bear=float(get_regime_threshold("BEAR", "rsi_strong_bear", 45.0)),
                atr_period=int(get_param("atr", "period", 14)),
                strong_move_pct=float(get_param("atr", "strong_move_pct", 1.5)),
                extreme_move_pct=float(get_param("atr", "extreme_move_pct", 3.0)),
            )

            # Create param_ranges with SAME VALUES (for optimizer - single-value ranges)
            param_ranges = AllParamRanges(
                adx=ADXParamRanges(
                    period=ParamRange(
                        min=current_params.adx_period,
                        max=current_params.adx_period,
                        step=1
                    ),
                    trending_threshold=ParamRange(
                        min=current_params.adx_trending_threshold,
                        max=current_params.adx_trending_threshold,
                        step=1
                    ),
                    weak_threshold=ParamRange(
                        min=current_params.adx_weak_threshold,
                        max=current_params.adx_weak_threshold,
                        step=1
                    ),
                    di_diff_threshold=ParamRange(
                        min=current_params.di_diff_threshold,
                        max=current_params.di_diff_threshold,
                        step=1
                    ),
                ),
                rsi=RSIParamRanges(
                    period=ParamRange(
                        min=current_params.rsi_period,
                        max=current_params.rsi_period,
                        step=1
                    ),
                    strong_bull=ParamRange(
                        min=current_params.rsi_strong_bull,
                        max=current_params.rsi_strong_bull,
                        step=1
                    ),
                    strong_bear=ParamRange(
                        min=current_params.rsi_strong_bear,
                        max=current_params.rsi_strong_bear,
                        step=1
                    ),
                ),
                atr=ATRParamRanges(
                    period=ParamRange(
                        min=current_params.atr_period,
                        max=current_params.atr_period,
                        step=1
                    ),
                    strong_move_pct=ParamRange(
                        min=current_params.strong_move_pct,
                        max=current_params.strong_move_pct,
                        step=0.1
                    ),
                    extreme_move_pct=ParamRange(
                        min=current_params.extreme_move_pct,
                        max=current_params.extreme_move_pct,
                        step=0.5
                    ),
                ),
            )

            logger.info(
                f"Calculating score with params from JSON: "
                f"adx={current_params.adx_period}/{current_params.adx_trending_threshold}/{current_params.adx_weak_threshold}, "
                f"di_diff={current_params.di_diff_threshold}, "
                f"rsi={current_params.rsi_period}"
            )

            # Get JSON config for per-regime threshold evaluation
            json_config_dict = None
            if isinstance(config, dict):
                json_config_dict = config
            elif hasattr(config, "model_dump"):
                json_config_dict = config.model_dump()
            elif hasattr(config, "dict"):
                json_config_dict = config.dict()

            # Create optimizer to classify regimes (we need the regimes Series)
            optimizer = RegimeOptimizer(
                data=df,
                param_ranges=param_ranges,
                json_config=json_config_dict
            )

            # Calculate indicators and classify regimes
            # Use JSON mode if config has optimization_results with regimes
            if json_config_dict and "optimization_results" in json_config_dict:
                logger.info("Using JSON-based regime classification for current score")
                indicators = optimizer._calculate_json_indicators(current_params)
                regimes = optimizer._classify_regimes_json(current_params, indicators)
            else:
                logger.info("Using legacy regime classification for current score")
                indicators = optimizer._calculate_indicators(current_params)
                regimes = optimizer._classify_regimes(current_params, indicators)

            # Convert regimes to Series for new scoring
            regimes_series = pd.Series(regimes, index=df.index)

            # Use new 5-component RegimeScore
            from src.core.scoring import calculate_regime_score, RegimeScoreConfig

            data_len = len(df)
            score_config = RegimeScoreConfig(
                warmup_bars=min(200, max(50, data_len // 10)),
                max_feature_lookback=max(
                    current_params.adx_period,
                    current_params.rsi_period,
                    current_params.atr_period,
                ),
                # Relaxed gates for scalping/high-frequency data
                min_segments=max(3, data_len // 200),
                min_avg_duration=2,
                max_switch_rate_per_1000=500,  # High switch rates are normal for scalping
                min_unique_labels=2,
                min_bars_for_scoring=max(30, data_len // 10),
            )
            score_result = calculate_regime_score(
                data=df,
                regimes=regimes_series,
                config=score_config,
            )

            score = score_result.total_score

            # Update main score label
            self._regime_opt_current_score_label.setText(f"{score:.1f}")

            # Color based on score and gate status
            if not score_result.gates_passed:
                color = "#ef4444"  # Red for gate failure
            elif score >= 75:
                color = "#22c55e"  # Green for good
            elif score >= 50:
                color = "#f59e0b"  # Orange for medium
            else:
                color = "#ef4444"  # Red for poor

            self._regime_opt_current_score_label.setStyleSheet(
                f"font-weight: bold; font-size: 12pt; color: {color};"
            )

            # Update components label with status
            if score_result.gates_passed:
                self._regime_opt_components_label.setText("✓ Valid")
                self._regime_opt_components_label.setStyleSheet("color: #22c55e; font-size: 9pt;")
            else:
                # Show gate failure reason
                failures = ", ".join(score_result.gate_failures[:2])
                self._regime_opt_components_label.setText(f"⚠️ {failures}")
                self._regime_opt_components_label.setStyleSheet("color: #ef4444; font-size: 9pt;")

            logger.info(f"Current regime score: {score:.2f}")

        except Exception as e:
            logger.error(f"Failed to calculate current regime score: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Calculation Failed",
                f"Failed to calculate score:\n{str(e)}"
            )

    @pyqtSlot()

    @pyqtSlot()
    def _on_regime_opt_draw_selected(self) -> None:
        """Draw selected optimization result's regime periods on chart.

        Clears all existing regime lines first, then draws the new ones.
        """
        # Get selected row from table
        selected_rows = self._regime_opt_top5_table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a result row from the table first."
            )
            return

        # Get row index and retrieve original index from UserRole
        row = selected_rows[0].row()
        rank_item = self._regime_opt_top5_table.item(row, 0)

        if rank_item is None:
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Could not retrieve selection data."
            )
            return

        # Get original index from UserRole
        original_index = rank_item.data(Qt.ItemDataRole.UserRole)
        if original_index is None:
            original_index = row

        if original_index >= len(self._regime_opt_all_results):
            QMessageBox.warning(
                self,
                "Invalid Selection",
                "Selected row is out of range."
            )
            return

        selected_result = self._regime_opt_all_results[original_index]
        regime_history = selected_result.get("regime_history", [])

        if not regime_history:
            QMessageBox.warning(
                self,
                "No Regime Data",
                "Selected result has no regime history to draw.\n\n"
                "The optimization may not have saved regime periods."
            )
            return

        # Emit signal to draw regime lines on chart (clears existing lines automatically)
        if hasattr(self, "draw_regime_lines_requested"):
            self.draw_regime_lines_requested.emit(regime_history)
            rank = row + 1
            score = selected_result.get("score", 0)
            logger.info(f"Drawing {len(regime_history)} regime periods from Rank #{rank} (score: {score:.1f})")

            QMessageBox.information(
                self,
                "Regime Lines Drawn",
                f"Drew {len(regime_history)} regime periods on chart.\n\n"
                f"Rank: #{rank}\n"
                f"Score: {score:.1f}"
            )
        else:
            QMessageBox.warning(
                self,
                "Signal Not Connected",
                "Chart drawing signal is not connected.\n"
                "Cannot draw regime lines."
            )
