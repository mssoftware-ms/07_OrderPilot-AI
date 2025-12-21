"""No-Trade Filter for Tradingbot.

Filters out conditions where trading should be avoided,
such as extreme volatility, news events, or market structure issues.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from enum import Enum

from .config import MarketType
from .models import FeatureVector, RegimeState, VolatilityLevel

logger = logging.getLogger(__name__)


class FilterReason(str, Enum):
    """Reasons for filtering a trade."""
    NONE = "none"
    EXTREME_VOLATILITY = "extreme_volatility"
    LOW_VOLUME = "low_volume"
    SPREAD_TOO_WIDE = "spread_too_wide"
    MARKET_HOURS = "market_hours"
    NEWS_BLACKOUT = "news_blackout"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    MAX_TRADES_REACHED = "max_trades_reached"
    REGIME_TRANSITION = "regime_transition"
    RSI_EXTREME = "rsi_extreme"
    CONSECUTIVE_LOSSES = "consecutive_losses"


@dataclass
class FilterResult:
    """Result of trade filter check."""
    allowed: bool
    reasons: list[FilterReason] = field(default_factory=list)
    details: dict[str, str] = field(default_factory=dict)

    def add_block(self, reason: FilterReason, detail: str = "") -> None:
        """Add a blocking reason."""
        self.allowed = False
        self.reasons.append(reason)
        if detail:
            self.details[reason.value] = detail

    def __bool__(self) -> bool:
        """Returns True if trade is allowed."""
        return self.allowed


@dataclass
class TradingSession:
    """Track daily trading session metrics."""
    date: datetime
    trades_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    consecutive_losses: int = 0
    realized_pnl: float = 0.0

    def record_trade(self, pnl: float) -> None:
        """Record a completed trade."""
        self.trades_count += 1
        self.realized_pnl += pnl

        if pnl > 0:
            self.winning_trades += 1
            self.consecutive_losses = 0
        else:
            self.losing_trades += 1
            self.consecutive_losses += 1


class NoTradeFilter:
    """Filter engine to block trades under unfavorable conditions.

    Implements multiple filter layers:
    1. Volatility filters
    2. Volume/liquidity filters
    3. Time-based filters
    4. Risk management filters
    5. Technical filters
    """

    # Default thresholds
    DEFAULT_CONFIG = {
        # Volatility
        'max_atr_pct': 5.0,  # Max ATR as % of price
        'extreme_vol_blocks': True,

        # Volume
        'min_volume_ratio': 0.3,  # Min volume vs avg

        # Time filters (for stocks)
        'avoid_first_minutes': 5,  # First N minutes after open
        'avoid_last_minutes': 5,   # Last N minutes before close

        # Risk limits
        'max_daily_trades': 10,
        'max_consecutive_losses': 3,
        'daily_loss_limit_pct': 2.0,  # Max daily loss as % of account

        # Technical filters
        'rsi_extreme_high': 85.0,
        'rsi_extreme_low': 15.0,
    }

    # Stock market hours (US Eastern)
    STOCK_MARKET_OPEN = time(9, 30)
    STOCK_MARKET_CLOSE = time(16, 0)

    def __init__(
        self,
        market_type: MarketType,
        account_value: float = 10000.0,
        config: dict | None = None
    ):
        """Initialize no-trade filter.

        Args:
            market_type: Type of market (CRYPTO or NASDAQ)
            account_value: Current account value for risk calculations
            config: Custom configuration overrides
        """
        self.market_type = market_type
        self.account_value = account_value
        self.config = {**self.DEFAULT_CONFIG, **(config or {})}

        # Session tracking
        self._session: TradingSession | None = None
        self._previous_regime: RegimeState | None = None

        # News blackout windows (can be populated from external source)
        self._news_blackouts: list[tuple[datetime, datetime]] = []

        logger.info(
            f"NoTradeFilter initialized for {market_type.value} "
            f"(max_trades={self.config['max_daily_trades']})"
        )

    @property
    def session(self) -> TradingSession:
        """Get current trading session, creating new one if needed."""
        today = datetime.utcnow().date()

        if self._session is None or self._session.date.date() != today:
            self._session = TradingSession(date=datetime.utcnow())
            logger.info(f"New trading session started: {today}")

        return self._session

    def check(
        self,
        features: FeatureVector,
        regime: RegimeState,
        timestamp: datetime | None = None
    ) -> FilterResult:
        """Check all filters for current market conditions.

        Args:
            features: Current feature vector
            regime: Current regime state
            timestamp: Override timestamp for testing

        Returns:
            FilterResult indicating if trade is allowed
        """
        result = FilterResult(allowed=True)
        ts = timestamp or datetime.utcnow()

        # 1. Volatility filters
        self._check_volatility(result, features, regime)

        # 2. Volume filters
        self._check_volume(result, features)

        # 3. Time-based filters
        self._check_time(result, ts)

        # 4. Risk management filters
        self._check_risk_limits(result)

        # 5. Technical filters
        self._check_technical(result, features)

        # 6. Regime transition filter
        self._check_regime_transition(result, regime)

        # Store current regime for next check
        self._previous_regime = regime

        if not result.allowed:
            logger.info(
                f"Trade blocked: {[r.value for r in result.reasons]}"
            )

        return result

    def _check_volatility(
        self,
        result: FilterResult,
        features: FeatureVector,
        regime: RegimeState
    ) -> None:
        """Check volatility filters."""
        # Extreme volatility regime
        if self.config['extreme_vol_blocks'] and regime.volatility == VolatilityLevel.EXTREME:
            result.add_block(
                FilterReason.EXTREME_VOLATILITY,
                f"Volatility={regime.volatility.value}"
            )
            return

        # ATR too high
        if features.atr_14 is not None and features.close > 0:
            atr_pct = (features.atr_14 / features.close) * 100
            if atr_pct > self.config['max_atr_pct']:
                result.add_block(
                    FilterReason.EXTREME_VOLATILITY,
                    f"ATR%={atr_pct:.2f}% > {self.config['max_atr_pct']}%"
                )

    def _check_volume(
        self,
        result: FilterResult,
        features: FeatureVector
    ) -> None:
        """Check volume/liquidity filters."""
        if features.volume_ratio is not None:
            if features.volume_ratio < self.config['min_volume_ratio']:
                result.add_block(
                    FilterReason.LOW_VOLUME,
                    f"Volume ratio={features.volume_ratio:.2f} < {self.config['min_volume_ratio']}"
                )

    def _check_time(
        self,
        result: FilterResult,
        ts: datetime
    ) -> None:
        """Check time-based filters."""
        # Only apply to stocks
        if self.market_type != MarketType.NASDAQ:
            return

        current_time = ts.time()

        # Check market hours
        if current_time < self.STOCK_MARKET_OPEN or current_time >= self.STOCK_MARKET_CLOSE:
            result.add_block(
                FilterReason.MARKET_HOURS,
                f"Outside market hours: {current_time}"
            )
            return

        # Avoid first N minutes
        avoid_until = (
            datetime.combine(ts.date(), self.STOCK_MARKET_OPEN) +
            timedelta(minutes=self.config['avoid_first_minutes'])
        ).time()
        if current_time < avoid_until:
            result.add_block(
                FilterReason.MARKET_HOURS,
                f"First {self.config['avoid_first_minutes']}min after open"
            )
            return

        # Avoid last N minutes
        avoid_from = (
            datetime.combine(ts.date(), self.STOCK_MARKET_CLOSE) -
            timedelta(minutes=self.config['avoid_last_minutes'])
        ).time()
        if current_time >= avoid_from:
            result.add_block(
                FilterReason.MARKET_HOURS,
                f"Last {self.config['avoid_last_minutes']}min before close"
            )
            return

        # Check news blackouts
        for start, end in self._news_blackouts:
            if start <= ts <= end:
                result.add_block(
                    FilterReason.NEWS_BLACKOUT,
                    f"News event: {start} - {end}"
                )
                return

    def _check_risk_limits(self, result: FilterResult) -> None:
        """Check risk management filters."""
        session = self.session

        # Max daily trades
        if session.trades_count >= self.config['max_daily_trades']:
            result.add_block(
                FilterReason.MAX_TRADES_REACHED,
                f"Trades today={session.trades_count}"
            )

        # Consecutive losses
        if session.consecutive_losses >= self.config['max_consecutive_losses']:
            result.add_block(
                FilterReason.CONSECUTIVE_LOSSES,
                f"Consecutive losses={session.consecutive_losses}"
            )

        # Daily loss limit
        if self.account_value > 0:
            daily_loss_pct = (-session.realized_pnl / self.account_value) * 100
            if daily_loss_pct >= self.config['daily_loss_limit_pct']:
                result.add_block(
                    FilterReason.DAILY_LOSS_LIMIT,
                    f"Daily loss={daily_loss_pct:.2f}%"
                )

    def _check_technical(
        self,
        result: FilterResult,
        features: FeatureVector
    ) -> None:
        """Check technical filters."""
        # RSI extremes
        if features.rsi_14 is not None:
            if features.rsi_14 >= self.config['rsi_extreme_high']:
                result.add_block(
                    FilterReason.RSI_EXTREME,
                    f"RSI={features.rsi_14:.1f} >= {self.config['rsi_extreme_high']}"
                )
            elif features.rsi_14 <= self.config['rsi_extreme_low']:
                result.add_block(
                    FilterReason.RSI_EXTREME,
                    f"RSI={features.rsi_14:.1f} <= {self.config['rsi_extreme_low']}"
                )

    def _check_regime_transition(
        self,
        result: FilterResult,
        regime: RegimeState
    ) -> None:
        """Check for regime transition."""
        if self._previous_regime is None:
            return

        # Block during significant regime changes
        prev = self._previous_regime
        curr = regime

        # Trend flip
        trend_flip = (
            (prev.regime.value.startswith('trend_') and curr.regime.value.startswith('trend_') and
             prev.regime != curr.regime)
        )

        # Volatility spike
        vol_spike = (
            prev.volatility in (VolatilityLevel.LOW, VolatilityLevel.NORMAL) and
            curr.volatility == VolatilityLevel.EXTREME
        )

        if trend_flip or vol_spike:
            result.add_block(
                FilterReason.REGIME_TRANSITION,
                f"Regime change: {prev.regime_label} -> {curr.regime_label}"
            )

    # ==================== Session Management ====================

    def record_trade(self, pnl: float) -> None:
        """Record a completed trade result.

        Args:
            pnl: Realized P&L of the trade
        """
        self.session.record_trade(pnl)
        logger.debug(
            f"Trade recorded: PnL={pnl:.2f}, "
            f"session_total={self.session.realized_pnl:.2f}"
        )

    def reset_session(self) -> None:
        """Force reset trading session."""
        self._session = TradingSession(date=datetime.utcnow())
        logger.info("Trading session reset")

    def update_account_value(self, value: float) -> None:
        """Update account value for risk calculations.

        Args:
            value: New account value
        """
        self.account_value = value

    def add_news_blackout(self, start: datetime, end: datetime) -> None:
        """Add a news blackout window.

        Args:
            start: Blackout start time
            end: Blackout end time
        """
        self._news_blackouts.append((start, end))
        # Keep sorted and remove expired
        now = datetime.utcnow()
        self._news_blackouts = [
            (s, e) for s, e in self._news_blackouts
            if e > now
        ]
        self._news_blackouts.sort(key=lambda x: x[0])

    def clear_news_blackouts(self) -> None:
        """Clear all news blackout windows."""
        self._news_blackouts.clear()

    # ==================== Query Methods ====================

    def is_trading_allowed(self) -> bool:
        """Quick check if trading is generally allowed.

        Returns:
            True if no session-level blocks
        """
        session = self.session

        if session.trades_count >= self.config['max_daily_trades']:
            return False
        if session.consecutive_losses >= self.config['max_consecutive_losses']:
            return False

        if self.account_value > 0:
            daily_loss_pct = (-session.realized_pnl / self.account_value) * 100
            if daily_loss_pct >= self.config['daily_loss_limit_pct']:
                return False

        return True

    def get_session_stats(self) -> dict:
        """Get current session statistics.

        Returns:
            Dict with session stats
        """
        session = self.session
        return {
            'date': session.date.isoformat(),
            'trades_count': session.trades_count,
            'winning_trades': session.winning_trades,
            'losing_trades': session.losing_trades,
            'consecutive_losses': session.consecutive_losses,
            'realized_pnl': session.realized_pnl,
            'win_rate': (
                session.winning_trades / session.trades_count
                if session.trades_count > 0 else 0.0
            )
        }

    def get_filter_config(self) -> dict:
        """Get current filter configuration.

        Returns:
            Copy of filter config
        """
        return self.config.copy()
