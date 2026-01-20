"""Partial Pattern Matcher for Early Signal Detection.

Matches incomplete patterns (e.g., 10/20 bars) against completed historical patterns
to provide early entry signals before the full pattern completes.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

from src.core.market_data.types import HistoricalBar
from .extractor import PatternExtractor, Pattern
from .qdrant_client import TradingPatternDB, PatternMatch

logger = logging.getLogger(__name__)


@dataclass
class PartialPatternAnalysis:
    """Analysis result from partial pattern matching."""

    # Partial pattern info
    bars_formed: int
    bars_required: int
    completion_ratio: float  # 0-1

    # Match statistics (confidence-adjusted)
    similar_patterns_count: int
    win_rate: float  # 0-1
    avg_return: float
    confidence: float  # Adjusted for partial completion

    # Best matches
    best_matches: list[PatternMatch]

    # Recommendation
    signal_boost: float  # -1 to +1
    recommendation: str
    early_entry_opportunity: bool  # True if high confidence despite incomplete

    # Details
    avg_similarity_score: float
    completion_penalty: float  # How much confidence was reduced
    projection_method: str  # "zero_pad", "last_value", "trend_projection"


class PartialPatternMatcher:
    """Matches partial/incomplete patterns against completed historical patterns.

    Use Cases:
    - Early entry detection (e.g., 50% pattern completion)
    - Progressive confirmation as pattern develops
    - Exit signal refinement
    """

    def __init__(
        self,
        full_window_size: int = 20,
        min_bars_required: int = 10,  # Minimum 50% completion
        confidence_penalty_alpha: float = 0.7,  # Penalty exponent (< 1 = penalty)
        projection_method: str = "trend_projection",  # "zero_pad", "last_value", "trend_projection"
    ):
        """Initialize partial pattern matcher.

        Args:
            full_window_size: Full pattern window size (e.g., 20 bars)
            min_bars_required: Minimum bars needed for matching (e.g., 10 = 50%)
            confidence_penalty_alpha: Exponent for confidence penalty (< 1 reduces confidence for partial)
            projection_method: How to project missing bars ("zero_pad", "last_value", "trend_projection")
        """
        self.full_window_size = full_window_size
        self.min_bars_required = min_bars_required
        self.confidence_penalty_alpha = confidence_penalty_alpha
        self.projection_method = projection_method

        self.extractor = PatternExtractor(window_size=full_window_size)
        self.db = TradingPatternDB()

    async def initialize(self) -> bool:
        """Initialize database connection.

        Returns:
            True if successful
        """
        return await self.db.initialize()

    async def analyze_partial_signal(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
        signal_direction: str = "long",
        cross_symbol_search: bool = True,
        similarity_threshold: float = 0.70,  # Lower than full pattern (0.75)
    ) -> Optional[PartialPatternAnalysis]:
        """Analyze a trading signal using partial pattern matching.

        Args:
            bars: Recent bars (can be < full_window_size)
            symbol: Trading symbol
            timeframe: Timeframe string
            signal_direction: Expected trade direction
            cross_symbol_search: Search across all symbols
            similarity_threshold: Minimum similarity score for matches

        Returns:
            PartialPatternAnalysis or None if not enough bars
        """
        bars_count = len(bars)

        # Validate minimum bars
        if bars_count < self.min_bars_required:
            logger.warning(
                f"Not enough bars for partial matching: {bars_count} < {self.min_bars_required}"
            )
            return None

        # Calculate completion ratio
        completion_ratio = min(bars_count / self.full_window_size, 1.0)

        logger.info(
            f"Partial pattern matching: {bars_count}/{self.full_window_size} bars "
            f"({completion_ratio:.1%} complete)"
        )

        try:
            # Project partial pattern to full size
            projected_pattern = self._project_partial_pattern(
                bars=bars,
                symbol=symbol,
                timeframe=timeframe,
            )

            if not projected_pattern:
                logger.warning("Failed to project partial pattern")
                return None

            # Search for similar completed patterns
            expected_trend = "up" if signal_direction == "long" else "down"

            similar = await self.db.search_similar(
                pattern=projected_pattern,
                limit=50,
                symbol_filter=None if cross_symbol_search else symbol,
                timeframe_filter=timeframe,
                trend_filter=expected_trend,
                score_threshold=similarity_threshold,
            )

            # Fallback: search without trend filter if not enough matches
            if len(similar) < 5:
                similar = await self.db.search_similar(
                    pattern=projected_pattern,
                    limit=50,
                    symbol_filter=None if cross_symbol_search else symbol,
                    timeframe_filter=timeframe,
                    trend_filter=None,
                    score_threshold=similarity_threshold - 0.1,
                )

            # Calculate statistics with confidence adjustment
            stats = await self.db.get_pattern_statistics(similar)

            # Adjust confidence based on completion ratio
            base_confidence = self._calculate_base_confidence(
                count=len(similar),
                avg_score=stats.get("avg_score", 0),
            )

            # Apply completion penalty: confidence = base_confidence * (completion_ratio ^ alpha)
            # Example: 50% completion with alpha=0.7 → penalty factor = 0.5^0.7 ≈ 0.62
            completion_penalty_factor = completion_ratio ** self.confidence_penalty_alpha
            adjusted_confidence = base_confidence * completion_penalty_factor

            # Calculate signal boost (similar to full pattern, but adjusted)
            signal_boost, recommendation = self._calculate_signal_boost(
                win_rate=stats.get("win_rate", 0.5),
                avg_return=stats.get("avg_return", 0),
                confidence=adjusted_confidence,
                matches=similar,
                expected_trend=expected_trend,
            )

            # Early entry opportunity: high confidence despite incomplete pattern
            early_entry_opportunity = (
                completion_ratio < 0.9
                and adjusted_confidence > 0.5
                and signal_boost > 0.4
                and len(similar) >= 10
            )

            return PartialPatternAnalysis(
                bars_formed=bars_count,
                bars_required=self.full_window_size,
                completion_ratio=completion_ratio,
                similar_patterns_count=len(similar),
                win_rate=stats.get("win_rate", 0.5),
                avg_return=stats.get("avg_return", 0),
                confidence=adjusted_confidence,
                best_matches=similar[:5],
                signal_boost=signal_boost,
                recommendation=recommendation,
                early_entry_opportunity=early_entry_opportunity,
                avg_similarity_score=stats.get("avg_score", 0),
                completion_penalty=1.0 - completion_penalty_factor,
                projection_method=self.projection_method,
            )

        except Exception as e:
            logger.error(f"Error analyzing partial signal: {e}")
            return None

    def _project_partial_pattern(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
    ) -> Optional[Pattern]:
        """Project partial pattern to full window size.

        Args:
            bars: Partial bars
            symbol: Trading symbol
            timeframe: Timeframe string

        Returns:
            Projected Pattern or None
        """
        bars_count = len(bars)
        missing_bars = self.full_window_size - bars_count

        if missing_bars <= 0:
            # Already full or over - just use most recent window
            return self.extractor.extract_current_pattern(
                bars=bars,
                symbol=symbol,
                timeframe=timeframe,
            )

        # Sort bars
        sorted_bars = sorted(bars, key=lambda b: b.timestamp)

        # Project based on selected method
        if self.projection_method == "zero_pad":
            projected_bars = self._zero_pad(sorted_bars, missing_bars)
        elif self.projection_method == "last_value":
            projected_bars = self._repeat_last_value(sorted_bars, missing_bars)
        elif self.projection_method == "trend_projection":
            projected_bars = self._trend_projection(sorted_bars, missing_bars)
        else:
            logger.warning(f"Unknown projection method: {self.projection_method}, using trend_projection")
            projected_bars = self._trend_projection(sorted_bars, missing_bars)

        # Create pattern from projected bars
        return self.extractor.extract_current_pattern(
            bars=projected_bars,
            symbol=symbol,
            timeframe=timeframe,
        )

    def _zero_pad(
        self,
        bars: list[HistoricalBar],
        missing_bars: int,
    ) -> list[HistoricalBar]:
        """Pad with zero-price bars (simplest, but loses info).

        Args:
            bars: Existing bars
            missing_bars: Number of bars to pad

        Returns:
            Padded bars
        """
        last_bar = bars[-1]
        last_time = last_bar.timestamp

        # Create zero bars (all prices = last close to maintain normalization)
        zero_bars = []
        for i in range(1, missing_bars + 1):
            # Use last close for all OHLC (effectively flat continuation)
            zero_bar = HistoricalBar(
                timestamp=last_time,  # Keep same timestamp (won't be used for matching)
                open=last_bar.close,
                high=last_bar.close,
                low=last_bar.close,
                close=last_bar.close,
                volume=0,
            )
            zero_bars.append(zero_bar)

        return bars + zero_bars

    def _repeat_last_value(
        self,
        bars: list[HistoricalBar],
        missing_bars: int,
    ) -> list[HistoricalBar]:
        """Repeat last bar values (assumes price stays flat).

        Args:
            bars: Existing bars
            missing_bars: Number of bars to repeat

        Returns:
            Extended bars
        """
        last_bar = bars[-1]

        repeated_bars = []
        for i in range(missing_bars):
            repeated_bar = HistoricalBar(
                timestamp=last_bar.timestamp,
                open=last_bar.close,
                high=last_bar.close,
                low=last_bar.close,
                close=last_bar.close,
                volume=last_bar.volume,
            )
            repeated_bars.append(repeated_bar)

        return bars + repeated_bars

    def _trend_projection(
        self,
        bars: list[HistoricalBar],
        missing_bars: int,
    ) -> list[HistoricalBar]:
        """Project trend forward using linear regression.

        Args:
            bars: Existing bars
            missing_bars: Number of bars to project

        Returns:
            Extended bars with trend projection
        """
        # Calculate linear trend from existing bars
        closes = np.array([float(b.close) for b in bars])
        x = np.arange(len(closes))

        # Linear fit: y = slope * x + intercept
        if len(x) > 1:
            slope, intercept = np.polyfit(x, closes, 1)
        else:
            slope, intercept = 0, closes[0]

        # Project forward
        projected_bars = []
        last_bar = bars[-1]
        last_close = float(last_bar.close)

        for i in range(1, missing_bars + 1):
            # Project close price
            projected_close = slope * (len(closes) + i) + intercept

            # Calculate realistic OHLC based on recent volatility
            recent_volatility = np.std(closes[-5:]) if len(closes) >= 5 else 0.01 * last_close

            projected_high = projected_close + recent_volatility * 0.5
            projected_low = projected_close - recent_volatility * 0.5
            projected_open = last_close

            projected_bar = HistoricalBar(
                timestamp=last_bar.timestamp,
                open=projected_open,
                high=projected_high,
                low=projected_low,
                close=projected_close,
                volume=last_bar.volume,  # Keep volume constant
            )

            projected_bars.append(projected_bar)
            last_close = projected_close

        return bars + projected_bars

    def _calculate_base_confidence(
        self,
        count: int,
        avg_score: float,
    ) -> float:
        """Calculate base confidence before completion penalty.

        Args:
            count: Number of matches
            avg_score: Average similarity score

        Returns:
            Base confidence (0-1)
        """
        # Count factor: more matches = higher confidence (max at 20+ matches)
        count_factor = min(count / 20, 1.0)

        # Score factor: higher similarity = higher confidence
        score_factor = avg_score if avg_score > 0 else 0.5

        # Combined confidence
        base_confidence = count_factor * score_factor

        return base_confidence

    def _calculate_signal_boost(
        self,
        win_rate: float,
        avg_return: float,
        confidence: float,
        matches: list[PatternMatch],
        expected_trend: str,
    ) -> tuple[float, str]:
        """Calculate signal boost and recommendation.

        Args:
            win_rate: Win rate from matches
            avg_return: Average return from matches
            confidence: Adjusted confidence
            matches: Pattern matches
            expected_trend: Expected trend direction

        Returns:
            Tuple of (signal_boost, recommendation)
        """
        count = len(matches)

        if count < 5:
            return 0.0, "insufficient_data"

        # Calculate trend consistency
        matching_trend = sum(1 for m in matches if m.trend_direction == expected_trend)
        trend_consistency = matching_trend / count if count > 0 else 0

        # Base boost from win rate
        win_rate_boost = (win_rate - 0.5) * 2  # -1 to +1

        # Trend boost
        trend_boost = (trend_consistency - 0.5) * 0.5  # -0.25 to +0.25

        # Return boost
        return_boost = max(min(avg_return / 2, 0.25), -0.25)

        # Combined boost
        signal_boost = win_rate_boost * 0.6 + trend_boost * 0.25 + return_boost * 0.15
        signal_boost = max(min(signal_boost, 1.0), -1.0)

        # Recommendation
        if confidence < 0.3:
            recommendation = "low_confidence"
        elif signal_boost > 0.3:
            recommendation = "partial_buy" if signal_boost > 0.6 else "partial_watch"
        elif signal_boost < -0.3:
            recommendation = "partial_avoid" if signal_boost < -0.6 else "partial_caution"
        else:
            recommendation = "partial_neutral"

        return signal_boost, recommendation
