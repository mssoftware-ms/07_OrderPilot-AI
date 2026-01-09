"""Data Preflight Quality Checks - Outliers, Gaps, Data Cleaning.

Refactored from 798 LOC monolith using composition pattern.

Module 4/5 of data_preflight.py split.

Contains:
- _check_outliers(): Z-score outliers, price spikes
- _check_gaps(): Time gap detection
- _clean_data(): Outlier correction with rolling median
"""

from __future__ import annotations

from datetime import timedelta

import pandas as pd

from src.core.trading_bot.data_preflight_state import (
    IssueType,
    IssueSeverity,
    PreflightIssue,
)


class DataPreflightQuality:
    """Helper für Quality Checks (Outliers, Gaps, Cleaning)."""

    def __init__(self, parent):
        """
        Args:
            parent: DataPreflightService Instanz
        """
        self.parent = parent

    def check_outliers(self, df: pd.DataFrame) -> tuple[list[PreflightIssue], int]:
        """Prüft auf Outliers mittels Z-Score.

        Checks:
            - Rolling Z-score outliers (window=20)
            - Price spikes (% change between bars)

        Args:
            df: DataFrame to check

        Returns:
            Tuple of (issues list, total outlier count)
        """
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
        outliers = z_scores.abs() > self.parent.config.outlier_zscore_threshold
        outlier_count = outliers.sum()

        if outlier_count > 0:
            outlier_indices = df.index[outliers].tolist()
            issues.append(
                PreflightIssue(
                    issue_type=IssueType.OUTLIERS_DETECTED,
                    severity=IssueSeverity.WARNING,
                    message=f"Detected {outlier_count} outliers (Z-Score > {self.parent.config.outlier_zscore_threshold})",
                    details={
                        "count": outlier_count,
                        "threshold": self.parent.config.outlier_zscore_threshold,
                        "first_outliers": [str(t) for t in outlier_indices[:3]],
                    },
                )
            )

        # Check for price spikes
        if "close" in df.columns and len(df) > 1:
            pct_changes = df["close"].pct_change().abs() * 100
            spikes = pct_changes > self.parent.config.max_price_change_pct
            spike_count = spikes.sum()

            if spike_count > 0:
                issues.append(
                    PreflightIssue(
                        issue_type=IssueType.PRICE_SPIKE,
                        severity=IssueSeverity.WARNING,
                        message=f"Detected {spike_count} price spikes (>{self.parent.config.max_price_change_pct}%)",
                        details={
                            "spike_count": spike_count,
                            "max_change_pct": pct_changes.max(),
                        },
                    )
                )
                outlier_count += spike_count

        return issues, outlier_count

    def check_gaps(
        self, df: pd.DataFrame, interval_minutes: int
    ) -> tuple[list[PreflightIssue], int]:
        """Prüft auf Zeitlücken.

        Checks:
            - Time gaps > expected interval * max_gap_multiplier

        Args:
            df: DataFrame to check
            interval_minutes: Expected interval in minutes

        Returns:
            Tuple of (issues list, gap count)
        """
        issues = []
        gap_count = 0

        if len(df) < 2:
            return issues, gap_count

        # Calculate time differences
        time_diffs = df.index.to_series().diff().dropna()

        # Expected interval
        expected = timedelta(minutes=interval_minutes)
        max_allowed = expected * self.parent.config.max_gap_multiplier

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

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Bereinigt Daten (Outlier-Korrektur).

        Verwendet Rolling-Median für extreme Outliers.

        Args:
            df: DataFrame to clean

        Returns:
            Cleaned DataFrame
        """
        df_clean = df.copy()

        window = 20
        threshold = self.parent.config.outlier_zscore_threshold

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
