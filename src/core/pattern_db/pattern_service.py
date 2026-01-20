"""Pattern Service for Bot Integration.

Provides pattern-based signal validation for the trading bot.
Uses similar historical patterns to estimate win probability.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from src.core.market_data.types import HistoricalBar
from .extractor import PatternExtractor, Pattern
from .qdrant_client import TradingPatternDB, PatternMatch
from .timeframe_converter import TimeframeConverter
from .partial_matcher import PartialPatternMatcher, PartialPatternAnalysis

logger = logging.getLogger(__name__)


@dataclass
class PatternAnalysis:
    """Analysis result from pattern matching."""

    # Match statistics
    similar_patterns_count: int
    win_rate: float  # 0-1
    avg_return: float  # Expected return %
    confidence: float  # 0-1 based on match count and score

    # Best matches
    best_matches: list[PatternMatch]

    # Recommendation
    signal_boost: float  # -1 to +1, positive = boost signal, negative = reduce
    recommendation: str  # "strong_buy", "buy", "neutral", "avoid", "strong_avoid"

    # Details
    avg_similarity_score: float
    trend_consistency: float  # How consistent is trend direction


class PatternService:
    """Service for pattern-based signal validation.

    Integrates with the trading bot to validate entry signals
    by comparing current patterns with historical outcomes.
    """

    def __init__(
        self,
        window_size: int = 20,
        min_similar_patterns: int = 5,
        min_win_rate_boost: float = 0.6,
        similarity_threshold: float = 0.75,
    ):
        """Initialize pattern service.

        Args:
            window_size: Pattern window size
            min_similar_patterns: Minimum patterns needed for valid analysis
            min_win_rate_boost: Win rate threshold for positive boost
            similarity_threshold: Minimum similarity score for matches
        """
        self.window_size = window_size
        self.min_similar_patterns = min_similar_patterns
        self.min_win_rate_boost = min_win_rate_boost
        self.similarity_threshold = similarity_threshold

        self.extractor = PatternExtractor(window_size=window_size)
        self.db = TradingPatternDB()

        # Phase 3: Partial Pattern Matching
        self.partial_matcher = PartialPatternMatcher(
            full_window_size=window_size,
            min_bars_required=window_size // 2,  # Minimum 50% completion
            confidence_penalty_alpha=0.7,  # Confidence penalty for partial patterns
            projection_method="trend_projection",  # Use trend projection for best results
        )

        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize the service (connect to Qdrant).

        Returns:
            True if successful
        """
        try:
            self._initialized = await self.db.initialize()

            # Phase 3: Initialize partial matcher
            await self.partial_matcher.initialize()

            if self._initialized:
                info = await self.db.get_collection_info()
                logger.info(f"PatternService initialized: {info.get('points_count', 0)} patterns")
                logger.info("Partial pattern matching enabled (min 50% completion)")
            return self._initialized
        except Exception as e:
            logger.error(f"Failed to initialize PatternService: {e}")
            return False

    async def analyze_signal(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
        signal_direction: str = "long",  # "long" or "short"
        cross_symbol_search: bool = True,
        target_timeframe: Optional[str] = None,  # NEW: Target timeframe for resampling
    ) -> Optional[PatternAnalysis]:
        """Analyze a trading signal using pattern matching.

        Args:
            bars: Recent bars (at least window_size)
            symbol: Trading symbol
            timeframe: Timeframe string (source timeframe of bars)
            signal_direction: Expected trade direction
            cross_symbol_search: Search across all symbols (recommended)
            target_timeframe: Optional target timeframe for resampling (e.g., "5m", "15m", "1h")
                             If None, uses source timeframe without resampling

        Returns:
            PatternAnalysis or None if not enough data
        """
        if not self._initialized:
            await self.initialize()

        # NEW: Timeframe conversion if requested
        analysis_bars = bars
        analysis_timeframe = timeframe

        if target_timeframe and target_timeframe != timeframe:
            logger.info(f"Resampling bars from {timeframe} → {target_timeframe}")

            # Check if conversion is possible
            can_convert, reason = TimeframeConverter.can_convert(timeframe, target_timeframe)

            if not can_convert:
                logger.warning(f"Cannot convert {timeframe} → {target_timeframe}: {reason}")
                return None

            # Resample bars
            try:
                analysis_bars = TimeframeConverter.resample_bars(
                    bars=bars,
                    from_timeframe=timeframe,
                    to_timeframe=target_timeframe,
                )
                analysis_timeframe = target_timeframe

                logger.info(
                    f"Resampled {len(bars)} bars ({timeframe}) → "
                    f"{len(analysis_bars)} bars ({target_timeframe})"
                )

            except Exception as e:
                logger.error(f"Failed to resample bars: {e}")
                return None

        # Check if enough bars after resampling
        if len(analysis_bars) < self.window_size:
            logger.warning(
                f"Not enough bars for pattern analysis after resampling: "
                f"{len(analysis_bars)} < {self.window_size}"
            )
            return None

        try:
            # Extract current pattern (using resampled bars if applicable)
            current_pattern = self.extractor.extract_current_pattern(
                bars=analysis_bars,
                symbol=symbol,
                timeframe=analysis_timeframe,
            )

            if not current_pattern:
                logger.warning("Failed to extract current pattern")
                return None

            # Expected trend based on signal direction
            expected_trend = "up" if signal_direction == "long" else "down"

            # Search for similar patterns
            # First try with trend filter for more relevant matches
            similar = await self.db.search_similar(
                pattern=current_pattern,
                limit=50,
                symbol_filter=None if cross_symbol_search else symbol,
                timeframe_filter=timeframe,
                trend_filter=expected_trend,
                score_threshold=self.similarity_threshold,
            )

            # If not enough, search without trend filter
            if len(similar) < self.min_similar_patterns:
                similar = await self.db.search_similar(
                    pattern=current_pattern,
                    limit=50,
                    symbol_filter=None if cross_symbol_search else symbol,
                    timeframe_filter=timeframe,
                    trend_filter=None,  # No trend filter
                    score_threshold=self.similarity_threshold - 0.1,  # Lower threshold
                )

            # Calculate statistics
            stats = await self.db.get_pattern_statistics(similar)

            # Calculate signal boost and recommendation
            analysis = self._calculate_analysis(
                matches=similar,
                stats=stats,
                signal_direction=signal_direction,
                current_pattern=current_pattern,
            )

            return analysis

        except Exception as e:
            logger.error(f"Error analyzing signal: {e}")
            return None

    def _calculate_analysis(
        self,
        matches: list[PatternMatch],
        stats: dict,
        signal_direction: str,
        current_pattern: Pattern,
    ) -> PatternAnalysis:
        """Calculate analysis from matched patterns.

        Args:
            matches: Similar pattern matches
            stats: Statistics from matches
            signal_direction: Expected trade direction
            current_pattern: Current pattern

        Returns:
            PatternAnalysis object
        """
        count = stats.get("count", 0)
        win_rate = stats.get("win_rate", 0.5)
        avg_return = stats.get("avg_return", 0)
        avg_score = stats.get("avg_score", 0)

        # Calculate confidence based on match count and score
        count_factor = min(count / 20, 1.0)  # Max confidence at 20+ matches
        score_factor = avg_score if avg_score > 0 else 0.5
        confidence = count_factor * score_factor

        # Calculate trend consistency
        expected_trend = "up" if signal_direction == "long" else "down"
        matching_trend = sum(1 for m in matches if m.trend_direction == expected_trend)
        trend_consistency = matching_trend / count if count > 0 else 0

        # Calculate signal boost
        # Positive boost if: high win rate + consistent trend + good confidence
        if count < self.min_similar_patterns:
            # Not enough data - neutral
            signal_boost = 0
            recommendation = "insufficient_data"
        else:
            # Base boost from win rate (center at 0.5)
            win_rate_boost = (win_rate - 0.5) * 2  # -1 to +1

            # Adjust by trend consistency
            trend_boost = (trend_consistency - 0.5) * 0.5  # -0.25 to +0.25

            # Adjust by return magnitude
            return_boost = max(min(avg_return / 2, 0.25), -0.25)  # Cap at ±0.25

            # Combined boost
            signal_boost = win_rate_boost * 0.6 + trend_boost * 0.25 + return_boost * 0.15
            signal_boost = max(min(signal_boost, 1.0), -1.0)  # Clamp to ±1

            # Recommendation based on boost and confidence
            if confidence < 0.3:
                recommendation = "low_confidence"
            elif signal_boost > 0.3:
                recommendation = "strong_buy" if signal_boost > 0.6 else "buy"
            elif signal_boost < -0.3:
                recommendation = "strong_avoid" if signal_boost < -0.6 else "avoid"
            else:
                recommendation = "neutral"

        return PatternAnalysis(
            similar_patterns_count=count,
            win_rate=win_rate,
            avg_return=avg_return,
            confidence=confidence,
            best_matches=matches[:5],  # Top 5 matches
            signal_boost=signal_boost,
            recommendation=recommendation,
            avg_similarity_score=avg_score,
            trend_consistency=trend_consistency,
        )

    async def get_quick_validation(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
        signal_direction: str = "long",
    ) -> tuple[float, str]:
        """Quick validation returning just boost and recommendation.

        Args:
            bars: Recent bars
            symbol: Trading symbol
            timeframe: Timeframe string
            signal_direction: Expected trade direction

        Returns:
            Tuple of (signal_boost, recommendation)
        """
        analysis = await self.analyze_signal(
            bars=bars,
            symbol=symbol,
            timeframe=timeframe,
            signal_direction=signal_direction,
        )

        if analysis:
            return analysis.signal_boost, analysis.recommendation
        return 0.0, "error"

    async def analyze_partial_signal(
        self,
        bars: list[HistoricalBar],
        symbol: str,
        timeframe: str,
        signal_direction: str = "long",
        cross_symbol_search: bool = True,
        target_timeframe: Optional[str] = None,
    ) -> Optional[PartialPatternAnalysis]:
        """Analyze a signal using partial pattern matching (Phase 3).

        Enables early entry detection by matching incomplete patterns (e.g., 10/20 bars)
        against completed historical patterns.

        Args:
            bars: Recent bars (can be < window_size, min 50% required)
            symbol: Trading symbol
            timeframe: Timeframe string (source timeframe of bars)
            signal_direction: Expected trade direction ("long" or "short")
            cross_symbol_search: Search across all symbols (recommended)
            target_timeframe: Optional target timeframe for resampling

        Returns:
            PartialPatternAnalysis or None if insufficient data

        Example:
            >>> # Early entry with 15 bars (75% complete)
            >>> analysis = await service.analyze_partial_signal(
            ...     bars=recent_15_bars,
            ...     symbol="BTCUSDT",
            ...     timeframe="1m",
            ...     signal_direction="long"
            ... )
            >>> if analysis and analysis.early_entry_opportunity:
            ...     print(f"Early entry at {analysis.completion_ratio:.1%} completion")
            ...     print(f"Confidence: {analysis.confidence:.2f}")
            ...     print(f"Signal boost: {analysis.signal_boost:+.2f}")
        """
        if not self._initialized:
            await self.initialize()

        # NEW: Timeframe conversion if requested
        analysis_bars = bars
        analysis_timeframe = timeframe

        if target_timeframe and target_timeframe != timeframe:
            logger.info(f"Resampling bars from {timeframe} → {target_timeframe}")

            # Check if conversion is possible
            can_convert, reason = TimeframeConverter.can_convert(timeframe, target_timeframe)

            if not can_convert:
                logger.warning(f"Cannot convert {timeframe} → {target_timeframe}: {reason}")
                return None

            # Resample bars
            try:
                analysis_bars = TimeframeConverter.resample_bars(
                    bars=bars,
                    from_timeframe=timeframe,
                    to_timeframe=target_timeframe,
                )
                analysis_timeframe = target_timeframe

                logger.info(
                    f"Resampled {len(bars)} bars ({timeframe}) → "
                    f"{len(analysis_bars)} bars ({target_timeframe})"
                )

            except Exception as e:
                logger.error(f"Failed to resample bars: {e}")
                return None

        # Delegate to partial matcher
        return await self.partial_matcher.analyze_partial_signal(
            bars=analysis_bars,
            symbol=symbol,
            timeframe=analysis_timeframe,
            signal_direction=signal_direction,
            cross_symbol_search=cross_symbol_search,
        )


# Global service instance
_pattern_service: Optional[PatternService] = None


async def get_pattern_service() -> PatternService:
    """Get or create the global pattern service instance.

    Returns:
        Initialized PatternService
    """
    global _pattern_service
    if _pattern_service is None:
        _pattern_service = PatternService()
        await _pattern_service.initialize()
    return _pattern_service
