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


# PREFLIGHT SERVICE
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
        # Validate DataFrame
        early_failure = self._check_dataframe_validity(df, symbol, timeframe)
        if early_failure:
            return early_failure

        # Run all checks
        check_results = self._run_all_checks(df, timeframe)

        # Calculate quality score
        quality_score = self._calculate_quality_score(check_results)

        # Clean data if needed
        cleaned_df = self._clean_data_if_needed(
            df, check_results["outlier_count"], clean_data
        )

        # Build and log result
        result = self._build_result(
            check_results, quality_score, cleaned_df, symbol, timeframe, df
        )
        self._log_result(result, symbol, timeframe)

        return result

    def _check_dataframe_validity(
        self, df: pd.DataFrame | None, symbol: str, timeframe: str
    ) -> PreflightResult | None:
        """Check basic DataFrame validity.

        Returns:
            PreflightResult if invalid, None if valid.
        """
        # Empty/None check
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

        # Index validation
        index_issues = self._basic_checks.check_index(df)
        if any(i.severity == IssueSeverity.CRITICAL for i in index_issues):
            return PreflightResult(
                status=PreflightStatus.FAILED,
                symbol=symbol,
                timeframe=timeframe,
                issues=index_issues,
                data_rows=len(df),
                quality_score=0,
            )

        return None

    def _run_all_checks(
        self, df: pd.DataFrame, timeframe: str
    ) -> dict:
        """Run all data quality checks.

        Returns:
            Dictionary with all check results.
        """
        interval_minutes = self._parse_timeframe(timeframe)
        issues = []

        # Minimum data check
        min_data_issues = self._basic_checks.check_minimum_data(df)
        issues.extend(min_data_issues)

        # Freshness check
        freshness_issues, freshness_seconds = self._basic_checks.check_freshness(
            df, interval_minutes
        )
        issues.extend(freshness_issues)

        # Price validation
        price_issues = self._price_volume.check_prices(df)
        issues.extend(price_issues)

        # Volume check
        volume_issues, zero_count = self._price_volume.check_volume(df)
        issues.extend(volume_issues)

        # Outlier detection
        outlier_issues, outlier_count = self._quality.check_outliers(df)
        issues.extend(outlier_issues)

        # Gap detection
        gap_issues, gap_count = self._quality.check_gaps(df, interval_minutes)
        issues.extend(gap_issues)

        return {
            "issues": issues,
            "freshness_seconds": freshness_seconds,
            "zero_count": zero_count,
            "outlier_count": outlier_count,
            "gap_count": gap_count,
        }

    def _calculate_quality_score(self, check_results: dict) -> int:
        """Calculate quality score based on check results.

        Args:
            check_results: Dictionary with check results.

        Returns:
            Quality score (0-100).
        """
        score = 100
        issues = check_results["issues"]

        # Penalty for critical issues
        if any(i.severity == IssueSeverity.CRITICAL for i in issues):
            score -= self.config.insufficient_data_penalty

        # Penalty for stale data
        if any(i.issue_type == IssueType.STALE_DATA for i in issues):
            score -= self.config.stale_data_penalty

        # Penalty for zero volume
        zero_count = check_results["zero_count"]
        if zero_count > 0:
            score -= self.config.zero_volume_penalty * min(zero_count, 3)

        # Penalty for outliers
        outlier_count = check_results["outlier_count"]
        if outlier_count > 0:
            score -= self.config.outlier_penalty * min(outlier_count, 5)

        # Penalty for gaps
        gap_count = check_results["gap_count"]
        if gap_count > 0:
            score -= self.config.gap_penalty * min(gap_count, 5)

        return max(0, min(100, score))

    def _clean_data_if_needed(
        self, df: pd.DataFrame, outlier_count: int, clean_data: bool
    ) -> pd.DataFrame | None:
        """Clean data if requested and outliers detected.

        Returns:
            Cleaned DataFrame or None.
        """
        if clean_data and outlier_count > 0:
            return self._quality.clean_data(df)
        return None

    def _build_result(
        self,
        check_results: dict,
        quality_score: int,
        cleaned_df: pd.DataFrame | None,
        symbol: str,
        timeframe: str,
        df: pd.DataFrame,
    ) -> PreflightResult:
        """Build final PreflightResult.

        Args:
            check_results: Check results dictionary.
            quality_score: Calculated quality score.
            cleaned_df: Cleaned DataFrame if cleaning was done.
            symbol: Trading symbol.
            timeframe: Timeframe string.
            df: Original DataFrame.

        Returns:
            PreflightResult.
        """
        issues = check_results["issues"]
        status = self._determine_status(issues)

        return PreflightResult(
            status=status,
            symbol=symbol,
            timeframe=timeframe,
            issues=issues,
            data_rows=len(df),
            data_freshness_seconds=check_results["freshness_seconds"],
            zero_volume_count=check_results["zero_count"],
            outlier_count=check_results["outlier_count"],
            gap_count=check_results["gap_count"],
            quality_score=quality_score,
            cleaned_df=cleaned_df,
        )

    def _determine_status(self, issues: list[PreflightIssue]) -> PreflightStatus:
        """Determine preflight status from issues.

        Args:
            issues: List of issues.

        Returns:
            PreflightStatus enum value.
        """
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        warning_count = sum(1 for i in issues if i.severity == IssueSeverity.WARNING)

        if critical_count > 0:
            return PreflightStatus.FAILED
        if warning_count > 0:
            return PreflightStatus.WARNING
        return PreflightStatus.PASSED

    def _log_result(
        self, result: PreflightResult, symbol: str, timeframe: str
    ) -> None:
        """Log preflight result.

        Args:
            result: Preflight result to log.
            symbol: Trading symbol.
            timeframe: Timeframe string.
        """
        if result.status == PreflightStatus.FAILED:
            logger.warning(
                f"Preflight FAILED for {symbol}/{timeframe}: {result.get_summary()}"
            )
        elif result.status == PreflightStatus.WARNING:
            logger.info(
                f"Preflight WARNING for {symbol}/{timeframe}: {len(result.issues)} issues"
            )
        else:
            logger.debug(f"Preflight PASSED for {symbol}/{timeframe}")

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


# CONVENIENCE FUNCTIONS
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
