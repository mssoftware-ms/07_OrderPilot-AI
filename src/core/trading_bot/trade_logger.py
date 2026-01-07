"""
Trade Logger - Detailliertes Logging-System für jeden Trade

Jeder Trade bekommt sein eigenes Log mit:
- Marktanalyse zum Entry-Zeitpunkt
- Alle Indikator-Werte (RSI, EMA, MACD, BB, ATR, ADX)
- Regime und Confluence Score
- AI Validation (wenn aktiviert)
- Entry/Exit Zeiten und Preise
- SL/TP Levels und Trailing Stop History
- Gewinn/Verlust Berechnung
- Performance-Metriken
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TradeOutcome(str, Enum):
    """Ergebnis eines Trades."""

    WIN = "WIN"
    LOSS = "LOSS"
    BREAKEVEN = "BREAKEVEN"
    OPEN = "OPEN"  # Trade noch offen


class ExitReason(str, Enum):
    """Grund für Trade-Exit."""

    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT = "TAKE_PROFIT"
    TRAILING_STOP = "TRAILING_STOP"
    SIGNAL_EXIT = "SIGNAL_EXIT"  # Von ExitTrigger - Signal-basierter Exit
    SIGNAL_REVERSAL = "SIGNAL_REVERSAL"  # Alias für Kompatibilität
    SESSION_END = "SESSION_END"
    MANUAL = "MANUAL"  # Von ExitTrigger
    MANUAL_CLOSE = "MANUAL_CLOSE"  # Alias für Kompatibilität
    DAILY_LOSS_LIMIT = "DAILY_LOSS_LIMIT"  # Von ExitTrigger
    MAX_DAILY_LOSS = "MAX_DAILY_LOSS"  # Alias für Kompatibilität
    BOT_STOPPED = "BOT_STOPPED"


@dataclass
class IndicatorSnapshot:
    """Snapshot aller Indikator-Werte zu einem Zeitpunkt."""

    timestamp: datetime

    # Trend Indikatoren
    ema_20: float | None = None
    ema_50: float | None = None
    ema_200: float | None = None
    ema_20_distance_pct: float | None = None  # Preis-Abstand zu EMA20 in %

    # Momentum
    rsi_14: float | None = None
    rsi_state: str | None = None  # OVERBOUGHT, OVERSOLD, NEUTRAL
    macd_line: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    macd_crossover: str | None = None  # BULLISH, BEARISH, NONE

    # Volatility
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_pct_b: float | None = None  # 0-1 Position in Bollinger Bands
    bb_width: float | None = None
    atr_14: float | None = None
    atr_percent: float | None = None  # ATR als % vom Preis

    # Trend Strength
    adx_14: float | None = None
    plus_di: float | None = None
    minus_di: float | None = None

    # Volume
    volume: float | None = None
    volume_sma_20: float | None = None
    volume_ratio: float | None = None  # Aktuelles Volume / SMA

    # Price Action
    current_price: float | None = None
    high_24h: float | None = None
    low_24h: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


@dataclass
class MarketContext:
    """Marktkontext zum Zeitpunkt des Trades."""

    regime: str  # STRONG_TREND_BULL, STRONG_TREND_BEAR, CHOP_RANGE, etc.
    regime_confidence: float | None = None

    # Multi-Timeframe Trends
    trend_1d: str | None = None  # BULLISH, BEARISH, NEUTRAL
    trend_4h: str | None = None
    trend_1h: str | None = None
    trend_5m: str | None = None

    # Support/Resistance
    nearest_support: float | None = None
    nearest_resistance: float | None = None
    distance_to_support_pct: float | None = None
    distance_to_resistance_pct: float | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return asdict(self)


@dataclass
class SignalDetails:
    """Details zur Signal-Generierung."""

    direction: str  # LONG, SHORT
    confluence_score: int  # 0-5
    conditions_met: list[str] = field(default_factory=list)
    conditions_failed: list[str] = field(default_factory=list)

    # AI Validation (wenn aktiviert)
    ai_enabled: bool = False
    ai_confidence: int | None = None
    ai_approved: bool | None = None
    ai_reasoning: str | None = None
    ai_setup_type: str | None = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return asdict(self)


@dataclass
class TrailingStopHistory:
    """Historie der Trailing-Stop Anpassungen."""

    timestamp: datetime
    old_sl: float
    new_sl: float
    trigger_price: float
    reason: str = "price_moved_favorably"

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        result = asdict(self)
        result["timestamp"] = self.timestamp.isoformat()
        return result


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
            if isinstance(v, Decimal):
                return str(v)
            if isinstance(v, datetime):
                return v.isoformat()
            if isinstance(v, Enum):
                return v.value
            if hasattr(v, "to_dict"):
                return v.to_dict()
            return v

        result = {}
        for key, value in asdict(self).items():
            if isinstance(value, list):
                result[key] = [convert_value(item) for item in value]
            elif isinstance(value, dict):
                result[key] = {k: convert_value(v) for k, v in value.items()}
            else:
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


class TradeLogger:
    """
    Manager für Trade-Logging.

    Erstellt und verwaltet Trade-Logs für jeden einzelnen Trade.
    """

    def __init__(
        self,
        log_directory: Path | str = "logs/trades",
        log_format: str = "both",
    ):
        self.log_directory = Path(log_directory)
        self.log_format = log_format
        self.log_directory.mkdir(parents=True, exist_ok=True)

        # Täglicher Unterordner
        self._current_day_dir: Path | None = None
        self._trade_counter = 0

        logger.info(f"TradeLogger initialized. Directory: {self.log_directory}")

    def _get_day_directory(self) -> Path:
        """Gibt Verzeichnis für aktuellen Tag zurück."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        day_dir = self.log_directory / today

        if self._current_day_dir != day_dir:
            day_dir.mkdir(parents=True, exist_ok=True)
            self._current_day_dir = day_dir
            self._trade_counter = self._count_existing_trades(day_dir)

        return day_dir

    def _count_existing_trades(self, directory: Path) -> int:
        """Zählt existierende Trades im Verzeichnis."""
        json_files = list(directory.glob("trade_*.json"))
        return len(json_files)

    def create_trade_log(self, symbol: str, bot_config: dict | None = None) -> TradeLogEntry:
        """
        Erstellt einen neuen Trade-Log-Eintrag.

        Returns:
            TradeLogEntry: Neuer Log-Eintrag (noch ohne Entry-Daten)
        """
        self._trade_counter += 1
        now = datetime.now(timezone.utc)

        trade_id = f"trade_{now.strftime('%Y%m%d_%H%M%S')}_{self._trade_counter:03d}"

        entry = TradeLogEntry(
            trade_id=trade_id,
            symbol=symbol,
            created_at=now,
            bot_config_snapshot=bot_config or {},
        )

        logger.info(f"Created new trade log: {trade_id}")
        return entry

    def save_trade_log(self, trade_log: TradeLogEntry) -> Path:
        """
        Speichert Trade-Log auf Disk.

        Args:
            trade_log: Zu speichernder Log-Eintrag

        Returns:
            Path: Pfad zur gespeicherten Datei
        """
        day_dir = self._get_day_directory()

        # Berechne finale Werte
        trade_log.calculate_pnl()
        trade_log.calculate_duration()

        # JSON speichern
        if self.log_format in ("json", "both"):
            json_path = day_dir / f"{trade_log.trade_id}.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(trade_log.to_dict(), f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON log: {json_path}")

        # Markdown speichern
        if self.log_format in ("markdown", "both"):
            md_path = day_dir / f"{trade_log.trade_id}.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(trade_log.to_markdown())
            logger.info(f"Saved Markdown log: {md_path}")

        return day_dir / trade_log.trade_id

    def update_trade_log(self, trade_log: TradeLogEntry) -> None:
        """
        Aktualisiert existierenden Trade-Log.

        Nützlich für Trailing-Stop Updates während Trade läuft.
        """
        self.save_trade_log(trade_log)

    def get_daily_summary(self, date: datetime | None = None) -> dict:
        """
        Erstellt Zusammenfassung für einen Tag.

        Args:
            date: Datum (default: heute)

        Returns:
            Dictionary mit Tages-Statistiken
        """
        if date is None:
            date = datetime.now(timezone.utc)

        day_str = date.strftime("%Y-%m-%d")
        day_dir = self.log_directory / day_str

        if not day_dir.exists():
            return {
                "date": day_str,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "breakeven": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
            }

        trades = []
        for json_file in day_dir.glob("trade_*.json"):
            with open(json_file, encoding="utf-8") as f:
                trades.append(json.load(f))

        if not trades:
            return {
                "date": day_str,
                "total_trades": 0,
                "wins": 0,
                "losses": 0,
                "breakeven": 0,
                "win_rate": 0.0,
                "total_pnl": 0.0,
                "avg_pnl": 0.0,
                "max_win": 0.0,
                "max_loss": 0.0,
            }

        wins = sum(1 for t in trades if t.get("outcome") == "WIN")
        losses = sum(1 for t in trades if t.get("outcome") == "LOSS")
        breakeven = sum(1 for t in trades if t.get("outcome") == "BREAKEVEN")

        pnls = [float(t.get("net_pnl", 0) or 0) for t in trades]

        return {
            "date": day_str,
            "total_trades": len(trades),
            "wins": wins,
            "losses": losses,
            "breakeven": breakeven,
            "win_rate": round(wins / len(trades) * 100, 1) if trades else 0.0,
            "total_pnl": round(sum(pnls), 2),
            "avg_pnl": round(sum(pnls) / len(pnls), 2) if pnls else 0.0,
            "max_win": round(max(pnls), 2) if pnls else 0.0,
            "max_loss": round(min(pnls), 2) if pnls else 0.0,
        }

    def cleanup_old_logs(self, retention_days: int = 90) -> int:
        """
        Löscht Logs älter als retention_days.

        Args:
            retention_days: Anzahl Tage die Logs behalten werden

        Returns:
            Anzahl gelöschter Dateien
        """
        if retention_days <= 0:
            return 0

        cutoff = datetime.now(timezone.utc).date()
        deleted = 0

        for day_dir in self.log_directory.iterdir():
            if not day_dir.is_dir():
                continue

            try:
                dir_date = datetime.strptime(day_dir.name, "%Y-%m-%d").date()
                age_days = (cutoff - dir_date).days

                if age_days > retention_days:
                    # Lösche alle Dateien im Verzeichnis
                    for file in day_dir.iterdir():
                        file.unlink()
                        deleted += 1
                    day_dir.rmdir()
                    logger.info(f"Deleted old log directory: {day_dir}")

            except ValueError:
                # Kein gültiges Datums-Verzeichnis, ignorieren
                continue

        return deleted
