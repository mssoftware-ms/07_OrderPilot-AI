"""
Data Preflight Checks - Zentraler Service für Datenqualitätsprüfung.

Konsolidiert:
- Freshness-Prüfung (Daten nicht zu alt)
- Volume-Prüfung (genug Daten, kein Zero-Volume)
- Outlier-Prüfung (keine Anomalien)
- Index-Validation (DatetimeIndex korrekt)
- Minimum Data Requirements (genug Bars für Indikatoren)

Wird einheitlich von Trading-Engine, AI Popup und Chatbot verwendet.

Phase 1.2 der Bot-Integration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    from src.core.market_data.bar_validator import BarValidator

logger = logging.getLogger(__name__)


# ENUMS & TYPES
class PreflightStatus(str, Enum):
    """Status der Preflight-Prüfung."""

    PASSED = "PASSED"
    WARNING = "WARNING"  # Prüfung bestanden mit Warnungen
    FAILED = "FAILED"


class IssueType(str, Enum):
    """Typen von erkannten Problemen."""

    # Critical - Block Trading
    EMPTY_DATA = "EMPTY_DATA"
    STALE_DATA = "STALE_DATA"
    INVALID_INDEX = "INVALID_INDEX"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NEGATIVE_PRICES = "NEGATIVE_PRICES"

    # Warning - Continue with Caution
    ZERO_VOLUME = "ZERO_VOLUME"
    OUTLIERS_DETECTED = "OUTLIERS_DETECTED"
    GAPS_DETECTED = "GAPS_DETECTED"
    LOW_VOLUME = "LOW_VOLUME"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    PRICE_SPIKE = "PRICE_SPIKE"


class IssueSeverity(str, Enum):
    """Schweregrad eines Problems."""

    CRITICAL = "CRITICAL"  # Blockiert Trading
    WARNING = "WARNING"  # Nur Warnung
    INFO = "INFO"  # Nur Info


# PREFLIGHT RESULT
@dataclass
class PreflightIssue:
    """Einzelnes erkanntes Problem."""

    issue_type: IssueType
    severity: IssueSeverity
    message: str
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "type": self.issue_type.value,
            "severity": self.severity.value,
            "message": self.message,
            "details": self.details,
        }


@dataclass
class PreflightResult:
    """
    Ergebnis der Preflight-Prüfung.

    Enthält Status, Issues und Metriken.
    """

    status: PreflightStatus
    symbol: str
    timeframe: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Issues
    issues: list[PreflightIssue] = field(default_factory=list)

    # Metriken
    data_rows: int = 0
    data_freshness_seconds: int = 0
    zero_volume_count: int = 0
    outlier_count: int = 0
    gap_count: int = 0

    # Qualitätsscore (0-100)
    quality_score: int = 100

    # Cleaned Data (optional)
    cleaned_df: "pd.DataFrame | None" = None

    def to_dict(self) -> dict:
        """Konvertiert zu Dictionary."""
        return {
            "status": self.status.value,
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "issues": [i.to_dict() for i in self.issues],
            "metrics": {
                "data_rows": self.data_rows,
                "data_freshness_seconds": self.data_freshness_seconds,
                "zero_volume_count": self.zero_volume_count,
                "outlier_count": self.outlier_count,
                "gap_count": self.gap_count,
                "quality_score": self.quality_score,
            },
        }

    @property
    def is_tradeable(self) -> bool:
        """Prüft ob Daten für Trading geeignet sind."""
        return self.status != PreflightStatus.FAILED

    @property
    def critical_issues(self) -> list[PreflightIssue]:
        """Gibt nur kritische Issues zurück."""
        return [i for i in self.issues if i.severity == IssueSeverity.CRITICAL]

    @property
    def warning_issues(self) -> list[PreflightIssue]:
        """Gibt nur Warnungen zurück."""
        return [i for i in self.issues if i.severity == IssueSeverity.WARNING]

    def get_summary(self) -> str:
        """Erzeugt Zusammenfassung als String."""
        lines = [
            f"Preflight {self.status.value} for {self.symbol}/{self.timeframe}",
            f"Quality Score: {self.quality_score}/100",
            f"Data: {self.data_rows} rows, {self.data_freshness_seconds}s old",
        ]
        if self.issues:
            lines.append(f"Issues: {len(self.issues)}")
            for issue in self.issues[:3]:  # Max 3 Issues anzeigen
                lines.append(f"  - [{issue.severity.value}] {issue.message}")
        return "\n".join(lines)


# PREFLIGHT CONFIG
@dataclass
class PreflightConfig:
    """Konfiguration für Preflight-Checks."""

    # Freshness
    max_lag_multiplier: float = 1.5  # Max Lag = interval * multiplier
    max_stale_seconds: int = 300  # 5 Minuten absolute Obergrenze

    # Minimum Data
    min_bars_required: int = 50  # Mindestens 50 Bars für Indikatoren
    min_bars_for_indicators: dict = field(default_factory=lambda: {
        "ema_200": 200,
        "ema_50": 50,
        "ema_20": 20,
        "rsi_14": 15,
        "macd": 35,
        "bb_20": 21,
        "atr_14": 15,
        "adx_14": 28,
    })

    # Volume
    zero_volume_tolerance: int = 2  # Max Zero-Volume Bars in letzten 10
    min_average_volume: float = 0.1  # Minimum avg volume ratio

    # Outliers
    outlier_zscore_threshold: float = 4.0  # Z-Score für Outlier
    max_price_change_pct: float = 10.0  # Max Price Change % zwischen Bars

    # Gaps
    max_gap_multiplier: float = 3.0  # Gap > interval * multiplier = Warning

    # Quality Score Penalties
    stale_data_penalty: int = 30
    zero_volume_penalty: int = 15
    outlier_penalty: int = 10
    gap_penalty: int = 5
    insufficient_data_penalty: int = 40


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
        self._bar_validator: "BarValidator | None" = None

    def run_preflight(
        self,
        df: pd.DataFrame | None,
        symbol: str,
        timeframe: str = "5m",
        clean_data: bool = True,
    ) -> PreflightResult:
        """
        Führt vollständige Preflight-Prüfung durch.

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

        # 2. Index Validation
        index_issues = self._check_index(df)
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

        # 3. Minimum Data Check
        min_data_issues = self._check_minimum_data(df)
        issues.extend(min_data_issues)
        if any(i.severity == IssueSeverity.CRITICAL for i in min_data_issues):
            quality_score -= self.config.insufficient_data_penalty

        # 4. Freshness Check
        interval_minutes = self._parse_timeframe(timeframe)
        freshness_issues, freshness_seconds = self._check_freshness(df, interval_minutes)
        issues.extend(freshness_issues)
        if freshness_issues:
            quality_score -= self.config.stale_data_penalty

        # 5. Price Validation (Negative/Zero)
        price_issues = self._check_prices(df)
        issues.extend(price_issues)

        # 6. Volume Check
        volume_issues, zero_count = self._check_volume(df)
        issues.extend(volume_issues)
        if zero_count > 0:
            quality_score -= self.config.zero_volume_penalty * min(zero_count, 3)

        # 7. Outlier Detection
        outlier_issues, outlier_count = self._check_outliers(df)
        issues.extend(outlier_issues)
        if outlier_count > 0:
            quality_score -= self.config.outlier_penalty * min(outlier_count, 5)

        # 8. Gap Detection
        gap_issues, gap_count = self._check_gaps(df, interval_minutes)
        issues.extend(gap_issues)
        if gap_count > 0:
            quality_score -= self.config.gap_penalty * min(gap_count, 5)

        # Clean Data if requested
        cleaned_df = None
        if clean_data and outlier_count > 0:
            cleaned_df = self._clean_data(df)

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
            logger.warning(f"Preflight FAILED for {symbol}/{timeframe}: {result.get_summary()}")
        elif status == PreflightStatus.WARNING:
            logger.info(f"Preflight WARNING for {symbol}/{timeframe}: {len(issues)} issues")
        else:
            logger.debug(f"Preflight PASSED for {symbol}/{timeframe}")

        return result

    # =========================================================================
    # CHECK METHODS
    # =========================================================================

    def _check_index(self, df: pd.DataFrame) -> list[PreflightIssue]:
        """Prüft Index-Validität."""
        issues = []

        if not isinstance(df.index, pd.DatetimeIndex):
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.INVALID_INDEX,
                    severity=IssueSeverity.CRITICAL,
                    message="DataFrame index is not DatetimeIndex",
                    details={"index_type": str(type(df.index))},
                )
            )
        else:
            # Check for duplicate indices
            if df.index.duplicated().any():
                dup_count = df.index.duplicated().sum()
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.INVALID_INDEX,
                        severity=IssueSeverity.WARNING,
                        message=f"Found {dup_count} duplicate timestamps",
                        details={"duplicate_count": dup_count},
                    )
                )

            # Check for monotonic increasing
            if not df.index.is_monotonic_increasing:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.INVALID_INDEX,
                        severity=IssueSeverity.WARNING,
                        message="Index is not monotonically increasing",
                    )
                )

        return issues

    def _check_minimum_data(self, df: pd.DataFrame) -> list[PreflightIssue]:
        """Prüft ob genug Daten für Indikatoren vorhanden sind."""
        issues = []
        row_count = len(df)

        if row_count < self.config.min_bars_required:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.INSUFFICIENT_DATA,
                    severity=IssueSeverity.CRITICAL,
                    message=f"Insufficient data: {row_count} bars (min: {self.config.min_bars_required})",
                    details={
                        "rows": row_count,
                        "required": self.config.min_bars_required,
                    },
                )
            )
        else:
            # Check specific indicator requirements
            missing_for = []
            for indicator, required in self.config.min_bars_for_indicators.items():
                if row_count < required:
                    missing_for.append(f"{indicator} (needs {required})")

            if missing_for:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.INSUFFICIENT_DATA,
                        severity=IssueSeverity.WARNING,
                        message=f"Insufficient data for: {', '.join(missing_for[:3])}",
                        details={"missing_for": missing_for, "rows": row_count},
                    )
                )

        return issues

    def _check_freshness(
        self, df: pd.DataFrame, interval_minutes: int
    ) -> tuple[list[PreflightIssue], int]:
        """Prüft Daten-Freshness."""
        issues = []
        freshness_seconds = 0

        try:
            last_time = df.index[-1]

            # Handle timezone
            if last_time.tzinfo is None:
                last_time = last_time.replace(tzinfo=timezone.utc)
            else:
                last_time = last_time.astimezone(timezone.utc)

            now = datetime.now(timezone.utc)
            delta = now - last_time
            freshness_seconds = int(delta.total_seconds())

            # Allowed lag based on interval
            allowed_lag = timedelta(
                minutes=interval_minutes * self.config.max_lag_multiplier
            )
            max_lag = timedelta(seconds=self.config.max_stale_seconds)

            if delta > max_lag:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.STALE_DATA,
                        severity=IssueSeverity.CRITICAL,
                        message=f"Data too stale: {freshness_seconds}s old (max: {self.config.max_stale_seconds}s)",
                        details={
                            "last_timestamp": last_time.isoformat(),
                            "age_seconds": freshness_seconds,
                            "max_allowed": self.config.max_stale_seconds,
                        },
                    )
                )
            elif delta > allowed_lag:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.STALE_DATA,
                        severity=IssueSeverity.WARNING,
                        message=f"Data slightly stale: {freshness_seconds}s old",
                        details={
                            "last_timestamp": last_time.isoformat(),
                            "age_seconds": freshness_seconds,
                        },
                    )
                )

        except Exception as e:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.INVALID_INDEX,
                    severity=IssueSeverity.WARNING,
                    message=f"Could not check freshness: {e}",
                )
            )

        return issues, freshness_seconds

    def _check_prices(self, df: pd.DataFrame) -> list[PreflightIssue]:
        """Prüft auf negative/null Preise."""
        issues = []

        price_cols = ["open", "high", "low", "close"]
        available_cols = [c for c in price_cols if c in df.columns]

        if not available_cols:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.EMPTY_DATA,
                    severity=IssueSeverity.CRITICAL,
                    message="No OHLC columns found",
                    details={"columns": list(df.columns)},
                )
            )
            return issues

        for col in available_cols:
            negative_count = (df[col] < 0).sum()
            zero_count = (df[col] == 0).sum()

            if negative_count > 0:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.NEGATIVE_PRICES,
                        severity=IssueSeverity.CRITICAL,
                        message=f"Negative prices in {col}: {negative_count} rows",
                        details={"column": col, "count": negative_count},
                    )
                )

            if zero_count > 0:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.NEGATIVE_PRICES,
                        severity=IssueSeverity.WARNING,
                        message=f"Zero prices in {col}: {zero_count} rows",
                        details={"column": col, "count": zero_count},
                    )
                )

        return issues

    def _check_volume(self, df: pd.DataFrame) -> tuple[list[PreflightIssue], int]:
        """Prüft Volume-Daten."""
        issues = []
        zero_count = 0

        if "volume" not in df.columns:
            return issues, zero_count

        # Check recent zero volume
        recent = df["volume"].tail(10)
        zero_count = (recent == 0).sum()

        if zero_count > self.config.zero_volume_tolerance:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.ZERO_VOLUME,
                    severity=IssueSeverity.WARNING,
                    message=f"Zero volume in {zero_count}/10 recent bars",
                    details={"zero_count": zero_count, "lookback": 10},
                )
            )

        # Check average volume
        avg_volume = df["volume"].mean()
        if avg_volume < self.config.min_average_volume:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.LOW_VOLUME,
                    severity=IssueSeverity.WARNING,
                    message=f"Very low average volume: {avg_volume:.4f}",
                    details={"avg_volume": avg_volume},
                )
            )

        return issues, zero_count

    def _check_outliers(self, df: pd.DataFrame) -> tuple[list[PreflightIssue], int]:
        """Prüft auf Outliers mittels Z-Score."""
        issues = []
        outlier_count = 0

        if "close" not in df.columns or len(df) < 20:
            return issues, outlier_count

        # Rolling Z-Score
        window = 20
        rolling_mean = df["close"].rolling(window=window).mean()
        rolling_std = df["close"].rolling(window=window).std()

        # Avoid division by zero
        rolling_std = rolling_std.replace(0, 1)

        z_scores = (df["close"] - rolling_mean) / rolling_std
        outliers = z_scores.abs() > self.config.outlier_zscore_threshold
        outlier_count = outliers.sum()

        if outlier_count > 0:
            outlier_indices = df.index[outliers].tolist()
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.OUTLIERS_DETECTED,
                    severity=IssueSeverity.WARNING,
                    message=f"Detected {outlier_count} outliers (Z-Score > {self.config.outlier_zscore_threshold})",
                    details={
                        "count": outlier_count,
                        "threshold": self.config.outlier_zscore_threshold,
                        "first_outliers": [str(t) for t in outlier_indices[:3]],
                    },
                )
            )

        # Check for price spikes
        if "close" in df.columns and len(df) > 1:
            pct_changes = df["close"].pct_change().abs() * 100
            spikes = pct_changes > self.config.max_price_change_pct
            spike_count = spikes.sum()

            if spike_count > 0:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.PRICE_SPIKE,
                        severity=IssueSeverity.WARNING,
                        message=f"Detected {spike_count} price spikes (>{self.config.max_price_change_pct}%)",
                        details={
                            "spike_count": spike_count,
                            "max_change_pct": pct_changes.max(),
                        },
                    )
                )
                outlier_count += spike_count

        return issues, outlier_count

    def _check_gaps(
        self, df: pd.DataFrame, interval_minutes: int
    ) -> tuple[list[PreflightIssue], int]:
        """Prüft auf Zeitlücken."""
        issues = []
        gap_count = 0

        if len(df) < 2:
            return issues, gap_count

        # Calculate time differences
        time_diffs = df.index.to_series().diff().dropna()

        # Expected interval
        expected = timedelta(minutes=interval_minutes)
        max_allowed = expected * self.config.max_gap_multiplier

        # Find gaps
        gaps = time_diffs > max_allowed
        gap_count = gaps.sum()

        if gap_count > 0:
            gap_indices = time_diffs[gaps].index.tolist()
            max_gap = time_diffs.max()

            issues.append(
                PreflightIssue(
                    issue_type=IssueType.GAPS_DETECTED,
                    severity=IssueSeverity.WARNING,
                    message=f"Detected {gap_count} time gaps (max: {max_gap})",
                    details={
                        "gap_count": gap_count,
                        "max_gap_seconds": max_gap.total_seconds(),
                        "first_gaps": [str(t) for t in gap_indices[:3]],
                    },
                )
            )

        return issues, gap_count

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Bereinigt Daten (Outlier-Korrektur).

        Verwendet Rolling-Median für extreme Outliers.
        """
        df_clean = df.copy()

        window = 20
        threshold = self.config.outlier_zscore_threshold

        for col in ["high", "low", "close"]:
            if col not in df_clean.columns:
                continue

            rolling_mean = df_clean[col].rolling(window=window).mean()
            rolling_std = df_clean[col].rolling(window=window).std().replace(0, 1)

            z_score = (df_clean[col] - rolling_mean) / rolling_std
            outliers = z_score.abs() > threshold

            if outliers.any():
                rolling_median = df_clean[col].rolling(window=3).median()
                df_clean.loc[outliers, col] = rolling_median.loc[outliers]

        return df_clean

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
