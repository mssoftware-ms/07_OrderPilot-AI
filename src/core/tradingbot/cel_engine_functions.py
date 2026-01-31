"""CEL Engine Functions - Custom trading functions for CEL expressions.

This module contains all custom function implementations for the CEL engine:
- Statistical functions (pctl, crossover)
- Null handling (isnull, nz, coalesce)
- Mathematical functions (clamp, pct_change, sqrt, pow, etc.)
- Status functions (is_trade_open, is_long, is_short, in_regime)
- Price functions (stop_hit_long, price_above_ema, etc.)
- Time functions (now, timestamp, bar_age, is_new_day)
- String functions (type, contains, split, join)
- Array functions (size, has, sum, avg, filter)
- Regime functions (last_closed_regime, new_regime_detected)
- Pattern functions (pin_bar, inside_bar, breakout patterns)
- SMC functions (liquidity_swept, fvg_exists, order_block_retest)

Part of the CEL (Common Expression Language) engine refactoring.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class CELFunctions:
    """Container for all CEL custom functions.

    All methods are static to allow direct function mapping in CEL engine.
    Instance methods are used for functions requiring context access.
    """

    def __init__(self, engine_instance=None):
        """Initialize CEL functions container.

        Args:
            engine_instance: Reference to parent CELEngine for context access
        """
        self._engine = engine_instance

    def _get_context_value(self, key: str):
        """Resolve a value from the last evaluation context.

        Supports both flat keys (e.g., "pattern.pin_bar_bullish")
        and nested dicts (e.g., context["pattern"]["pin_bar_bullish"]).
        """
        if not self._engine:
            return None
        ctx = self._engine._last_context or {}
        if key in ctx:
            return ctx.get(key)
        if "." in key:
            namespace, sub = key.split(".", 1)
            container = ctx.get(namespace)
            if isinstance(container, dict):
                return container.get(sub)
        return None

    def _context_flag(self, *keys: str) -> bool:
        """Return boolean flag for the first available key."""
        for key in keys:
            value = self._get_context_value(key)
            if value is not None:
                return bool(value)
        return False

    @staticmethod
    def _func_pctl(series: list | pd.Series, percentile: float, window: int | None = None) -> float:
        """Calculate percentile of a series.

        Args:
            series: Data series (list or Series)
            percentile: Percentile rank (0-100)
            window: Rolling window size (None = use all data)

        Returns:
            Percentile value

        Example:
            >>> pctl([10, 20, 30, 40, 50], 50)  # Median
            30.0
        """
        if isinstance(series, pd.Series):
            data = series.values
        elif isinstance(series, list):
            data = np.array(series)
        else:
            data = np.array([series])

        # Use window if specified
        if window is not None and len(data) > window:
            data = data[-window:]

        # Filter out NaN/None
        data = data[~pd.isna(data)]

        if len(data) == 0:
            return 0.0

        return float(np.percentile(data, percentile))

    @staticmethod
    def _func_crossover(series1: float | list, series2: float | list) -> bool:
        """Check if series1 crossed above series2 (bullish crossover).

        Args:
            series1: Current and previous values [current, previous]
            series2: Current and previous values [current, previous]

        Returns:
            True if series1 crossed above series2

        Example:
            >>> crossover([10, 8], [9, 9])  # 8 < 9, 10 > 9 => crossover
            True
        """
        # Handle scalar vs list inputs
        if isinstance(series1, (int, float)):
            # If scalar, assume no crossover (need history)
            return False
        if isinstance(series2, (int, float)):
            s2_curr = s2_prev = series2
        else:
            s2_curr, s2_prev = series2[0], series2[1] if len(series2) > 1 else series2[0]

        s1_curr, s1_prev = series1[0], series1[1] if len(series1) > 1 else series1[0]

        # Crossover: was below, now above
        return s1_prev <= s2_prev and s1_curr > s2_curr

    @staticmethod
    def _func_isnull(value: Any) -> bool:
        """Check if value is null/None/NaN.

        Args:
            value: Value to check

        Returns:
            True if value is null/None/NaN

        Example:
            >>> isnull(None)
            True
            >>> isnull(float('nan'))
            True
        """
        if value is None:
            return True
        if isinstance(value, float) and np.isnan(value):
            return True
        return False

    @staticmethod
    def _func_nz(value: Any, default: Any = 0) -> Any:
        """Return default if value is null, otherwise return value.

        Args:
            value: Value to check
            default: Default value if null

        Returns:
            value if not null, else default

        Example:
            >>> nz(None, 100)
            100
            >>> nz(42, 100)
            42
        """
        if CELFunctions._func_isnull(value):
            return default
        return value

    @staticmethod
    def _func_coalesce(*args) -> Any:
        """Return first non-null value from arguments.

        Args:
            *args: Values to check in order

        Returns:
            First non-null value, or None if all null

        Example:
            >>> coalesce(None, None, 42, 100)
            42
        """
        for arg in args:
            if not CELFunctions._func_isnull(arg):
                return arg
        return None

    # ========================================================================
    # Phase 1.1: Mathematical & Trading Functions
    # ========================================================================

    @staticmethod
    def _func_clamp(value: float, min_val: float, max_val: float) -> float:
        """Constrain value between min and max.

        Args:
            value: Value to clamp
            min_val: Minimum value
            max_val: Maximum value

        Returns:
            Clamped value

        Example:
            >>> clamp(15, 10, 20)
            15
            >>> clamp(5, 10, 20)
            10
            >>> clamp(25, 10, 20)
            20
        """
        if min_val > max_val:
            raise ValueError(f"min_val ({min_val}) must be <= max_val ({max_val})")
        return max(min_val, min(value, max_val))

    @staticmethod
    def _func_pct_change(old: float, new: float) -> float:
        """Calculate percentage change from old to new value.

        Args:
            old: Old value
            new: New value

        Returns:
            Percentage change (e.g., 10.5 for 10.5% increase)

        Example:
            >>> pct_change(100, 110)
            10.0
            >>> pct_change(100, 90)
            -10.0
        """
        if old == 0:
            # Avoid division by zero: return 0 if both are 0, else 100% change
            return 0.0 if new == 0 else (100.0 if new > 0 else -100.0)
        return ((new - old) / abs(old)) * 100.0

    @staticmethod
    def _func_pct_from_level(price: float, level: float) -> float:
        """Calculate percentage distance from price to level.

        Args:
            price: Current price
            level: Reference level

        Returns:
            Absolute percentage distance

        Example:
            >>> pct_from_level(110, 100)
            10.0
            >>> pct_from_level(90, 100)
            10.0
        """
        if level == 0:
            return 0.0
        return abs((price - level) / level) * 100.0

    @staticmethod
    def _func_level_at_pct(entry: float, pct: float, side: str) -> float:
        """Calculate price level at percentage distance from entry.

        Args:
            entry: Entry price
            pct: Percentage distance (positive number, e.g., 2.0 for 2%)
            side: Trade side ('long' or 'short')

        Returns:
            Price level

        Example:
            >>> level_at_pct(100, 2.0, 'long')  # Stop loss 2% below
            98.0
            >>> level_at_pct(100, 2.0, 'short')  # Stop loss 2% above
            102.0
        """
        if side.lower() == 'long':
            # Long: level below entry (stop loss)
            return entry * (1 - pct / 100.0)
        elif side.lower() == 'short':
            # Short: level above entry (stop loss)
            return entry * (1 + pct / 100.0)
        else:
            raise ValueError(f"Invalid side: {side}. Must be 'long' or 'short'")

    @staticmethod
    def _func_retracement(from_price: float, to_price: float, pct: float) -> float:
        """Calculate Fibonacci retracement level.

        Args:
            from_price: Starting price (swing low for uptrend, high for downtrend)
            to_price: Ending price (swing high for uptrend, low for downtrend)
            pct: Retracement percentage (e.g., 38.2, 50, 61.8)

        Returns:
            Retracement level price

        Example:
            >>> retracement(100, 200, 50)  # 50% retracement
            150.0
            >>> retracement(200, 100, 61.8)  # 61.8% retracement down
            138.2
        """
        return from_price + (to_price - from_price) * (pct / 100.0)

    @staticmethod
    def _func_extension(from_price: float, to_price: float, pct: float) -> float:
        """Calculate Fibonacci extension level.

        Args:
            from_price: Starting price
            to_price: Ending price
            pct: Extension percentage (e.g., 127.2, 161.8, 261.8)

        Returns:
            Extension level price

        Example:
            >>> extension(100, 200, 161.8)  # 161.8% extension
            361.8
        """
        move = to_price - from_price
        return to_price + move * (pct / 100.0)

    # ========================================================================
    # Phase 1.2: Status Functions
    # ========================================================================

    @staticmethod
    def _func_is_trade_open(trade: dict) -> bool:
        """Check if a trade is currently open.

        Args:
            trade: Trade context dict with 'is_open' or 'status' field

        Returns:
            True if trade is open

        Example:
            >>> is_trade_open({"is_open": True})
            True
            >>> is_trade_open({"status": "open"})
            True
        """
        if isinstance(trade, dict):
            # Check 'is_open' field first
            if 'is_open' in trade:
                return bool(trade['is_open'])
            # Fallback: check 'status' field
            if 'status' in trade:
                return str(trade['status']).lower() in ('open', 'active')
        return False

    @staticmethod
    def _func_is_long(trade: dict) -> bool:
        """Check if current trade is LONG.

        Args:
            trade: Trade context dict with 'side' field

        Returns:
            True if trade side is LONG

        Example:
            >>> is_long({"side": "long"})
            True
            >>> is_long({"side": "short"})
            False
        """
        if isinstance(trade, dict) and 'side' in trade:
            return str(trade['side']).lower() == 'long'
        return False

    @staticmethod
    def _func_is_short(trade: dict) -> bool:
        """Check if current trade is SHORT.

        Args:
            trade: Trade context dict with 'side' field

        Returns:
            True if trade side is SHORT

        Example:
            >>> is_short({"side": "short"})
            True
            >>> is_short({"side": "long"})
            False
        """
        if isinstance(trade, dict) and 'side' in trade:
            return str(trade['side']).lower() == 'short'
        return False

    @staticmethod
    def _func_is_bullish_signal(strategy: dict) -> bool:
        """Check if strategy has bullish bias.

        Args:
            strategy: Strategy context dict with 'signal' or 'bias' field

        Returns:
            True if bullish signal active

        Example:
            >>> is_bullish_signal({"signal": "bullish"})
            True
            >>> is_bullish_signal({"bias": "long"})
            True
        """
        if isinstance(strategy, dict):
            # Check 'signal' field
            if 'signal' in strategy:
                return str(strategy['signal']).lower() in ('bullish', 'buy', 'long')
            # Check 'bias' field
            if 'bias' in strategy:
                return str(strategy['bias']).lower() in ('bullish', 'long', 'up')
        return False

    @staticmethod
    def _func_is_bearish_signal(strategy: dict) -> bool:
        """Check if strategy has bearish bias.

        Args:
            strategy: Strategy context dict with 'signal' or 'bias' field

        Returns:
            True if bearish signal active

        Example:
            >>> is_bearish_signal({"signal": "bearish"})
            True
            >>> is_bearish_signal({"bias": "short"})
            True
        """
        if isinstance(strategy, dict):
            # Check 'signal' field
            if 'signal' in strategy:
                return str(strategy['signal']).lower() in ('bearish', 'sell', 'short')
            # Check 'bias' field
            if 'bias' in strategy:
                return str(strategy['bias']).lower() in ('bearish', 'short', 'down')
        return False

    @staticmethod
    def _func_in_regime(regime: str | list, regime_id: str) -> bool:
        """Check if currently in specified regime.

        Args:
            regime: Current regime (string ID or list of active regime IDs)
            regime_id: Regime ID to check

        Returns:
            True if in specified regime

        Example:
            >>> in_regime("trending_strong", "trending_strong")
            True
            >>> in_regime(["trending", "high_vol"], "trending")
            True
        """
        if isinstance(regime, str):
            return regime == regime_id
        elif isinstance(regime, list):
            return regime_id in regime
        return False

    # ========================================================================
    # Phase 1.3: Price Functions
    # ========================================================================

    @staticmethod
    def _func_stop_hit_long(trade: dict, current_price: float) -> bool:
        """Check if long stop loss was hit.

        Args:
            trade: Trade context with 'stop_price' or 'stop_loss' field
            current_price: Current market price

        Returns:
            True if stop was hit (price <= stop)

        Example:
            >>> stop_hit_long({"stop_price": 100}, 99)
            True
            >>> stop_hit_long({"stop_price": 100}, 101)
            False
        """
        if not isinstance(trade, dict):
            return False

        stop_price = trade.get('stop_price') or trade.get('stop_loss')
        if stop_price is None:
            return False

        return current_price <= float(stop_price)

    @staticmethod
    def _func_stop_hit_short(trade: dict, current_price: float) -> bool:
        """Check if short stop loss was hit.

        Args:
            trade: Trade context with 'stop_price' or 'stop_loss' field
            current_price: Current market price

        Returns:
            True if stop was hit (price >= stop)

        Example:
            >>> stop_hit_short({"stop_price": 100}, 101)
            True
            >>> stop_hit_short({"stop_price": 100}, 99)
            False
        """
        if not isinstance(trade, dict):
            return False

        stop_price = trade.get('stop_price') or trade.get('stop_loss')
        if stop_price is None:
            return False

        return current_price >= float(stop_price)

    @staticmethod
    def _func_tp_hit(trade: dict, current_price: float) -> bool:
        """Check if take profit was hit.

        Args:
            trade: Trade context with 'tp_price', 'take_profit', and 'side' fields
            current_price: Current market price

        Returns:
            True if take profit was hit

        Example:
            >>> tp_hit({"tp_price": 110, "side": "long"}, 111)
            True
            >>> tp_hit({"tp_price": 90, "side": "short"}, 89)
            True
        """
        if not isinstance(trade, dict):
            return False

        tp_price = trade.get('tp_price') or trade.get('take_profit')
        if tp_price is None:
            return False

        side = trade.get('side', '').lower()
        tp_price = float(tp_price)

        if side == 'long':
            return current_price >= tp_price
        elif side == 'short':
            return current_price <= tp_price
        else:
            # Unknown side, check both directions
            return current_price >= tp_price or current_price <= tp_price

    @staticmethod
    def _func_price_above_ema(price: float, ema: float) -> bool:
        """Check if price is above EMA.

        Args:
            price: Current price
            ema: EMA value

        Returns:
            True if price > EMA

        Example:
            >>> price_above_ema(105, 100)
            True
            >>> price_above_ema(95, 100)
            False
        """
        return price > ema

    @staticmethod
    def _func_price_below_ema(price: float, ema: float) -> bool:
        """Check if price is below EMA.

        Args:
            price: Current price
            ema: EMA value

        Returns:
            True if price < EMA

        Example:
            >>> price_below_ema(95, 100)
            True
            >>> price_below_ema(105, 100)
            False
        """
        return price < ema

    @staticmethod
    def _func_price_above_level(price: float, level: float) -> bool:
        """Check if price is above specified level.

        Args:
            price: Current price
            level: Price level (support/resistance)

        Returns:
            True if price > level

        Example:
            >>> price_above_level(105, 100)
            True
        """
        return price > level

    @staticmethod
    def _func_price_below_level(price: float, level: float) -> bool:
        """Check if price is below specified level.

        Args:
            price: Current price
            level: Price level (support/resistance)

        Returns:
            True if price < level

        Example:
            >>> price_below_level(95, 100)
            True
        """
        return price < level

    # ========================================================================
    # Phase 1.4: Time Functions
    # ========================================================================

    @staticmethod
    def _func_now() -> int:
        """Get current Unix timestamp in seconds.

        Returns:
            Current timestamp (seconds since epoch)

        Example:
            >>> now()  # e.g., 1706356800
            1706356800
        """
        return int(datetime.now().timestamp())

    @staticmethod
    def _func_timestamp(dt: str | datetime | int) -> int:
        """Convert datetime to Unix timestamp.

        Args:
            dt: Datetime (ISO string, datetime object, or timestamp)

        Returns:
            Unix timestamp in seconds

        Example:
            >>> timestamp("2024-01-27T12:00:00")
            1706356800
            >>> timestamp(1706356800)
            1706356800
        """
        if isinstance(dt, int):
            return dt
        elif isinstance(dt, datetime):
            return int(dt.timestamp())
        elif isinstance(dt, str):
            # Parse ISO format datetime string
            try:
                parsed = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                return int(parsed.timestamp())
            except ValueError:
                # Fallback: try common formats
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
                    try:
                        parsed = datetime.strptime(dt, fmt)
                        return int(parsed.timestamp())
                    except ValueError:
                        continue
                raise ValueError(f"Cannot parse datetime: {dt}")
        else:
            raise TypeError(f"Invalid type for timestamp: {type(dt)}")

    @staticmethod
    def _func_bar_age(bar_time: int | str | datetime) -> int:
        """Calculate age of bar in seconds.

        Args:
            bar_time: Bar timestamp (Unix seconds, ISO string, or datetime)

        Returns:
            Age in seconds

        Example:
            >>> bar_age(1706356800)  # If now is 1706356900
            100
        """
        bar_ts = CELFunctions._func_timestamp(bar_time)
        now_ts = CELFunctions._func_now()
        return now_ts - bar_ts

    @staticmethod
    def _func_bars_since(trade: dict, current_bar: int) -> int:
        """Calculate number of bars since trade entry.

        Args:
            trade: Trade context with 'entry_bar' or 'bars_in_trade' field
            current_bar: Current bar index

        Returns:
            Number of bars since entry

        Example:
            >>> bars_since({"entry_bar": 100}, 105)
            5
            >>> bars_since({"bars_in_trade": 10}, 0)
            10
        """
        if not isinstance(trade, dict):
            return 0

        # Check if already calculated
        if 'bars_in_trade' in trade:
            return int(trade['bars_in_trade'])

        # Calculate from entry bar
        entry_bar = trade.get('entry_bar')
        if entry_bar is not None:
            return current_bar - int(entry_bar)

        return 0

    @staticmethod
    def _func_is_new_day(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if current time is a new day compared to previous.

        Args:
            prev_time: Previous timestamp
            curr_time: Current timestamp

        Returns:
            True if day changed

        Example:
            >>> is_new_day("2024-01-27T23:59:59", "2024-01-28T00:00:01")
            True
            >>> is_new_day("2024-01-27T10:00:00", "2024-01-27T14:00:00")
            False
        """
        prev_ts = CELFunctions._func_timestamp(prev_time)
        curr_ts = CELFunctions._func_timestamp(curr_time)

        prev_dt = datetime.fromtimestamp(prev_ts)
        curr_dt = datetime.fromtimestamp(curr_ts)

        return prev_dt.date() != curr_dt.date()

    @staticmethod
    def _func_is_new_hour(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if current time is a new hour compared to previous.

        Args:
            prev_time: Previous timestamp
            curr_time: Current timestamp

        Returns:
            True if hour changed

        Example:
            >>> is_new_hour("2024-01-27T10:59:59", "2024-01-27T11:00:01")
            True
            >>> is_new_hour("2024-01-27T10:00:00", "2024-01-27T10:30:00")
            False
        """
        prev_ts = CELFunctions._func_timestamp(prev_time)
        curr_ts = CELFunctions._func_timestamp(curr_time)

        prev_dt = datetime.fromtimestamp(prev_ts)
        curr_dt = datetime.fromtimestamp(curr_ts)

        return prev_dt.hour != curr_dt.hour or prev_dt.date() != curr_dt.date()

    # ========================================================================
    # Phase 1.5: String & Type Functions
    # ========================================================================

    @staticmethod
    def _func_type(value: Any) -> str:
        """Get type name of value.

        Args:
            value: Any value

        Returns:
            Type name (string)

        Example:
            >>> type(42)
            'int'
            >>> type("hello")
            'str'
        """
        return type(value).__name__

    @staticmethod
    def _func_string(value: Any) -> str:
        """Convert value to string.

        Args:
            value: Any value

        Returns:
            String representation

        Example:
            >>> string(42)
            '42'
            >>> string(True)
            'True'
        """
        return str(value)

    @staticmethod
    def _func_int(value: Any) -> int:
        """Convert value to integer.

        Args:
            value: Numeric value or string

        Returns:
            Integer value

        Example:
            >>> int("42")
            42
            >>> int(42.7)
            42
        """
        return int(float(value))  # Handle both int and float strings

    @staticmethod
    def _func_double(value: Any) -> float:
        """Convert value to float (double).

        Args:
            value: Numeric value or string

        Returns:
            Float value

        Example:
            >>> double("42.5")
            42.5
            >>> double(42)
            42.0
        """
        return float(value)

    @staticmethod
    def _func_bool(value: Any) -> bool:
        """Convert value to boolean.

        Args:
            value: Any value

        Returns:
            Boolean value

        Example:
            >>> bool("true")
            True
            >>> bool(0)
            False
        """
        if isinstance(value, str):
            return value.lower() in ('true', '1', 'yes', 'on')
        return bool(value)

    @staticmethod
    def _func_contains(haystack: str, needle: str) -> bool:
        """Check if string contains substring.

        Args:
            haystack: String to search in
            needle: Substring to search for

        Returns:
            True if found

        Example:
            >>> contains("hello world", "world")
            True
            >>> contains("hello world", "xyz")
            False
        """
        return needle in haystack

    @staticmethod
    def _func_starts_with(text: str, prefix: str) -> bool:
        """Check if string starts with prefix.

        Args:
            text: String to check
            prefix: Prefix to match

        Returns:
            True if starts with prefix

        Example:
            >>> startsWith("hello world", "hello")
            True
        """
        return text.startswith(prefix)

    @staticmethod
    def _func_ends_with(text: str, suffix: str) -> bool:
        """Check if string ends with suffix.

        Args:
            text: String to check
            suffix: Suffix to match

        Returns:
            True if ends with suffix

        Example:
            >>> endsWith("hello world", "world")
            True
        """
        return text.endswith(suffix)

    @staticmethod
    def _func_to_lower_case(text: str) -> str:
        """Convert string to lowercase.

        Args:
            text: String to convert

        Returns:
            Lowercase string

        Example:
            >>> toLowerCase("HELLO World")
            'hello world'
        """
        return text.lower()

    @staticmethod
    def _func_to_upper_case(text: str) -> str:
        """Convert string to uppercase.

        Args:
            text: String to convert

        Returns:
            Uppercase string

        Example:
            >>> toUpperCase("hello World")
            'HELLO WORLD'
        """
        return text.upper()

    @staticmethod
    def _func_substring(text: str, start: int, end: int | None = None) -> str:
        """Extract substring.

        Args:
            text: String to extract from
            start: Start index (inclusive)
            end: End index (exclusive), None = to end

        Returns:
            Substring

        Example:
            >>> substring("hello world", 0, 5)
            'hello'
            >>> substring("hello world", 6)
            'world'
        """
        if end is None:
            return text[start:]
        return text[start:end]

    @staticmethod
    def _func_split(text: str, delimiter: str) -> list[str]:
        """Split string by delimiter.

        Args:
            text: String to split
            delimiter: Delimiter string

        Returns:
            List of parts

        Example:
            >>> split("a,b,c", ",")
            ['a', 'b', 'c']
        """
        return text.split(delimiter)

    @staticmethod
    def _func_join(parts: list, delimiter: str) -> str:
        """Join list of strings with delimiter.

        Args:
            parts: List of strings
            delimiter: Delimiter to join with

        Returns:
            Joined string

        Example:
            >>> join(['a', 'b', 'c'], ",")
            'a,b,c'
        """
        return delimiter.join(str(p) for p in parts)

    # ========================================================================
    # Phase 1.6: Array Functions
    # ========================================================================

    @staticmethod
    def _func_size(array: list | dict) -> int:
        """Get size/length of array or map.

        Args:
            array: List or dict

        Returns:
            Number of elements

        Example:
            >>> size([1, 2, 3])
            3
            >>> size({"a": 1, "b": 2})
            2
        """
        return len(array)

    @staticmethod
    def _func_has(array: list, element: Any) -> bool:
        """Check if array contains element.

        Args:
            array: List to search
            element: Element to find

        Returns:
            True if element in array

        Example:
            >>> has([1, 2, 3], 2)
            True
            >>> has([1, 2, 3], 5)
            False
        """
        return element in array

    @staticmethod
    def _func_all(array: list, condition: Any = None) -> bool:
        """Check if all elements match condition (or are truthy).

        Args:
            array: List to check
            condition: Condition function (not supported in CEL, checks truthiness)

        Returns:
            True if all elements are truthy

        Example:
            >>> all([True, True, True])
            True
            >>> all([True, False, True])
            False
        """
        # Note: CEL doesn't support lambda functions, so we check truthiness
        return all(array)

    @staticmethod
    def _func_any(array: list, condition: Any = None) -> bool:
        """Check if any element matches condition (or is truthy).

        Args:
            array: List to check
            condition: Condition function (not supported in CEL, checks truthiness)

        Returns:
            True if any element is truthy

        Example:
            >>> any([False, False, True])
            True
            >>> any([False, False, False])
            False
        """
        # Note: CEL doesn't support lambda functions, so we check truthiness
        return any(array)

    @staticmethod
    def _func_map(array: list, transform: Any) -> list:
        """Map function over array (limited support without lambdas).

        Args:
            array: List to map over
            transform: Transform function (not fully supported in CEL)

        Returns:
            Transformed list

        Note:
            CEL doesn't support lambda functions, so this is limited.
            Returns original array.

        Example:
            >>> map([1, 2, 3], lambda x: x * 2)  # Not supported in CEL
            [1, 2, 3]
        """
        # Note: Without lambda support, return original array
        # This is a placeholder for future CEL macro support
        return array

    @staticmethod
    def _func_filter(array: list, condition: Any) -> list:
        """Filter array by condition (limited support without lambdas).

        Args:
            array: List to filter
            condition: Filter condition (not fully supported in CEL)

        Returns:
            Filtered list

        Note:
            CEL doesn't support lambda functions, so this is limited.
            Returns original array.

        Example:
            >>> filter([1, 2, 3, 4], lambda x: x > 2)  # Not supported in CEL
            [1, 2, 3, 4]
        """
        # Note: Without lambda support, return original array
        # This is a placeholder for future CEL macro support
        return array

    @staticmethod
    def _func_sum(array: list) -> float:
        """Calculate sum of array elements.

        Args:
            array: List of numbers

        Returns:
            Sum of all elements

        Example:
            >>> sum([1, 2, 3, 4])
            10.0
        """
        return sum(float(x) for x in array if x is not None)

    @staticmethod
    def _func_avg(array: list) -> float:
        """Calculate average of array elements.

        Args:
            array: List of numbers

        Returns:
            Average value

        Example:
            >>> avg([1, 2, 3, 4])
            2.5
        """
        if not array:
            return 0.0
        values = [float(x) for x in array if x is not None]
        return sum(values) / len(values) if values else 0.0

    @staticmethod
    def _func_first(array: list) -> Any:
        """Get first element of array.

        Args:
            array: List

        Returns:
            First element or None if empty

        Example:
            >>> first([1, 2, 3])
            1
        """
        return array[0] if array else None

    @staticmethod
    def _func_last(array: list) -> Any:
        """Get last element of array.

        Args:
            array: List

        Returns:
            Last element or None if empty

        Example:
            >>> last([1, 2, 3])
            3
        """
        return array[-1] if array else None

    @staticmethod
    def _func_index_of(array: list, element: Any) -> int:
        """Find index of element in array.

        Args:
            array: List to search
            element: Element to find

        Returns:
            Index of element, or -1 if not found

        Example:
            >>> indexOf([1, 2, 3], 2)
            1
            >>> indexOf([1, 2, 3], 5)
            -1
        """
        try:
            return array.index(element)
        except ValueError:
            return -1

    @staticmethod
    def _func_slice(array: list, start: int, end: int | None = None) -> list:
        """Slice array.

        Args:
            array: List to slice
            start: Start index (inclusive)
            end: End index (exclusive), None = to end

        Returns:
            Sliced list

        Example:
            >>> slice([1, 2, 3, 4, 5], 1, 3)
            [2, 3]
            >>> slice([1, 2, 3, 4, 5], 2)
            [3, 4, 5]
        """
        if end is None:
            return array[start:]
        return array[start:end]

    @staticmethod
    def _func_distinct(array: list) -> list:
        """Get distinct/unique elements from array.

        Args:
            array: List with potential duplicates

        Returns:
            List with unique elements (order preserved)

        Example:
            >>> distinct([1, 2, 2, 3, 1, 4])
            [1, 2, 3, 4]
        """
        # Preserve order while removing duplicates
        seen = set()
        result = []
        for item in array:
            # Handle unhashable types
            try:
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            except TypeError:
                # Unhashable type (e.g., dict, list), always include
                result.append(item)
        return result

    @staticmethod
    def _func_sort(array: list, reverse: bool = False) -> list:
        """Sort array.

        Args:
            array: List to sort
            reverse: Sort in descending order

        Returns:
            Sorted list

        Example:
            >>> sort([3, 1, 4, 1, 5])
            [1, 1, 3, 4, 5]
            >>> sort([3, 1, 4], True)
            [4, 3, 1]
        """
        return sorted(array, reverse=reverse)

    @staticmethod
    def _func_reverse(array: list) -> list:
        """Reverse array.

        Args:
            array: List to reverse

        Returns:
            Reversed list

        Example:
            >>> reverse([1, 2, 3])
            [3, 2, 1]
        """
        return list(reversed(array))

    # ========================================================================
    # Additional Math Functions (Phase 1 Completion)
    # ========================================================================

    @staticmethod
    def _func_floor(value: float) -> float:
        """Round down to nearest integer.

        Args:
            value: Number to floor

        Returns:
            Floored value

        Example:
            >>> floor(3.7)
            3.0
            >>> floor(-3.2)
            -4.0
        """
        import math
        return math.floor(value)

    @staticmethod
    def _func_ceil(value: float) -> float:
        """Round up to nearest integer.

        Args:
            value: Number to ceil

        Returns:
            Ceiled value

        Example:
            >>> ceil(3.2)
            4.0
            >>> ceil(-3.7)
            -3.0
        """
        import math
        return math.ceil(value)

    @staticmethod
    def _func_round(value: float, decimals: int = 0) -> float:
        """Round to N decimal places.

        Args:
            value: Number to round
            decimals: Number of decimal places (default: 0)

        Returns:
            Rounded value

        Example:
            >>> round(3.14159, 2)
            3.14
            >>> round(3.7, 0)
            4.0
        """
        return round(value, decimals)

    @staticmethod
    def _func_sqrt(value: float) -> float:
        """Calculate square root.

        Args:
            value: Number to take square root of

        Returns:
            Square root

        Raises:
            ValueError: If value is negative

        Example:
            >>> sqrt(16.0)
            4.0
            >>> sqrt(2.0)
            1.414...
        """
        import math
        if value < 0:
            raise ValueError(f"Cannot take square root of negative number: {value}")
        return math.sqrt(value)

    @staticmethod
    def _func_pow(base: float, exponent: float) -> float:
        """Calculate base raised to exponent power.

        Args:
            base: Base number
            exponent: Exponent

        Returns:
            base^exponent

        Example:
            >>> pow(2.0, 3.0)
            8.0
            >>> pow(5.0, 2.0)
            25.0
        """
        return pow(base, exponent)

    @staticmethod
    def _func_exp(value: float) -> float:
        """Calculate e raised to power of value (e^x).

        Args:
            value: Exponent

        Returns:
            e^value

        Example:
            >>> exp(0.0)
            1.0
            >>> exp(1.0)
            2.718...
        """
        import math
        return math.exp(value)

    # ========================================================================
    # Additional Time Functions (Phase 1 Completion)
    # ========================================================================

    @staticmethod
    def _func_is_new_week(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if new week started between two timestamps.

        Args:
            prev_time: Previous timestamp (Unix seconds, ISO string, or datetime)
            curr_time: Current timestamp (Unix seconds, ISO string, or datetime)

        Returns:
            True if new week started (Monday transition)

        Example:
            >>> is_new_week(prev_sunday, curr_monday)
            True
            >>> is_new_week(monday_morning, monday_evening)
            False
        """
        def to_datetime(val: int | str | datetime) -> datetime:
            """Convert timestamp to datetime."""
            if isinstance(val, datetime):
                return val
            elif isinstance(val, int):
                return datetime.fromtimestamp(val)
            else:  # String
                return datetime.fromisoformat(val)

        prev_dt = to_datetime(prev_time)
        curr_dt = to_datetime(curr_time)

        # Check if week changed (ISO week number)
        return prev_dt.isocalendar()[1] != curr_dt.isocalendar()[1]

    @staticmethod
    def _func_is_new_month(prev_time: int | str | datetime, curr_time: int | str | datetime) -> bool:
        """Check if new month started between two timestamps.

        Args:
            prev_time: Previous timestamp (Unix seconds, ISO string, or datetime)
            curr_time: Current timestamp (Unix seconds, ISO string, or datetime)

        Returns:
            True if new month started

        Example:
            >>> is_new_month(jan_31, feb_01)
            True
            >>> is_new_month(jan_15, jan_20)
            False
        """
        def to_datetime(val: int | str | datetime) -> datetime:
            """Convert timestamp to datetime."""
            if isinstance(val, datetime):
                return val
            elif isinstance(val, int):
                return datetime.fromtimestamp(val)
            else:  # String
                return datetime.fromisoformat(val)

        prev_dt = to_datetime(prev_time)
        curr_dt = to_datetime(curr_time)

        # Check if month changed
        return prev_dt.month != curr_dt.month or prev_dt.year != curr_dt.year

    # ========================================================================
    # Additional Price Functions (Phase 1 Completion)
    # ========================================================================

    @staticmethod
    def _func_highest(series: list | pd.Series, period: int) -> float:
        """Get highest value over period.

        Args:
            series: Price series (list or pandas Series)
            period: Lookback period

        Returns:
            Highest value in last N periods

        Example:
            >>> highest([100, 105, 110, 108, 112], 5)
            112.0
            >>> highest([100, 105, 110], 2)
            110.0
        """
        if isinstance(series, pd.Series):
            series = series.tolist()

        # Take last N periods
        data = series[-period:] if len(series) >= period else series

        return max(data) if data else 0.0

    @staticmethod
    def _func_lowest(series: list | pd.Series, period: int) -> float:
        """Get lowest value over period.

        Args:
            series: Price series (list or pandas Series)
            period: Lookback period

        Returns:
            Lowest value in last N periods

        Example:
            >>> lowest([100, 95, 90, 92, 88], 5)
            88.0
            >>> lowest([100, 95, 90], 2)
            90.0
        """
        if isinstance(series, pd.Series):
            series = series.tolist()

        # Take last N periods
        data = series[-period:] if len(series) >= period else series

        return min(data) if data else 0.0

    @staticmethod
    def _func_sma(series: list | pd.Series, period: int) -> float:
        """Calculate Simple Moving Average.

        Args:
            series: Price series (list or pandas Series)
            period: SMA period

        Returns:
            Simple moving average of last N periods

        Example:
            >>> sma([100, 102, 104, 106, 108], 5)
            104.0
            >>> sma([10, 20, 30], 2)
            25.0
        """
        if isinstance(series, pd.Series):
            series = series.tolist()

        # Take last N periods
        data = series[-period:] if len(series) >= period else series

        if not data:
            return 0.0

        return sum(data) / len(data)

    # ========================================================================
    # Phase 1.7: Regime Functions
    # ========================================================================

    def _func_trigger_regime_analysis(self) -> bool:
        """Trigger regime analysis on visible chart range.

        This function:
        1. Gets chart window reference from context
        2. Calls trigger_regime_update() on the chart to analyze visible range
        3. Returns true if successful, false otherwise

        Returns:
            True if regime analysis was triggered successfully

        Example:
            >>> # In CEL expression (run before entry check):
            >>> trigger_regime_analysis() && last_closed_regime() == 'EXTREME_BULL'
            True

            >>> # Ensure regime data is fresh before trade decision
            >>> trigger_regime_analysis() && !is_trade_open(trade) && in_regime('TREND_UP')
            True

        Note:
            This function requires the context to have:
            - 'chart_window' reference with trigger_regime_update() method

            If chart_window is not available, logs a warning and returns False.
        """
        try:
            ctx = self._engine._last_context if self._engine else {}

            # Debug: Log context
            print(f"[CEL] trigger_regime_analysis: _last_context keys: {list(ctx.keys())}", flush=True)
            print(f"[CEL] trigger_regime_analysis: chart_window in ctx: {'chart_window' in ctx}", flush=True)

            # Get chart window reference from context
            if 'chart_window' not in ctx:
                logger.warning("❌ trigger_regime_analysis: No chart_window in context!")
                print("[CEL] ❌ trigger_regime_analysis: No chart_window in context!", flush=True)
                print(f"[CEL] ❌ Available keys: {list(ctx.keys())}", flush=True)
                return False

            chart_window = ctx['chart_window']
            print(f"[CEL] ✅ chart_window found: {type(chart_window).__name__}", flush=True)

            # Fallback: if ChartWindow wrapper was injected, unwrap to its chart_widget
            if not hasattr(chart_window, 'trigger_regime_update') and hasattr(chart_window, 'chart_widget'):
                inner = getattr(chart_window, 'chart_widget')
                if hasattr(inner, 'trigger_regime_update'):
                    print("[CEL] ℹ️ Unwrapped chart_window.chart_widget for regime update", flush=True)
                    chart_window = inner

            # Check if regime update is available (from RegimeDisplayMixin)
            if not hasattr(chart_window, 'trigger_regime_update'):
                logger.warning("❌ trigger_regime_analysis: Chart window has no trigger_regime_update method")
                print("[CEL] ❌ Chart window has no trigger_regime_update method", flush=True)
                return False

            # Trigger regime analysis (with immediate execution, no debounce, force=True)
            # force=True bypasses hash check to ensure detection always runs
            print("[CEL] 🔄 Triggering regime_update(debounce_ms=0, force=True)...", flush=True)
            chart_window.trigger_regime_update(debounce_ms=0, force=True)

            logger.info("✅ Regime analysis triggered successfully")
            print("[CEL] ✅ Regime analysis triggered successfully", flush=True)
            return True

        except Exception as e:
            logger.error(f"❌ Error triggering regime analysis: {e}", exc_info=True)
            print(f"[CEL] ❌ Error: {e}", flush=True)
            return False

    def _func_last_closed_regime(self) -> str:
        """Get regime of the last closed candle.

        Returns:
            Regime string (e.g., 'STRONG_BULL', 'BULL', 'SIDEWAYS', 'BEAR', 'STRONG_BEAR')
            Returns 'UNKNOWN' if data is not available.

        Priority order for reading regime:
        1. chart_window._last_closed_regime (set by trigger_regime_analysis())
        2. last_closed_candle.regime from context
        3. chart_data[-2].regime from context
        4. prev_regime from context
        5. 'UNKNOWN' as fallback

        Example:
            >>> # In CEL expression:
            >>> trigger_regime_analysis() && last_closed_regime() == 'STRONG_BULL'
            True
        """
        ctx = self._engine._last_context if self._engine else {}

        # Priority 1: Read from ChartWindow (set by trigger_regime_analysis())
        # This is the most up-to-date value after regime analysis runs
        # Note: RegimeDisplayMixin stores this in _last_regime_name
        if 'chart_window' in ctx:
            chart_window = ctx['chart_window']
            if hasattr(chart_window, '_last_regime_name'):
                regime = getattr(chart_window, '_last_regime_name', None)
                if regime and regime != 'UNKNOWN':
                    logger.debug(f"last_closed_regime: Read '{regime}' from chart_window._last_regime_name")
                    return str(regime)

        # Priority 2: Try to get from last_closed_candle object
        if 'last_closed_candle' in ctx:
            candle = ctx['last_closed_candle']
            if isinstance(candle, dict) and 'regime' in candle:
                regime = candle['regime']
                logger.debug(f"last_closed_regime: Read '{regime}' from last_closed_candle")
                return str(regime)

        # Priority 3: try to get from chart_data history
        if 'chart_data' in ctx:
            chart_data = ctx['chart_data']
            if isinstance(chart_data, list) and len(chart_data) >= 2:
                # Last closed candle is at index -2 (current candle at -1)
                last_closed = chart_data[-2]
                if isinstance(last_closed, dict) and 'regime' in last_closed:
                    regime = last_closed['regime']
                    logger.debug(f"last_closed_regime: Read '{regime}' from chart_data[-2]")
                    return str(regime)

        # Priority 4: check for prev_regime field
        if 'prev_regime' in ctx:
            regime = ctx['prev_regime']
            logger.debug(f"last_closed_regime: Read '{regime}' from prev_regime")
            return str(regime)

        # Default: unknown
        logger.warning("last_closed_regime: No regime data found, returning 'UNKNOWN'")
        return 'UNKNOWN'

    def _func_new_regime_detected(self) -> bool:
        """Check if a new regime was detected on the last closed candle.

        This function compares the previous regime with the current regime
        to detect regime changes (transitions).

        Returns:
            True if regime changed compared to previous candle,
            False if no change or data unavailable.

        Example:
            >>> # In CEL expression - only enter on regime change:
            >>> trigger_regime_analysis() && new_regime_detected() && last_closed_regime() == 'STRONG_BULL'
            True

            >>> # Enter on any STRONG_BULL, even without regime change:
            >>> trigger_regime_analysis() && last_closed_regime() == 'STRONG_BULL'
            True
        """
        ctx = self._engine._last_context if self._engine else {}

        # Get previous regime from context
        prev_regime = ctx.get('prev_regime', 'UNKNOWN')

        # Get current regime (uses the same priority logic)
        current_regime = self._func_last_closed_regime()

        # Detect change
        if prev_regime == 'UNKNOWN' or current_regime == 'UNKNOWN':
            # Can't detect change if either is unknown
            return False

        is_new = prev_regime != current_regime
        if is_new:
            logger.info(f"new_regime_detected: Regime changed from '{prev_regime}' to '{current_regime}'")

        return is_new

    # ========================================================================
    # Pattern / Breakout / SMC Helpers
    # ========================================================================

    def _get_context_value(self, key: str) -> Any:
        """Resolve a value from the last evaluation context.

        Supports both flat keys (e.g., "pattern.pin_bar_bullish")
        and nested dicts (e.g., context["pattern"]["pin_bar_bullish"]).
        """
        ctx = self._engine._last_context if self._engine else {}
        if key in ctx:
            return ctx.get(key)
        if "." in key:
            namespace, sub = key.split(".", 1)
            container = ctx.get(namespace)
            if isinstance(container, dict):
                return container.get(sub)
        return None

    def _context_flag(self, *keys: str) -> bool:
        """Return boolean flag for the first available key."""
        for key in keys:
            value = self._get_context_value(key)
            if value is not None:
                return bool(value)
        return False

    # Pattern functions
    def _func_pin_bar_bullish(self) -> bool:
        return self._context_flag(
            "pattern.pin_bar_bullish", "patterns.pin_bar_bullish", "pin_bar_bullish",
            "pattern.pin_bar", "patterns.pin_bar", "pin_bar"
        )

    def _func_pin_bar_bearish(self) -> bool:
        return self._context_flag(
            "pattern.pin_bar_bearish", "patterns.pin_bar_bearish", "pin_bar_bearish",
            "pattern.pin_bar", "patterns.pin_bar", "pin_bar"
        )

    def _func_inside_bar(self) -> bool:
        return self._context_flag("pattern.inside_bar", "patterns.inside_bar", "inside_bar")

    def _func_inverted_hammer(self) -> bool:
        return self._context_flag("pattern.inverted_hammer", "patterns.inverted_hammer", "inverted_hammer")

    def _func_bull_flag(self) -> bool:
        return self._context_flag("pattern.bull_flag", "patterns.bull_flag", "bull_flag")

    def _func_bear_flag(self) -> bool:
        return self._context_flag("pattern.bear_flag", "patterns.bear_flag", "bear_flag")

    def _func_cup_and_handle(self) -> bool:
        return self._context_flag("pattern.cup_and_handle", "patterns.cup_and_handle", "cup_and_handle")

    def _func_double_bottom(self) -> bool:
        return self._context_flag("pattern.double_bottom", "patterns.double_bottom", "double_bottom")

    def _func_double_top(self) -> bool:
        return self._context_flag("pattern.double_top", "patterns.double_top", "double_top")

    def _func_ascending_triangle(self) -> bool:
        return self._context_flag("pattern.ascending_triangle", "patterns.ascending_triangle", "ascending_triangle")

    def _func_descending_triangle(self) -> bool:
        return self._context_flag("pattern.descending_triangle", "patterns.descending_triangle", "descending_triangle")

    # Breakout functions
    def _func_breakout_above(self) -> bool:
        return self._context_flag("breakout.breakout_above", "pattern.breakout_above", "breakout_above")

    def _func_breakdown_below(self) -> bool:
        return self._context_flag("breakout.breakdown_below", "pattern.breakdown_below", "breakdown_below")

    def _func_false_breakout(self) -> bool:
        return self._context_flag("breakout.false_breakout", "pattern.false_breakout", "false_breakout")

    def _func_break_of_structure(self) -> bool:
        return self._context_flag("breakout.break_of_structure", "pattern.break_of_structure", "break_of_structure")

    # Smart Money Concepts
    def _func_liquidity_swept(self) -> bool:
        return self._context_flag("smc.liquidity_swept", "pattern.liquidity_swept", "liquidity_swept")

    def _func_fvg_exists(self) -> bool:
        return self._context_flag("smc.fvg_exists", "pattern.fvg_exists", "fvg_exists")

    def _func_order_block_retest(self) -> bool:
        return self._context_flag("smc.order_block_retest", "pattern.order_block_retest", "order_block_retest")

    def _func_harmonic_pattern_detected(self) -> bool:
        return self._context_flag(
            "smc.harmonic_pattern_detected", "pattern.harmonic_pattern_detected", "harmonic_pattern_detected"
        )

