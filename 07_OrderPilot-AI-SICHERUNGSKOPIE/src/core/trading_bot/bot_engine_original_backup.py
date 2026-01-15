"""
Trading Bot Engine - Zentrale State Machine und Orchestrierung

Die Haupt-Engine des Trading Bots. Koordiniert:
- State Machine (IDLE → ANALYZING → IN_POSITION)
- Signal-Generierung
- Risk Management
- Position Monitoring
- AI Validation
- Trade Logging

WICHTIG: Arbeitet NUR im Paper-Modus!
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Any

import pandas as pd

if TYPE_CHECKING:
    from PyQt6.QtCore import pyqtSignal

    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
    from src.core.broker.broker_types import OrderRequest, OrderResponse, Position

from .ai_validator import AISignalValidator, AIValidation
from .bot_config import BotConfig
from .position_monitor import (
    ExitResult,
    ExitTrigger,
    MonitoredPosition,
    PositionMonitor,
)
from .risk_manager import RiskCalculation, RiskManager
from .signal_generator import SignalDirection, SignalGenerator, TradeSignal
from .strategy_config import StrategyConfig, get_strategy_config
from .trade_logger import (
    ExitReason,
    IndicatorSnapshot,
    MarketContext,
    SignalDetails,
    TradeLogEntry,
    TradeLogger,
    TradeOutcome,
)

logger = logging.getLogger(__name__)


class BotState(str, Enum):
    """Bot-Zustände."""

    IDLE = "IDLE"  # Bot gestoppt
    STARTING = "STARTING"  # Bot startet
    ANALYZING = "ANALYZING"  # Markt wird analysiert, keine Position
    WAITING_SIGNAL = "WAITING_SIGNAL"  # Warte auf Signal
    VALIDATING = "VALIDATING"  # Signal wird validiert (AI)
    OPENING_POSITION = "OPENING_POSITION"  # Order wird platziert
    IN_POSITION = "IN_POSITION"  # Position offen, überwache
    CLOSING_POSITION = "CLOSING_POSITION"  # Position wird geschlossen
    STOPPING = "STOPPING"  # Bot stoppt
    ERROR = "ERROR"  # Fehler-Zustand


@dataclass
class BotStatistics:
    """Tagesstatistiken des Bots."""

    date: str
    trades_total: int = 0
    trades_won: int = 0
    trades_lost: int = 0
    trades_breakeven: int = 0
    total_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    max_drawdown: Decimal = field(default_factory=lambda: Decimal("0"))
    peak_pnl: Decimal = field(default_factory=lambda: Decimal("0"))
    signals_generated: int = 0
    signals_rejected_confluence: int = 0
    signals_rejected_ai: int = 0

    @property
    def win_rate(self) -> float:
        """Gewinnrate in %."""
        if self.trades_total == 0:
            return 0.0
        return round(self.trades_won / self.trades_total * 100, 1)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "date": self.date,
            "trades_total": self.trades_total,
            "trades_won": self.trades_won,
            "trades_lost": self.trades_lost,
            "trades_breakeven": self.trades_breakeven,
            "win_rate": self.win_rate,
            "total_pnl": str(self.total_pnl),
            "max_drawdown": str(self.max_drawdown),
            "signals_generated": self.signals_generated,
            "signals_rejected_confluence": self.signals_rejected_confluence,
            "signals_rejected_ai": self.signals_rejected_ai,
        }


class TradingBotEngine:
    """
    Haupt-Engine des Trading Bots.

    Koordiniert alle Komponenten und verwaltet den Bot-Lebenszyklus.

    SICHERHEIT: Arbeitet NUR mit BitunixPaperAdapter!
    """

    def __init__(
        self,
        adapter: "BitunixPaperAdapter",
        config: BotConfig | None = None,
        strategy_config_path: Path | str | None = None,
    ):
        """
        Args:
            adapter: BitunixPaperAdapter (NUR PAPER!)
            config: Bot-Konfiguration
            strategy_config_path: Pfad zur JSON Strategie-Konfiguration
        """
        # SICHERHEITS-CHECK: Nur Paper-Adapter erlaubt!
        adapter_class = type(adapter).__name__
        if "Paper" not in adapter_class:
            raise ValueError(
                f"SICHERHEITSFEHLER: TradingBotEngine akzeptiert NUR Paper-Adapter! "
                f"Erhalten: {adapter_class}"
            )

        self.adapter = adapter
        self.config = config or BotConfig()
        self.strategy_config = get_strategy_config(strategy_config_path)

        # Komponenten initialisieren
        self.signal_generator = SignalGenerator(
            min_confluence=self.strategy_config.min_confluence_long
        )
        self.risk_manager = RiskManager(
            config=self.config,
            strategy_config=self.strategy_config,
        )
        self.position_monitor = PositionMonitor(
            risk_manager=self.risk_manager,
            check_interval_ms=self.config.position_check_interval_ms,
        )
        # AISignalValidator - Provider und Model kommen aus QSettings (File -> Settings -> AI)!
        self.ai_validator = AISignalValidator(
            enabled=self.strategy_config.ai_config.enabled,
            confidence_threshold_trade=self.strategy_config.ai_config.confidence_threshold_trade,
            confidence_threshold_deep=self.strategy_config.ai_config.confidence_threshold_deep,
            deep_analysis_enabled=self.strategy_config.ai_config.deep_analysis_enabled,
            fallback_to_technical=self.strategy_config.ai_config.fallback_to_technical,
        )
        self.trade_logger = TradeLogger(
            log_directory=self.config.logging.log_directory,
            log_format=self.config.logging.log_format,
        )

        # State
        self._state = BotState.IDLE
        self._running = False
        self._current_trade_log: TradeLogEntry | None = None
        self._last_signal: TradeSignal | None = None
        self._last_analysis_time: datetime | None = None
        self._last_error: str | None = None

        # Chart Data (von UI übergeben - vermeidet doppeltes Laden!)
        self._chart_data: pd.DataFrame | None = None
        self._chart_symbol: str | None = None
        self._chart_timeframe: str | None = None

        # Statistics
        self._stats = BotStatistics(
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )

        # Callbacks für UI
        self._on_state_changed: Callable[[BotState], None] | None = None
        self._on_signal_generated: Callable[[TradeSignal], None] | None = None
        self._on_position_opened: Callable[[MonitoredPosition], None] | None = None
        self._on_position_closed: Callable[[TradeLogEntry], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._on_log: Callable[[str], None] | None = None

        # Timer/Task
        self._analysis_task: asyncio.Task | None = None

        # Setup Position Monitor Callbacks
        self.position_monitor.set_exit_callback(self._on_exit_triggered)
        self.position_monitor.set_trailing_callback(self._on_trailing_updated)
        self.position_monitor.set_price_callback(self._on_price_updated)

        logger.info(
            f"TradingBotEngine initialized. "
            f"Symbol: {self.config.symbol}, "
            f"Leverage: {self.strategy_config.risk_config.leverage}x, "
            f"AI: {'Enabled' if self.ai_validator.enabled else 'Disabled'}"
        )

    @property
    def state(self) -> BotState:
        """Aktueller Bot-Zustand."""
        return self._state

    @property
    def is_running(self) -> bool:
        """Bot läuft?"""
        return self._running

    @property
    def has_position(self) -> bool:
        """Position offen?"""
        return self.position_monitor.has_position

    @property
    def statistics(self) -> BotStatistics:
        """Aktuelle Statistiken."""
        return self._stats

    def _set_state(self, new_state: BotState) -> None:
        """Setzt neuen Zustand und triggert Callback."""
        old_state = self._state
        self._state = new_state
        self._log(f"State: {old_state.value} → {new_state.value}")

        if self._on_state_changed:
            self._on_state_changed(new_state)

    def _log(self, message: str) -> None:
        """Loggt Nachricht und triggert Callback."""
        timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
        full_message = f"[{timestamp}] {message}"
        logger.info(f"Bot: {message}")

        if self._on_log:
            self._on_log(full_message)

    # === Chart Data Interface ===

    def set_chart_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str,
    ) -> None:
        """
        Setzt Chart-Daten für die Analyse.

        Wird vom UI aufgerufen wenn Chart-Daten geladen werden.
        Der Bot verwendet diese Daten anstatt eigene zu laden.

        Args:
            data: DataFrame mit OHLCV-Daten und Indikatoren
            symbol: Symbol (z.B. 'BTCUSDT')
            timeframe: Timeframe (z.B. '5m', '1H')
        """
        if data is None or data.empty:
            logger.warning("set_chart_data: Empty data received, ignoring")
            return

        self._chart_data = data.copy()  # Kopie um Änderungen zu vermeiden
        self._chart_symbol = symbol
        self._chart_timeframe = timeframe

        self._log(
            f"Chart-Daten erhalten: {symbol} {timeframe}, "
            f"{len(data)} Bars"
        )
        logger.info(
            f"TradingBotEngine: Chart data set - {symbol} {timeframe}, "
            f"{len(data)} bars, columns: {list(data.columns)}"
        )

    def clear_chart_data(self) -> None:
        """Löscht die Chart-Daten (z.B. bei Symbol-Wechsel)."""
        self._chart_data = None
        self._chart_symbol = None
        self._chart_timeframe = None
        logger.debug("TradingBotEngine: Chart data cleared")

    @property
    def has_chart_data(self) -> bool:
        """Sind Chart-Daten verfügbar?"""
        return (
            self._chart_data is not None
            and not self._chart_data.empty
        )

    # === Lifecycle ===

    async def start(self) -> None:
        """Startet den Bot."""
        if self._running:
            self._log("Bot is already running")
            return

        self._set_state(BotState.STARTING)
        self._running = True

        try:
            # Adapter verbinden
            if not self.adapter.connected:
                await self.adapter.connect()
                self._log("Adapter connected")

            # Stats zurücksetzen wenn neuer Tag
            self._check_daily_reset()

            # Gespeicherte Position laden (falls vorhanden)
            if self.load_position():
                self._log("Weiter mit wiederhergestellter Position")
                # State ist bereits IN_POSITION durch load_position()
            else:
                # Analysis-Loop starten (nur wenn keine Position)
                self._analysis_task = asyncio.create_task(self._run_analysis_loop())
                self._set_state(BotState.ANALYZING)

            self._log("Bot started successfully")

        except Exception as e:
            self._last_error = str(e)
            self._set_state(BotState.ERROR)
            self._log(f"Failed to start: {e}")
            if self._on_error:
                self._on_error(str(e))

    async def stop(self, close_position: bool = False) -> None:
        """
        Stoppt den Bot.

        Args:
            close_position: True = Position schließen, False = Position speichern
        """
        if not self._running:
            return

        self._set_state(BotState.STOPPING)
        self._running = False

        # Analysis-Task stoppen
        if self._analysis_task:
            self._analysis_task.cancel()
            try:
                await self._analysis_task
            except asyncio.CancelledError:
                pass

        # Offene Position behandeln
        if self.has_position:
            if close_position:
                self._log("Position wird geschlossen...")
                exit_result = ExitResult(
                    should_exit=True,
                    trigger=ExitTrigger.BOT_STOPPED,
                    trigger_price=self.position_monitor.position.current_price,
                    reason="Bot stopped",
                )
                await self._close_position(exit_result)
            else:
                # Position speichern für nächsten Start
                self._log("Position wird für nächsten Start gespeichert...")
                self.save_position()

        self._set_state(BotState.IDLE)
        self._log("Bot stopped")

    # === Analysis Loop ===

    async def _run_analysis_loop(self) -> None:
        """Haupt-Analyse-Loop."""
        interval = self.config.analysis_interval_seconds

        while self._running:
            try:
                await self._run_analysis_cycle()
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"Analysis error: {e}")
                logger.exception("Analysis cycle error")
                await asyncio.sleep(interval)

    async def _run_analysis_cycle(self) -> None:
        """Ein Analyse-Zyklus."""
        if not self._running:
            return

        # Keine Analyse wenn Position offen und Monitor aktiv
        if self._state == BotState.IN_POSITION:
            # Nur Exit-Signal prüfen
            await self._check_exit_signal()
            return

        self._set_state(BotState.ANALYZING)

        # Marktdaten holen
        df = await self._fetch_market_data()
        if df is None or df.empty:
            self._log("No market data available")
            return

        # Regime erkennen
        regime = self._detect_regime(df)

        # Signal generieren
        signal = self.signal_generator.generate_signal(
            df=df,
            regime=regime,
            require_regime_alignment=self.config.require_regime_alignment,
        )

        self._last_signal = signal
        self._last_analysis_time = datetime.now(timezone.utc)
        self._stats.signals_generated += 1

        if self._on_signal_generated:
            self._on_signal_generated(signal)

        # Kein valides Signal
        if not signal.is_valid:
            self._set_state(BotState.WAITING_SIGNAL)
            self._stats.signals_rejected_confluence += 1
            return

        self._log(
            f"Signal: {signal.direction.value} "
            f"(Confluence: {signal.confluence_score}/5)"
        )

        # Immer Indikatoren und Kontext extrahieren (für Logging)
        indicators = self.signal_generator.extract_indicator_snapshot(df)
        market_context = self._extract_market_context(df, regime)

        # AI Validation - IMMER wenn aktiviert!
        # AI hat Veto-Recht über alle Trades
        ai_result = None

        if self.ai_validator.enabled:
            # AI ist aktiviert -> IMMER validieren, AI hat Veto-Recht!
            self._set_state(BotState.VALIDATING)
            self._log(
                f"AI-Validierung für {signal.direction.value} "
                f"(Confluence: {signal.confluence_score}/5)"
            )

            # Hierarchische Validierung: Quick -> ggf. Deep
            ai_result = await self.ai_validator.validate_signal_hierarchical(
                signal=signal,
                indicators=indicators,
                market_context=market_context,
                ohlcv_data=df,  # Für Deep Analysis
            )

            # Log Validierungslevel
            level_info = f"[{ai_result.validation_level.value.upper()}]"
            if ai_result.deep_analysis_triggered:
                level_info += " (Deep Analysis triggered)"

            if not ai_result.approved:
                self._log(
                    f"Signal rejected by AI {level_info}: "
                    f"Confidence {ai_result.confidence_score}% - {ai_result.reasoning[:100]}"
                )
                self._stats.signals_rejected_ai += 1
                self._set_state(BotState.WAITING_SIGNAL)
                return

            self._log(
                f"AI approved {level_info}: {ai_result.confidence_score}% - {ai_result.setup_type}"
            )

        # Trade ausführen (nur wenn AI nicht aktiviert ODER AI approved)
        await self._execute_trade(signal, indicators, market_context, ai_result, df)

    async def _check_exit_signal(self) -> None:
        """Prüft auf Exit-Signal durch Signal-Umkehr."""
        if not self.position_monitor.has_position:
            return

        pos = self.position_monitor.position

        # Marktdaten holen
        df = await self._fetch_market_data()
        if df is None or df.empty:
            return

        # Exit-Signal prüfen
        should_exit, reason = self.signal_generator.check_exit_signal(
            df=df,
            current_position_side=pos.side,
        )

        if should_exit:
            exit_result = self.position_monitor.trigger_signal_exit(reason)
            await self._close_position(exit_result)

    # === Trade Execution ===

    async def _execute_trade(
        self,
        signal: TradeSignal,
        indicators: IndicatorSnapshot,
        market_context: MarketContext,
        ai_result: AIValidation | None,
        df: pd.DataFrame,
    ) -> None:
        """Führt Trade aus."""
        self._set_state(BotState.OPENING_POSITION)

        try:
            # Aktuelle Daten
            current = df.iloc[-1]
            entry_price = Decimal(str(current.get("close", 0)))
            atr = Decimal(str(current.get("atr_14") or current.get("atr") or 100))

            # Balance holen
            balance = await self._get_balance()
            if balance <= 0:
                self._log("Insufficient balance")
                self._set_state(BotState.WAITING_SIGNAL)
                return

            # Risk Check
            side = "BUY" if signal.direction == SignalDirection.LONG else "SELL"

            is_valid, reason, risk_calc = self.risk_manager.validate_trade(
                balance=balance,
                entry_price=entry_price,
                side=side,
                atr=atr,
            )

            if not is_valid:
                self._log(f"Trade rejected: {reason}")
                self._set_state(BotState.WAITING_SIGNAL)
                return

            # Trade Log erstellen
            self._current_trade_log = self.trade_logger.create_trade_log(
                symbol=self.config.symbol,
                bot_config=self.config.to_dict(),
            )
            self._current_trade_log.entry_indicators = indicators
            self._current_trade_log.market_context = market_context
            self._current_trade_log.signal_details = SignalDetails(
                direction=signal.direction.value,
                confluence_score=signal.confluence_score,
                conditions_met=[c.name for c in signal.conditions_met],
                conditions_failed=[c.name for c in signal.conditions_failed],
                ai_enabled=ai_result is not None,
                ai_confidence=ai_result.confidence_score if ai_result else None,
                ai_approved=ai_result.approved if ai_result else None,
                ai_reasoning=ai_result.reasoning if ai_result else None,
                ai_setup_type=ai_result.setup_type if ai_result else None,
            )

            # Order erstellen
            from src.core.broker.broker_types import OrderRequest, OrderSide, OrderType

            order = OrderRequest(
                symbol=self.config.symbol,
                side=OrderSide.BUY if side == "BUY" else OrderSide.SELL,
                order_type=OrderType.MARKET,
                quantity=risk_calc.quantity,
                notes=f"Bot trade, leverage={self.strategy_config.risk_config.leverage}x",
            )

            # Order platzieren
            self._log(f"Placing {side} order: {risk_calc.quantity} @ ~{entry_price}")

            response = await self.adapter.place_order(order)

            if response and response.broker_order_id:
                # Trade Log aktualisieren
                self._current_trade_log.entry_time = datetime.now(timezone.utc)
                self._current_trade_log.entry_price = entry_price
                self._current_trade_log.entry_quantity = risk_calc.quantity
                self._current_trade_log.entry_side = side
                self._current_trade_log.entry_order_id = response.broker_order_id
                self._current_trade_log.initial_stop_loss = risk_calc.stop_loss
                self._current_trade_log.initial_take_profit = risk_calc.take_profit
                self._current_trade_log.current_stop_loss = risk_calc.stop_loss
                self._current_trade_log.atr_at_entry = atr
                self._current_trade_log.position_size_usd = risk_calc.position_value_usd
                self._current_trade_log.risk_amount_usd = risk_calc.risk_amount_usd
                self._current_trade_log.leverage = self.strategy_config.risk_config.leverage

                # Position Monitor setzen
                monitored_pos = self.position_monitor.set_position(
                    symbol=self.config.symbol,
                    side=side,
                    entry_price=entry_price,
                    quantity=risk_calc.quantity,
                    stop_loss=risk_calc.stop_loss,
                    take_profit=risk_calc.take_profit,
                    trailing_atr=atr if self.strategy_config.trailing_stop_enabled else None,
                    trade_log=self._current_trade_log,
                )

                self._set_state(BotState.IN_POSITION)
                self._log(
                    f"Position opened: {side} {risk_calc.quantity} BTC @ {entry_price}"
                )
                self._log(f"SL: {risk_calc.stop_loss}, TP: {risk_calc.take_profit}")

                if self._on_position_opened:
                    self._on_position_opened(monitored_pos)

            else:
                self._log("Order failed")
                self._set_state(BotState.WAITING_SIGNAL)

        except Exception as e:
            self._log(f"Trade execution failed: {e}")
            logger.exception("Trade execution error")
            self._set_state(BotState.WAITING_SIGNAL)

    async def _close_position(self, exit_result: ExitResult) -> None:
        """Schließt Position."""
        if not self.position_monitor.has_position:
            return

        self._set_state(BotState.CLOSING_POSITION)

        pos = self.position_monitor.position
        exit_price = exit_result.trigger_price or pos.current_price

        try:
            # Gegen-Order erstellen
            from src.core.broker.broker_types import OrderRequest, OrderSide, OrderType

            close_side = OrderSide.SELL if pos.side == "BUY" else OrderSide.BUY

            order = OrderRequest(
                symbol=pos.symbol,
                side=close_side,
                order_type=OrderType.MARKET,
                quantity=pos.quantity,
                notes=f"Bot close: {exit_result.trigger.value}",
            )

            response = await self.adapter.place_order(order)

            # Trade Log aktualisieren
            if self._current_trade_log:
                self._current_trade_log.exit_time = datetime.now(timezone.utc)
                self._current_trade_log.exit_price = exit_price
                self._current_trade_log.exit_reason = ExitReason(exit_result.trigger.value)
                self._current_trade_log.exit_order_id = (
                    response.broker_order_id if response else None
                )

                # Exit Indicators
                df = await self._fetch_market_data()
                if df is not None and not df.empty:
                    self._current_trade_log.exit_indicators = (
                        self.signal_generator.extract_indicator_snapshot(df)
                    )

                # Fees (geschätzt)
                fee_rate = Decimal("0.0006")  # 0.06% Taker
                self._current_trade_log.fees_paid = (
                    pos.quantity * pos.entry_price * fee_rate * 2  # Entry + Exit
                )

                # Trade Log speichern
                self.trade_logger.save_trade_log(self._current_trade_log)

                # Statistics aktualisieren
                self._update_statistics(self._current_trade_log)

                if self._on_position_closed:
                    self._on_position_closed(self._current_trade_log)

            # Position Monitor clearen
            self.position_monitor.clear_position()
            self._current_trade_log = None

            self._log(
                f"Position closed: {exit_result.trigger.value} @ {exit_price}"
            )

            self._set_state(BotState.WAITING_SIGNAL)

        except Exception as e:
            self._log(f"Failed to close position: {e}")
            logger.exception("Position close error")
            self._set_state(BotState.IN_POSITION)  # Bleibe in Position

    # === Callbacks ===

    async def _on_exit_triggered(
        self, position: MonitoredPosition, exit_result: ExitResult
    ) -> None:
        """Callback wenn Exit getriggert wird."""
        await self._close_position(exit_result)

    async def _on_trailing_updated(
        self, position: MonitoredPosition, old_sl: Decimal, new_sl: Decimal
    ) -> None:
        """Callback bei Trailing-Stop Update."""
        self._log(f"Trailing stop updated: {old_sl} → {new_sl}")

    async def _on_price_updated(self, position: MonitoredPosition) -> None:
        """Callback bei Preis-Update."""
        # Kann für UI-Updates verwendet werden
        pass

    # === Price Updates ===

    async def on_price_update(self, price: Decimal) -> None:
        """
        Wird von außen aufgerufen bei Preis-Updates (Streaming).

        Args:
            price: Aktueller Marktpreis
        """
        if self._state == BotState.IN_POSITION:
            await self.position_monitor.on_price_update(price)

    # === Helper ===

    async def _fetch_market_data(self) -> pd.DataFrame | None:
        """
        Holt Marktdaten mit Indikatoren.

        Priorisierung:
        1. Chart-Daten (falls verfügbar und Symbol passt) - kein API-Call!
        2. Fallback: API via HistoryManager/Adapter
        """
        try:
            # === OPTION 1: Chart-Daten verwenden (bevorzugt) ===
            if self.has_chart_data:
                chart_symbol = (self._chart_symbol or "").upper()
                config_symbol = self.config.symbol.upper()

                if chart_symbol == config_symbol:
                    self._log(
                        f"Verwende Chart-Daten: {chart_symbol} "
                        f"({len(self._chart_data)} Bars)"
                    )
                    df = self._chart_data.copy()

                    # Indikatoren berechnen falls nicht vorhanden
                    if "ema_20" not in df.columns:
                        df = self._calculate_indicators(df)

                    return df
                else:
                    logger.debug(
                        f"Chart-Symbol ({chart_symbol}) != Config ({config_symbol}), "
                        "verwende API-Fallback"
                    )

            # === OPTION 2: API-Fallback via Adapter/HistoryManager ===
            bars = await self.adapter.get_historical_bars(
                symbol=self.config.symbol,
                timeframe="5m",
                limit=200,
            )

            if not bars:
                return None

            df = pd.DataFrame(bars)

            # Indikatoren berechnen
            df = self._calculate_indicators(df)

            return df

        except Exception as e:
            logger.error(f"Failed to fetch market data: {e}")
            return None

    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """Berechnet technische Indikatoren."""
        try:
            import talib

            close = df["close"].values
            high = df["high"].values
            low = df["low"].values

            # EMAs
            df["ema_20"] = talib.EMA(close, timeperiod=20)
            df["ema_50"] = talib.EMA(close, timeperiod=50)
            df["ema_200"] = talib.EMA(close, timeperiod=200)

            # RSI
            df["rsi_14"] = talib.RSI(close, timeperiod=14)

            # MACD
            macd, macd_signal, macd_hist = talib.MACD(close)
            df["macd"] = macd
            df["macd_signal"] = macd_signal
            df["macd_hist"] = macd_hist

            # Bollinger Bands
            upper, middle, lower = talib.BBANDS(close, timeperiod=20)
            df["bb_upper"] = upper
            df["bb_middle"] = middle
            df["bb_lower"] = lower

            # ATR
            df["atr_14"] = talib.ATR(high, low, close, timeperiod=14)

            # ADX
            df["adx_14"] = talib.ADX(high, low, close, timeperiod=14)

        except ImportError:
            # Fallback ohne TA-Lib
            logger.warning("TA-Lib not available, using pandas calculations")
            df["ema_20"] = df["close"].ewm(span=20).mean()
            df["ema_50"] = df["close"].ewm(span=50).mean()

        return df

    def _detect_regime(self, df: pd.DataFrame) -> str:
        """Erkennt Market Regime."""
        if df.empty:
            return "NEUTRAL"

        current = df.iloc[-1]

        ema20 = current.get("ema_20")
        ema50 = current.get("ema_50")
        adx = current.get("adx_14")

        if not all([ema20, ema50]):
            return "NEUTRAL"

        # Einfache Regime-Erkennung
        if ema20 > ema50:
            if adx and adx > 30:
                return "STRONG_TREND_BULL"
            return "WEAK_TREND_BULL"
        elif ema20 < ema50:
            if adx and adx > 30:
                return "STRONG_TREND_BEAR"
            return "WEAK_TREND_BEAR"
        else:
            return "CHOP_RANGE"

    def _extract_market_context(
        self, df: pd.DataFrame, regime: str
    ) -> MarketContext:
        """Extrahiert Marktkontext."""
        return MarketContext(
            regime=regime,
            trend_5m=self._get_trend_from_ema(df),
        )

    def _get_trend_from_ema(self, df: pd.DataFrame) -> str:
        """Bestimmt Trend aus EMAs."""
        if df.empty:
            return "NEUTRAL"

        current = df.iloc[-1]
        ema20 = current.get("ema_20")
        ema50 = current.get("ema_50")

        if ema20 and ema50:
            if ema20 > ema50:
                return "BULLISH"
            elif ema20 < ema50:
                return "BEARISH"

        return "NEUTRAL"

    async def _get_balance(self) -> Decimal:
        """Holt aktuellen Kontostand."""
        try:
            balance = await self.adapter.get_balance()
            return Decimal(str(balance.cash)) if balance else Decimal("0")
        except Exception as e:
            logger.error(f"Failed to get balance: {e}")
            return Decimal("0")

    def _check_daily_reset(self) -> None:
        """Prüft ob neuer Tag und setzt Stats zurück."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if self._stats.date != today:
            self._stats = BotStatistics(date=today)

    def _update_statistics(self, trade_log: TradeLogEntry) -> None:
        """Aktualisiert Statistiken nach Trade."""
        self._stats.trades_total += 1

        if trade_log.outcome == TradeOutcome.WIN:
            self._stats.trades_won += 1
        elif trade_log.outcome == TradeOutcome.LOSS:
            self._stats.trades_lost += 1
        else:
            self._stats.trades_breakeven += 1

        if trade_log.net_pnl:
            self._stats.total_pnl += trade_log.net_pnl

            # Drawdown tracking
            if self._stats.total_pnl > self._stats.peak_pnl:
                self._stats.peak_pnl = self._stats.total_pnl

            current_drawdown = self._stats.peak_pnl - self._stats.total_pnl
            if current_drawdown > self._stats.max_drawdown:
                self._stats.max_drawdown = current_drawdown

        # Risk Manager informieren
        if trade_log.net_pnl:
            self.risk_manager.record_trade_result(trade_log.net_pnl)

    # === Public Callbacks ===

    def set_state_callback(self, callback: Callable[[BotState], None]) -> None:
        """Setzt Callback für State-Änderungen."""
        self._on_state_changed = callback

    def set_signal_callback(self, callback: Callable[[TradeSignal], None]) -> None:
        """Setzt Callback für neue Signale."""
        self._on_signal_generated = callback

    def set_position_opened_callback(
        self, callback: Callable[[MonitoredPosition], None]
    ) -> None:
        """Setzt Callback für Position-Öffnung."""
        self._on_position_opened = callback

    def set_position_closed_callback(
        self, callback: Callable[[TradeLogEntry], None]
    ) -> None:
        """Setzt Callback für Position-Schließung."""
        self._on_position_closed = callback

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Fehler."""
        self._on_error = callback

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Log-Nachrichten."""
        self._on_log = callback

    def update_config(self, config: BotConfig) -> None:
        """
        Aktualisiert die Bot-Konfiguration.

        Einige Änderungen werden erst nach Neustart wirksam.
        HINWEIS: Provider und Model kommen aus QSettings (File -> Settings -> AI)!
        """
        self.config = config
        # Update Risk Manager mit neuer Config
        self.risk_manager.update_config(config)
        # AI Validator aktualisieren (Provider/Model kommen aus QSettings!)
        self.ai_validator.update_config(
            enabled=config.ai.enabled,
            confidence_threshold=config.ai.confidence_threshold,
        )
        # Trade Logger Verzeichnis aktualisieren
        if config.logging.enabled:
            config.logging.log_directory.mkdir(parents=True, exist_ok=True)
        self._log(f"Config aktualisiert: Risk={config.risk_per_trade_percent}%, SL={config.sl_atr_multiplier}x ATR")
        logger.info("Bot config updated")

    # === Manual Controls ===

    async def manual_close_position(self) -> None:
        """Schließt Position manuell."""
        if not self.has_position:
            self._log("No position to close")
            return

        exit_result = self.position_monitor.trigger_manual_exit("Manual close by user")
        await self._close_position(exit_result)

    def get_current_status(self) -> dict:
        """Gibt aktuellen Bot-Status zurück."""
        return {
            "state": self._state.value,
            "running": self._running,
            "has_position": self.has_position,
            "position": self.position_monitor.get_position_status(),
            "last_signal": {
                "direction": self._last_signal.direction.value,
                "confluence": self._last_signal.confluence_score,
                "strength": self._last_signal.strength.value,
            }
            if self._last_signal
            else None,
            "last_analysis": self._last_analysis_time.isoformat()
            if self._last_analysis_time
            else None,
            "statistics": self._stats.to_dict(),
            "last_error": self._last_error,
        }

    # === Position Persistenz ===

    _POSITION_FILE = Path("config/trading_bot/active_position.json")

    def save_position(self) -> bool:
        """
        Speichert aktive Position in Datei.

        Wird beim Beenden aufgerufen um Position zu erhalten.

        Returns:
            True wenn erfolgreich gespeichert
        """
        import json

        try:
            self._POSITION_FILE.parent.mkdir(parents=True, exist_ok=True)

            if self.position_monitor.has_position:
                position = self.position_monitor.position
                data = {
                    "position": position.to_dict(),
                    "bot_state": self._state.value,
                    "saved_at": datetime.now(timezone.utc).isoformat(),
                }
                self._POSITION_FILE.write_text(json.dumps(data, indent=2))
                logger.info(f"Position saved: {position.symbol} {position.side}")
                self._log(f"💾 Position gespeichert: {position.symbol}")
                return True
            else:
                # Keine Position - Datei löschen falls vorhanden
                if self._POSITION_FILE.exists():
                    self._POSITION_FILE.unlink()
                    logger.debug("No position to save, removed old file")
                return True

        except Exception as e:
            logger.error(f"Failed to save position: {e}")
            return False

    def load_position(self) -> bool:
        """
        Lädt gespeicherte Position aus Datei.

        Wird beim Start aufgerufen um Position wiederherzustellen.

        Returns:
            True wenn Position geladen wurde
        """
        import json

        try:
            if not self._POSITION_FILE.exists():
                logger.debug("No saved position file found")
                return False

            data = json.loads(self._POSITION_FILE.read_text())
            position_data = data.get("position")

            if not position_data:
                logger.debug("Saved position file is empty")
                return False

            # Position wiederherstellen
            position = self.position_monitor.restore_position(position_data)

            if position:
                self._set_state(BotState.IN_POSITION)
                self._log(
                    f"📂 Position wiederhergestellt: {position.symbol} {position.side} "
                    f"@ {position.entry_price}"
                )

                # UI Callback triggern
                if self._on_position_opened:
                    self._on_position_opened(position)

                # Position-Datei nach erfolgreichem Laden löschen
                # (wird beim nächsten Save neu erstellt)
                self._POSITION_FILE.unlink()
                logger.info(
                    f"Position restored from file: {position.symbol} {position.side}, "
                    f"Entry: {position.entry_price}, SL: {position.stop_loss}, TP: {position.take_profit}"
                )
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to load position: {e}")
            return False
