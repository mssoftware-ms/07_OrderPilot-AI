from __future__ import annotations

import json
import logging
from pathlib import Path

from PyQt6.QtWidgets import (
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

        self.active_strategy_label = QLabel("None")
        self.active_strategy_label.setStyleSheet(
            "font-weight: bold; font-size: 14px; color: #26a69a;"
        )
        current_layout.addRow("Active:", self.active_strategy_label)

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
