"""AI Chat Tab - Phase 5.8-5.10.

Chat interface that uses MarketContext as single data source.
Provides Quick Actions and Draw-to-Chart capabilities.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional, Dict, List, Callable

from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QLineEdit, QScrollArea, QFrame, QComboBox,
    QProgressBar, QMessageBox, QApplication,
)
from PyQt6.QtGui import QFont, QTextCursor

from src.ui.icons import get_icon

if TYPE_CHECKING:
    from src.core.analysis.context import AnalysisContext
    from src.core.trading_bot.market_context import MarketContext

logger = logging.getLogger(__name__)


# Quick Action Prompts
QUICK_ACTION_PROMPTS = {
    "trend": "Analysiere den aktuellen Trend. Beschreibe: 1) Trend-Richtung (bullish/bearish/neutral), 2) Trend-Stärke, 3) Wichtige Strukturpunkte (Higher Highs/Lows oder Lower Highs/Lows).",
    "levels": "Identifiziere die wichtigsten Support- und Resistance-Level. Liste die Top 5 Levels mit: 1) Preiszone, 2) Typ (Support/Resistance), 3) Stärke, 4) Anzahl Berührungen.",
    "entry": "Bewerte potenzielle Entry-Setups. Beschreibe: 1) Aktueller Entry-Score, 2) Empfohlene Entry-Zone, 3) Konfluenz-Faktoren, 4) Risiko-Bewertung.",
    "risiken": "Analysiere die aktuellen Risiken. Beschreibe: 1) Marktregime, 2) Volatilität, 3) Potenzielle Invalidierungs-Level, 4) Empfohlene Stop-Loss-Zonen.",
    "szenarien": "Entwickle 3 mögliche Szenarien: 1) Bullish Case (Wahrscheinlichkeit, Targets), 2) Bearish Case (Wahrscheinlichkeit, Targets), 3) Neutral/Range Case. Beschreibe für jedes Szenario die Trigger und Invalidierungs-Level.",
}


# Chat Worker Thread
class ChatWorker(QThread):
    """Background worker for AI chat requests."""

    finished = pyqtSignal(str)  # AI response text
    error = pyqtSignal(str)

    def __init__(self, prompt: str, context_text: str, model: str = "gpt-4o-mini"):
        super().__init__()
        self.prompt = prompt
        self.context_text = context_text
        self.model = model

    def run(self):
        """Execute AI chat request."""
        import asyncio
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            response = loop.run_until_complete(self._call_ai())
            self.finished.emit(response)
            loop.close()

        except Exception as e:
            logger.error(f"Chat worker error: {e}", exc_info=True)
            self.error.emit(str(e))

    async def _call_ai(self) -> str:
        """Call AI API with context and prompt."""
        from src.config.loader import config_manager

        # Build system message with MarketContext
        system_message = f"""Du bist ein Trading-Analyst. Antworte präzise und strukturiert auf Deutsch.

MARKT-KONTEXT:
{self.context_text}

