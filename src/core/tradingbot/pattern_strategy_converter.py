"""Pattern Strategy to Bot Configuration Converter.

Converts pattern-based trading strategies (from Strategy Concept feature)
into BotController-compatible configuration.

Maps pattern metadata (entry_price, stop_loss, take_profit) to:
- StrategyProfile for bot execution
- Risk parameters based on pattern characteristics
- Trailing stop configuration optimized for pattern type
"""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from .models import RegimeType, StrategyProfile, TrailingMode, VolatilityLevel

logger = logging.getLogger(__name__)


class PatternStrategyConverter:
    """Converts pattern-based strategies to BotController configuration."""

    # Pattern-specific trailing configurations
    PATTERN_TRAILING_CONFIG = {
        'cup_and_handle': {
            'mode': TrailingMode.ATR,
            'multiplier': 1.5,  # Conservative - pattern has clear structure
            'entry_threshold': 0.65,  # Medium-high confidence needed
        },
        'triple_bottom': {
            'mode': TrailingMode.ATR,
            'multiplier': 1.3,  # More aggressive - strong reversal signal
            'entry_threshold': 0.70,  # High confidence - reversal pattern
        },
        'ascending_triangle': {
            'mode': TrailingMode.ATR,
            'multiplier': 1.4,  # Balanced - breakout pattern
            'entry_threshold': 0.65,  # Medium-high confidence
        },
        'default': {
            'mode': TrailingMode.ATR,
            'multiplier': 1.5,
            'entry_threshold': 0.60,
        },
    }

    # Pattern-to-regime mapping
    PATTERN_REGIME_MAPPING = {
        'cup_and_handle': [RegimeType.TREND_UP, RegimeType.RANGE],
        'triple_bottom': [RegimeType.RANGE, RegimeType.TREND_UP],
        'ascending_triangle': [RegimeType.TREND_UP],
    }

    def convert_to_strategy_profile(
        self,
        pattern_type: str,
        strategy_data: dict[str, Any],
    ) -> StrategyProfile:
        """Convert pattern strategy to StrategyProfile for BotController.

        Args:
            pattern_type: Pattern type identifier (e.g., "cup_and_handle")
            strategy_data: Strategy data from Pattern Integration widget
                Expected keys:
                - pattern_name: Human-readable pattern name
                - pattern_data: Pattern metadata
                    - entry_price: Entry price level
                    - stop_loss: Stop loss price level
                    - take_profit: Take profit price level
                    - pivots: Pattern pivots (optional)
                - strategy: Strategy metadata (optional)
                    - success_rate: Historical success rate
                    - profit_factor: Historical profit factor
                    - sample_size: Number of historical trades

        Returns:
            StrategyProfile configured for this pattern

        Example:
            >>> converter = PatternStrategyConverter()
            >>> strategy_data = {
            ...     'pattern_name': 'Cup and Handle Breakout',
            ...     'pattern_data': {
            ...         'entry_price': 151.0,
            ...         'stop_loss': 140.0,
            ...         'take_profit': 173.0,
            ...     },
            ...     'strategy': {
            ...         'success_rate': 0.95,
            ...     }
            ... }
            >>> profile = converter.convert_to_strategy_profile('cup_and_handle', strategy_data)
            >>> profile.name
            'Cup and Handle Breakout'
        """
        pattern_name = strategy_data.get('pattern_name', 'Unknown Pattern')
        pattern_data_dict = strategy_data.get('pattern_data', {})
        strategy_meta = strategy_data.get('strategy', {})

        # Get pattern-specific configuration
        config = self.PATTERN_TRAILING_CONFIG.get(
            pattern_type,
            self.PATTERN_TRAILING_CONFIG['default']
        )

        # Extract entry/stop/target
        entry_price = pattern_data_dict.get('entry_price')
        stop_loss = pattern_data_dict.get('stop_loss')
        take_profit = pattern_data_dict.get('take_profit')

        if not all([entry_price, stop_loss, take_profit]):
            logger.warning(
                f"Pattern strategy missing entry/stop/target levels: {pattern_name}"
            )

        # Calculate risk parameters
        risk = abs(entry_price - stop_loss) if entry_price and stop_loss else 0.0
        reward = abs(take_profit - entry_price) if take_profit and entry_price else 0.0
        risk_reward_ratio = reward / risk if risk > 0 else 0.0

        logger.info(
            f"Converting pattern strategy: {pattern_name}, "
            f"Entry={entry_price}, SL={stop_loss}, TP={take_profit}, "
            f"R:R={risk_reward_ratio:.2f}"
        )

        # Map pattern to applicable regimes
        regimes = self.PATTERN_REGIME_MAPPING.get(pattern_type, [])

        # Determine volatility levels based on risk
        volatility_levels = self._determine_volatility_levels(risk, entry_price)

        # Build StrategyProfile
        return StrategyProfile(
            name=pattern_name,
            description=f"Pattern-based strategy: {pattern_type} with {risk_reward_ratio:.2f} R:R",
            # Applicable conditions
            regimes=regimes,
            volatility_levels=volatility_levels,
            # Parameters
            entry_threshold=config['entry_threshold'],
            trailing_mode=config['mode'],
            trailing_multiplier=config['multiplier'],
            # Historical performance (from strategy metadata)
            win_rate=strategy_meta.get('success_rate'),
            profit_factor=strategy_meta.get('profit_factor'),
            expectancy=None,  # Not provided by pattern analysis
            sample_size=strategy_meta.get('sample_size', 0),
            # Robustness
            is_robust=strategy_meta.get('success_rate', 0) >= 0.80,  # 80%+ win rate = robust
            last_validated=datetime.now(),
        )

    def _determine_volatility_levels(
        self,
        risk: float,
        entry_price: float
    ) -> list[VolatilityLevel]:
        """Determine applicable volatility levels based on risk."""
        if entry_price is None or entry_price == 0:
            return []

        risk_pct = (risk / entry_price) * 100.0

        # Map risk% to volatility levels
        if risk_pct < 1.0:
            # Very tight stop = low volatility environment
            return [VolatilityLevel.LOW]
        elif risk_pct < 2.0:
            # Normal stop = normal volatility
            return [VolatilityLevel.NORMAL]
        elif risk_pct < 4.0:
            # Wide stop = high volatility
            return [VolatilityLevel.HIGH]
        else:
            # Very wide stop = extreme volatility
            return [VolatilityLevel.EXTREME]

    def extract_fixed_levels(
        self,
        strategy_data: dict[str, Any]
    ) -> tuple[float | None, float | None, float | None]:
        """Extract fixed entry/stop/target levels from pattern strategy.

        Args:
            strategy_data: Strategy data dict

        Returns:
            Tuple of (entry_price, stop_loss, take_profit)
        """
        pattern_data = strategy_data.get('pattern_data', {})

        entry_price = pattern_data.get('entry_price')
        stop_loss = pattern_data.get('stop_loss')
        take_profit = pattern_data.get('take_profit')

        return entry_price, stop_loss, take_profit

    def validate_strategy_data(self, strategy_data: dict[str, Any]) -> tuple[bool, str]:
        """Validate pattern strategy data has required fields.

        Args:
            strategy_data: Strategy data dict

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not strategy_data:
            return False, "Strategy data is empty"

        if 'pattern_name' not in strategy_data:
            return False, "Missing 'pattern_name' field"

        if 'pattern_data' not in strategy_data:
            return False, "Missing 'pattern_data' field"

        pattern_data = strategy_data['pattern_data']

        # Check for required price levels
        required_fields = ['entry_price', 'stop_loss', 'take_profit']
        missing_fields = [f for f in required_fields if f not in pattern_data]

        if missing_fields:
            return False, f"Missing required fields: {', '.join(missing_fields)}"

        # Validate price levels are positive
        entry = pattern_data.get('entry_price')
        stop = pattern_data.get('stop_loss')
        target = pattern_data.get('take_profit')

        if any(v is None or v <= 0 for v in [entry, stop, target]):
            return False, "Entry, stop loss, and take profit must be positive numbers"

        # Validate risk:reward makes sense (stop != entry, target != entry)
        if entry == stop:
            return False, "Stop loss cannot equal entry price (zero risk)"

        if entry == target:
            return False, "Take profit cannot equal entry price (zero reward)"

        # Validate direction (for long positions: target > entry > stop)
        if target > entry:
            # Long position
            if stop >= entry:
                return False, "For long position: stop loss must be below entry"
        else:
            # Short position
            if stop <= entry:
                return False, "For short position: stop loss must be above entry"

        return True, ""
