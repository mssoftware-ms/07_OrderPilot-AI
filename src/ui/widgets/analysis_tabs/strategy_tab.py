"""Tab 1: Strategy Selection & Gating with AI Daily Trend Analysis."""

from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QFrame, QMessageBox, QTableWidget, QTableWidgetItem,
    QTextEdit, QGroupBox, QProgressBar, QSplitter, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal

from src.core.analysis.context import AnalysisContext
from src.core.analysis.config_store import AnalysisConfigStore

if TYPE_CHECKING:
    pass

# Use dedicated analysis logger
analysis_logger = logging.getLogger('ai_analysis')


class StrategyTab(QWidget):
    """UI for selecting strategy, checking regime compatibility, and AI daily trend analysis."""

    # Signal emitted when AI analysis completes
    analysis_completed = pyqtSignal(dict)

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self.context.regime_changed.connect(self._on_regime_changed)

        # AI analysis components
        self._analysis_worker = None
        self._ai_engine = None
        self._last_analysis_result: dict | None = None

        self._setup_ui()

        # Init defaults
        self._load_strategies()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Use splitter for resizable sections
        splitter = QSplitter(Qt.Orientation.Vertical)

        # === TOP SECTION: Strategy Selection ===
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)

        # 1. Regime Display (Header)
        regime_frame = QFrame()
        regime_frame.setStyleSheet("""
            QFrame {
                background-color: #2a2a2a;
                border-radius: 5px;
                border: 1px solid #444;
            }
        """)
        regime_layout = QHBoxLayout(regime_frame)

        self.regime_label = QLabel("Markt-Regime: UNKNOWN")
        self.regime_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #aaa;")
        regime_layout.addWidget(self.regime_label)
        top_layout.addWidget(regime_frame)

        # 2. Strategy Selection
        strat_layout = QHBoxLayout()
        strat_layout.addWidget(QLabel("Strategie wählen:"))

        self.strategy_combo = QComboBox()
        self.strategy_combo.currentIndexChanged.connect(self._on_strategy_selected)
        strat_layout.addWidget(self.strategy_combo, 1)
        top_layout.addLayout(strat_layout)

        # 3. Gating Status (Traffic Light)
        self.gating_label = QLabel("⚠️ Bitte Regime analysieren (Tab 0)")
        self.gating_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.gating_label.setStyleSheet("""
            background-color: #333;
            color: #ddd;
            padding: 10px;
            border-radius: 4px;
            font-weight: bold;
        """)
        top_layout.addWidget(self.gating_label)

        # 4. Description
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #888; font-style: italic;")
        top_layout.addWidget(self.desc_label)

        # 5. Auto-Config Button
        self.auto_config_btn = QPushButton("⚙️ Auto-Konfiguration anwenden")
        self.auto_config_btn.setToolTip("Lädt Standard-Timeframes und Indikatoren für diese Strategie")
        self.auto_config_btn.clicked.connect(self._on_auto_config)
        self.auto_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        top_layout.addWidget(self.auto_config_btn)

        splitter.addWidget(top_widget)

        # === BOTTOM SECTION: AI Daily Trend Analysis ===
        self._setup_ai_analysis_section(splitter)

        # Set splitter sizes (40% top, 60% bottom)
        splitter.setSizes([200, 300])

        layout.addWidget(splitter)

    def _setup_ai_analysis_section(self, splitter: QSplitter):
        """Setup the AI Daily Trend Analysis section."""
        ai_group = QGroupBox("📊 KI Tagestrend-Analyse")
        ai_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 1px solid #444;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        ai_layout = QVBoxLayout(ai_group)
        ai_layout.setSpacing(8)

        # Analysis button row
        btn_row = QHBoxLayout()

        self.btn_analyze_trend = QPushButton("🔍 Tagestrend analysieren")
        self.btn_analyze_trend.setToolTip(
            "Startet KI-Analyse für den aktuellen Tagestrend.\n"
            "Identifiziert Setup-Typ, Einstiegszonen und Handelsempfehlung."
        )
        self.btn_analyze_trend.clicked.connect(self._on_analyze_daily_trend)
        self.btn_analyze_trend.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:disabled { background-color: #555; color: #888; }
        """)
        btn_row.addWidget(self.btn_analyze_trend)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMaximum(0)  # Indeterminate
        self.progress_bar.setStyleSheet("QProgressBar { max-height: 8px; }")
        btn_row.addWidget(self.progress_bar)

        btn_row.addStretch()
        ai_layout.addLayout(btn_row)

        # Daily Bias Display
        bias_frame = QFrame()
        bias_frame.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-radius: 4px;
                border: 1px solid #333;
            }
        """)
        bias_layout = QHBoxLayout(bias_frame)
        bias_layout.setContentsMargins(10, 8, 10, 8)

        self.lbl_daily_bias = QLabel("Tagestrend: —")
        self.lbl_daily_bias.setStyleSheet("font-size: 15px; font-weight: bold; color: #aaa;")
        bias_layout.addWidget(self.lbl_daily_bias)

        self.lbl_confidence = QLabel("Konfidenz: —")
        self.lbl_confidence.setStyleSheet("font-size: 13px; color: #888;")
        bias_layout.addWidget(self.lbl_confidence)

        self.lbl_setup_type = QLabel("Setup: —")
        self.lbl_setup_type.setStyleSheet("font-size: 13px; color: #888;")
        bias_layout.addWidget(self.lbl_setup_type)

        bias_layout.addStretch()
        ai_layout.addWidget(bias_frame)

        # Tags Table (parsed [#VARNAME; WERT] data)
        self.tags_table = QTableWidget()
        self.tags_table.setColumnCount(2)
        self.tags_table.setHorizontalHeaderLabels(["Parameter", "Wert"])
        self.tags_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tags_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tags_table.setAlternatingRowColors(True)
        self.tags_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                gridline-color: #333;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background-color: #333;
                color: white;
                padding: 6px;
                font-weight: bold;
                border: 1px solid #444;
            }
        """)
        self.tags_table.setMaximumHeight(180)
        ai_layout.addWidget(self.tags_table)

        # Full Analysis Text
        lbl_analysis = QLabel("Vollständige Analyse:")
        lbl_analysis.setStyleSheet("font-weight: bold; margin-top: 5px;")
        ai_layout.addWidget(lbl_analysis)

        self.txt_analysis = QTextEdit()
        self.txt_analysis.setReadOnly(True)
        self.txt_analysis.setPlaceholderText(
            "Hier erscheint die vollständige KI-Analyse mit Handelsempfehlung, "
            "Einstiegszonen und Begründung..."
        )
        self.txt_analysis.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
            }
        """)
        ai_layout.addWidget(self.txt_analysis)

        # Notes section
        self.lbl_notes = QLabel("")
        self.lbl_notes.setWordWrap(True)
        self.lbl_notes.setStyleSheet("color: #888; font-size: 11px; font-style: italic;")
        ai_layout.addWidget(self.lbl_notes)

        splitter.addWidget(ai_group)

    def _load_strategies(self):
        strategies = AnalysisConfigStore.get_default_strategies()
        for strat in strategies:
            self.strategy_combo.addItem(strat.name, strat)

        # Set "Daytrading" as default (Issue #9)
        daytrading_index = self.strategy_combo.findText("Daytrading")
        if daytrading_index >= 0:
            self.strategy_combo.setCurrentIndex(daytrading_index)
            self._on_strategy_selected(daytrading_index)
        elif strategies:
            # Fallback: select first strategy if Daytrading not found
            self.strategy_combo.setCurrentIndex(0)
            self._on_strategy_selected(0)

    def _on_strategy_selected(self, index):
        strat = self.strategy_combo.itemData(index)
        if not strat:
            return

        analysis_logger.info("Strategy selected", extra={
            'tab': 'strategy_tab',
            'action': 'strategy_selected',
            'strategy_name': strat.name,
            'allowed_regimes': strat.allowed_regimes,
            'step': 'user_action'
        })

        self.context.set_strategy(strat.name)
        self.desc_label.setText(strat.description)
        self._update_gating()

    def _on_regime_changed(self, regime: str):
        analysis_logger.info("Regime changed in strategy tab", extra={
            'tab': 'strategy_tab',
            'action': 'regime_changed',
            'regime': regime,
            'step': 'context_update'
        })

        self.regime_label.setText(f"Markt-Regime: {regime}")
        # Color coding for regime
        color = "#aaa"
        if "TREND" in regime: color = "#4CAF50" # Green
        elif "RANGE" in regime: color = "#FFC107" # Amber
        elif "HIGH_VOL" in regime: color = "#F44336" # Red

        self.regime_label.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {color};")
        self._update_gating()

    def _update_gating(self):
        regime = self.context.get_regime()
        strat = self.context.get_selected_strategy()

        if not strat or regime == "UNKNOWN":
            self.gating_label.setText("⚠️ Warte auf Analyse aus Tab 0...")
            self.gating_label.setStyleSheet("background-color: #333; color: #ddd; padding: 10px; border-radius: 4px;")
            return

        allowed = strat.allowed_regimes
        # Simple permissive check (substring match)
        # e.g. regime="TREND_BULL", allowed=["TREND_BULL", ...]

        is_compatible = regime in allowed

        analysis_logger.info("Strategy gating check", extra={
            'tab': 'strategy_tab',
            'action': 'gating_check',
            'strategy': strat.name,
            'regime': regime,
            'is_compatible': is_compatible,
            'allowed_regimes': allowed,
            'step': 'validation'
        })

        if is_compatible:
            self.gating_label.setText(f"✅ Strategie '{strat.name}' ist für '{regime}' geeignet.")
            self.gating_label.setStyleSheet("background-color: #1b5e20; color: #fff; padding: 10px; border-radius: 4px; font-weight: bold;")
        else:
            self.gating_label.setText(f"⛔ Strategie '{strat.name}' wird bei '{regime}' NICHT empfohlen!")
            self.gating_label.setStyleSheet("background-color: #b71c1c; color: #fff; padding: 10px; border-radius: 4px; font-weight: bold;")

    def _on_auto_config(self):
        strategy = self.context.get_selected_strategy()
        analysis_logger.info("Auto-configuration applied", extra={
            'tab': 'strategy_tab',
            'action': 'auto_config',
            'strategy': strategy.name if strategy else 'None',
            'step': 'user_action'
        })
        self.context.apply_auto_config()
        QMessageBox.information(self, "Konfiguration", "Standard-Timeframes und Indikatoren wurden geladen.")

    # ==================== AI Daily Trend Analysis ====================

    def _on_analyze_daily_trend(self):
        """Trigger AI analysis for daily trend."""
        from src.ui.ai_analysis_worker import AnalysisWorker

        # Get chart context from parent hierarchy
        try:
            # Navigate up to find chart window
            parent = self.parent()
            while parent and not hasattr(parent, 'chart_widget'):
                parent = parent.parent()

            if not parent or not hasattr(parent, 'chart_widget'):
                QMessageBox.warning(
                    self, "Fehler",
                    "Chart-Widget nicht gefunden.\n"
                    "Bitte öffnen Sie diese Analyse aus einem Chart-Fenster."
                )
                return

            chart_widget = parent.chart_widget

            # Get required context
            history_manager = getattr(chart_widget, 'history_manager', None)
            symbol = getattr(chart_widget, 'symbol', None)
            timeframe = getattr(chart_widget, 'current_timeframe', '1T')
            asset_class = getattr(chart_widget, 'current_asset_class', None)
            data_source = getattr(chart_widget, 'current_data_source', None)

            if not history_manager:
                QMessageBox.warning(self, "Fehler", "History Manager nicht verfügbar.")
                return

            if not symbol:
                QMessageBox.warning(self, "Fehler", "Kein Symbol geladen.")
                return

            # Get or create AI engine
            if not self._ai_engine:
                self._ai_engine = self._create_ai_engine()
                if not self._ai_engine:
                    QMessageBox.warning(
                        self, "KI nicht konfiguriert",
                        "Bitte konfigurieren Sie die KI-Einstellungen:\n"
                        "Settings → AI → API Key eingeben"
                    )
                    return

            # Update UI state
            self.btn_analyze_trend.setEnabled(False)
            self.progress_bar.setVisible(True)
            self.lbl_daily_bias.setText("Tagestrend: Analysiere...")
            self.lbl_daily_bias.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFC107;")

            analysis_logger.info("Starting daily trend analysis", extra={
                'tab': 'strategy_tab',
                'action': 'daily_trend_analysis',
                'symbol': symbol,
                'timeframe': timeframe,
                'step': 'start'
            })

            # Start worker
            self._analysis_worker = AnalysisWorker(
                self._ai_engine, symbol, timeframe,
                history_manager, asset_class, data_source
            )
            self._analysis_worker.finished.connect(self._on_analysis_finished)
            self._analysis_worker.error.connect(self._on_analysis_error)
            self._analysis_worker.start()

        except Exception as e:
            analysis_logger.error(f"Failed to start daily trend analysis: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Analyse konnte nicht gestartet werden:\n{e}")
            self._reset_ui_state()

    def _create_ai_engine(self):
        """Create AI analysis engine using settings."""
        from PyQt6.QtCore import QSettings

        settings = QSettings("OrderPilot", "OrderPilot-AI")
        api_key = settings.value("ai_api_key", "")

        if not api_key:
            # Try environment variable
            import os
            api_key = os.environ.get("OPENAI_API_KEY", "")

        if not api_key:
            return None

        try:
            from src.core.ai_analysis.engine import AIAnalysisEngine
            engine = AIAnalysisEngine(api_key=api_key)
            return engine
        except Exception as e:
            analysis_logger.error(f"Failed to create AI engine: {e}")
            return None

    def _on_analysis_finished(self, result):
        """Handle completed AI analysis."""
        self._reset_ui_state()

        if not result:
            self.lbl_daily_bias.setText("Tagestrend: Analyse fehlgeschlagen")
            self.lbl_daily_bias.setStyleSheet("font-size: 15px; font-weight: bold; color: #F44336;")
            return

        try:
            # Convert to dict if Pydantic model
            if hasattr(result, 'model_dump'):
                result_dict = result.model_dump()
            else:
                result_dict = result

            self._last_analysis_result = result_dict

            # Update display
            self._update_analysis_display(result_dict)

            # Emit signal for other components
            self.analysis_completed.emit(result_dict)

            analysis_logger.info("Daily trend analysis completed", extra={
                'tab': 'strategy_tab',
                'action': 'daily_trend_analysis',
                'setup_type': result_dict.get('setup_type'),
                'confidence': result_dict.get('confidence_score'),
                'step': 'complete'
            })

        except Exception as e:
            analysis_logger.error(f"Failed to process analysis result: {e}", exc_info=True)
            self.lbl_daily_bias.setText("Tagestrend: Verarbeitungsfehler")

    def _on_analysis_error(self, error_msg: str):
        """Handle analysis error."""
        self._reset_ui_state()

        self.lbl_daily_bias.setText("Tagestrend: Fehler")
        self.lbl_daily_bias.setStyleSheet("font-size: 15px; font-weight: bold; color: #F44336;")
        self.txt_analysis.setText(f"Fehler bei der Analyse:\n\n{error_msg}")

        analysis_logger.error("Daily trend analysis error", extra={
            'tab': 'strategy_tab',
            'action': 'daily_trend_analysis',
            'error': error_msg,
            'step': 'error'
        })

    def _reset_ui_state(self):
        """Reset UI state after analysis."""
        self.btn_analyze_trend.setEnabled(True)
        self.progress_bar.setVisible(False)

    def _update_analysis_display(self, result: dict):
        """Update UI with analysis result."""
        # Extract key fields
        setup_detected = result.get('setup_detected', False)
        setup_type = result.get('setup_type', 'UNKNOWN')
        confidence = result.get('confidence_score', 0)
        reasoning = result.get('reasoning', '')
        invalidation = result.get('invalidation_level')
        notes = result.get('notes', [])

        # Update bias display based on setup type
        bias_text, bias_color = self._get_bias_from_reasoning(reasoning, setup_type)
        self.lbl_daily_bias.setText(f"Tagestrend: {bias_text}")
        self.lbl_daily_bias.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {bias_color};")

        # Confidence
        self.lbl_confidence.setText(f"Konfidenz: {confidence}%")
        conf_color = "#4CAF50" if confidence >= 70 else "#FFC107" if confidence >= 50 else "#F44336"
        self.lbl_confidence.setStyleSheet(f"font-size: 13px; color: {conf_color};")

        # Setup type
        setup_icon = "✅" if setup_detected else "⚠️"
        self.lbl_setup_type.setText(f"Setup: {setup_icon} {setup_type}")

        # Parse and display tags from reasoning
        tags = self._parse_analysis_tags(reasoning)
        self._populate_tags_table(tags)

        # Full analysis text with formatting
        formatted_text = self._format_analysis_text(reasoning, invalidation, notes)
        self.txt_analysis.setText(formatted_text)

        # Notes summary
        if notes:
            notes_text = "📝 Hinweise: " + " | ".join(notes[:2])
            if len(notes) > 2:
                notes_text += f" (+{len(notes)-2} weitere)"
            self.lbl_notes.setText(notes_text)
        else:
            self.lbl_notes.setText("")

    def _get_bias_from_reasoning(self, reasoning: str, setup_type: str) -> tuple[str, str]:
        """Extract daily bias from reasoning text."""
        reasoning_upper = reasoning.upper()

        # Check for explicit direction indicators
        if "[#LONG; BEVORZUGT]" in reasoning_upper or "#LONG; BEVORZUGT" in reasoning_upper:
            return "📈 LONG bevorzugt", "#4CAF50"
        elif "[#SHORT; BEVORZUGT]" in reasoning_upper or "#SHORT; BEVORZUGT" in reasoning_upper:
            return "📉 SHORT bevorzugt", "#F44336"

        # Fallback: check regime
        if "TREND_BULL" in reasoning_upper or "BULLISCH" in reasoning_upper:
            return "📈 Bullisch", "#4CAF50"
        elif "TREND_BEAR" in reasoning_upper or "BEARISCH" in reasoning_upper:
            return "📉 Bärisch", "#F44336"
        elif "RANGE" in reasoning_upper or "SEITWÄRTS" in reasoning_upper:
            return "↔️ Seitwärts", "#FFC107"

        # Based on setup type
        if setup_type in ("BREAKOUT", "TREND_CONTINUATION"):
            return "📈 Trend-Setup", "#4CAF50"
        elif setup_type == "REVERSAL":
            return "🔄 Umkehr-Setup", "#FFC107"

        return "— Neutral", "#aaa"

    def _parse_analysis_tags(self, reasoning: str) -> list[tuple[str, str]]:
        """Parse [#VARNAME; WERT] tags from reasoning text.

        Returns:
            List of (tag_name, value) tuples
        """
        tags = []

        # Pattern: [#NAME; VALUE] or [#NAME;VALUE]
        pattern = r'\[#([A-Za-z_]+)\s*;\s*([^\]]+)\]'
        matches = re.findall(pattern, reasoning)

        for tag_name, value in matches:
            # Clean up tag name for display
            display_name = tag_name.replace('_', ' ').title()
            # Clean up value (trim whitespace)
            clean_value = value.strip()
            tags.append((display_name, clean_value))

        return tags

    def _populate_tags_table(self, tags: list[tuple[str, str]]):
        """Populate the tags table with parsed data."""
        self.tags_table.setRowCount(len(tags))

        for row, (tag_name, value) in enumerate(tags):
            # Tag name (bold, colored)
            name_item = QTableWidgetItem(tag_name)
            name_item.setForeground(Qt.GlobalColor.cyan)
            self.tags_table.setItem(row, 0, name_item)

            # Value
            value_item = QTableWidgetItem(value)

            # Color coding for specific tags
            if tag_name.lower() in ('long', 'einstiegszonen long'):
                value_item.setForeground(Qt.GlobalColor.green)
            elif tag_name.lower() in ('short', 'einstiegszonen short'):
                value_item.setForeground(Qt.GlobalColor.red)
            elif 'widerstand' in tag_name.lower():
                value_item.setForeground(Qt.GlobalColor.yellow)

            self.tags_table.setItem(row, 1, value_item)

    def _format_analysis_text(self, reasoning: str, invalidation: float | None, notes: list) -> str:
        """Format the full analysis text with line breaks."""
        lines = []

        # Main reasoning - replace tags with readable format
        formatted_reasoning = reasoning

        # Add line breaks after each tag
        formatted_reasoning = re.sub(r'\]\s*\[', ']\n[', formatted_reasoning)

        lines.append("═══════════════════════════════════════════")
        lines.append("📊 ANALYSE")
        lines.append("═══════════════════════════════════════════")
        lines.append("")
        lines.append(formatted_reasoning)

        # Invalidation level
        if invalidation:
            lines.append("")
            lines.append("───────────────────────────────────────────")
            lines.append(f"⚠️ INVALIDIERUNG: {invalidation:.1f}")
            lines.append("───────────────────────────────────────────")

        # Notes
        if notes:
            lines.append("")
            lines.append("═══════════════════════════════════════════")
            lines.append("📝 HINWEISE")
            lines.append("═══════════════════════════════════════════")
            for i, note in enumerate(notes, 1):
                lines.append(f"{i}. {note}")

        return "\n".join(lines)

    def get_last_analysis(self) -> dict | None:
        """Get the last analysis result."""
        return self._last_analysis_result

    def set_chart_context(self, chart_widget):
        """Set chart context for analysis (called from parent window)."""
        self._chart_widget = chart_widget
