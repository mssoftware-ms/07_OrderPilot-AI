"""Regime Optimization - User Actions Mixin.

Handles user action events and interactions.

Agent: CODER-013
Task: 3.1.3 - Split regime_optimization_mixin
File: 3/5 - Actions (390 LOC target)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from src.core.tradingbot.config.regime_loader_v2 import RegimeConfigLoaderV2

logger = logging.getLogger(__name__)


class RegimeOptimizationActionsMixin:
    """User action handlers for regime optimization.

    Handles:
        - Export results to JSON
        - Save selected result to history
        - Apply selected result to regime config
    """

    @pyqtSlot()
    def _on_regime_opt_export(self) -> None:
        """Export optimization results with parameter ranges to JSON."""
        from PyQt6.QtWidgets import QFileDialog, QMessageBox
        import json

        if not self._regime_opt_all_results:
            QMessageBox.warning(
                self,
                "No Results",
                "No optimization results available. Run optimization first."
            )
            return

        # Get default export directory
        # Path: src/ui/dialogs/entry_analyzer/this_file.py -> 5x parent = project root
        project_root = Path(__file__).parent.parent.parent.parent.parent
        default_dir = project_root / "03_JSON" / "Entry_Analyzer" / "Regime"
        default_dir.mkdir(parents=True, exist_ok=True)

        # Get symbol and timeframe for filename with timestamp
        symbol = getattr(self, "_current_symbol", "BTCUSDT")
        timeframe = getattr(self, "_current_timeframe", "5m")
        timestamp = datetime.utcnow().strftime("%y%m%d%H%M%S")
        default_filename = f"{timestamp}_regime_optimization_results_{symbol}_{timeframe}.json"

        # Open file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Regime Optimization Results",
            str(default_dir / default_filename),
            "JSON Files (*.json)"
        )

        if not file_path:
            return  # User cancelled

        try:
            # Get parameter ranges from Setup tab
            param_ranges = {}
            if hasattr(self, "_regime_setup_config"):
                param_ranges = self._regime_setup_config.copy()

            # Get max_trials
            max_trials = getattr(self, "_regime_opt_max_trials", None)
            max_trials_value = max_trials.value() if max_trials else 150

            # Build export data
            # NOTE: entry_params and evaluation_params are NOT included -
            #       Only entry_expression is used for Trading Bot execution.
            export_data = {
                "version": "2.0",
                "meta": {
                    "stage": "regime_optimization",
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "created_at": datetime.utcnow().isoformat() + "Z",
                    "total_combinations": len(self._regime_opt_all_results),
                    "completed": len(self._regime_opt_all_results),
                    "method": "tpe_multivariate",
                    "max_trials": max_trials_value,
                },
                "parameter_ranges": param_ranges,
                "results": self._regime_opt_all_results,
            }

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Exported {len(self._regime_opt_all_results)} results to {file_path}")

            QMessageBox.information(
                self,
                "Export Successful",
                f"Exported {len(self._regime_opt_all_results)} results to:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export results:\n{str(e)}"
            )


    @pyqtSlot()
    def _on_save_selected_to_history(self) -> None:
        """Save selected optimization result to optimization_results[] in JSON.

        Adds selected result to history without applying parameters.
        Keeps top 10 results in history.
        """
        from PyQt6.QtWidgets import QMessageBox
        import json

        try:
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
            rank_item = self._regime_opt_top5_table.item(row, 0)  # Rank column stores original index

            if rank_item is None:
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Could not retrieve selection data."
                )
                return

            # Get original index from UserRole (stored during table population)
            original_index = rank_item.data(Qt.ItemDataRole.UserRole)
            if original_index is None:
                # Fallback to row index if UserRole not set (backwards compatibility)
                original_index = row

            if original_index >= len(self._regime_opt_all_results):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Selected row is out of range."
                )
                return

            selected_result = self._regime_opt_all_results[original_index]
            params = selected_result.get("params", {})
            score = selected_result.get("score", 0)
            metrics = selected_result.get("metrics", {})
            trial_number = selected_result.get("trial_number", original_index + 1)
            rank = row + 1  # Visual rank for display

            logger.info(f"Saving optimization result (score {score:.2f}) to history")

            # Load current JSON config
            config_path = Path("03_JSON/Entry_Analyzer/Regime/entry_analyzer_regime.json")
            if not config_path.exists():
                QMessageBox.critical(
                    self,
                    "Config Not Found",
                    f"Regime config file not found:\n{config_path}"
                )
                return

            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Convert params to new v2.0 format (indicator.param: value)
            converted_params = self._convert_params_to_v2_format(params)

            # Create optimization result entry
            result_entry = {
                "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "score": float(score),
                "rank": rank,
                "params": converted_params,
                "metrics": metrics,
                "trial_number": trial_number,
                "optimization_config": {
                    "mode": "QUICK",
                    "max_trials": getattr(self, "_regime_opt_max_trials", None).value() if hasattr(self, "_regime_opt_max_trials") else 150,
                    "symbol": getattr(self, "_current_symbol", "UNKNOWN"),
                    "timeframe": getattr(self, "_current_timeframe", "5m")
                },
                "applied": False
            }

            # Add to optimization_results (insert at beginning)
            if "optimization_results" not in config_data:
                config_data["optimization_results"] = []

            config_data["optimization_results"].insert(0, result_entry)

            # Keep only top 10
            config_data["optimization_results"] = config_data["optimization_results"][:10]

            # Update metadata
            config_data["metadata"]["updated_at"] = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            # Save updated config
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Successfully saved result to history: {config_path}")

            QMessageBox.information(
                self,
                "Saved to History",
                f"Successfully saved optimization result to history!\n\n"
                f"Score: {score:.2f}\n"
                f"Rank: #{rank}\n"
                f"Trial: {trial_number}\n\n"
                f"Total in history: {len(config_data['optimization_results'])}/10"
            )

        except Exception as e:
            logger.error(f"Failed to save result to history: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Save Failed",
                f"Failed to save result to history:\n\n{str(e)}"
            )


    @pyqtSlot()
    def _on_apply_selected_to_regime_config(self) -> None:
        """Save & Load in Regime - Export selected result and load in Regime tab.

        Builds pure v2.0 format from scratch (no v1.0 base config).

        Workflow:
        1. Build v2.0 config from optimization result
        2. Build indicators[] from flattened params
        3. Build regimes[] from regime threshold params
        4. Save to new file using RegimeConfigLoaderV2
        5. Clear both tables
        6. Load new config in Regime tab
        """
        from PyQt6.QtWidgets import QMessageBox
        from datetime import datetime
        from src.core.tradingbot.config.regime_loader_v2 import RegimeConfigLoaderV2

        try:
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
            rank_item = self._regime_opt_top5_table.item(row, 0)  # Rank column stores original index

            if rank_item is None:
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Could not retrieve selection data."
                )
                return

            # Get original index from UserRole (stored during table population)
            original_index = rank_item.data(Qt.ItemDataRole.UserRole)
            if original_index is None:
                # Fallback to row index if UserRole not set (backwards compatibility)
                original_index = row

            if original_index >= len(self._regime_opt_all_results):
                QMessageBox.warning(
                    self,
                    "Invalid Selection",
                    "Selected row is out of range."
                )
                return

            selected_result = self._regime_opt_all_results[original_index]
            params = selected_result.get("params", {})
            score = selected_result.get("score", 0)
            rank = row + 1  # Display rank (visual position in table)

            logger.info(f"Save & Load in Regime: Rank #{rank}, score {score:.2f}")

            # Build parameter summary dynamically
            param_summary = "\n".join([f"  {k}: {v}" for k, v in params.items()])

            # Get symbol and timeframe for filename
            symbol = getattr(self, "_current_symbol", "BTCUSDT")
            timeframe = getattr(self, "_current_timeframe", "5m")

            # Confirm with user
            reply = QMessageBox.question(
                self,
                "Save & Load in Regime",
                f"Save and load optimization result in Regime tab?\n\n"
                f"Rank: #{rank}\n"
                f"Score: {score:.2f}\n\n"
                f"Parameters:\n{param_summary}\n\n"
                f"This will:\n"
                f"1. Create new regime config (Rank #{rank})\n"
                f"2. Update indicator parameters\n"
                f"3. Update regime thresholds\n"
                f"4. Load config in Regime tab",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Step 1: Build indicators[] from flattened params
            indicators = self._build_indicators_from_params(params)

            # Step 2: Build regimes[] from regime threshold params
            regimes = self._build_regimes_from_params(params)

            # Step 3: Build v2.0 config structure
            trial_number = selected_result.get("trial_number", rank)
            metrics = selected_result.get("metrics", {})
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

            config_data = {
                "schema_version": "2.0.0",
                "metadata": {
                    "author": "OrderPilot-AI",
                    "created_at": timestamp,
                    "updated_at": timestamp,
                    "tags": [symbol, timeframe, "regime", "optimization"],
                    "notes": (
                        f"Rank #{rank} optimization result applied on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC. "
                        f"Score: {score:.2f}. Trial: {trial_number}"
                    ),
                    "trading_style": "Daytrading",  # Default, can be customized
                    "description": f"Optimized regime configuration for {symbol} {timeframe} with {len(indicators)} indicators and {len(regimes)} regimes."
                },
                "optimization_results": [
                    {
                        "timestamp": timestamp,
                        "score": float(score),
                        "trial_number": trial_number,
                        "applied": True,
                        "indicators": indicators,
                        "regimes": regimes
                    }
                ]
                # NOTE: entry_params and evaluation_params are NOT included -
                #       Only entry_expression is used for Trading Bot execution.
            }

            # Step 4: Save to new file with validation
            project_root = Path(__file__).parent.parent.parent.parent.parent
            export_dir = project_root / "03_JSON" / "Entry_Analyzer" / "Regime"
            export_dir.mkdir(parents=True, exist_ok=True)

            timestamp_str = datetime.utcnow().strftime("%y%m%d%H%M%S")
            export_filename = f"{timestamp_str}_regime_optimization_results_{symbol}_{timeframe}_#{rank}.json"
            export_path = export_dir / export_filename

            logger.info(f"Saving v2.0 config to: {export_path}")

            # Use RegimeConfigLoaderV2 for validation and save
            loader = RegimeConfigLoaderV2()
            loader.save_config(config_data, export_path, indent=2, validate=True)

            logger.info(f"Successfully saved v2.0 regime config (Rank #{rank}) to: {export_path}")

            # Step 5: Clear detected regimes table (will be repopulated with new config)
            # NOTE: Keep optimization results table - results are valuable for reference
            if hasattr(self, "_detected_regimes_table"):
                self._detected_regimes_table.setRowCount(0)
                logger.info("Cleared Detected Regimes table (will repopulate with new config)")

            # Step 6: Load new file in Regime tab
            if hasattr(self, "_load_regime_config"):
                self._load_regime_config(export_path, show_error=True)
                logger.info(f"Loaded config in Regime tab: {export_path}")

            QMessageBox.information(
                self,
                "Success",
                f"Successfully saved and loaded v2.0 regime config!\n\n"
                f"File: {export_filename}\n\n"
                f"Rank: #{rank}\n"
                f"Score: {score:.2f}\n\n"
                f"Config loaded in Regime tab."
            )

        except Exception as e:
            import traceback
            full_traceback = traceback.format_exc()
            logger.error(f"Failed to save & load regime config: {e}")
            logger.error(f"Full traceback:\n{full_traceback}")
            QMessageBox.critical(
                self,
                "Save & Load Failed",
                f"Failed to save & load regime config:\n\n{str(e)}\n\nDetails in log file."
            )

