"""Data Preflight Service - Refactored Main Orchestrator.

Refactored from 798 LOC monolith using composition pattern.

Module 5/5 - Main Orchestrator.

Delegates to 4 specialized helper modules:
- DataPreflightBasicChecks: Index, Minimum Data, Freshness
- DataPreflightPriceVolume: Prices, Volume
- DataPreflightQuality: Outliers, Gaps, Data Cleaning

Provides:
- DataPreflightService.run_preflight(): Main orchestration method
- Convenience functions: run_preflight(), quick_validate()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import pandas as pd

from src.core.trading_bot.data_preflight_state import (
    IssueType,
    IssueSeverity,
    PreflightConfig,
    PreflightIssue,
    PreflightResult,
    PreflightStatus,
)
from src.core.trading_bot.data_preflight_basic_checks import DataPreflightBasicChecks
from src.core.trading_bot.data_preflight_price_volume import DataPreflightPriceVolume
from src.core.trading_bot.data_preflight_quality import DataPreflightQuality

if TYPE_CHECKING:
    from src.core.market_data.bar_validator import BarValidator

logger = logging.getLogger(__name__)


# =============================================================================
# PREFLIGHT SERVICE
# =============================================================================


class DataPreflightService:
    """
    Zentraler Service für Datenqualitätsprüfung.

    Wird von Trading-Engine, AI Popup und Chatbot verwendet.

    Usage:
        service = DataPreflightService()
        result = service.run_preflight(df, symbol="BTCUSD", timeframe="5m")
        if result.is_tradeable:
            # Proceed with trading
        else:
            # Show error to user
    """

    def __init__(self, config: PreflightConfig | None = None):
        self.config = config or PreflightConfig()
        self._bar_validator: BarValidator | None = None

        # Instantiate helper modules (composition pattern)
        self._basic_checks = DataPreflightBasicChecks(parent=self)
        self._price_volume = DataPreflightPriceVolume(parent=self)
        self._quality = DataPreflightQuality(parent=self)

    def run_preflight(
        self,
        df: pd.DataFrame | None,
        symbol: str,
        timeframe: str = "5m",
        clean_data: bool = True,
    ) -> PreflightResult:
        """
        Führt vollständige Preflight-Prüfung durch.

        Orchestrates 8 check steps:
            1. Empty/None check
            2. Index validation (delegates to _basic_checks)
            3. Minimum data check (delegates to _basic_checks)
            4. Freshness check (delegates to _basic_checks)
            5. Price validation (delegates to _price_volume)
            6. Volume check (delegates to _price_volume)
            7. Outlier detection (delegates to _quality)
            8. Gap detection (delegates to _quality)

        Args:
            df: DataFrame mit OHLCV-Daten
            symbol: Trading-Symbol
            timeframe: Timeframe (z.B. "5m", "1h")
            clean_data: Daten bereinigen falls möglich

        Returns:
            PreflightResult mit Status und Issues
        """
        issues: list[PreflightIssue] = []
        quality_score = 100

        # 1. Empty/None Check
        if df is None or df.empty:
            return PreflightResult(
                status=PreflightStatus.FAILED,
                symbol=symbol,
                timeframe=timeframe,
                issues=[
                    PreflightIssue(
                        issue_type=IssueType.EMPTY_DATA,
                        severity=IssueSeverity.CRITICAL,
                        message="DataFrame is empty or None",
                    )
                ],
                quality_score=0,
            )

        # 2. Index Validation (delegates to _basic_checks)
        index_issues = self._basic_checks.check_index(df)
        issues.extend(index_issues)
        if any(i.severity == IssueSeverity.CRITICAL for i in index_issues):
            return PreflightResult(
                status=PreflightStatus.FAILED,
                symbol=symbol,
                timeframe=timeframe,
                issues=issues,
                data_rows=len(df),
                quality_score=0,
            )

        # 3. Minimum Data Check (delegates to _basic_checks)
        min_data_issues = self._basic_checks.check_minimum_data(df)
        issues.extend(min_data_issues)
        if any(i.severity == IssueSeverity.CRITICAL for i in min_data_issues):
            quality_score -= self.config.insufficient_data_penalty

        # 4. Freshness Check (delegates to _basic_checks)
        interval_minutes = self._parse_timeframe(timeframe)
        freshness_issues, freshness_seconds = self._basic_checks.check_freshness(
            df, interval_minutes
        )
        issues.extend(freshness_issues)
        if freshness_issues:
            quality_score -= self.config.stale_data_penalty

        # 5. Price Validation (delegates to _price_volume)
        price_issues = self._price_volume.check_prices(df)
        issues.extend(price_issues)

        # 6. Volume Check (delegates to _price_volume)
        volume_issues, zero_count = self._price_volume.check_volume(df)
        issues.extend(volume_issues)
        if zero_count > 0:
            quality_score -= self.config.zero_volume_penalty * min(zero_count, 3)

        # 7. Outlier Detection (delegates to _quality)
        outlier_issues, outlier_count = self._quality.check_outliers(df)
        issues.extend(outlier_issues)
        if outlier_count > 0:
            quality_score -= self.config.outlier_penalty * min(outlier_count, 5)

        # 8. Gap Detection (delegates to _quality)
        gap_issues, gap_count = self._quality.check_gaps(df, interval_minutes)
        issues.extend(gap_issues)
        if gap_count > 0:
            quality_score -= self.config.gap_penalty * min(gap_count, 5)

        # Clean Data if requested (delegates to _quality)
        cleaned_df = None
        if clean_data and outlier_count > 0:
            cleaned_df = self._quality.clean_data(df)

        # Determine final status
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        if critical_count > 0:
            status = PreflightStatus.FAILED
        elif warning_count > 0:
            status = PreflightStatus.WARNING
        else:
            status = PreflightStatus.PASSED

        # Clamp quality score
        quality_score = max(0, min(100, quality_score))

        result = PreflightResult(
            status=status,
            symbol=symbol,
            timeframe=timeframe,
            issues=issues,
            data_rows=len(df),
            data_freshness_seconds=freshness_seconds,
            zero_volume_count=zero_count,
            outlier_count=outlier_count,
            gap_count=gap_count,
            quality_score=quality_score,
            cleaned_df=cleaned_df if clean_data else None,
        )

        # Log result
        if status == PreflightStatus.FAILED:
            logger.warning(
                f"Preflight FAILED for {symbol}/{timeframe}: {result.get_summary()}"
            )
        elif status == PreflightStatus.WARNING:
            logger.info(
                f"Preflight WARNING for {symbol}/{timeframe}: {len(issues)} issues"
            )
        else:
            logger.debug(f"Preflight PASSED for {symbol}/{timeframe}")

        return result

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    @staticmethod
    def _parse_timeframe(timeframe: str) -> int:
        """
        Parst Timeframe-String zu Minuten.

        Args:
            timeframe: z.B. "5m", "1h", "4h", "1d"

        Returns:
            Minuten als Integer
        """
        timeframe = timeframe.lower().strip()

        multipliers = {
            "m": 1,
            "min": 1,
            "h": 60,
            "hour": 60,
            "d": 1440,
            "day": 1440,
            "w": 10080,
            "week": 10080,
        }

        for suffix, mult in multipliers.items():
            if timeframe.endswith(suffix):
                try:
                    num = int(timeframe[: -len(suffix)])
                    return num * mult
                except ValueError:
                    pass

        # Default fallback
        return 5


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================


def run_preflight(
    df: pd.DataFrame | None,
    symbol: str,
    timeframe: str = "5m",
    config: PreflightConfig | None = None,
) -> PreflightResult:
    """
    Convenience-Funktion für Preflight-Check.

    Usage:
        result = run_preflight(df, "BTCUSD", "5m")
        if result.is_tradeable:
            proceed()
    """
    service = DataPreflightService(config)
    return service.run_preflight(df, symbol, timeframe)


def quick_validate(
    df: pd.DataFrame | None,
    symbol: str = "UNKNOWN",
    min_rows: int = 50,
) -> tuple[bool, str]:
    """
    Schnelle Validierung ohne volles Preflight.

    Returns:
        Tuple von (is_valid, error_message)
    """
    if df is None or df.empty:
        return False, "DataFrame is empty or None"

    if not isinstance(df.index, pd.DatetimeIndex):
        return False, "DataFrame index is not DatetimeIndex"

    if len(df) < min_rows:
        return False, f"Insufficient data: {len(df)} rows (min: {min_rows})"

    return True, ""


# Re-export für backward compatibility
__all__ = [
    "DataPreflightService",
    "run_preflight",
    "quick_validate",
]
