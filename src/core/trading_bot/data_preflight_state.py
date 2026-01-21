"""Data Preflight State - Enums, Dataclasses and Config.

Refactored from 798 LOC monolith using composition pattern.

Module 1/5 of data_preflight.py split.

Contains:
- PreflightStatus enum (PASSED, WARNING, FAILED)
- IssueType enum (EMPTY_DATA, STALE_DATA, etc.)
- IssueSeverity enum (CRITICAL, WARNING, INFO)
- PreflightIssue dataclass (single issue)
- PreflightResult dataclass (full result with metrics + properties)
- PreflightConfig dataclass (all thresholds and penalties)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

import pandas as pd


# ENUMS
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


# DATACLASSES
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
    cleaned_df: pd.DataFrame | None = None

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


# CONFIG
@dataclass
class PreflightConfig:
    """Konfiguration für Preflight-Checks."""

    # Freshness
    max_lag_multiplier: float = 1.5  # Max Lag = interval * multiplier
    max_stale_seconds: int = 300  # 5 Minuten absolute Obergrenze

    # Minimum Data
    min_bars_required: int = 50  # Mindestens 50 Bars für Indikatoren
    min_bars_for_indicators: dict = field(
        default_factory=lambda: {
            "ema_200": 200,
            "ema_50": 50,
            "ema_20": 20,
            "rsi_14": 15,
            "macd": 35,
            "bb_20": 21,
            "atr_14": 15,
            "adx_14": 28,
        }
    )

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
