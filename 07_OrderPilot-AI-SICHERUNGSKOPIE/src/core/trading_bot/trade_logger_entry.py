"""Trade Logger Entry - TradeLogEntry Dataclass with Business Logic.

Refactored from 735 LOC monolith using composition pattern.

Module 2/4 of trade_logger.py split.

Contains:
- TradeLogEntry dataclass
- add_note(): Fügt Notiz hinzu
- record_trailing_stop_update(): Zeichnet Trailing-Stop Anpassungen auf
- calculate_pnl(): Berechnet P&L nach Trade-Schließung
- calculate_duration(): Berechnet Trade-Dauer
- to_dict(): Konvertiert zu Dictionary (JSON)
- to_markdown(): Generiert Markdown-Report
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any

from src.core.trading_bot.trade_logger_state import (
    ExitReason,
    IndicatorSnapshot,
    MarketContext,
    SignalDetails,
    TradeOutcome,
    TrailingStopHistory,
)


@dataclass
class TradeLogEntry:
    """
    Vollständiger Log-Eintrag für einen Trade.

    Enthält alle Informationen für Post-Trade-Analyse.
    """

    # === IDENTIFIKATION ===
    trade_id: str  # Unique ID (z.B. "trade_20240115_143052_001")
    symbol: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # === ENTRY ===
    entry_time: datetime | None = None
    entry_price: Decimal | None = None
    entry_quantity: Decimal | None = None
    entry_side: str | None = None  # BUY, SELL
    entry_order_id: str | None = None

    # === EXIT ===
    exit_time: datetime | None = None
    exit_price: Decimal | None = None
    exit_reason: ExitReason | None = None
    exit_order_id: str | None = None

    # === RISK MANAGEMENT ===
    initial_stop_loss: Decimal | None = None
    initial_take_profit: Decimal | None = None
    current_stop_loss: Decimal | None = None
    atr_at_entry: Decimal | None = None
    position_size_usd: Decimal | None = None
    risk_amount_usd: Decimal | None = None
    leverage: int = 10

    # === P&L ===
    realized_pnl: Decimal | None = None
    realized_pnl_percent: float | None = None
    fees_paid: Decimal | None = None
    net_pnl: Decimal | None = None
    outcome: TradeOutcome = TradeOutcome.OPEN

    # === DURATION ===
    duration_seconds: int | None = None
    duration_formatted: str | None = None  # "2h 15m 30s"

    # === SNAPSHOTS ===
    entry_indicators: IndicatorSnapshot | None = None
    exit_indicators: IndicatorSnapshot | None = None
    market_context: MarketContext | None = None
    signal_details: SignalDetails | None = None

    # === TRAILING STOP HISTORY ===
    trailing_stop_history: list[TrailingStopHistory] = field(default_factory=list)

    # === BOT CONFIG (für Reproduzierbarkeit) ===
    bot_config_snapshot: dict = field(default_factory=dict)

    # === NOTES ===
    notes: list[str] = field(default_factory=list)

    def add_note(self, note: str) -> None:
        """Fügt eine Notiz hinzu."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        self.notes.append(f"[{timestamp}] {note}")

    def record_trailing_stop_update(
        self, old_sl: float, new_sl: float, trigger_price: float
    ) -> None:
        """Zeichnet Trailing-Stop Anpassung auf."""
        self.trailing_stop_history.append(
            TrailingStopHistory(
                timestamp=datetime.now(timezone.utc),
                old_sl=old_sl,
                new_sl=new_sl,
                trigger_price=trigger_price,
            )
        )
        self.current_stop_loss = Decimal(str(new_sl))

    def calculate_pnl(self) -> None:
        """Berechnet P&L nach Trade-Schließung."""
        if not all([self.entry_price, self.exit_price, self.entry_quantity]):
            return

        entry = float(self.entry_price)
        exit_p = float(self.exit_price)
        qty = float(self.entry_quantity)

        if self.entry_side == "BUY":
            raw_pnl = (exit_p - entry) * qty
        else:  # SELL (Short)
            raw_pnl = (entry - exit_p) * qty

        # Mit Leverage
        raw_pnl *= self.leverage

        self.realized_pnl = Decimal(str(round(raw_pnl, 2)))
        self.realized_pnl_percent = round((raw_pnl / (entry * qty)) * 100, 2)

        # Net PnL (nach Fees)
        fees = float(self.fees_paid or 0)
        self.net_pnl = Decimal(str(round(raw_pnl - fees, 2)))

        # Outcome bestimmen
        if self.net_pnl > 0:
            self.outcome = TradeOutcome.WIN
        elif self.net_pnl < 0:
            self.outcome = TradeOutcome.LOSS
        else:
            self.outcome = TradeOutcome.BREAKEVEN

    def calculate_duration(self) -> None:
        """Berechnet Trade-Dauer."""
        if not self.entry_time or not self.exit_time:
            return

        delta = self.exit_time - self.entry_time
        self.duration_seconds = int(delta.total_seconds())

        # Formatierung
        hours, remainder = divmod(self.duration_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)

        parts = []
        if hours:
            parts.append(f"{hours}h")
        if minutes:
            parts.append(f"{minutes}m")
        parts.append(f"{seconds}s")

        self.duration_formatted = " ".join(parts)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary (für JSON Export)."""

        def convert_value(v: Any) -> Any:
            """Rekursiv konvertiert Werte zu JSON-serialisierbaren Typen."""
            if isinstance(v, Decimal):
                return str(v)
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, Enum):
                return v.value
            if isinstance(v, dict):
                # Rekursiv durch verschachtelte Dicts gehen
                return {k: convert_value(val) for k, val in v.items()}
            if isinstance(v, list):
                # Rekursiv durch Listen gehen
                return [convert_value(item) for item in v]
            if hasattr(v, "to_dict"):
                return v.to_dict()
            return v

        result = {}
        for key, value in asdict(self).items():
            result[key] = convert_value(value)

        return result

    def to_markdown(self) -> str:
        """Generiert Markdown-Report für den Trade."""
        lines = [
            f"# Trade Report: {self.trade_id}",
            "",
            f"**Symbol:** {self.symbol}",
            f"**Created:** {self.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "---",
            "",
            "## Trade Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Direction | {self.entry_side or 'N/A'} |",
            f"| Entry Price | ${self.entry_price or 'N/A'} |",
            f"| Exit Price | ${self.exit_price or 'N/A'} |",
            f"| Quantity | {self.entry_quantity or 'N/A'} BTC |",
            f"| Leverage | {self.leverage}x |",
            f"| Duration | {self.duration_formatted or 'N/A'} |",
            f"| Outcome | **{self.outcome.value}** |",
            f"| Net P&L | ${self.net_pnl or 'N/A'} ({self.realized_pnl_percent or 0}%) |",
            "",
            "---",
            "",
            "## Risk Management",
            "",
            f"| Parameter | Value |",
            f"|-----------|-------|",
            f"| Initial SL | ${self.initial_stop_loss or 'N/A'} |",
            f"| Initial TP | ${self.initial_take_profit or 'N/A'} |",
            f"| Final SL | ${self.current_stop_loss or 'N/A'} |",
            f"| ATR at Entry | ${self.atr_at_entry or 'N/A'} |",
            f"| Risk Amount | ${self.risk_amount_usd or 'N/A'} |",
            f"| Exit Reason | {self.exit_reason.value if self.exit_reason else 'N/A'} |",
            "",
        ]

        # Entry Indicators
        if self.entry_indicators:
            ind = self.entry_indicators
            lines.extend(
                [
                    "---",
                    "",
                    "## Entry Indicators",
                    "",
                    f"**Time:** {ind.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}",
                    "",
                    "### Trend",
                    f"- EMA 20: ${ind.ema_20:.2f}" if ind.ema_20 else "- EMA 20: N/A",
                    f"- EMA 50: ${ind.ema_50:.2f}" if ind.ema_50 else "- EMA 50: N/A",
                    f"- EMA 200: ${ind.ema_200:.2f}"
                    if ind.ema_200
                    else "- EMA 200: N/A",
                    f"- Price to EMA20: {ind.ema_20_distance_pct:.2f}%"
                    if ind.ema_20_distance_pct
                    else "",
                    "",
                    "### Momentum",
                    f"- RSI (14): {ind.rsi_14:.1f} ({ind.rsi_state})"
                    if ind.rsi_14
                    else "- RSI: N/A",
                    f"- MACD: {ind.macd_line:.2f} / Signal: {ind.macd_signal:.2f}"
                    if ind.macd_line
                    else "- MACD: N/A",
                    f"- MACD Crossover: {ind.macd_crossover}"
                    if ind.macd_crossover
                    else "",
                    "",
                    "### Volatility",
                    f"- ATR (14): ${ind.atr_14:.2f} ({ind.atr_percent:.2f}%)"
                    if ind.atr_14
                    else "- ATR: N/A",
                    f"- Bollinger %B: {ind.bb_pct_b:.2f}"
                    if ind.bb_pct_b is not None
                    else "",
                    f"- BB Width: {ind.bb_width:.4f}" if ind.bb_width else "",
                    "",
                    "### Trend Strength",
                    f"- ADX (14): {ind.adx_14:.1f}" if ind.adx_14 else "- ADX: N/A",
                    f"- +DI: {ind.plus_di:.1f} / -DI: {ind.minus_di:.1f}"
                    if ind.plus_di
                    else "",
                    "",
                ]
            )

        # Market Context
        if self.market_context:
            ctx = self.market_context
            lines.extend(
                [
                    "---",
                    "",
                    "## Market Context",
                    "",
                    f"**Regime:** {ctx.regime}",
                    "",
                    "### Multi-Timeframe Trends",
                    f"- 1D: {ctx.trend_1d or 'N/A'}",
                    f"- 4H: {ctx.trend_4h or 'N/A'}",
                    f"- 1H: {ctx.trend_1h or 'N/A'}",
                    f"- 5M: {ctx.trend_5m or 'N/A'}",
                    "",
                    "### Support/Resistance",
                    f"- Nearest Support: ${ctx.nearest_support:.2f} ({ctx.distance_to_support_pct:.2f}% away)"
                    if ctx.nearest_support
                    else "- Support: N/A",
                    f"- Nearest Resistance: ${ctx.nearest_resistance:.2f} ({ctx.distance_to_resistance_pct:.2f}% away)"
                    if ctx.nearest_resistance
                    else "- Resistance: N/A",
                    "",
                ]
            )

        # Signal Details
        if self.signal_details:
            sig = self.signal_details
            lines.extend(
                [
                    "---",
                    "",
                    "## Signal Analysis",
                    "",
                    f"**Direction:** {sig.direction}",
                    f"**Confluence Score:** {sig.confluence_score}/5",
                    "",
                    "### Conditions Met",
                ]
            )
            for cond in sig.conditions_met:
                lines.append(f"- ✅ {cond}")

            lines.append("")
            lines.append("### Conditions Failed")
            for cond in sig.conditions_failed:
                lines.append(f"- ❌ {cond}")

            if sig.ai_enabled:
                lines.extend(
                    [
                        "",
                        "### AI Validation",
                        f"- **Confidence:** {sig.ai_confidence}%",
                        f"- **Approved:** {'Yes' if sig.ai_approved else 'No'}",
                        f"- **Setup Type:** {sig.ai_setup_type or 'N/A'}",
                        f"- **Reasoning:** {sig.ai_reasoning or 'N/A'}",
                    ]
                )

            lines.append("")

        # Trailing Stop History
        if self.trailing_stop_history:
            lines.extend(
                [
                    "---",
                    "",
                    "## Trailing Stop History",
                    "",
                    "| Time | Old SL | New SL | Trigger Price |",
                    "|------|--------|--------|---------------|",
                ]
            )
            for ts in self.trailing_stop_history:
                time_str = ts.timestamp.strftime("%H:%M:%S")
                lines.append(
                    f"| {time_str} | ${ts.old_sl:.2f} | ${ts.new_sl:.2f} | ${ts.trigger_price:.2f} |"
                )
            lines.append("")

        # Notes
        if self.notes:
            lines.extend(
                [
                    "---",
                    "",
                    "## Trade Notes",
                    "",
                ]
            )
            for note in self.notes:
                lines.append(f"- {note}")
            lines.append("")

        # Bot Config
        if self.bot_config_snapshot:
            lines.extend(
                [
                    "---",
                    "",
                    "## Bot Configuration (at trade time)",
                    "",
                    "```json",
                    json.dumps(self.bot_config_snapshot, indent=2),
                    "```",
                ]
            )

        return "\n".join(lines)
