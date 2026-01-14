"""Trade Simulator for Entry Optimization.

Provides deterministic trade simulation over a candle slice
for evaluating entry signal quality.

Phase 2.4: Deterministische Trade-Simulation im sichtbaren Slice
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from .types import EntrySide, EntryEvent

logger = logging.getLogger(__name__)


@dataclass
class TradeResult:
    """Result of a single simulated trade.

    Attributes:
        entry_event: The entry signal that triggered this trade.
        entry_price: Actual entry price.
        exit_price: Price at exit.
        exit_reason: Why the trade exited.
        pnl_pct: Profit/loss as percentage.
        r_multiple: PnL in terms of risk units (R).
        is_winner: Whether trade was profitable.
        bars_held: Number of bars the trade was held.
    """

    entry_event: EntryEvent
    entry_price: float
    exit_price: float
    exit_reason: str  # "stop", "target", "trailing", "time", "end_of_data"
    pnl_pct: float
    r_multiple: float
    is_winner: bool
    bars_held: int

    @property
    def side(self) -> EntrySide:
        """Trade side."""
        return self.entry_event.side


@dataclass
class SimulationConfig:
    """Configuration for trade simulation.

    Attributes:
        entry_mode: "close" (entry at signal candle close) or "next_open".
        stop_mode: "atr" or "fixed_pct".
        atr_multiplier: ATR multiplier for stop calculation.
        fixed_stop_pct: Fixed stop as percentage of entry price.
        target_r: Take profit in R multiples (0 = no target).
        trailing_enabled: Whether to use trailing stop.
        trailing_activation_r: R multiple to activate trailing.
        trailing_step_pct: Trailing step percentage.
        max_bars: Maximum bars to hold trade.
        fee_pct: Trading fee as percentage (one-way).
        slippage_pct: Slippage as percentage.
    """

    entry_mode: str = "close"
    stop_mode: str = "atr"
    atr_multiplier: float = 2.0
    fixed_stop_pct: float = 1.0
    target_r: float = 0.0  # 0 = no target
    trailing_enabled: bool = True
    trailing_activation_r: float = 1.0
    trailing_step_pct: float = 0.5
    max_bars: int = 100
    fee_pct: float = 0.1
    slippage_pct: float = 0.05


@dataclass
class SimulationResult:
    """Aggregated results of trade simulation.

    Attributes:
        trades: List of individual trade results.
        total_trades: Number of trades simulated.
        winners: Number of winning trades.
        losers: Number of losing trades.
        win_rate: Percentage of winners.
        avg_r: Average R-multiple.
        profit_factor: Gross profit / gross loss.
        max_drawdown_pct: Maximum drawdown percentage.
        expectancy: Expected R per trade.
    """

    trades: list[TradeResult] = field(default_factory=list)
    total_trades: int = 0
    winners: int = 0
    losers: int = 0
    win_rate: float = 0.0
    avg_r: float = 0.0
    profit_factor: float = 0.0
    max_drawdown_pct: float = 0.0
    expectancy: float = 0.0

    @classmethod
    def from_trades(cls, trades: list[TradeResult]) -> SimulationResult:
        """Calculate statistics from trade list."""
        if not trades:
            return cls()

        winners = [t for t in trades if t.is_winner]
        losers = [t for t in trades if not t.is_winner]

        total = len(trades)
        win_count = len(winners)
        loss_count = len(losers)
        win_rate = win_count / total if total > 0 else 0.0

        # R-multiples
        r_values = [t.r_multiple for t in trades]
        avg_r = sum(r_values) / len(r_values) if r_values else 0.0

        # Profit factor
        gross_profit = sum(t.r_multiple for t in winners) if winners else 0.0
        gross_loss = abs(sum(t.r_multiple for t in losers)) if losers else 0.001
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0.0

        # Drawdown (simplified: cumulative R)
        cumulative = 0.0
        peak = 0.0
        max_dd = 0.0
        for t in trades:
            cumulative += t.r_multiple
            peak = max(peak, cumulative)
            dd = peak - cumulative
            max_dd = max(max_dd, dd)

        # Expectancy
        avg_win = (sum(t.r_multiple for t in winners) / win_count) if winners else 0.0
        avg_loss = (abs(sum(t.r_multiple for t in losers)) / loss_count) if losers else 0.0
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)

        return cls(
            trades=trades,
            total_trades=total,
            winners=win_count,
            losers=loss_count,
            win_rate=win_rate,
            avg_r=avg_r,
            profit_factor=profit_factor,
            max_drawdown_pct=max_dd,
            expectancy=expectancy,
        )


class TradeSimulator:
    """Simulates trades based on entry signals over candle data.

    Provides deterministic simulation for optimizer scoring.
    """

    def __init__(self, config: SimulationConfig | None = None) -> None:
        """Initialize the simulator.

        Args:
            config: Simulation configuration.
        """
        self.config = config or SimulationConfig()

    def simulate(
        self,
        entries: list[EntryEvent],
        candles: list[dict],
        features: dict[str, list[float]] | None = None,
    ) -> SimulationResult:
        """Simulate trades for given entries.

        Args:
            entries: Entry signals to simulate.
            candles: OHLCV candle data.
            features: Pre-calculated features (for ATR, etc.).

        Returns:
            SimulationResult with all trade statistics.
        """
        if not entries or not candles:
            return SimulationResult()

        # Build timestamp -> index mapping
        ts_to_idx = {c["timestamp"]: i for i, c in enumerate(candles)}

        # Calculate ATR if needed
        atr_values = self._calculate_atr(candles) if self.config.stop_mode == "atr" else []

        trades: list[TradeResult] = []

        for entry in entries:
            # Find candle index for entry
            entry_idx = ts_to_idx.get(entry.timestamp)
            if entry_idx is None:
                continue

            # Skip if not enough data after entry
            if entry_idx >= len(candles) - 1:
                continue

            trade = self._simulate_single_trade(
                entry=entry,
                entry_idx=entry_idx,
                candles=candles,
                atr_values=atr_values,
            )
            if trade:
                trades.append(trade)

        return SimulationResult.from_trades(trades)

    def _simulate_single_trade(
        self,
        entry: EntryEvent,
        entry_idx: int,
        candles: list[dict],
        atr_values: list[float],
    ) -> TradeResult | None:
        """Simulate a single trade.

        Args:
            entry: Entry signal.
            entry_idx: Index of entry candle.
            candles: All candles.
            atr_values: Pre-calculated ATR values.

        Returns:
            TradeResult or None if simulation failed.
        """
        # Calculate entry price with slippage
        entry_price, start_idx = self._calculate_entry_price(
            entry, entry_idx, candles
        )

        # Calculate stop loss and distance
        stop_price, stop_distance = self._calculate_stop_loss(
            entry, entry_price, entry_idx, atr_values
        )

        # Calculate target price if enabled
        target_price = self._calculate_target_price(
            entry, entry_price, stop_distance
        )

        # Simulate trade bar by bar
        exit_result = self._simulate_trade_bars(
            entry, entry_price, stop_price, target_price,
            stop_distance, start_idx, candles
        )

        # Calculate final P&L and R-multiple
        pnl_pct, r_multiple = self._calculate_trade_pnl(
            entry, entry_price, exit_result["exit_price"],
            stop_distance
        )

        return TradeResult(
            entry_event=entry,
            entry_price=entry_price,
            exit_price=exit_result["exit_price"],
            exit_reason=exit_result["exit_reason"],
            pnl_pct=pnl_pct,
            r_multiple=r_multiple,
            is_winner=pnl_pct > 0,
            bars_held=exit_result["bars_held"],
        )

    def _calculate_entry_price(
        self, entry: EntryEvent, entry_idx: int, candles: list[dict]
    ) -> tuple[float, int]:
        """Calculate entry price with slippage.

        Args:
            entry: Entry event.
            entry_idx: Entry candle index.
            candles: All candles.

        Returns:
            Tuple of (entry_price, start_idx).
        """
        # Determine base entry price
        if self.config.entry_mode == "next_open" and entry_idx + 1 < len(candles):
            entry_price = candles[entry_idx + 1]["open"]
            start_idx = entry_idx + 1
        else:
            entry_price = candles[entry_idx]["close"]
            start_idx = entry_idx

        # Apply slippage
        slippage = entry_price * self.config.slippage_pct / 100
        if entry.side == EntrySide.LONG:
            entry_price += slippage
        else:
            entry_price -= slippage

        return entry_price, start_idx

    def _calculate_stop_loss(
        self, entry: EntryEvent, entry_price: float,
        entry_idx: int, atr_values: list[float]
    ) -> tuple[float, float]:
        """Calculate stop loss price and distance.

        Args:
            entry: Entry event.
            entry_price: Entry price.
            entry_idx: Entry candle index.
            atr_values: ATR values.

        Returns:
            Tuple of (stop_price, stop_distance).
        """
        # Calculate stop distance
        if self.config.stop_mode == "atr" and entry_idx < len(atr_values):
            atr = atr_values[entry_idx]
            stop_distance = atr * self.config.atr_multiplier
        else:
            stop_distance = entry_price * self.config.fixed_stop_pct / 100

        # Calculate stop price based on side
        if entry.side == EntrySide.LONG:
            stop_price = entry_price - stop_distance
        else:
            stop_price = entry_price + stop_distance

        return stop_price, stop_distance

    def _calculate_target_price(
        self, entry: EntryEvent, entry_price: float, stop_distance: float
    ) -> float | None:
        """Calculate target price if enabled.

        Args:
            entry: Entry event.
            entry_price: Entry price.
            stop_distance: Stop loss distance.

        Returns:
            Target price or None if not enabled.
        """
        if self.config.target_r <= 0:
            return None

        if entry.side == EntrySide.LONG:
            return entry_price + stop_distance * self.config.target_r
        else:
            return entry_price - stop_distance * self.config.target_r

    def _simulate_trade_bars(
        self, entry: EntryEvent, entry_price: float, stop_price: float,
        target_price: float | None, stop_distance: float,
        start_idx: int, candles: list[dict]
    ) -> dict:
        """Simulate trade bar by bar until exit.

        Args:
            entry: Entry event.
            entry_price: Entry price.
            stop_price: Initial stop price.
            target_price: Target price (or None).
            stop_distance: Stop distance for trailing calculation.
            start_idx: Starting candle index.
            candles: All candles.

        Returns:
            Dictionary with exit_price, exit_reason, bars_held.
        """
        trailing_stop = stop_price
        trailing_active = False
        exit_price = entry_price
        exit_reason = "end_of_data"
        bars_held = 0

        for i in range(start_idx + 1, min(len(candles), start_idx + self.config.max_bars + 1)):
            bar = candles[i]
            bars_held += 1

            # Check stop and target based on side
            if entry.side == EntrySide.LONG:
                result = self._check_stop_target_long(
                    bar, trailing_stop, target_price
                )
            else:
                result = self._check_stop_target_short(
                    bar, trailing_stop, target_price
                )

            if result:
                exit_price = result["price"]
                exit_reason = result["reason"]
                break

            # Update trailing stop if enabled
            if self.config.trailing_enabled:
                trailing_stop, trailing_active = self._update_trailing_stop(
                    entry, bar, entry_price, stop_distance,
                    trailing_stop, trailing_active
                )

            # Check max bars
            if bars_held >= self.config.max_bars:
                exit_price = bar["close"]
                exit_reason = "time"
                break

        return {
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "bars_held": bars_held,
        }

    def _check_stop_target_long(
        self, bar: dict, trailing_stop: float, target_price: float | None
    ) -> dict | None:
        """Check if stop or target was hit for long position.

        Args:
            bar: Current candle.
            trailing_stop: Current trailing stop.
            target_price: Target price (or None).

        Returns:
            Dictionary with price and reason if hit, None otherwise.
        """
        if bar["low"] <= trailing_stop:
            return {"price": trailing_stop, "reason": "stop"}
        if target_price and bar["high"] >= target_price:
            return {"price": target_price, "reason": "target"}
        return None

    def _check_stop_target_short(
        self, bar: dict, trailing_stop: float, target_price: float | None
    ) -> dict | None:
        """Check if stop or target was hit for short position.

        Args:
            bar: Current candle.
            trailing_stop: Current trailing stop.
            target_price: Target price (or None).

        Returns:
            Dictionary with price and reason if hit, None otherwise.
        """
        if bar["high"] >= trailing_stop:
            return {"price": trailing_stop, "reason": "stop"}
        if target_price and bar["low"] <= target_price:
            return {"price": target_price, "reason": "target"}
        return None

    def _update_trailing_stop(
        self, entry: EntryEvent, bar: dict, entry_price: float,
        stop_distance: float, trailing_stop: float, trailing_active: bool
    ) -> tuple[float, bool]:
        """Update trailing stop based on current price movement.

        Args:
            entry: Entry event.
            bar: Current candle.
            entry_price: Entry price.
            stop_distance: Stop distance.
            trailing_stop: Current trailing stop.
            trailing_active: Whether trailing is active.

        Returns:
            Tuple of (new_trailing_stop, new_trailing_active).
        """
        if entry.side == EntrySide.LONG:
            current_r = (bar["high"] - entry_price) / stop_distance
            if current_r >= self.config.trailing_activation_r:
                trailing_active = True
            if trailing_active:
                new_stop = bar["high"] - stop_distance * self.config.trailing_step_pct
                trailing_stop = max(trailing_stop, new_stop)
        else:
            current_r = (entry_price - bar["low"]) / stop_distance
            if current_r >= self.config.trailing_activation_r:
                trailing_active = True
            if trailing_active:
                new_stop = bar["low"] + stop_distance * self.config.trailing_step_pct
                trailing_stop = min(trailing_stop, new_stop)

        return trailing_stop, trailing_active

    def _calculate_trade_pnl(
        self, entry: EntryEvent, entry_price: float,
        exit_price: float, stop_distance: float
    ) -> tuple[float, float]:
        """Calculate P&L percentage and R-multiple.

        Args:
            entry: Entry event.
            entry_price: Entry price.
            exit_price: Exit price.
            stop_distance: Stop distance.

        Returns:
            Tuple of (pnl_pct, r_multiple).
        """
        # Calculate raw P&L
        if entry.side == EntrySide.LONG:
            pnl_raw = (exit_price - entry_price) / entry_price
        else:
            pnl_raw = (entry_price - exit_price) / entry_price

        # Apply fees
        total_fees = 2 * self.config.fee_pct / 100  # Entry + exit
        pnl_pct = (pnl_raw - total_fees) * 100

        # Calculate R-multiple
        r_multiple = pnl_raw / (stop_distance / entry_price) if stop_distance > 0 else 0

        return pnl_pct, r_multiple

    def _calculate_atr(self, candles: list[dict], period: int = 14) -> list[float]:
        """Calculate Average True Range.

        Args:
            candles: OHLCV data.
            period: ATR period.

        Returns:
            List of ATR values.
        """
        if len(candles) < period:
            return [0.0] * len(candles)

        tr_values = []
        for i, c in enumerate(candles):
            high = c["high"]
            low = c["low"]
            prev_close = candles[i - 1]["close"] if i > 0 else c["close"]

            tr = max(
                high - low,
                abs(high - prev_close),
                abs(low - prev_close),
            )
            tr_values.append(tr)

        # Simple moving average for ATR
        atr = []
        for i in range(len(candles)):
            if i < period - 1:
                atr.append(tr_values[i])
            else:
                atr.append(sum(tr_values[i - period + 1 : i + 1]) / period)

        return atr