ANWEISUNGEN:
- Basiere deine Analyse ausschließlich auf den bereitgestellten Daten
- Verwende konkrete Zahlen aus dem Kontext
- Markiere Preislevel im Format: [#Level-Typ; Preis-Range] z.B. [#Support Zone; 91038-91120]
- Bei Level-Empfehlungen: gib exakte Preise an
"""

        try:
            # Try OpenAI first
            api_key = config_manager.get_credential("openai_api_key")
            if api_key:
                import openai
                client = openai.AsyncOpenAI(api_key=api_key)

                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": self.prompt},
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                )
                return response.choices[0].message.content

        except Exception as e:
            logger.warning(f"OpenAI failed: {e}, trying Anthropic...")

        try:
            # Fallback to Anthropic
            api_key = config_manager.get_credential("anthropic_api_key")
            if api_key:
                import anthropic
                client = anthropic.AsyncAnthropic(api_key=api_key)

                response = await client.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=2000,
                    system=system_message,
                    messages=[{"role": "user", "content": self.prompt}],
                )
                return response.content[0].text

        except Exception as e:
            logger.warning(f"Anthropic failed: {e}")

        raise RuntimeError("Keine AI-API verfügbar. Bitte API-Key in Settings konfigurieren.")


# AI Chat Tab Widget
class AIChatTab(QWidget):
    """AI Chat Tab with MarketContext integration (Phase 5.8-5.10).

    Features:
        - MarketContext as single data source (5.8)
        - Draw-to-Chart from AI responses (5.9)
        - Quick Action buttons (5.10)
    """

    # Signal to request drawing on chart
    draw_level_requested = pyqtSignal(str, float, float, str)  # (level_type, top, bottom, label)
    draw_zone_requested = pyqtSignal(str, float, float, str)  # (zone_type, top, bottom, label)

    def __init__(self, context: "AnalysisContext"):
        super().__init__()
        self.context = context
        self._market_context: Optional["MarketContext"] = None
        self._chat_history: List[Dict[str, str]] = []
        self._worker: Optional[ChatWorker] = None

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the chat UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header (Issue #20: Emoji entfernt)
        header = QLabel("AI Trading Chat")
        header.setProperty("class", "header")
        layout.addWidget(header)

        # Context Status (Issue #20: Emoji entfernt)
        self.context_status = QLabel("Kein MarketContext geladen")
        self.context_status.setProperty("class", "status-label")
        layout.addWidget(self.context_status)

        # Quick Actions (Phase 5.10)
        quick_actions_frame = QFrame()
        # Remove hardcoded frame style
        quick_layout = QHBoxLayout(quick_actions_frame)
        quick_layout.setContentsMargins(5, 5, 5, 5)

        quick_label = QLabel("Quick Actions:")
        quick_label.setProperty("class", "label-bold")
        quick_layout.addWidget(quick_label)

        # Issue #20: Material Design Icons statt Emojis + Icon-Größe
        ICON_SIZE = QSize(16, 16)
        # Issue #20: Kleinere Schriftgröße für Buttons
        button_font = QFont()
        button_font.setPointSize(9)

        for action_key, action_label, icon_name in [
            ("trend", "Trend", "chart"),
            ("levels", "Levels", "entry_analyzer"),
            ("entry", "Entry", "entry_analyzer"),
            ("risiken", "Risiken", "warning"),
            ("szenarien", "Szenarien", "lightbulb"),
        ]:
            btn = QPushButton(action_label)  # Issue #20: Emoji entfernt
            btn.setIcon(get_icon(icon_name))  # Issue #20: Material Design Icon
            btn.setIconSize(ICON_SIZE)  # Issue #20
            btn.setFont(button_font)  # Issue #20: Kleinere Schrift
            btn.setProperty("class", "action-button")
            btn.setFixedHeight(28)  # Issue #20: Einheitliche Höhe
            btn.clicked.connect(lambda checked, k=action_key: self._on_quick_action(k))
            quick_layout.addWidget(btn)

        quick_layout.addStretch()

        # Refresh context button (Issue #20)
        self.btn_refresh_context = QPushButton("Context")  # Issue #20: Emoji entfernt
        self.btn_refresh_context.setIcon(get_icon("refresh"))  # Issue #20
        self.btn_refresh_context.setIconSize(ICON_SIZE)  # Issue #20
        self.btn_refresh_context.setFont(button_font)  # Issue #20
        self.btn_refresh_context.setFixedHeight(28)  # Issue #20
        self.btn_refresh_context.setToolTip("MarketContext aktualisieren")
        self.btn_refresh_context.clicked.connect(self._refresh_context)
        quick_layout.addWidget(self.btn_refresh_context)

        layout.addWidget(quick_actions_frame)

        # Chat Display (Issue #19: Größere Mindesthöhe für bessere Lesbarkeit)
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setMinimumHeight(400)  # Issue #19: Mindesthöhe für Chat
        # Issue #19: Ensure it expands
        from PyQt6.QtWidgets import QSizePolicy
        self.chat_display.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        # Style handled by theme
        self.chat_display.setPlaceholderText(
            "Willkommen! Klicke auf eine Quick Action oder stelle eine Frage.\n\n"
            "Der Chat verwendet den aktuellen MarketContext als Datengrundlage."
        )
        layout.addWidget(self.chat_display, stretch=1)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Input Area
        input_layout = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Stelle eine Frage zum aktuellen Markt...")
        # Style handled by theme
        self.input_field.returnPressed.connect(self._on_send_message)
        input_layout.addWidget(self.input_field, stretch=1)

        self.btn_send = QPushButton("Senden")
        self.btn_send.setProperty("class", "primary")
        self.btn_send.clicked.connect(self._on_send_message)
        input_layout.addWidget(self.btn_send)

        layout.addLayout(input_layout)

        # Footer with Draw-to-Chart info (Issue #20: Emoji entfernt)
        footer = QLabel("AI kann Level im Format [#Support Zone; 91038-91120] vorschlagen - klicke darauf zum Zeichnen")
        footer.setProperty("class", "info-label")
        layout.addWidget(footer)

    def _connect_signals(self):
        """Connect internal signals."""
        pass

    def set_market_context(self, context: "MarketContext") -> None:
        """Set the MarketContext for chat (Phase 5.8).

        Args:
            context: MarketContext instance
        """
        self._market_context = context
        if context:
            self.context_status.setText(
                f"MarketContext: {context.symbol} | {context.timeframe} | "  # Issue #20: Emoji entfernt
                f"Regime: {context.regime.value if context.regime else 'N/A'}"
            )
            # Issue #20: Entferne hardcoded inline styles, nutze Theme-Properties
            self.context_status.setProperty("status", "active")
            self.context_status.style().unpolish(self.context_status)
            self.context_status.style().polish(self.context_status)
        else:
            self.context_status.setText("Kein MarketContext geladen")  # Issue #20: Emoji entfernt
            self.context_status.setProperty("status", "inactive")
            self.context_status.style().unpolish(self.context_status)
            self.context_status.style().polish(self.context_status)

    def _refresh_context(self) -> None:
        """Refresh MarketContext from chart."""
        try:
            from src.core.trading_bot.market_context_builder import MarketContextBuilder

            # Try to get data from AnalysisContext
            if hasattr(self.context, 'symbol') and hasattr(self.context, 'timeframe'):
                builder = MarketContextBuilder()
                # Get DataFrame from context if available
                df = getattr(self.context, '_df', None)
                if df is not None and len(df) > 0:
                    context = builder.build(
                        symbol=self.context.symbol,
                        timeframe=self.context.timeframe,
                        df=df,
                    )
                    self.set_market_context(context)
                    self._add_system_message("MarketContext aktualisiert ✓")
                    return

            self._add_system_message("⚠️ Keine Daten für Context-Refresh verfügbar")

        except Exception as e:
            logger.error(f"Context refresh failed: {e}")
            self._add_system_message(f"❌ Context-Refresh fehlgeschlagen: {e}")

    def _get_context_text(self) -> str:
        """Get MarketContext as text for AI prompt."""
        if self._market_context is None:
            return "Kein MarketContext verfügbar."

        try:
            # Use the AI prompt context method if available
            if hasattr(self._market_context, 'to_ai_prompt_context'):
                return self._market_context.to_ai_prompt_context()

            # Fallback: build context text manually
            ctx = self._market_context
            lines = [
                f"Symbol: {ctx.symbol}",
                f"Timeframe: {ctx.timeframe}",
                f"Regime: {ctx.regime.value if ctx.regime else 'N/A'}",
                f"Trend: {ctx.trend.value if ctx.trend else 'N/A'}",
            ]

            if ctx.candle_summary:
                cs = ctx.candle_summary
                lines.extend([
                    f"\nPreise:",
                    f"  Open: {cs.open:.2f}",
                    f"  High: {cs.high:.2f}",
                    f"  Low: {cs.low:.2f}",
                    f"  Close: {cs.close:.2f}",
                ])

            if ctx.indicators:
                ind = ctx.indicators
                lines.append("\nIndikatoren:")
                if ind.rsi:
                    lines.append(f"  RSI: {ind.rsi:.2f}")
                if ind.atr:
                    lines.append(f"  ATR: {ind.atr:.4f}")
                if ind.adx:
                    lines.append(f"  ADX: {ind.adx:.2f}")

            if ctx.levels and ctx.levels.levels:
                lines.append("\nLevels:")
                for lvl in ctx.levels.levels[:5]:
                    lines.append(f"  {lvl.level_type.value}: {lvl.price_low:.2f} - {lvl.price_high:.2f}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Failed to build context text: {e}")
            return f"Context-Fehler: {e}"

    def _on_quick_action(self, action_key: str) -> None:
        """Handle quick action button click (Phase 5.10).

        Args:
            action_key: Key from QUICK_ACTION_PROMPTS
        """
        prompt = QUICK_ACTION_PROMPTS.get(action_key)
        if prompt:
            self._send_chat_message(prompt, is_quick_action=True)

    def _on_send_message(self) -> None:
        """Handle send button click."""
        text = self.input_field.text().strip()
        if text:
            self.input_field.clear()
            self._send_chat_message(text)

    def _send_chat_message(self, message: str, is_quick_action: bool = False) -> None:
        """Send a chat message to AI.

        Args:
            message: User message or quick action prompt
            is_quick_action: Whether this is a quick action
        """
        if self._worker and self._worker.isRunning():
            QMessageBox.warning(self, "Busy", "Bitte warten bis die aktuelle Anfrage abgeschlossen ist.")
            return

        # Add user message to display
        action_label = " (Quick Action)" if is_quick_action else ""
        self._add_user_message(message, action_label)

        # Get context
        context_text = self._get_context_text()

        # Start worker
        self.progress_bar.setVisible(True)
        self.btn_send.setEnabled(False)

        self._worker = ChatWorker(message, context_text)
        self._worker.finished.connect(self._on_chat_response)
        self._worker.error.connect(self._on_chat_error)
        self._worker.start()

    def _on_chat_response(self, response: str) -> None:
        """Handle AI response.

        Args:
            response: AI response text
        """
        self.progress_bar.setVisible(False)
        self.btn_send.setEnabled(True)

        # Add response to display
        self._add_ai_message(response)

        # Parse and enable draw-to-chart for levels (Phase 5.9)
        self._process_draw_commands(response)

    def _on_chat_error(self, error: str) -> None:
        """Handle chat error.

        Args:
            error: Error message
        """
        self.progress_bar.setVisible(False)
        self.btn_send.setEnabled(True)
        self._add_system_message(f"❌ Fehler: {error}")

    def _add_user_message(self, message: str, suffix: str = "") -> None:
        """Add user message to chat display (Issue #19/#20: Verbesserte Lesbarkeit)."""
        timestamp = datetime.now().strftime("%H:%M")
        # Issue #19/#20: Größere max-width, größere Schrift, Theme-Farben
        html = f"""
        <div style="margin: 15px 0; text-align: right;">
            <span style="color: #888; font-size: 10px;">{timestamp}{suffix}</span><br>
            <span style="background-color: #9C27B0; color: white; padding: 12px 16px;
                         border-radius: 10px; display: inline-block; max-width: 95%;
                         font-size: 13px; line-height: 1.6; word-wrap: break-word;">
                {message}
            </span>
        </div>
        """
        self.chat_display.append(html)
        self._scroll_to_bottom()

    def _add_ai_message(self, message: str) -> None:
        """Add AI message to chat display (Issue #19/#20: Verbesserte Lesbarkeit)."""
        timestamp = datetime.now().strftime("%H:%M")

        # Convert level tags to clickable links
        import re
        pattern = r'\[#([^;]+);\s*([0-9.]+)-([0-9.]+)\]'

        def make_clickable(match):
            level_type = match.group(1)
            low = match.group(2)
            high = match.group(3)
            return f'<a href="draw:{level_type}:{low}:{high}" style="color: #4CAF50; text-decoration: underline;">[#{level_type}; {low}-{high}]</a>'

        message_with_links = re.sub(pattern, make_clickable, message)

        # Issue #19/#20: Größere max-width, größere Schrift, besseres Dark Theme
        html = f"""
        <div style="margin: 15px 0; text-align: left;">
            <span style="color: #888; font-size: 10px;">AI • {timestamp}</span><br>
            <span style="background-color: #2D2D2D; color: #E0E0E0; padding: 12px 16px;
                         border-radius: 10px; display: inline-block; max-width: 95%;
                         white-space: pre-wrap; font-size: 13px; line-height: 1.6; word-wrap: break-word;">
                {message_with_links}
            </span>
        </div>
        """
        self.chat_display.append(html)
        self._scroll_to_bottom()

    def _add_system_message(self, message: str) -> None:
        """Add system message to chat display (Issue #20: Bessere Theme-Integration)."""
        # Issue #20: Größere Schrift für bessere Lesbarkeit
        html = f"""
        <div style="margin: 8px 0; text-align: center;">
            <span style="color: #888; font-size: 11px; font-style: italic;">
                {message}
            </span>
        </div>
        """
        self.chat_display.append(html)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self) -> None:
        """Scroll chat display to bottom."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_display.setTextCursor(cursor)

    def _process_draw_commands(self, response: str) -> None:
        """Extract and process draw commands from AI response (Phase 5.9).

        Args:
            response: AI response text
        """
        import re

        # Find all level tags: [#Level-Type; low-high]
        pattern = r'\[#([^;]+);\s*([0-9.]+)-([0-9.]+)\]'
        matches = re.findall(pattern, response)

        if matches:
            self._add_system_message(f"📊 {len(matches)} Level gefunden - klicke zum Zeichnen")

            # Store for later drawing
            self._detected_levels = [
                {"type": m[0], "low": float(m[1]), "high": float(m[2])}
                for m in matches
            ]

    def draw_detected_level(self, index: int) -> None:
        """Draw a detected level on the chart.

        Args:
            index: Index in _detected_levels list
        """
        if not hasattr(self, '_detected_levels') or index >= len(self._detected_levels):
            return

        level = self._detected_levels[index]
        level_type = level["type"].lower()

        # Determine zone type
        if "support" in level_type:
            zone_type = "support"
        elif "resistance" in level_type:
            zone_type = "resistance"
        else:
            zone_type = "support"  # Default

        # Emit signal for chart drawing
        self.draw_zone_requested.emit(
            zone_type,
            level["high"],
            level["low"],
            level["type"]
        )
        self._add_system_message(f"✅ Level gezeichnet: {level['type']}")
