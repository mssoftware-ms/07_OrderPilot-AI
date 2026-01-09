"""Data Preflight Basic Checks - Index, Minimum Data, Freshness.

Refactored from 798 LOC monolith using composition pattern.

Module 2/5 of data_preflight.py split.

Contains:
- _check_index(): Validates DatetimeIndex, duplicates, monotonic
- _check_minimum_data(): Ensures minimum bars for indicators
- _check_freshness(): Checks data staleness (lag multiplier, max stale)
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pandas as pd

from src.core.trading_bot.data_preflight_state import (
    IssueType,
    IssueSeverity,
    PreflightIssue,
)


class DataPreflightBasicChecks:
    """Helper für Basic Preflight Checks (Index, Min Data, Freshness)."""

    def __init__(self, parent):
        """
        Args:
            parent: DataPreflightService Instanz
        """
        self.parent = parent

    def check_index(self, df: pd.DataFrame) -> list[PreflightIssue]:
        """Prüft Index-Validität.

        Checks:
            - DatetimeIndex type
            - Duplicate timestamps
            - Monotonic increasing order

        Args:
            df: DataFrame to check

        Returns:
            List of PreflightIssue (empty if no issues)
        """
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

    def check_minimum_data(self, df: pd.DataFrame) -> list[PreflightIssue]:
        """Prüft ob genug Daten für Indikatoren vorhanden sind.

        Checks:
            - Minimum bars required (50)
            - Specific indicator requirements (EMA 200, MACD, etc.)

        Args:
            df: DataFrame to check

        Returns:
            List of PreflightIssue (empty if no issues)
        """
        issues = []
        row_count = len(df)

        if row_count < self.parent.config.min_bars_required:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.INSUFFICIENT_DATA,
                    severity=IssueSeverity.CRITICAL,
                    message=f"Insufficient data: {row_count} bars (min: {self.parent.config.min_bars_required})",
                    details={
                        "rows": row_count,
                        "required": self.parent.config.min_bars_required,
                    },
                )
            )
        else:
            # Check specific indicator requirements
            missing_for = []
            for indicator, required in self.parent.config.min_bars_for_indicators.items():
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

    def check_freshness(
        self, df: pd.DataFrame, interval_minutes: int
    ) -> tuple[list[PreflightIssue], int]:
        """Prüft Daten-Freshness.

        Checks:
            - Last timestamp age vs interval (max_lag_multiplier)
            - Absolute staleness limit (max_stale_seconds)

        Args:
            df: DataFrame to check
            interval_minutes: Expected interval in minutes

        Returns:
            Tuple of (issues list, freshness in seconds)
        """
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
                minutes=interval_minutes * self.parent.config.max_lag_multiplier
            )
            max_lag = timedelta(seconds=self.parent.config.max_stale_seconds)

            if delta > max_lag:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.STALE_DATA,
                        severity=IssueSeverity.CRITICAL,
                        message=f"Data too stale: {freshness_seconds}s old (max: {self.parent.config.max_stale_seconds}s)",
                        details={
                            "last_timestamp": last_time.isoformat(),
                            "age_seconds": freshness_seconds,
                            "max_allowed": self.parent.config.max_stale_seconds,
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
