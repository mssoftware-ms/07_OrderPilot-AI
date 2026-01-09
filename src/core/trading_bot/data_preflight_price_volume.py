"""Data Preflight Price & Volume Checks.

Refactored from 798 LOC monolith using composition pattern.

Module 3/5 of data_preflight.py split.

Contains:
- _check_prices(): Validates OHLC columns, negative/zero prices
- _check_volume(): Zero volume detection, low average volume
"""

from __future__ import annotations

import pandas as pd

from src.core.trading_bot.data_preflight_state import (
    IssueType,
    IssueSeverity,
    PreflightIssue,
)


class DataPreflightPriceVolume:
    """Helper für Price & Volume Checks."""

    def __init__(self, parent):
        """
        Args:
            parent: DataPreflightService Instanz
        """
        self.parent = parent

    def check_prices(self, df: pd.DataFrame) -> list[PreflightIssue]:
        """Prüft auf negative/null Preise.

        Checks:
            - OHLC columns exist
            - No negative prices
            - No zero prices (warning)

        Args:
            df: DataFrame to check

        Returns:
            List of PreflightIssue (empty if no issues)
        """
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

    def check_volume(self, df: pd.DataFrame) -> tuple[list[PreflightIssue], int]:
        """Prüft Volume-Daten.

        Checks:
            - Zero volume in recent bars (last 10)
            - Low average volume

        Args:
            df: DataFrame to check

        Returns:
            Tuple of (issues list, zero volume count)
        """
        issues = []
        zero_count = 0

        if "volume" not in df.columns:
            return issues, zero_count

        # Check recent zero volume
        recent = df["volume"].tail(10)
        zero_count = (recent == 0).sum()

        if zero_count > self.parent.config.zero_volume_tolerance:
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
        if avg_volume < self.parent.config.min_average_volume:
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.LOW_VOLUME,
                    severity=IssueSeverity.WARNING,
                    message=f"Very low average volume: {avg_volume:.4f}",
                    details={"avg_volume": avg_volume},
                )
            )

        return issues, zero_count
