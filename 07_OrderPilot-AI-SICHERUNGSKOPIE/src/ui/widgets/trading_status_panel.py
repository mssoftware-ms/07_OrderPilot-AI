"""
Trading Status Panel - Live-Anzeige von Trading-Signalen und Status.

Zeigt in Echtzeit:
- Aktuelles Markt-Regime mit Farbcodierung
- Entry Score mit Quality Tier
- LLM Validation Status
- Gate Status (Blocked/Allowed)
- Trigger Information
- Leverage Empfehlung

Phase 5.5 der Bot-Integration.
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QGroupBox,
    QLabel,
    QFrame,
    QProgressBar,
    QPushButton,
)
from PyQt6.QtGui import QFont

if TYPE_CHECKING:
    from src.core.trading_bot import (
        MarketContext,
        RegimeResult,
        EntryScoreResult,
        LLMValidationResult,
        LeverageResult,
        TriggerResult,
    )

logger = logging.getLogger(__name__)


class StatusCard(QFrame):
    """Reusable status card component."""

    def __init__(
        self,
        title: str,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        self.setStyleSheet("""
            StatusCard {
                background-color: #2d2d2d;
                border-radius: 8px;
                padding: 8px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(12, 8, 12, 8)

        # Title
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("color: #888; font-size: 10px; font-weight: bold;")
        layout.addWidget(self._title_label)

        # Value
        self._value_label = QLabel("-")
        self._value_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold;")
        layout.addWidget(self._value_label)

        # Subtitle
        self._subtitle_label = QLabel("")
        self._subtitle_label.setStyleSheet("color: #888; font-size: 10px;")
        layout.addWidget(self._subtitle_label)

    def set_value(self, value: str, color: str = "white") -> None:
        """Set the main value."""
        self._value_label.setText(value)
        self._value_label.setStyleSheet(f"color: {color}; font-size: 16px; font-weight: bold;")

    def set_subtitle(self, text: str) -> None:
        """Set the subtitle text."""
        self._subtitle_label.setText(text)


class ScoreBar(QWidget):
    """Visual score bar with colored segments."""

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        # Progress bar
        self._bar = QProgressBar()
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(True)
        self._bar.setFixedHeight(20)
        layout.addWidget(self._bar)

        # Labels
        label_layout = QHBoxLayout()
        label_layout.setContentsMargins(0, 0, 0, 0)

        for label, pos in [("0", "left"), ("0.5", "center"), ("1.0", "right")]:
            lbl = QLabel(label)
            lbl.setStyleSheet("color: #666; font-size: 9px;")
            if pos == "center":
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            elif pos == "right":
                lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            label_layout.addWidget(lbl)

        layout.addLayout(label_layout)

    def set_score(self, score: float, quality: str = "WEAK") -> None:
        """Set the score value with quality-based coloring."""
        value = int(score * 100)
        self._bar.setValue(value)
        self._bar.setFormat(f"{score:.2f} ({quality})")

        colors = {
            "EXCELLENT": "#4CAF50",  # Green
            "GOOD": "#8BC34A",       # Light Green
            "MODERATE": "#FFC107",   # Amber
            "WEAK": "#FF9800",       # Orange
            "NO_SIGNAL": "#f44336",  # Red
        }

        color = colors.get(quality, "#888")
        self._bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #444;
                border-radius: 4px;
                text-align: center;
                color: white;
                background-color: #333;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)


class TradingStatusPanel(QWidget):
    """
    Comprehensive trading status panel.

    Shows real-time status of:
    - Market regime
    - Entry score
    - LLM validation
    - Gate status
    - Trigger info
    - Leverage recommendation

    Signals:
        refresh_requested: Emitted when user requests refresh
    """

    refresh_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._setup_ui()

        # Auto-refresh timer (optional)
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._on_refresh)

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(8)

        # Header with refresh button
        header_layout = QHBoxLayout()
        header = QLabel("<b>Trading Status</b>")
        header_layout.addWidget(header)
        header_layout.addStretch()

        self._last_update_label = QLabel("Nicht aktualisiert")
        self._last_update_label.setStyleSheet("color: #888; font-size: 10px;")
        header_layout.addWidget(self._last_update_label)

        self._refresh_btn = QPushButton("Aktualisieren")
        self._refresh_btn.setFixedWidth(100)
        self._refresh_btn.clicked.connect(self._on_refresh)
        header_layout.addWidget(self._refresh_btn)

        main_layout.addLayout(header_layout)

        # Status Cards Row 1
        row1 = QHBoxLayout()

        # Regime Card
        self._regime_card = StatusCard("REGIME")
        row1.addWidget(self._regime_card)

        # Entry Direction Card
        self._direction_card = StatusCard("DIRECTION")
        row1.addWidget(self._direction_card)

        # LLM Action Card
        self._llm_card = StatusCard("LLM VALIDATION")
        row1.addWidget(self._llm_card)

        main_layout.addLayout(row1)

        # Entry Score Bar
        score_group = QGroupBox("Entry Score")
        score_layout = QVBoxLayout(score_group)
        self._score_bar = ScoreBar()
        score_layout.addWidget(self._score_bar)

        # Component breakdown
        self._components_label = QLabel("Komponenten: -")
        self._components_label.setStyleSheet("color: #888; font-size: 10px;")
        self._components_label.setWordWrap(True)
        score_layout.addWidget(self._components_label)

        main_layout.addWidget(score_group)

        # Gates & Trigger Row
        row2 = QHBoxLayout()

        # Gate Status
        gate_group = QGroupBox("Gate Status")
        gate_layout = QFormLayout(gate_group)

        self._gate_status_label = QLabel("-")
        self._gate_status_label.setStyleSheet("font-weight: bold;")
        gate_layout.addRow("Status:", self._gate_status_label)

        self._gate_reason_label = QLabel("-")
        self._gate_reason_label.setWordWrap(True)
        self._gate_reason_label.setStyleSheet("color: #888; font-size: 10px;")
        gate_layout.addRow("Reason:", self._gate_reason_label)

        row2.addWidget(gate_group)

        # Trigger Info
        trigger_group = QGroupBox("Trigger Info")
        trigger_layout = QFormLayout(trigger_group)

        self._trigger_type_label = QLabel("-")
        trigger_layout.addRow("Typ:", self._trigger_type_label)

        self._trigger_conf_label = QLabel("-")
        trigger_layout.addRow("Confidence:", self._trigger_conf_label)

        self._trigger_level_label = QLabel("-")
        trigger_layout.addRow("Level:", self._trigger_level_label)

        row2.addWidget(trigger_group)

        main_layout.addLayout(row2)

        # Leverage Row
        leverage_group = QGroupBox("Leverage Empfehlung")
        leverage_layout = QFormLayout(leverage_group)

        self._leverage_value_label = QLabel("-")
        self._leverage_value_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        leverage_layout.addRow("Empfohlen:", self._leverage_value_label)

        self._leverage_max_label = QLabel("-")
        leverage_layout.addRow("Max (Asset Tier):", self._leverage_max_label)

        self._leverage_regime_label = QLabel("-")
        leverage_layout.addRow("Regime Modifier:", self._leverage_regime_label)

        self._liq_distance_label = QLabel("-")
        leverage_layout.addRow("Liq. Abstand:", self._liq_distance_label)

        main_layout.addWidget(leverage_group)

        # Spacer
        main_layout.addStretch()

    def _on_refresh(self) -> None:
        """Handle refresh button click."""
        self.refresh_requested.emit()
        self._last_update_label.setText(f"Aktualisiert: {datetime.now().strftime('%H:%M:%S')}")

    def update_regime(self, regime_result: Optional["RegimeResult"]) -> None:
        """Update regime display."""
        if regime_result is None:
            self._regime_card.set_value("-", "#888")
            self._regime_card.set_subtitle("Kein Regime erkannt")
            return

        regime = regime_result.regime
        regime_colors = {
            "STRONG_TREND_BULL": "#4CAF50",
            "STRONG_TREND_BEAR": "#f44336",
            "WEAK_TREND_BULL": "#8BC34A",
            "WEAK_TREND_BEAR": "#FF7043",
            "CHOP_RANGE": "#FFC107",
            "VOLATILITY_EXPLOSIVE": "#9C27B0",
            "NEUTRAL": "#888",
        }

        regime_name = regime.value if hasattr(regime, 'value') else str(regime)
        color = regime_colors.get(regime_name, "#888")

        # Shorten display name
        display_name = regime_name.replace("_", " ").replace("STRONG ", "").replace("WEAK ", "~")

        self._regime_card.set_value(display_name, color)

        entry_text = "Entry ERLAUBT" if regime_result.allows_market_entry else "Entry BLOCKIERT"
        self._regime_card.set_subtitle(f"ADX: {regime_result.adx:.1f} | {entry_text}")

    def update_entry_score(self, score_result: Optional["EntryScoreResult"]) -> None:
        """Update entry score display."""
        if score_result is None:
            self._score_bar.set_score(0, "NO_SIGNAL")
            self._direction_card.set_value("-", "#888")
            self._components_label.setText("Komponenten: -")
            self._gate_status_label.setText("-")
            self._gate_reason_label.setText("-")
            return

        # Score bar
        quality = score_result.quality.value if hasattr(score_result.quality, 'value') else str(score_result.quality)
        self._score_bar.set_score(score_result.final_score, quality)

        # Direction
        direction = score_result.direction.value if hasattr(score_result.direction, 'value') else str(score_result.direction)
        direction_colors = {"LONG": "#4CAF50", "SHORT": "#f44336", "NEUTRAL": "#888"}
        self._direction_card.set_value(direction, direction_colors.get(direction, "#888"))
        self._direction_card.set_subtitle(f"Raw: {score_result.raw_score:.3f} → Final: {score_result.final_score:.3f}")

        # Components breakdown
        if score_result.components:
            comp_parts = []
            for c in score_result.components[:4]:  # Show top 4
                comp_parts.append(f"{c.name[:4]}: {c.raw_score:.2f}")
            self._components_label.setText("Komponenten: " + " | ".join(comp_parts))

        # Gate status
        if score_result.gate_result:
            gate = score_result.gate_result
            gate_status = gate.status.value if hasattr(gate.status, 'value') else str(gate.status)
            gate_colors = {"PASSED": "#4CAF50", "BLOCKED": "#f44336", "BOOSTED": "#2196F3", "REDUCED": "#FF9800"}
            self._gate_status_label.setText(gate_status)
            self._gate_status_label.setStyleSheet(f"color: {gate_colors.get(gate_status, '#888')}; font-weight: bold;")
            self._gate_reason_label.setText(gate.reason or "-")

    def update_llm_validation(self, llm_result: Optional["LLMValidationResult"]) -> None:
        """Update LLM validation display."""
        if llm_result is None:
            self._llm_card.set_value("-", "#888")
            self._llm_card.set_subtitle("Keine Validierung")
            return

        action = llm_result.action.value if hasattr(llm_result.action, 'value') else str(llm_result.action)
        action_colors = {
            "approve": "#4CAF50",
            "boost": "#2196F3",
            "veto": "#f44336",
            "caution": "#FF9800",
            "defer": "#888",
        }

        color = action_colors.get(action, "#888")
        self._llm_card.set_value(action.upper(), color)

        tier = llm_result.tier.value if hasattr(llm_result.tier, 'value') else str(llm_result.tier)
        self._llm_card.set_subtitle(f"Conf: {llm_result.confidence}% | {tier} | {llm_result.latency_ms}ms")

    def update_trigger(self, trigger_result: Optional["TriggerResult"]) -> None:
        """Update trigger info display."""
        if trigger_result is None or trigger_result.status.value != "TRIGGERED":
            self._trigger_type_label.setText("-")
            self._trigger_conf_label.setText("-")
            self._trigger_level_label.setText("-")
            return

        trigger_type = trigger_result.trigger_type.value if hasattr(trigger_result.trigger_type, 'value') else str(trigger_result.trigger_type)
        self._trigger_type_label.setText(trigger_type)
        self._trigger_conf_label.setText(f"{trigger_result.confidence:.0%}")
        self._trigger_level_label.setText(f"{trigger_result.level_price:.2f}" if trigger_result.level_price else "-")

    def update_leverage(self, leverage_result: Optional["LeverageResult"]) -> None:
        """Update leverage display."""
        if leverage_result is None:
            self._leverage_value_label.setText("-")
            self._leverage_max_label.setText("-")
            self._leverage_regime_label.setText("-")
            self._liq_distance_label.setText("-")
            return

        # Recommended leverage
        action_colors = {"APPROVED": "#4CAF50", "REDUCED": "#FF9800", "BLOCKED": "#f44336"}
        action = leverage_result.action.value if hasattr(leverage_result.action, 'value') else str(leverage_result.action)
        color = action_colors.get(action, "#888")

        self._leverage_value_label.setText(f"{leverage_result.recommended_leverage}x")
        self._leverage_value_label.setStyleSheet(f"color: {color}; font-size: 14px; font-weight: bold;")

        # Max from tier
        self._leverage_max_label.setText(f"{leverage_result.max_allowed_leverage}x ({leverage_result.asset_tier.value})")

        # Regime modifier
        self._leverage_regime_label.setText(f"{leverage_result.regime_modifier:.0%}")

        # Liquidation distance
        if leverage_result.liquidation_distance_pct:
            liq_color = "#4CAF50" if leverage_result.liquidation_distance_pct >= 5.0 else "#f44336"
            self._liq_distance_label.setText(f"{leverage_result.liquidation_distance_pct:.1f}%")
            self._liq_distance_label.setStyleSheet(f"color: {liq_color};")
        else:
            self._liq_distance_label.setText("-")

    def update_all(
        self,
        regime_result: Optional["RegimeResult"] = None,
        score_result: Optional["EntryScoreResult"] = None,
        llm_result: Optional["LLMValidationResult"] = None,
        trigger_result: Optional["TriggerResult"] = None,
        leverage_result: Optional["LeverageResult"] = None,
    ) -> None:
        """Update all status displays at once."""
        self.update_regime(regime_result)
        self.update_entry_score(score_result)
        self.update_llm_validation(llm_result)
        self.update_trigger(trigger_result)
        self.update_leverage(leverage_result)
        self._last_update_label.setText(f"Aktualisiert: {datetime.now().strftime('%H:%M:%S')}")

    def start_auto_refresh(self, interval_ms: int = 5000) -> None:
        """Start auto-refresh timer."""
        self._refresh_timer.start(interval_ms)

    def stop_auto_refresh(self) -> None:
        """Stop auto-refresh timer."""
        self._refresh_timer.stop()
