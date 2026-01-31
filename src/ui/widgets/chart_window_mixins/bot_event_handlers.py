"""Bot Event Handlers - UI event handlers and settings management.

Contains methods for handling UI events and managing bot settings:
- Button click handlers (start, stop, pause)
- Mode change handlers (KI mode, trailing mode)
- Settings persistence
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt

if TYPE_CHECKING:
    from src.core.tradingbot import BotController

logger = logging.getLogger(__name__)


class BotEventHandlersMixin:
    """Mixin providing bot event handlers and settings management."""

    # ==================== BUTTON EVENT HANDLERS ====================

    def _on_bot_start_clicked(self) -> None:
        """Handle bot start button click.

        If RegimeEngineJSON (Config) is selected in Daily Strategy tab,
        skip the dialog and start bot directly with automatic regime detection.
        Otherwise, open the strategy selection dialog.
        """
        # Check if JSON mode is selected in Daily Strategy tab (radio button ID 2)
        if hasattr(self, 'analysis_method_group') and self.analysis_method_group.checkedId() == 2:
            logger.info("Bot start requested - JSON mode selected, skipping dialog")
            self._start_bot_with_json_auto()
            return

        logger.info("Bot start requested - opening strategy selection dialog")

        # Open strategy selection dialog
        from src.ui.dialogs.bot_start_strategy_dialog import BotStartStrategyDialog

        dialog = BotStartStrategyDialog(parent=self)

        # Connect strategy applied signal
        dialog.strategy_applied.connect(self._on_strategy_selected)

        result = dialog.exec()

        if result != BotStartStrategyDialog.DialogCode.Accepted:
            logger.info("Bot start cancelled by user")
            return

        # If accepted, strategy has been applied and bot will start via signal

    def _start_bot_with_json_auto(self) -> None:
        """Start bot with automatic JSON-based regime detection and strategy scoring.

        Workflow:
        1. Calculate features from chart data
        2. Detect current market regime
        3. Load ALL available JSON configs
        4. Score each config against current regime
        5. Select best matching config
        6. Start bot with best config
        """
        from pathlib import Path
        from PyQt6.QtWidgets import QMessageBox

        try:
            self._update_bot_status("ANALYZING", "#ffeb3b")

            # Get chart widget data
            chart_widget = getattr(self, 'chart_widget', None)
            if not chart_widget or not hasattr(chart_widget, 'data') or chart_widget.data is None:
                self._update_bot_status("ERROR", "#f44336")
                logger.error("No chart data available for regime detection")
                QMessageBox.warning(
                    self,
                    "Keine Chart-Daten",
                    "Bitte laden Sie zuerst Chart-Daten, bevor Sie den Bot starten."
                )
                return

            df = chart_widget.data
            if len(df) < 50:
                self._update_bot_status("ERROR", "#f44336")
                logger.error("Not enough data for regime detection")
                QMessageBox.warning(
                    self,
                    "Nicht genug Daten",
                    "Es werden mindestens 50 Kerzen für die Regime-Erkennung benötigt."
                )
                return

            # ========== Step 1: Calculate Features ==========
            from src.core.tradingbot.feature_engine import FeatureEngine

            symbol = getattr(chart_widget, 'current_symbol', 'UNKNOWN')
            feature_engine = FeatureEngine()
            features = feature_engine.calculate_features(df, symbol)

            if not features:
                self._update_bot_status("ERROR", "#f44336")
                logger.error("Feature calculation failed")
                QMessageBox.warning(
                    self,
                    "Feature-Fehler",
                    "Feature-Berechnung fehlgeschlagen. Nicht genug Daten?"
                )
                return

            # ========== Step 2: Detect Regime ==========
            from src.core.tradingbot.regime_engine import RegimeEngine

            regime_engine = RegimeEngine()
            current_regime = regime_engine.classify(features)

            regime_str = current_regime.regime.value if hasattr(current_regime.regime, 'value') else str(current_regime.regime)
            confidence = getattr(current_regime, 'regime_confidence', 0.5)
            logger.info(f"Detected regime: {regime_str} (confidence: {confidence:.1%})")

            # Update Daily Strategy display
            if hasattr(self, 'regime_label'):
                self.regime_label.setText(regime_str)
            if hasattr(self, '_set_daily_status'):
                self._set_daily_status(f"Regime erkannt: {regime_str}")

            # ========== Step 3: Find JSON Configs ==========
            config_dir = Path("03_JSON/Trading_Bot")

            if not config_dir.exists():
                self._update_bot_status("ERROR", "#f44336")
                logger.error(f"Config directory not found: {config_dir}")
                QMessageBox.warning(
                    self,
                    "Verzeichnis fehlt",
                    f"Config-Verzeichnis nicht gefunden:\n{config_dir}"
                )
                return

            # Only get JSON files directly in this directory (no subdirectories)
            config_files = list(config_dir.glob("*.json"))

            if not config_files:
                self._update_bot_status("ERROR", "#f44336")
                logger.error("No JSON strategy configs found")
                QMessageBox.warning(
                    self,
                    "Keine JSON-Configs",
                    f"Keine JSON-Strategie-Dateien gefunden in:\n" +
                    "\n".join(str(d) for d in config_dirs)
                )
                return

            logger.info(f"Found {len(config_files)} JSON configs to evaluate")

            # ========== Step 4: Score Each Config Against Current Regime ==========
            from src.core.tradingbot.config.loader import ConfigLoader
            from src.core.tradingbot.config.detector import RegimeDetector
            from src.core.tradingbot.config.router import StrategyRouter
            from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

            # Track all evaluated configs with their results
            evaluated_configs = []  # List of (config_path, strategy_name, score, matched_set)
            errors = []  # Track evaluation errors

            calculator = IndicatorValueCalculator()
            indicator_values = calculator.calculate_indicator_values(features)

            # Log key indicator values for debugging
            key_indicators = ['rsi14', 'adx14', 'macd12_26_9', 'stoch14', 'bb20']
            debug_values = []
            for ind in key_indicators:
                if ind in indicator_values:
                    vals = indicator_values[ind]
                    if isinstance(vals, dict):
                        val_str = ", ".join(f"{k}={v:.2f}" for k, v in vals.items() if isinstance(v, (int, float)))
                        debug_values.append(f"{ind}: {{{val_str}}}")
            logger.info(f"Current indicator values: {'; '.join(debug_values)}")

            for config_file in config_files:
                try:
                    loader = ConfigLoader()
                    config = loader.load_config(str(config_file))

                    if not config or not hasattr(config, 'regimes'):
                        errors.append(f"{config_file.name}: Keine Regimes definiert")
                        continue

                    # Detect active regimes from this config
                    detector = RegimeDetector(config.regimes)
                    active_regimes = detector.detect_active_regimes(indicator_values, scope='entry')

                    if not active_regimes:
                        errors.append(f"{config_file.name}: Kein passendes Regime erkannt")
                        continue

                    # Route to strategy set
                    if hasattr(config, 'routing') and hasattr(config, 'strategy_sets'):
                        router = StrategyRouter(config.routing, config.strategy_sets)
                        matched_sets = router.route_regimes(active_regimes)

                        if matched_sets:
                            # Take best scoring match from this config
                            best_match = max(matched_sets, key=lambda m: m.match_score)
                            evaluated_configs.append((
                                str(config_file),
                                best_match.name,
                                best_match.match_score,
                                best_match
                            ))
                            logger.info(
                                f"Config '{config_file.name}' → Strategy: {best_match.name} "
                                f"(Score: {best_match.match_score:.2f})"
                            )
                        else:
                            errors.append(f"{config_file.name}: Keine Strategie geroutet")
                    else:
                        errors.append(f"{config_file.name}: Kein Routing/Strategy-Sets")

                except Exception as e:
                    errors.append(f"{config_file.name}: {str(e)[:50]}")
                    logger.warning(f"Failed to evaluate config {config_file.name}: {e}")
                    continue

            # Log errors for debugging
            if errors:
                logger.warning(f"Config evaluation errors:\n" + "\n".join(errors))

            # ========== Step 5: Select Best Strategy ==========
            if not evaluated_configs:
                self._update_bot_status("ERROR", "#f44336")
                logger.error(f"No strategy matched for regime: {regime_str}")

                error_details = "\n".join(errors[:5]) if errors else "Keine Details verfügbar"
                QMessageBox.warning(
                    self,
                    "Keine Strategie gefunden",
                    f"Keine Strategie passt zum aktuellen Regime:\n{regime_str}\n\n"
                    f"{len(config_files)} Configs geprüft.\n\n"
                    f"Fehler:\n{error_details}"
                )
                return

            # Sort by score (highest first)
            evaluated_configs.sort(key=lambda x: x[2], reverse=True)
            best_config_path, best_strategy_name, best_score, best_matched_set = evaluated_configs[0]

            # If score is low, ask user if they want to proceed
            if best_score < 0.7:
                # Build options list
                options_text = "\n".join([
                    f"  • {name}: {score:.1%}" for _, name, score, _ in evaluated_configs[:5]
                ])

                reply = QMessageBox.question(
                    self,
                    "Strategie mit niedrigem Score",
                    f"Aktuelles Regime: {regime_str}\n\n"
                    f"Beste Strategie: {best_strategy_name}\n"
                    f"Score: {best_score:.1%}\n\n"
                    f"Alle bewerteten Strategien:\n{options_text}\n\n"
                    f"Mit bester Strategie fortfahren?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if reply != QMessageBox.StandardButton.Yes:
                    self._update_bot_status("STOPPED", "#9e9e9e")
                    logger.info("User cancelled low-score strategy")
                    return

            # ========== Step 6: Start Bot with Best Config ==========
            logger.info(
                f"Selected config: {Path(best_config_path).name} "
                f"(Strategy: {best_matched_set.name}, Score: {best_score:.2f})"
            )

            if hasattr(self, '_set_daily_status'):
                self._set_daily_status(
                    f"Beste Strategie: {best_matched_set.name} (Score: {best_score:.2f})"
                )

            # Start bot with best JSON config
            self._start_bot_with_json_config(best_config_path, best_matched_set)

            # Update UI state
            self.bot_start_btn.setEnabled(False)
            self.bot_stop_btn.setEnabled(True)
            self.bot_pause_btn.setEnabled(True)

            if hasattr(self, '_update_signals_tab_bot_button'):
                self._update_signals_tab_bot_button(running=True)

            self._subscribe_to_regime_changes()

        except Exception as e:
            logger.error(f"Failed to start bot with JSON auto: {e}", exc_info=True)
            self._update_bot_status("ERROR", "#f44336")
            QMessageBox.critical(
                self,
                "Bot Start Fehler",
                f"Fehler beim automatischen Bot-Start:\n{e}"
            )

    def _on_strategy_selected(self, config_path: str, matched_strategy_set: Any) -> None:
        """Handle strategy selection from dialog - starts bot with selected strategy.

        Args:
            config_path: Path to selected JSON config
            matched_strategy_set: Matched strategy set from routing
        """
        logger.info(f"Strategy selected: {config_path}")
        self._update_bot_status("STARTING", "#ffeb3b")

        try:
            # Store config path and strategy set for bot initialization
            self._selected_config_path = config_path
            self._selected_strategy_set = matched_strategy_set

            # Start bot with JSON config
            self._start_bot_with_json_config(config_path, matched_strategy_set)

        except Exception as e:
            logger.error(f"Failed to start bot: {e}", exc_info=True)
            self._update_bot_status("ERROR", "#f44336")
            # Issue #9: Update Trading tab button on error
            if hasattr(self, '_update_signals_tab_bot_button'):
                self._update_signals_tab_bot_button(running=False)

            # Show error message
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Bot Start Error",
                f"Failed to start bot:\n{e}"
            )
            return

        self.bot_start_btn.setEnabled(False)
        self.bot_stop_btn.setEnabled(True)
        self.bot_pause_btn.setEnabled(True)

        # Issue #9: Update Trading tab button to show running state (green)
        if hasattr(self, '_update_signals_tab_bot_button'):
            self._update_signals_tab_bot_button(running=True)

        # Subscribe to regime_changed events for UI notifications
        self._subscribe_to_regime_changes()

    def _subscribe_to_regime_changes(self) -> None:
        """Subscribe to regime_changed events from BotController."""
        try:
            # Check if bot controller has event bus
            if not self._bot_controller or not hasattr(self._bot_controller, '_event_bus'):
                logger.debug("Bot controller has no event bus - skipping regime change subscription")
                return

            event_bus = self._bot_controller._event_bus
            if event_bus is None:
                logger.debug("Event bus is None - skipping regime change subscription")
                return

            # Subscribe to regime_changed event
            event_bus.subscribe('regime_changed', self._on_regime_changed_notification)
            logger.info("Subscribed to regime_changed events")

        except Exception as e:
            logger.error(f"Failed to subscribe to regime changes: {e}", exc_info=True)

    def _on_regime_changed_notification(self, event_data: dict) -> None:
        """Handle regime_changed event from BotController.

        Args:
            event_data: Dictionary with keys:
                - old_strategy: Previous strategy name
                - new_strategy: New strategy name
                - new_regimes: Comma-separated regime names
                - timestamp: Event timestamp
        """
        try:
            old_strategy = event_data.get('old_strategy', 'None')
            new_strategy = event_data.get('new_strategy', 'Unknown')
            new_regimes = event_data.get('new_regimes', 'Unknown')

            # Log notification
            logger.info(
                f"Regime changed notification: {old_strategy} -> {new_strategy} "
                f"(Regimes: {new_regimes})"
            )

            # Update regime badge if available
            if hasattr(self, '_regime_badge') and self._regime_badge:
                regime_text = f"{new_regimes}"
                self._regime_badge.set_regime(regime_text)
                self._regime_badge.setToolTip(f"Current Strategy: {new_strategy}")

            # Show notification message in status bar or bot log
            notification_msg = (
                f"⚠ Regime-Wechsel: Neue Strategie '{new_strategy}' aktiv "
                f"(Regimes: {new_regimes})"
            )

            # Log to bot activity log
            if self._bot_controller and hasattr(self._bot_controller, '_log_activity'):
                self._bot_controller._log_activity("STRATEGY_SWITCH", notification_msg)

            # Show visual notification (yellow background, auto-hide after 10 seconds)
            if hasattr(self, 'bot_status_label'):
                self._show_strategy_change_notification(new_strategy, new_regimes)

        except Exception as e:
            logger.error(f"Error handling regime change notification: {e}", exc_info=True)

    def _show_strategy_change_notification(self, strategy_name: str, regimes: str) -> None:
        """Show visual notification for strategy change.

        Args:
            strategy_name: Name of new strategy
            regimes: Comma-separated regime names
        """
        try:
            # Create notification label if not exists
            if not hasattr(self, '_strategy_notification_label'):
                from PyQt6.QtWidgets import QLabel
                from PyQt6.QtCore import QTimer

                self._strategy_notification_label = QLabel()
                self._strategy_notification_label.setStyleSheet(
                    "background-color: #ffa726; color: white; "
                    "padding: 8px; border-radius: 4px; font-weight: bold;"
                )
                self._strategy_notification_label.setWordWrap(True)

                # Add to bot tab layout if available
                if hasattr(self, 'bot_tab') and hasattr(self.bot_tab, 'layout'):
                    layout = self.bot_tab.layout()
                    if layout:
                        # Insert at top of layout
                        layout.insertWidget(0, self._strategy_notification_label)

                # Create timer for auto-hide
                self._strategy_notification_timer = QTimer()
                self._strategy_notification_timer.setSingleShot(True)
                self._strategy_notification_timer.timeout.connect(
                    lambda: self._strategy_notification_label.setVisible(False)
                )

            # Update notification text
            self._strategy_notification_label.setText(
                f"⚠ Strategy switched to: {strategy_name} (Regimes: {regimes})"
            )
            self._strategy_notification_label.setVisible(True)

            # Auto-hide after 10 seconds
            if hasattr(self, '_strategy_notification_timer'):
                self._strategy_notification_timer.start(10000)

        except Exception as e:
            logger.error(f"Failed to show strategy change notification: {e}", exc_info=True)

    def _on_bot_start_json_clicked(self) -> None:
        """Handle bot start (JSON Entry) button click - loads Regime JSON with entry_expression.

        NEUER HANDLER für JSON-basierte Entry Logik:
        1. File Picker für Regime JSON (mit entry_expression)
        2. Lädt JSON und validiert entry_expression
        3. Startet Bot mit JSON Entry Scorer
        4. Nach Entry: Normale Bot-Logik (Tabelle füllen, SL/TP, etc.)
        """
        logger.info("Bot start (JSON Entry) requested")

        # File Picker für Regime JSON
        from PyQt6.QtWidgets import QFileDialog, QMessageBox

        json_file, _ = QFileDialog.getOpenFileName(
            self,
            "Regime JSON mit entry_expression auswählen",
            "03_JSON/Entry_Analyzer/Regime/",
            "JSON Files (*.json)"
        )

        if not json_file:
            logger.info("JSON Entry bot start cancelled - no file selected")
            return

        logger.info(f"Loading Regime JSON: {json_file}")

        try:
            # Lade und validiere JSON
            from src.core.tradingbot.json_entry_loader import JsonEntryConfig

            config = JsonEntryConfig.from_files(regime_json_path=json_file)

            # Validiere dass entry_expression vorhanden ist
            if not config.entry_expression or config.entry_expression.strip() == "":
                QMessageBox.critical(
                    self,
                    "❌ Keine Entry Expression",
                    f"Die JSON-Datei enthält keine 'entry_expression'!\n\n"
                    f"Datei: {json_file}\n\n"
                    f"Bitte füge zuerst eine entry_expression hinzu.\n"
                    f"Nutze dazu:\n"
                    f"• Entry Analyzer → CEL Editor\n"
                    f"• Oder: Python Script add_entry_expression.py"
                )
                return

            # Zeige Info welche Expression geladen wurde
            QMessageBox.information(
                self,
                "✅ JSON geladen",
                f"Regime JSON erfolgreich geladen!\n\n"
                f"Datei: {Path(json_file).name}\n"
                f"Regimes: {len(config.regime_thresholds)}\n"
                f"Indicators: {len(config.indicators)}\n\n"
                f"Entry Expression (erste 100 Zeichen):\n"
                f"{config.entry_expression[:100]}...\n\n"
                f"Bot wird jetzt gestartet mit JSON Entry Logik."
            )

            # Starte Bot mit JSON Entry Config
            logger.info(f"Starting bot with JSON Entry config: {config.regime_json_path}")
            logger.info(f"Entry expression: {config.entry_expression[:80]}...")

            # Store config for bot initialization
            self._json_entry_config = config

            # Start bot with JSON Entry mode
            self._start_bot_with_json_entry(config)

        except FileNotFoundError as e:
            QMessageBox.critical(
                self,
                "❌ Datei nicht gefunden",
                f"Regime JSON konnte nicht geladen werden:\n\n{e}"
            )
            logger.error(f"JSON file not found: {e}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "❌ Fehler beim Laden",
                f"Fehler beim Laden der Regime JSON:\n\n{e}\n\n"
                f"Prüfe ob das JSON-Format korrekt ist."
            )
            logger.exception(f"Failed to load JSON Entry config: {e}")

    def _on_bot_stop_clicked(self) -> None:
        """Handle bot stop button click."""
        logger.info("Bot stop requested")
        self._stop_bot()

        self._update_bot_status("STOPPED", "#9e9e9e")
        self.bot_start_btn.setEnabled(True)
        self.bot_stop_btn.setEnabled(False)
        self.bot_pause_btn.setEnabled(False)

        # Issue #9: Update Trading tab button to show stopped state (red)
        if hasattr(self, '_update_signals_tab_bot_button'):
            self._update_signals_tab_bot_button(running=False)

    def _on_bot_pause_clicked(self) -> None:
        """Handle bot pause button click."""
        bot_controller = getattr(self, "_bot_controller", None)
        if bot_controller:
            if self.bot_pause_btn.text() == "Pause":
                bot_controller.pause()
                self.bot_pause_btn.setText("Resume")
                self._update_bot_status("PAUSED", "#ff9800")
            else:
                bot_controller.resume()
                self.bot_pause_btn.setText("Pause")
                self._update_bot_status("RUNNING", "#26a69a")

    # ==================== MODE CHANGE HANDLERS ====================

    def _on_ki_mode_changed(self, mode: str) -> None:
        """Handle KI mode change."""
        logger.info(f"KI mode changed to: {mode}")
        bot_controller = getattr(self, "_bot_controller", None)
        if bot_controller:
            bot_controller.set_ki_mode(mode)

    def _on_trailing_mode_changed(self, mode: str = "") -> None:
        """Handle trailing mode change - toggle field visibility based on mode."""
        current_mode = self.trailing_mode_combo.currentText()
        is_pct = current_mode == "PCT"
        is_atr = current_mode == "ATR"

        disabled_style = "color: #666666;"
        enabled_style = ""

        # PCT distance only for PCT mode
        self.trailing_distance_spin.setEnabled(is_pct)
        self.trailing_distance_spin.setStyleSheet(enabled_style if is_pct else disabled_style)

        # ATR settings only for ATR mode
        self.regime_adaptive_cb.setEnabled(is_atr)
        self.atr_multiplier_spin.setEnabled(is_atr)
        self.atr_trending_spin.setEnabled(is_atr)
        self.atr_ranging_spin.setEnabled(is_atr)
        self.volatility_bonus_spin.setEnabled(is_atr)

        self.regime_adaptive_cb.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_multiplier_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_trending_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.atr_ranging_spin.setStyleSheet(enabled_style if is_atr else disabled_style)
        self.volatility_bonus_spin.setStyleSheet(enabled_style if is_atr else disabled_style)

        # Update regime-adaptive visibility when in ATR mode
        if is_atr:
            self._on_regime_adaptive_changed()

    def _on_regime_adaptive_changed(self, state: int = 0) -> None:
        """Handle regime-adaptive checkbox change - toggle field visibility."""
        if self.trailing_mode_combo.currentText() != "ATR":
            return

        is_adaptive = self.regime_adaptive_cb.isChecked()

        # Fixed multiplier only visible when NOT adaptive
        self.atr_multiplier_spin.setEnabled(not is_adaptive)

        # Adaptive settings only visible when adaptive
        self.atr_trending_spin.setEnabled(is_adaptive)
        self.atr_ranging_spin.setEnabled(is_adaptive)
        self.volatility_bonus_spin.setEnabled(is_adaptive)

        disabled_style = "color: #666666;"
        enabled_style = ""

        self.atr_multiplier_spin.setStyleSheet(enabled_style if not is_adaptive else disabled_style)
        self.atr_trending_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)
        self.atr_ranging_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)
        self.volatility_bonus_spin.setStyleSheet(enabled_style if is_adaptive else disabled_style)

    def _on_display_option_changed(self, state: int) -> None:
        """Handle display option checkbox change."""
        if not hasattr(self, 'chart_widget'):
            return

        # Entry markers visibility
        show_markers = self.show_entry_markers_cb.isChecked()
        if hasattr(self.chart_widget, '_bot_overlay_state'):
            if not show_markers:
                self.chart_widget.clear_bot_markers()

        # Stop lines visibility
        show_stops = self.show_stop_lines_cb.isChecked()
        if hasattr(self.chart_widget, '_bot_overlay_state'):
            if not show_stops:
                self.chart_widget.clear_stop_lines()
            else:
                bot_controller = getattr(self, "_bot_controller", None)
                if bot_controller and bot_controller.position:
                    self.chart_widget.display_position(bot_controller.position)

    def _on_debug_hud_changed(self, state: int) -> None:
        """Handle debug HUD checkbox change."""
        if hasattr(self, 'chart_widget') and hasattr(self.chart_widget, 'set_debug_hud_visible'):
            self.chart_widget.set_debug_hud_visible(state == Qt.CheckState.Checked.value)

    def _on_derivathandel_changed(self, state: int) -> None:
        """Handle Derivathandel checkbox change - toggle derivative columns visibility."""
        is_enabled = self.enable_derivathandel_cb.isChecked()
        logger.info(f"Derivathandel: {'enabled' if is_enabled else 'disabled'}")

        # Toggle derivative columns visibility in signals table
        # Issue #19 FIX: Correct columns are 18, 19, 20, 21 (D P&L €, D P&L %, Hebel, WKN)
        # NOT 13, 14, 15, 16, 17 which are P&L USDT, Trading fees %, Trading fees, Invest, Stück!
        if hasattr(self, 'signals_table'):
            for col in [18, 19, 20, 21]:  # D P&L €, D P&L %, Hebel, WKN
                self.signals_table.setColumnHidden(col, not is_enabled)

        # Toggle derivative labels visibility in Current Position GroupBox
        deriv_labels = [
            'deriv_separator', 'deriv_wkn_label', 'deriv_leverage_label',
            'deriv_spread_label', 'deriv_ask_label', 'deriv_pnl_label'
        ]
        for label_name in deriv_labels:
            label = getattr(self, label_name, None)
            if label:
                label.setVisible(is_enabled)

    def _on_force_reselect(self) -> None:
        """Handle force re-selection button click."""
        logger.info("Forcing strategy re-selection")
        bot_controller = getattr(self, "_bot_controller", None)
        if bot_controller:
            bot_controller.force_strategy_reselection()

    def _clear_ki_log(self) -> None:
        """Clear KI log display."""
        self.ki_log_text.clear()
        self._ki_log_entries.clear()

    # ==================== SYMBOL & SETTINGS MANAGEMENT ====================

    def update_bot_symbol(self, symbol: str | None = None) -> None:
        """Update the bot panel with current symbol and load its settings.

        Args:
            symbol: Symbol to use, or None to get from chart
        """
        if symbol is None:
            symbol = getattr(self, 'current_symbol', None)
            if symbol is None and hasattr(self, 'chart_widget'):
                symbol = getattr(self.chart_widget, 'current_symbol', None)

        if not symbol:
            symbol = "UNKNOWN"

        if hasattr(self, 'bot_symbol_label'):
            self.bot_symbol_label.setText(symbol)

        if symbol != self._current_bot_symbol:
            self._current_bot_symbol = symbol
            self._last_tick_price = 0.0  # Reset last tick price on symbol change
            self._load_bot_settings(symbol)
            logger.info(f"Bot panel updated for symbol: {symbol}")

    def _load_bot_settings(self, symbol: str) -> None:
        """Load saved settings for a symbol into UI controls.

        Args:
            symbol: Symbol to load settings for
        """
        settings = self._bot_settings_manager.get_settings(symbol)

        if not settings:
            logger.debug(f"No saved settings for {symbol}, using defaults")
            return

        logger.info(f"Loading bot settings for {symbol}")

        try:
            # Bot settings
            self._apply_combo_setting(settings, "ki_mode", self.ki_mode_combo)
            self._apply_combo_setting(settings, "trailing_mode", self.trailing_mode_combo)
            self._apply_spin_setting(settings, "initial_sl_pct", self.initial_sl_spin)
            self._apply_spin_setting(settings, "bot_capital", self.bot_capital_spin)
            self._apply_spin_setting(settings, "risk_per_trade_pct", self.risk_per_trade_spin)
            self._apply_spin_setting(settings, "max_trades_per_day", self.max_trades_spin)
            self._apply_spin_setting(settings, "max_daily_loss_pct", self.max_daily_loss_spin)
            self._apply_checkbox_setting(
                settings, "disable_restrictions", self.disable_restrictions_cb
            )
            self._apply_checkbox_setting(
                settings, "disable_macd_exit", self.disable_macd_exit_cb
            )
            self._apply_checkbox_setting(
                settings, "disable_macd_entry", self.disable_macd_entry_cb
            )
            self._apply_checkbox_setting(settings, "disable_rsi_exit", self.disable_rsi_exit_cb)
            self._apply_checkbox_setting(
                settings, "disable_rsi_entry", self.disable_rsi_entry_cb
            )
            self._apply_checkbox_setting(
                settings,
                "enable_derivathandel",
                self.enable_derivathandel_cb,
                on_change=lambda: self._on_derivathandel_changed(0),
            )

            # Trailing stop settings
            self._apply_checkbox_setting(settings, "regime_adaptive", self.regime_adaptive_cb)
            # Issue #44: Add hasattr checks for bot UI widgets that may not exist
            if hasattr(self, 'atr_multiplier_spin'):
                self._apply_spin_setting(settings, "atr_multiplier", self.atr_multiplier_spin)
            if hasattr(self, 'atr_trending_spin'):
                self._apply_spin_setting(settings, "atr_trending", self.atr_trending_spin)
            if hasattr(self, 'atr_ranging_spin'):
                self._apply_spin_setting(settings, "atr_ranging", self.atr_ranging_spin)
            if hasattr(self, 'volatility_bonus_spin'):
                self._apply_spin_setting(settings, "volatility_bonus", self.volatility_bonus_spin)
            if hasattr(self, 'min_step_spin'):
                self._apply_spin_setting(settings, "min_step", self.min_step_spin)
            if hasattr(self, 'tra_percent_spin'):
                self._apply_spin_setting(
                    settings, "tra_percent", self.tra_percent_spin
                )
            if hasattr(self, 'trailing_distance_spin'):
                self._apply_spin_setting(
                    settings, "trailing_distance", self.trailing_distance_spin
                )
            if hasattr(self, 'min_score_spin'):
                self._apply_spin_setting(settings, "min_score", self.min_score_spin)
            self._apply_checkbox_setting(settings, "use_pattern", self.use_pattern_cb)
            self._apply_spin_setting(
                settings, "pattern_similarity", self.pattern_similarity_spin
            )
            self._apply_spin_setting(
                settings, "pattern_min_matches", self.pattern_matches_spin
            )
            self._apply_spin_setting(
                settings, "pattern_winrate", self.pattern_winrate_spin
            )

            # Update UI state
            self._on_trailing_mode_changed()
            self._on_regime_adaptive_changed()

            logger.info(f"Loaded {len(settings)} settings for {symbol}")

        except Exception as e:
            logger.error(f"Error loading settings for {symbol}: {e}")

    def _apply_combo_setting(self, settings: dict, key: str, combo) -> None:
        if key not in settings:
            return
        idx = combo.findText(settings[key])
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _apply_spin_setting(self, settings: dict, key: str, spin) -> None:
        if key in settings:
            spin.setValue(settings[key])

    def _apply_checkbox_setting(self, settings: dict, key: str, checkbox, on_change=None) -> None:
        if key in settings:
            checkbox.setChecked(settings[key])
            if on_change:
                on_change()

    def _save_bot_settings(self, symbol: str) -> None:
        """Save current UI settings for a symbol.

        Args:
            symbol: Symbol to save settings for
        """
        settings = {
            # Bot settings
            "ki_mode": self.ki_mode_combo.currentText(),
            "trailing_mode": self.trailing_mode_combo.currentText(),
            "initial_sl_pct": self.initial_sl_spin.value(),
            "bot_capital": self.bot_capital_spin.value(),
            "risk_per_trade_pct": self.risk_per_trade_spin.value(),
            "max_trades_per_day": self.max_trades_spin.value(),
            "max_daily_loss_pct": self.max_daily_loss_spin.value(),
            "disable_restrictions": self.disable_restrictions_cb.isChecked(),
            "disable_macd_exit": self.disable_macd_exit_cb.isChecked(),
            "disable_macd_entry": self.disable_macd_entry_cb.isChecked(),
            "disable_rsi_exit": self.disable_rsi_exit_cb.isChecked(),
            "disable_rsi_entry": self.disable_rsi_entry_cb.isChecked(),
            "enable_derivathandel": self.enable_derivathandel_cb.isChecked(),

            # Trailing stop settings
            "regime_adaptive": self.regime_adaptive_cb.isChecked(),
            "tra_percent": self.tra_percent_spin.value() if hasattr(self, 'tra_percent_spin') else None,
            "trailing_distance": self.trailing_distance_spin.value() if hasattr(self, 'trailing_distance_spin') else None,
            "use_pattern": self.use_pattern_cb.isChecked(),
            "pattern_similarity": self.pattern_similarity_spin.value(),
            "pattern_min_matches": self.pattern_matches_spin.value(),
            "pattern_winrate": self.pattern_winrate_spin.value(),
        }

        # Issue #44: Add optional settings only if widgets exist
        if hasattr(self, 'atr_multiplier_spin'):
            settings["atr_multiplier"] = self.atr_multiplier_spin.value()
        if hasattr(self, 'atr_trending_spin'):
            settings["atr_trending"] = self.atr_trending_spin.value()
        if hasattr(self, 'atr_ranging_spin'):
            settings["atr_ranging"] = self.atr_ranging_spin.value()
        if hasattr(self, 'volatility_bonus_spin'):
            settings["volatility_bonus"] = self.volatility_bonus_spin.value()
        if hasattr(self, 'min_step_spin'):
            settings["min_step"] = self.min_step_spin.value()
        if hasattr(self, 'min_score_spin'):
            settings["min_score"] = self.min_score_spin.value()

        self._bot_settings_manager.save_settings(symbol, settings)
        logger.info(f"Saved bot settings for {symbol}")
