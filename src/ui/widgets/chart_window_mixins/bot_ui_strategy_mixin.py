from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QPlainTextEdit,
    QTableWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


logger = logging.getLogger(__name__)

class BotUIStrategyMixin:
    """BotUIStrategyMixin extracted from BotUIPanelsMixin."""
    def _create_strategy_selection_tab(self) -> QWidget:
        """Create daily strategy selection tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # ==================== CURRENT STRATEGY ====================
        current_group = QGroupBox("Current Strategy")
        current_layout = QFormLayout()

        # Auto-detection checkbox
        auto_detect_row = QHBoxLayout()
        self.auto_detect_checkbox = QCheckBox("Automatische Erkennung")
        self.auto_detect_checkbox.setChecked(True)  # Default: auto-detection enabled
        self.auto_detect_checkbox.setToolTip(
            "Aktiviert: Strategie wird automatisch erkannt\n"
            "Deaktiviert: Manuelle Strategieauswahl"
        )
        self.auto_detect_checkbox.stateChanged.connect(self._on_auto_detect_changed)
        auto_detect_row.addWidget(self.auto_detect_checkbox)
        auto_detect_row.addStretch()
        current_layout.addRow("Modus:", auto_detect_row)

        # Active strategy ComboBox with detect button
        active_row = QHBoxLayout()
        self.active_strategy_combo = QComboBox()
        self.active_strategy_combo.setMinimumWidth(250)
        self.active_strategy_combo.setStyleSheet(
            "font-weight: bold; font-size: 12px; color: #26a69a;"
        )
        self.active_strategy_combo.setEditable(False)
        self.active_strategy_combo.setEnabled(False)  # Disabled by default (auto mode)
        self.active_strategy_combo.currentTextChanged.connect(self._on_strategy_combo_changed)
        active_row.addWidget(self.active_strategy_combo)

        self.detect_strategy_btn = QPushButton("🔍 Detect Strategy")
        self.detect_strategy_btn.setToolTip("Automatische Strategie-Erkennung basierend auf aktueller Marktlage")
        self.detect_strategy_btn.clicked.connect(self._on_detect_strategy)
        self.detect_strategy_btn.setMaximumWidth(140)
        active_row.addWidget(self.detect_strategy_btn)

        # Manual set button (for manual mode)
        self.set_strategy_btn = QPushButton("✓ Setzen")
        self.set_strategy_btn.setToolTip("Gewählte Strategie manuell setzen")
        self.set_strategy_btn.clicked.connect(self._on_set_manual_strategy)
        self.set_strategy_btn.setMaximumWidth(100)
        self.set_strategy_btn.setVisible(False)  # Hidden in auto mode
        active_row.addWidget(self.set_strategy_btn)

        active_row.addStretch()
        current_layout.addRow("Active:", active_row)

        self.regime_label = QLabel("Unknown")
        current_layout.addRow("Regime:", self.regime_label)

        self.volatility_label = QLabel("Normal")
        current_layout.addRow("Volatility:", self.volatility_label)

        self.selection_time_label = QLabel("-")
        current_layout.addRow("Selected At:", self.selection_time_label)

        self.next_selection_label = QLabel("-")
        current_layout.addRow("Next Selection:", self.next_selection_label)

        # Issue #2: Add indicator set display
        self.strategy_indicators_label = QLabel("-")
        self.strategy_indicators_label.setStyleSheet("color: #888; font-size: 11px;")
        self.strategy_indicators_label.setWordWrap(True)
        current_layout.addRow("Indicators:", self.strategy_indicators_label)

        current_group.setLayout(current_layout)
        layout.addWidget(current_group)

        # ==================== STRATEGY SCORES ====================
        scores_group = QGroupBox("Strategy Scores")
        scores_layout = QVBoxLayout()

        self.strategy_scores_table = QTableWidget()
        self.strategy_scores_table.setColumnCount(5)
        self.strategy_scores_table.setHorizontalHeaderLabels([
            "Strategy", "Score", "PF", "WinRate", "MaxDD"
        ])
        self.strategy_scores_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.strategy_scores_table.setAlternatingRowColors(True)
        self.strategy_scores_table.setMaximumHeight(200)
        scores_layout.addWidget(self.strategy_scores_table)

        scores_group.setLayout(scores_layout)
        layout.addWidget(scores_group)

        # ==================== WALK-FORWARD RESULTS ====================
        wf_group = QGroupBox("Walk-Forward Results")
        wf_layout = QVBoxLayout()

        self.wf_results_text = QTextEdit()
        self.wf_results_text.setReadOnly(True)
        self.wf_results_text.setMaximumHeight(150)
        self.wf_results_text.setPlaceholderText(
            "Walk-forward evaluation results will appear here..."
        )
        wf_layout.addWidget(self.wf_results_text)

        wf_group.setLayout(wf_layout)
        layout.addWidget(wf_group)

        # ==================== DAILY STRATEGY WORKFLOW & JSON ====================
        ds_group = QGroupBox("Tradingbot Daily Strategie")
        ds_layout = QVBoxLayout()

        # Status label
        self.daily_strategy_status = QLabel("Bereit")
        self.daily_strategy_status.setStyleSheet("color: #26a69a; font-weight: bold;")
        ds_layout.addWidget(self.daily_strategy_status)

        # Button row
        btn_row = QHBoxLayout()
        self.run_daily_workflow_btn = QPushButton("▶ Workflow ausführen")
        self.run_daily_workflow_btn.setToolTip(
            "1) Strategie neu wählen → 2) AI-Analyse starten → 3) Overview → 4) Chart-Analyse"
        )
        self.run_daily_workflow_btn.clicked.connect(self._run_daily_strategy_workflow)
        btn_row.addWidget(self.run_daily_workflow_btn)

        self.generate_daily_json_btn = QPushButton("💾 JSON generieren")
        self.generate_daily_json_btn.setToolTip("Schreibt Vorlage nach data/daily_strategy.json und füllt das Feld")
        self.generate_daily_json_btn.clicked.connect(self._generate_daily_strategy_json)
        btn_row.addWidget(self.generate_daily_json_btn)

        self.load_daily_json_btn = QPushButton("📂 JSON laden")
        self.load_daily_json_btn.setToolTip("Liest data/daily_strategy.json und füllt das Feld")
        self.load_daily_json_btn.clicked.connect(self._load_daily_strategy_json)
        btn_row.addWidget(self.load_daily_json_btn)

        btn_row.addStretch()
        ds_layout.addLayout(btn_row)

        # JSON variables editor
        self.daily_strategy_json_edit = QPlainTextEdit()
        self.daily_strategy_json_edit.setPlaceholderText(
            "JSON-Variablen (setup_detected, setup_type, confidence_score, ...)")
        self.daily_strategy_json_edit.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        self.daily_strategy_json_edit.setMinimumHeight(150)
        ds_layout.addWidget(self.daily_strategy_json_edit)

        # Full analysis field
        self.daily_strategy_analysis_edit = QTextEdit()
        self.daily_strategy_analysis_edit.setReadOnly(True)
        self.daily_strategy_analysis_edit.setPlaceholderText(
            "Ausgabe der AI-Analyse / Chart-Analyse wird hier angezeigt")
        self.daily_strategy_analysis_edit.setMinimumHeight(120)
        ds_layout.addWidget(self.daily_strategy_analysis_edit)

        ds_group.setLayout(ds_layout)
        layout.addWidget(ds_group)

        # Manual override button
        override_layout = QHBoxLayout()
        self.force_reselect_btn = QPushButton("Force Re-Selection")
        self.force_reselect_btn.clicked.connect(self._on_force_reselect)
        override_layout.addWidget(self.force_reselect_btn)
        override_layout.addStretch()
        layout.addLayout(override_layout)

        layout.addStretch()
        return widget

    # =========================================================================
    # Daily Strategy helpers
    # =========================================================================

    def _update_daily_analysis_view(self, result: dict) -> None:
        """Populate the Daily Strategy tab with the latest AI analysis result.

        Args:
            result: dict from AIAnalysisOutput.model_dump()
        """
        try:
            if hasattr(self, "daily_strategy_json_edit"):
                self.daily_strategy_json_edit.setPlainText(
                    json.dumps(result, indent=2, ensure_ascii=False)
                )

            reasoning = result.get("reasoning", "") or ""
            notes = result.get("notes", [])
            combined = reasoning
            if notes:
                combined += "\n\n" + "\n".join(notes)

            if hasattr(self, "daily_strategy_analysis_edit"):
                self.daily_strategy_analysis_edit.setPlainText(combined)

            self._set_daily_status("AI-Tagesanalyse aktualisiert")
        except Exception as e:
            logger.warning(f"Could not update daily analysis view: {e}")
            self._set_daily_status(f"Anzeige-Update fehlgeschlagen: {e}", error=True)

    def _run_daily_strategy_workflow(self) -> None:
        """Run the requested workflow: chart function -> AI analysis -> tabs.

        Steps:
        1) Force strategy reselection (Chart function)
        2) Open AI-Analyse Popup and start analysis
        3) Show Overview tab
        4) Show Chart/Deep Analysis tab
        """
        try:
            # Step 1: chart function (existing force reselect)
            if hasattr(self, '_on_force_reselect'):
                self._on_force_reselect()
                self._set_daily_status("Strategie neu gewählt")

            # Step 2: open AI Analysis window
            ai_window = getattr(self, '_ai_analysis_window', None)
            if not ai_window:
                if hasattr(self, '_handlers') and hasattr(self._handlers, 'on_ai_analysis_button_clicked'):
                    self._handlers.on_ai_analysis_button_clicked(True)
                    ai_window = getattr(self, '_ai_analysis_window', None)
                else:
                    from src.ui.ai_analysis_window import AIAnalysisWindow
                    ai_window = AIAnalysisWindow(self, symbol=getattr(self, 'symbol', ""))
                    self._ai_analysis_window = ai_window

            if ai_window:
                ai_window.show()
                ai_window.raise_()
                ai_window.activateWindow()
                # Step 3: run analysis
                if hasattr(ai_window, '_handlers'):
                    ai_window._handlers.start_analysis()
                    self._set_daily_status("AI-Analyse gestartet")
                # Step 4: tab order Overview -> Chart Analysis
                if hasattr(ai_window, 'tabs'):
                    ai_window.tabs.setCurrentIndex(0)  # Overview
                    if ai_window.tabs.count() > 1:
                        ai_window.tabs.setCurrentIndex(1)  # Deep/Chart Analysis
            else:
                self._set_daily_status("AI-Analyse Fenster nicht verfügbar", error=True)

        except Exception as e:
            logger.error(f"Daily strategy workflow failed: {e}")
            self._set_daily_status(f"Fehler: {e}", error=True)

    def _set_daily_status(self, text: str, error: bool = False) -> None:
        if hasattr(self, 'daily_strategy_status'):
            color = "#f44336" if error else "#26a69a"
            self.daily_strategy_status.setText(text)
            self.daily_strategy_status.setStyleSheet(f"color: {color}; font-weight: bold;")
        if hasattr(self, '_add_ki_log_entry'):
            self._add_ki_log_entry("DAILY", text)

    def _generate_daily_strategy_json(self) -> None:
        """Generate template JSON file and populate editor."""
        template = {
            "setup_detected": False,
            "setup_type": "NO_SETUP",
            "confidence_score": 44,
            "reasoning": (
                "[#REGIME:; CHOP_RANGE] [#Symbol; BTCUSDT] [#Timeframe; 5T] "
                "[#Preis; 90940.7] [#RSI; 47.71 (NEUTRAL)] [#ADX14; 14.37] "
                "[#EMA20_Dist%; -0.04] [#EMA200_Dist%; 0.17] [#ATR14; 89.897] "
                "[#Range_High; 91252.3] [#Range_Low; 90835.6]\\n\\n"
                "Struktur/Price Action: ... (Beispiel siehe Issue 21)"
            ),
            "invalidation_level": 90854.4,
            "notes": [
                "[#Trend; Seitwaerts/Range (Chop)]",
                "[#Widerstand; 91016.2 / 91017.9 (Trigger-Zone)]",
                "[#Support; 90889.6 (minor), darunter 90854.4, tiefer 90835.6]",
                "[#Long; Bedingt LONG erst bei Close > 91016.2]",
                "[#Short; Bedingt SHORT erst bei Breakdown < 90854.4]",
                "[#Tradingempfehlung; Einstieg NEIN (warten auf Bestaetigung)]",
                "[#Stop/Invalidation; Unter 90854.4]",
                "[#Tagesstrategie; Sideways Range]",
            ],
        }

        text = json.dumps(template, indent=2, ensure_ascii=False)
        self.daily_strategy_json_edit.setPlainText(text)

        path = Path("data/daily_strategy.json")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
            self._set_daily_status(f"JSON gespeichert: {path}")
        except Exception as e:
            self._set_daily_status(f"Speichern fehlgeschlagen: {e}", error=True)

    def _load_daily_strategy_json(self) -> None:
        """Load JSON file into editor and analysis field if available."""
        path = Path("data/daily_strategy.json")
        if not path.exists():
            self._set_daily_status(f"Datei fehlt: {path}", error=True)
            return

        try:
            text = path.read_text(encoding="utf-8")
            self.daily_strategy_json_edit.setPlainText(text)
            self._set_daily_status(f"JSON geladen: {path}")
            # Try to display reasoning in analysis field
            try:
                data = json.loads(text)
                reasoning = data.get("reasoning", "")
                notes = data.get("notes", [])
                combined = reasoning + "\\n\\n" + "\\n".join(notes) if notes else reasoning
                if hasattr(self, "daily_strategy_analysis_edit"):
                    self.daily_strategy_analysis_edit.setPlainText(combined)
            except Exception:
                pass
        except Exception as e:
            self._set_daily_status(f"Laden fehlgeschlagen: {e}", error=True)

    def _populate_strategy_combo(self) -> None:
        """Populate strategy ComboBox with all available strategies."""
        if not hasattr(self, 'active_strategy_combo'):
            logger.debug("active_strategy_combo not found, skipping populate")
            return

        logger.info("_populate_strategy_combo called")

        try:
            # Check if bot controller exists
            if not self._bot_controller:
                logger.warning("Bot controller not available")
                return

            # Get all available strategies from catalog (direct access to private attribute)
            try:
                catalog = self._bot_controller._strategy_catalog
                strategies = catalog.get_all_strategies()
                logger.info(f"Retrieved {len(strategies)} strategies from catalog")
            except AttributeError as e:
                logger.error(f"Cannot access strategy catalog: {e}")
                return

            if not strategies:
                logger.warning("No strategies found in catalog")
                return

            # Block signals to prevent triggering change events
            self.active_strategy_combo.blockSignals(True)
            self.active_strategy_combo.clear()
            logger.debug("Cleared combo box")

            # Add "Neutral" as first entry (default when no strategy selected)
            self.active_strategy_combo.addItem("Neutral (keine Strategie)", userData=None)

            # Add strategies to combo box
            strategy_names = []
            for strategy in strategies:
                # StrategyDefinition has a 'profile' attribute with the name
                strategy_name = strategy.profile.name
                display_name = self._format_strategy_name(strategy_name)
                strategy_names.append((strategy_name, display_name))
                logger.debug(f"Added strategy: {strategy_name} -> {display_name}")

            # Sort by display name
            strategy_names.sort(key=lambda x: x[1])

            # Add to combo box
            for name, display_name in strategy_names:
                self.active_strategy_combo.addItem(display_name, userData=name)

            # Set Neutral as default
            self.active_strategy_combo.setCurrentIndex(0)

            self.active_strategy_combo.blockSignals(False)
            logger.info(f"✓ Strategy combo populated with {len(strategy_names)} strategies + Neutral")

        except Exception as e:
            logger.error(f"Failed to populate strategy combo: {e}", exc_info=True)

    def _format_strategy_name(self, name: str) -> str:
        """Format strategy name for display (e.g., 'trend_following_conservative' -> 'Trend Following Conservative')."""
        return " ".join(word.capitalize() for word in name.split("_"))

    def _on_strategy_combo_changed(self, text: str) -> None:
        """Handle strategy combo box selection change (only reacts in manual mode for live updates)."""
        # This is only for display purposes - actual setting happens via "Setzen" button
        # in manual mode, or automatically in auto mode
        pass

    def _on_auto_detect_changed(self, state: int) -> None:
        """Handle auto-detection checkbox state change."""
        try:
            is_auto = self.auto_detect_checkbox.isChecked()

            # Update bot controller flag
            if self._bot_controller:
                self._bot_controller._manual_strategy_mode = not is_auto
                logger.info(f"Bot controller manual mode flag set to: {not is_auto}")

            # Auto mode: ComboBox disabled, Detect button visible, Set button hidden
            # Manual mode: ComboBox enabled, Detect button hidden, Set button visible
            self.active_strategy_combo.setEnabled(not is_auto)
            self.detect_strategy_btn.setVisible(is_auto)
            self.set_strategy_btn.setVisible(not is_auto)

            mode_text = "Automatisch" if is_auto else "Manuell"
            logger.info(f"Strategy selection mode changed to: {mode_text}")
            self._set_daily_status(f"Strategie-Modus: {mode_text}")

            # Log to Signals tab
            if hasattr(self, '_log_bot_activity'):
                self._log_bot_activity("STRATEGY", f"Modus gewechselt: {mode_text}")

        except Exception as e:
            logger.error(f"Failed to change auto-detect mode: {e}")

    def _on_set_manual_strategy(self) -> None:
        """Set manually selected strategy from ComboBox."""
        try:
            if not self._bot_controller:
                self._set_daily_status("Bot Controller nicht verfügbar", error=True)
                return

            # Get selected strategy from ComboBox
            index = self.active_strategy_combo.currentIndex()
            strategy_name = self.active_strategy_combo.itemData(index)
            display_name = self.active_strategy_combo.currentText()

            if strategy_name is None:
                # "Neutral" selected
                self._set_manual_strategy_in_bot(None)
                self._set_daily_status("Strategie manuell gesetzt: Neutral")
                logger.info("Manual strategy set: neutral (keine Strategie)")

                # Log to Signals tab
                if hasattr(self, '_log_bot_activity'):
                    self._log_bot_activity("STRATEGY", "Manuell gesetzt: neutral (keine Strategie)")
            else:
                # Specific strategy selected
                self._set_manual_strategy_in_bot(strategy_name)
                self._set_daily_status(f"Strategie manuell gesetzt: {display_name}")
                logger.info(f"Manual strategy set: {strategy_name}")

                # Log to Signals tab
                if hasattr(self, '_log_bot_activity'):
                    self._log_bot_activity("STRATEGY", f"Manuell gesetzt: {strategy_name}")

        except Exception as e:
            logger.error(f"Failed to set manual strategy: {e}")
            self._set_daily_status(f"Manuelle Strategie-Auswahl fehlgeschlagen: {e}", error=True)

    def _set_manual_strategy_in_bot(self, strategy_name: str | None) -> None:
        """Set strategy in bot controller (for manual mode).

        Args:
            strategy_name: Strategy name or None for neutral
        """
        if not self._bot_controller:
            return

        try:
            if strategy_name is None:
                # Set to neutral (no strategy)
                self._bot_controller._active_strategy = None
                logger.info("Bot strategy set to: neutral")
            else:
                # Get strategy definition and set profile
                strategy_def = self._bot_controller._strategy_catalog.get_strategy(strategy_name)
                if strategy_def:
                    self._bot_controller._active_strategy = strategy_def.profile
                    logger.info(f"Bot strategy set to: {strategy_name}")
                else:
                    logger.error(f"Strategy definition not found: {strategy_name}")
                    raise ValueError(f"Strategie nicht gefunden: {strategy_name}")

        except Exception as e:
            logger.error(f"Failed to set strategy in bot controller: {e}")
            raise

    def _on_detect_strategy(self) -> None:
        """Trigger automatic strategy detection based on current market conditions."""
        try:
            if not self._bot_controller:
                self._set_daily_status("Bot Controller nicht verfügbar", error=True)
                return

            self._set_daily_status("Strategie-Erkennung läuft...")
            logger.info("Manual strategy detection triggered")

            # Force immediate strategy reselection
            if hasattr(self._bot_controller, 'force_strategy_reselection_now'):
                selected_name = self._bot_controller.force_strategy_reselection_now()

                # Log detected strategy to Signals tab
                if hasattr(self, '_log_bot_activity'):
                    strategy_display = selected_name if selected_name else "neutral (keine Strategie)"
                    self._log_bot_activity("STRATEGY", f"Erkannte Strategie: {strategy_display}")

                # Update the daily strategy panel to reflect the new selection
                if hasattr(self, '_update_daily_strategy_panel'):
                    self._update_daily_strategy_panel()

                if selected_name:
                    self._set_daily_status(f"Strategie erkannt: {selected_name}")
                else:
                    self._set_daily_status("Keine Strategie erkannt (neutral)")
            else:
                self._set_daily_status("Strategie-Erkennung nicht verfügbar", error=True)

        except Exception as e:
            logger.error(f"Strategy detection failed: {e}")
            self._set_daily_status(f"Strategie-Erkennung fehlgeschlagen: {e}", error=True)

    def _update_active_strategy_display(self, strategy_name: str | None) -> None:
        """Update the active strategy ComboBox to show the current strategy.

        Args:
            strategy_name: Internal strategy name (e.g., 'trend_following_conservative') or None for neutral
        """
        if not hasattr(self, 'active_strategy_combo'):
            logger.debug("active_strategy_combo not found")
            return

        logger.info(f"_update_active_strategy_display called with: {strategy_name}")

        try:
            combo_count = self.active_strategy_combo.count()
            logger.info(f"ComboBox has {combo_count} items")

            if combo_count == 0:
                logger.warning("ComboBox is empty, populating first")
                self._populate_strategy_combo()
                combo_count = self.active_strategy_combo.count()
                logger.info(f"After populate: {combo_count} items")

            # Block signals to prevent triggering change event
            self.active_strategy_combo.blockSignals(True)

            # If strategy_name is None, select "Neutral" (index 0)
            if strategy_name is None:
                self.active_strategy_combo.setCurrentIndex(0)
                logger.info("✓ Active strategy display updated: Neutral (index 0)")
            else:
                # Find and select the strategy in combo box
                found = False
                for i in range(self.active_strategy_combo.count()):
                    item_data = self.active_strategy_combo.itemData(i)
                    logger.debug(f"Item {i}: {self.active_strategy_combo.itemText(i)} (data: {item_data})")
                    if item_data == strategy_name:
                        self.active_strategy_combo.setCurrentIndex(i)
                        logger.info(f"✓ Active strategy display updated: {strategy_name} at index {i}")
                        found = True
                        break

                if not found:
                    logger.warning(f"Strategy '{strategy_name}' not found in combo box, defaulting to Neutral")
                    self.active_strategy_combo.setCurrentIndex(0)

            self.active_strategy_combo.blockSignals(False)
        except Exception as e:
            logger.error(f"Failed to update active strategy display: {e}", exc_info=True)
