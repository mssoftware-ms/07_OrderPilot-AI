"""
BacktestRunner - Core Engine für Single-Run Backtesting

Führt einen vollständigen Backtest durch:
- Lädt 1m Daten via ReplayMarketDataProvider
- Resampled zu MTF via MTFResampler
- Generiert Signale via Strategy/SignalGenerator
- Führt Trades aus via ExecutionSimulator
- Berechnet Metriken

Features:
- Deterministisch und reproduzierbar
- No-Leak Garantie (strikt candle-by-candle)
- Realistische Execution (Fees, Slippage, Leverage)
- Vollständiges Trade Lifecycle (Entry → Manage → Exit)
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, Callable, Any
from enum import Enum

import pandas as pd
import numpy as np

from .config import BacktestConfig, ExecutionConfig
from .replay_provider import ReplayMarketDataProvider, CandleSnapshot
from .mtf_resampler import MTFResampler
from .execution_simulator import (
    ExecutionSimulator,
    SimulatedOrder,
    SimulatedFill,
    OrderSide,
    OrderType,
    FillStatus,
)
from src.core.models.backtest_models import (
    BacktestResult,
    BacktestMetrics,
    Trade,
    TradeSide,
    EquityPoint,
    Bar,
)

if TYPE_CHECKING:
    from src.core.trading_bot.signal_generator import SignalGenerator

logger = logging.getLogger(__name__)


class TradeStatus(Enum):
    """Status eines Trades im Backtest."""
    PENDING = "pending"
    OPEN = "open"
    CLOSED = "closed"


@dataclass
class OpenPosition:
    """Eine offene Position während des Backtests.

    Attributes:
        id: Eindeutige Position-ID
        symbol: Trading-Symbol
        side: Long oder Short
        entry_price: Entry-Preis
        entry_time: Entry-Zeitpunkt
        size: Position-Größe
        stop_loss: Stop-Loss Preis
        take_profit: Take-Profit Preis
        leverage: Verwendeter Hebel
        margin_used: Gebundene Margin
        entry_fill: Original Entry Fill
        entry_reason: Begründung für Entry
    """
    id: str
    symbol: str
    side: OrderSide
    entry_price: float
    entry_time: datetime
    size: float
    stop_loss: float | None = None
    take_profit: float | None = None
    leverage: int = 1
    margin_used: float = 0.0
    entry_fill: SimulatedFill | None = None
    entry_reason: str = ""
    entry_fee: float = 0.0

    @property
    def trade_side(self) -> TradeSide:
        """Konvertiert OrderSide zu TradeSide."""
        return TradeSide.LONG if self.side == OrderSide.BUY else TradeSide.SHORT


@dataclass
class BacktestState:
    """Zustand während des Backtests.

    Attributes:
        equity: Aktuelles Eigenkapital
        cash: Verfügbares Cash
        open_positions: Offene Positionen
        closed_trades: Geschlossene Trades
        equity_curve: Equity über Zeit
        daily_pnl: Täglicher P&L
        trade_count_today: Trades heute
        loss_streak: Aktuelle Verlust-Serie
        current_date: Aktuelles Datum
    """
    equity: float
    cash: float
    open_positions: list[OpenPosition] = field(default_factory=list)
    closed_trades: list[Trade] = field(default_factory=list)
    equity_curve: list[EquityPoint] = field(default_factory=list)
    daily_pnl: float = 0.0
    trade_count_today: int = 0
    loss_streak: int = 0
    current_date: datetime | None = None
    last_trade_time: datetime | None = None
    cooldown_until: datetime | None = None


class BacktestRunner:
    """Core Engine für Backtesting.

    Führt einen vollständigen Backtest durch mit:
    - Candle-by-Candle Replay
    - Multi-Timeframe Resampling (No-Leak)
    - Signal-Generierung
    - Trade Execution mit Fees/Slippage
    - Risk Management (Daily Loss, Max Trades, Streak Cooldown)

    Usage:
        runner = BacktestRunner(config)
        result = await runner.run()

        # Oder mit Custom Signal Generator:
        result = await runner.run(signal_generator=my_generator)
    """

    def __init__(
        self,
        config: BacktestConfig,
        signal_callback: Callable[[CandleSnapshot, pd.DataFrame, dict[str, pd.DataFrame]], dict | None] | None = None,
    ):
        """Initialisiert den Runner.

        Args:
            config: Backtest-Konfiguration
            signal_callback: Optional: Callback für Signal-Generierung
                             Erhält (candle, history_1m, mtf_data) und gibt Signal-Dict zurück
        """
        self.config = config
        self.signal_callback = signal_callback

        # Komponenten
        self.replay_provider = ReplayMarketDataProvider(history_window=200)
        self.mtf_resampler = MTFResampler(
            timeframes=config.mtf_timeframes,
            history_bars_per_tf=100,
        )
        self.execution_sim = ExecutionSimulator(config.execution)

        # State
        self.state: BacktestState | None = None
        self._is_running = False
        self._should_stop = False

        # Progress Callback
        self._progress_callback: Callable[[int, str], None] | None = None

        logger.info(f"BacktestRunner initialized: {config.symbol} from {config.start_date} to {config.end_date}")

    def set_progress_callback(self, callback: Callable[[int, str], None]) -> None:
        """Setzt Callback für Progress-Updates."""
        self._progress_callback = callback

    def _emit_progress(self, progress: int, message: str) -> None:
        """Emittiert Progress-Update."""
        if self._progress_callback:
            self._progress_callback(progress, message)

    async def run(self) -> BacktestResult:
        """Führt den Backtest durch.

        Returns:
            BacktestResult mit allen Trades, Metriken, Equity Curve
        """
        if self._is_running:
            raise RuntimeError("Backtest already running")

        self._is_running = True
        self._should_stop = False

        try:
            # 1. Initialisierung
            self._emit_progress(0, "Initialisiere...")
            self._init_state()

            # 2. Daten laden
            self._emit_progress(5, "Lade historische Daten...")
            bar_count = await self.replay_provider.load_data(
                symbol=self.config.symbol,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
            )
            logger.info(f"Loaded {bar_count} bars")

            if bar_count < 200:
                raise ValueError(f"Nicht genug Daten: {bar_count} bars (min. 200 benötigt)")

            # 3. Haupt-Loop
            self._emit_progress(10, "Starte Backtest...")
            iterator = self.replay_provider.iterate()
            processed = 0
            total_to_process = len(iterator)

            for candle, history in iterator:
                if self._should_stop:
                    logger.info("Backtest stopped by user")
                    break

                # Process candle
                await self._process_candle(candle, history)

                # Progress update (alle 100 Candles)
                processed += 1
                if processed % 100 == 0:
                    progress = 10 + int((processed / total_to_process) * 80)
                    self._emit_progress(progress, f"Verarbeite Candle {processed}/{total_to_process}")

            # 4. Offene Positionen schließen (EOD)
            self._emit_progress(90, "Schließe offene Positionen...")
            await self._close_all_positions("End of backtest")

            # 5. Metriken berechnen
            self._emit_progress(95, "Berechne Metriken...")
            result = self._calculate_result()

            self._emit_progress(100, "Fertig!")
            logger.info(f"Backtest completed: {len(self.state.closed_trades)} trades")

            return result

        finally:
            self._is_running = False

    def stop(self) -> None:
        """Stoppt den laufenden Backtest."""
        self._should_stop = True

    def _init_state(self) -> None:
        """Initialisiert den Backtest-State."""
        self.state = BacktestState(
            equity=self.config.initial_capital,
            cash=self.config.initial_capital,
        )

        # Initial Equity Point
        self.state.equity_curve.append(EquityPoint(
            time=self.config.start_date,
            equity=self.config.initial_capital,
        ))

    async def _process_candle(self, candle: CandleSnapshot, history_1m: pd.DataFrame) -> None:
        """Verarbeitet eine einzelne Candle.

        Args:
            candle: Aktuelle Candle
            history_1m: History (ohne aktuelle Candle)
        """
        current_time = candle.datetime

        # 1. Tages-Reset prüfen
        self._check_daily_reset(current_time)

        # 2. MTF Update
        mtf_data = self.mtf_resampler.update(candle.timestamp, history_1m)

        # 3. Risk Management Check (Daily Loss, Cooldown)
        if not self._risk_check_passed(current_time):
            return

        # 4. Offene Positionen managen (SL/TP)
        await self._manage_positions(candle)

        # 5. Neue Signale generieren
        signal = self._generate_signal(candle, history_1m, mtf_data)

        # 6. Signal ausführen
        if signal and signal.get("action") in ["buy", "sell"]:
            await self._execute_signal(signal, candle)

        # 7. Equity Curve updaten (alle 15 Minuten)
        if candle.bar_index % 15 == 0:
            self._update_equity_curve(current_time, candle.close)

    def _check_daily_reset(self, current_time: datetime) -> None:
        """Prüft auf Tages-Wechsel und resettet Daily-Counter."""
        if self.state.current_date is None:
            self.state.current_date = current_time.date()
            return

        if current_time.date() != self.state.current_date:
            # Neuer Tag
            logger.debug(f"New day: {current_time.date()}")
            self.state.current_date = current_time.date()
            self.state.daily_pnl = 0.0
            self.state.trade_count_today = 0

    def _risk_check_passed(self, current_time: datetime) -> bool:
        """Prüft Risk Management Regeln."""
        # 1. Daily Loss Check
        max_daily_loss = self.config.initial_capital * (self.config.max_daily_loss_pct / 100)
        if self.state.daily_pnl < -max_daily_loss:
            logger.debug("Daily loss limit reached")
            return False

        # 2. Max Trades Check
        if self.state.trade_count_today >= self.config.max_trades_per_day:
            logger.debug("Max daily trades reached")
            return False

        # 3. Cooldown Check
        if self.state.cooldown_until and current_time < self.state.cooldown_until:
            return False

        # 4. Loss Streak Check
        if self.state.loss_streak >= self.config.max_loss_streak:
            if self.state.cooldown_until is None:
                from datetime import timedelta
                self.state.cooldown_until = current_time + timedelta(minutes=self.config.cooldown_after_streak_min)
                logger.debug(f"Loss streak cooldown until {self.state.cooldown_until}")
            return False

        return True

    async def _manage_positions(self, candle: CandleSnapshot) -> None:
        """Managed offene Positionen (SL/TP Check)."""
        positions_to_close = []

        for position in self.state.open_positions:
            close_reason = None
            close_price = None

            # SL Check
            if position.stop_loss:
                if position.side == OrderSide.BUY and candle.low <= position.stop_loss:
                    close_reason = "Stop Loss"
                    close_price = position.stop_loss
                elif position.side == OrderSide.SELL and candle.high >= position.stop_loss:
                    close_reason = "Stop Loss"
                    close_price = position.stop_loss

            # TP Check
            if not close_reason and position.take_profit:
                if position.side == OrderSide.BUY and candle.high >= position.take_profit:
                    close_reason = "Take Profit"
                    close_price = position.take_profit
                elif position.side == OrderSide.SELL and candle.low <= position.take_profit:
                    close_reason = "Take Profit"
                    close_price = position.take_profit

            # Liquidation Check
            if not close_reason and position.leverage > 1:
                is_liquidated, _ = self.execution_sim.check_liquidation(
                    position_side=position.side,
                    entry_price=position.entry_price,
                    current_price=candle.close,
                    leverage=position.leverage,
                )
                if is_liquidated:
                    close_reason = "Liquidation"
                    close_price = candle.close  # Vereinfacht

            if close_reason:
                positions_to_close.append((position, close_reason, close_price, candle))

        # Positionen schließen
        for position, reason, price, candle in positions_to_close:
            await self._close_position(position, price, candle.datetime, reason)

    def _generate_signal(
        self,
        candle: CandleSnapshot,
        history_1m: pd.DataFrame,
        mtf_data: dict[str, pd.DataFrame],
    ) -> dict | None:
        """Generiert Trading-Signal.

        Returns:
            Signal-Dict mit: action, side, sl, tp, leverage, reason
            oder None
        """
        if self.signal_callback:
            return self.signal_callback(candle, history_1m, mtf_data)

        # Default: Keine Signale (muss via Callback oder Strategy bereitgestellt werden)
        return None

    async def _execute_signal(self, signal: dict, candle: CandleSnapshot) -> None:
        """Führt ein Signal aus."""
        if not signal:
            return

        action = signal.get("action")
        if action not in ["buy", "sell"]:
            return

        # Keine neuen Trades wenn bereits Position offen
        if self.state.open_positions:
            return

        # Position Size berechnen
        risk_amount = self.state.equity * (self.config.risk_per_trade_pct / 100)

        sl_distance = signal.get("sl_distance", candle.close * 0.01)  # Default 1%
        if sl_distance <= 0:
            sl_distance = candle.close * 0.01

        leverage = min(signal.get("leverage", 1), self.config.execution.max_leverage)
        position_size = (risk_amount * leverage) / sl_distance

        # Order erstellen
        side = OrderSide.BUY if action == "buy" else OrderSide.SELL

        order = SimulatedOrder(
            order_id=f"order_{uuid.uuid4().hex[:8]}",
            symbol=self.config.symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=position_size,
            leverage=leverage,
            timestamp=candle.timestamp,
        )

        # ATR für Slippage (aus History)
        atr = self._calculate_atr(candle, 14)

        # Order ausführen
        fill = self.execution_sim.execute_order(
            order=order,
            market_price=candle.close,
            atr=atr,
            available_margin=self.state.cash,
        )

        if fill.status != FillStatus.FILLED:
            logger.warning(f"Order rejected: {fill.reason}")
            return

        # SL/TP berechnen
        sl_price = signal.get("stop_loss")
        if sl_price is None:
            if side == OrderSide.BUY:
                sl_price = fill.fill_price - sl_distance
            else:
                sl_price = fill.fill_price + sl_distance

        tp_price = signal.get("take_profit")

        # Position erstellen
        position = OpenPosition(
            id=fill.order_id,
            symbol=self.config.symbol,
            side=side,
            entry_price=fill.fill_price,
            entry_time=candle.datetime,
            size=fill.fill_quantity,
            stop_loss=sl_price,
            take_profit=tp_price,
            leverage=leverage,
            margin_used=fill.margin_used,
            entry_fill=fill,
            entry_reason=signal.get("reason", ""),
            entry_fee=fill.fee,
        )

        self.state.open_positions.append(position)
        self.state.cash -= fill.margin_used
        self.state.trade_count_today += 1

        logger.debug(
            f"Position opened: {side.value} {position.size:.4f} @ {fill.fill_price:.2f} "
            f"(SL: {sl_price:.2f}, TP: {tp_price})"
        )

    async def _close_position(
        self,
        position: OpenPosition,
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
    ) -> None:
        """Schließt eine Position und erstellt Trade-Record."""
        # Exit Order
        exit_side = OrderSide.SELL if position.side == OrderSide.BUY else OrderSide.BUY

        order = SimulatedOrder(
            order_id=f"exit_{uuid.uuid4().hex[:8]}",
            symbol=position.symbol,
            side=exit_side,
            order_type=OrderType.MARKET,
            quantity=position.size,
            leverage=position.leverage,
            timestamp=int(exit_time.timestamp() * 1000),
        )

        fill = self.execution_sim.execute_order(
            order=order,
            market_price=exit_price,
            available_margin=None,  # Exit braucht keine Margin
        )

        # PnL berechnen
        pnl_data = self.execution_sim.calculate_pnl(
            entry_price=position.entry_price,
            exit_price=fill.fill_price,
            quantity=position.size,
            side=position.side,
            leverage=position.leverage,
            include_fees=True,
            entry_fee=position.entry_fee,
            exit_fee=fill.fee,
        )

        net_pnl = pnl_data["net_pnl"]

        # Trade erstellen
        trade = Trade(
            id=position.id,
            symbol=position.symbol,
            side=position.trade_side,
            size=position.size,
            entry_time=position.entry_time,
            entry_price=position.entry_price,
            entry_reason=position.entry_reason,
            exit_time=exit_time,
            exit_price=fill.fill_price,
            exit_reason=exit_reason,
            stop_loss=position.stop_loss,
            take_profit=position.take_profit,
            realized_pnl=net_pnl,
            realized_pnl_pct=pnl_data["return_pct"],
            commission=position.entry_fee + fill.fee,
            slippage=fill.slippage,
        )

        # State updaten
        self.state.closed_trades.append(trade)
        self.state.open_positions.remove(position)
        self.state.cash += position.margin_used + net_pnl
        self.state.equity = self.state.cash + self._calculate_unrealized_pnl(exit_price)
        self.state.daily_pnl += net_pnl

        # Loss Streak tracking
        if net_pnl < 0:
            self.state.loss_streak += 1
        else:
            self.state.loss_streak = 0
            self.state.cooldown_until = None

        logger.debug(
            f"Position closed: {trade.side.value} @ {fill.fill_price:.2f} "
            f"| PnL: {net_pnl:+.2f} ({pnl_data['return_pct']:+.1f}%) | Reason: {exit_reason}"
        )

    async def _close_all_positions(self, reason: str) -> None:
        """Schließt alle offenen Positionen."""
        if not self.state or not self.state.open_positions:
            return

        # Letzte Candle für Exit-Preis
        if self.replay_provider.data is not None and not self.replay_provider.data.empty:
            last_row = self.replay_provider.data.iloc[-1]
            exit_price = float(last_row["close"])
            exit_time = datetime.fromtimestamp(last_row["timestamp"] / 1000, tz=timezone.utc)
        else:
            return

        for position in list(self.state.open_positions):
            await self._close_position(position, exit_price, exit_time, reason)

    def _calculate_unrealized_pnl(self, current_price: float) -> float:
        """Berechnet unrealized PnL aller offenen Positionen."""
        total = 0.0
        for position in self.state.open_positions:
            if position.side == OrderSide.BUY:
                pnl = (current_price - position.entry_price) * position.size * position.leverage
            else:
                pnl = (position.entry_price - current_price) * position.size * position.leverage
            total += pnl
        return total

    def _update_equity_curve(self, time: datetime, current_price: float) -> None:
        """Fügt Punkt zur Equity Curve hinzu."""
        unrealized = self._calculate_unrealized_pnl(current_price)
        equity = self.state.cash + unrealized

        # Margin in offenen Positionen hinzurechnen
        for pos in self.state.open_positions:
            equity += pos.margin_used

        self.state.equity = equity
        self.state.equity_curve.append(EquityPoint(time=time, equity=equity))

    def _calculate_atr(self, candle: CandleSnapshot, period: int = 14) -> float | None:
        """Berechnet ATR aus History."""
        if self.replay_provider.data is None:
            return None

        end_idx = candle.bar_index
        start_idx = max(0, end_idx - period)

        if end_idx - start_idx < period:
            return None

        data = self.replay_provider.data.iloc[start_idx:end_idx]

        high = data["high"].values
        low = data["low"].values
        close = data["close"].values

        prev_close = np.roll(close, 1)
        prev_close[0] = close[0]

        tr = np.maximum(
            high - low,
            np.maximum(
                np.abs(high - prev_close),
                np.abs(low - prev_close)
            )
        )

        return float(np.mean(tr[-period:]))

    def _calculate_result(self) -> BacktestResult:
        """Berechnet das finale BacktestResult."""
        trades = self.state.closed_trades
        equity_curve = self.state.equity_curve

        # Metriken berechnen
        metrics = self._calculate_metrics(trades, equity_curve)

        # Bars für Result (vereinfacht - nur Timestamps)
        bars = []
        if self.replay_provider.data is not None:
            for _, row in self.replay_provider.data.iloc[::60].iterrows():  # Jede Stunde
                bars.append(Bar(
                    time=datetime.fromtimestamp(row["timestamp"] / 1000, tz=timezone.utc),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]),
                    symbol=self.config.symbol,
                ))

        return BacktestResult(
            symbol=self.config.symbol,
            timeframe=self.config.base_timeframe,
            mode="backtest",
            start=self.config.start_date,
            end=self.config.end_date,
            initial_capital=self.config.initial_capital,
            final_capital=self.state.equity,
            bars=bars,
            trades=trades,
            equity_curve=equity_curve,
            metrics=metrics,
            strategy_name=self.config.strategy_preset,
            strategy_params=self.config.parameter_overrides,
        )

    def _calculate_metrics(
        self,
        trades: list[Trade],
        equity_curve: list[EquityPoint],
    ) -> BacktestMetrics:
        """Berechnet Performance-Metriken."""
        if not trades:
            return BacktestMetrics()

        # Basis-Statistiken
        total_trades = len(trades)
        winners = [t for t in trades if t.realized_pnl > 0]
        losers = [t for t in trades if t.realized_pnl <= 0]

        winning_trades = len(winners)
        losing_trades = len(losers)

        win_rate = winning_trades / total_trades if total_trades > 0 else 0

        # P&L Statistiken
        gross_profit = sum(t.realized_pnl for t in winners)
        gross_loss = abs(sum(t.realized_pnl for t in losers))

        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf') if gross_profit > 0 else 0

        avg_win = gross_profit / winning_trades if winning_trades > 0 else 0
        avg_loss = -gross_loss / losing_trades if losing_trades > 0 else 0

        # Expectancy = (Win% * AvgWin) - (Loss% * AvgLoss)
        loss_rate = losing_trades / total_trades if total_trades > 0 else 0
        expectancy = (win_rate * avg_win) + (loss_rate * avg_loss)  # avg_loss ist negativ

        # R-Multiples
        r_multiples = [t.r_multiple for t in trades if t.r_multiple is not None]
        avg_r = np.mean(r_multiples) if r_multiples else None
        best_r = max(r_multiples) if r_multiples else None
        worst_r = min(r_multiples) if r_multiples else None

        # Drawdown
        max_dd_pct, max_dd_duration = self._calculate_drawdown(equity_curve)

        # Streaks
        max_wins, max_losses = self._calculate_streaks(trades)

        # Returns
        total_return = ((self.state.equity / self.config.initial_capital) - 1) * 100

        # Sharpe (vereinfacht)
        sharpe = self._calculate_sharpe(equity_curve)

        # Trade Duration
        durations = [t.duration for t in trades if t.duration is not None]
        avg_duration_min = np.mean(durations) / 60 if durations else None

        return BacktestMetrics(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            profit_factor=profit_factor,
            expectancy=expectancy,
            max_drawdown_pct=max_dd_pct,
            max_drawdown_duration_days=max_dd_duration,
            sharpe_ratio=sharpe,
            avg_r_multiple=avg_r,
            best_r_multiple=best_r,
            worst_r_multiple=worst_r,
            avg_win=avg_win,
            avg_loss=avg_loss,
            largest_win=max(t.realized_pnl for t in winners) if winners else 0,
            largest_loss=min(t.realized_pnl for t in losers) if losers else 0,
            total_return_pct=total_return,
            avg_trade_duration_minutes=avg_duration_min,
            max_consecutive_wins=max_wins,
            max_consecutive_losses=max_losses,
        )

    def _calculate_drawdown(self, equity_curve: list[EquityPoint]) -> tuple[float, float | None]:
        """Berechnet Max Drawdown."""
        if len(equity_curve) < 2:
            return 0.0, None

        equities = [e.equity for e in equity_curve]
        times = [e.time for e in equity_curve]

        peak = equities[0]
        max_dd = 0.0
        dd_start = times[0]
        max_dd_duration = 0.0

        for i, eq in enumerate(equities):
            if eq > peak:
                peak = eq
                dd_start = times[i]

            dd = (peak - eq) / peak * 100 if peak > 0 else 0

            if dd > max_dd:
                max_dd = dd
                duration = (times[i] - dd_start).total_seconds() / 86400
                max_dd_duration = max(max_dd_duration, duration)

        return max_dd, max_dd_duration if max_dd_duration > 0 else None

    def _calculate_streaks(self, trades: list[Trade]) -> tuple[int, int]:
        """Berechnet längste Win/Loss Streaks."""
        if not trades:
            return 0, 0

        max_wins = 0
        max_losses = 0
        current_wins = 0
        current_losses = 0

        for trade in trades:
            if trade.realized_pnl > 0:
                current_wins += 1
                current_losses = 0
                max_wins = max(max_wins, current_wins)
            else:
                current_losses += 1
                current_wins = 0
                max_losses = max(max_losses, current_losses)

        return max_wins, max_losses

    def _calculate_sharpe(self, equity_curve: list[EquityPoint], risk_free_rate: float = 0.0) -> float | None:
        """Berechnet Sharpe Ratio (annualisiert)."""
        if len(equity_curve) < 30:
            return None

        equities = [e.equity for e in equity_curve]
        returns = np.diff(equities) / equities[:-1]

        if len(returns) < 2:
            return None

        avg_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return None

        # Annualisieren (angenommen 1440 Punkte pro Tag bei 1m TF, aber wir samplen alle 15min)
        # Vereinfacht: 96 Punkte pro Tag
        annualized_factor = np.sqrt(96 * 365)

        sharpe = ((avg_return - risk_free_rate) / std_return) * annualized_factor

        return float(sharpe)
