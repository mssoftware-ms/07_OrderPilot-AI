"""Backtesting error handling with improved error messages (7.3.3).

Provides clear, actionable error messages for common backtest failures.
"""

from typing import Optional, Dict, Any


class BacktestError(Exception):
    """Base exception for backtesting errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None, suggestions: Optional[list[str]] = None):
        """Initialize backtestexception.

        Args:
            message: Error message
            details: Additional error details
            suggestions: List of suggested solutions
        """
        self.message = message
        self.details = details or {}
        self.suggestions = suggestions or []
        super().__init__(self.format_error())

    def format_error(self) -> str:
        """Format error message with details and suggestions."""
        lines = [f"⚠️ {self.message}"]

        if self.details:
            lines.append("\nDetails:")
            for key, value in self.details.items():
                lines.append(f"  • {key}: {value}")

        if self.suggestions:
            lines.append("\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                lines.append(f"  {i}. {suggestion}")

        return "\n".join(lines)


class DataLoadError(BacktestError):
    """Error loading market data."""

    @classmethod
    def no_data_found(cls, symbol: str, start_date: str, end_date: str, db_path: str) -> 'DataLoadError':
        """Create error for missing data."""
        return cls(
            f"No market data found for symbol '{symbol}'",
            details={
                "Symbol": symbol,
                "Date Range": f"{start_date} to {end_date}",
                "Database": db_path
            },
            suggestions=[
                "Check if symbol format is correct (try 'bitunix:BTCUSDT' or 'BTCUSDT')",
                "Verify data exists in the database for this date range",
                "Download historical data using the data loader",
                "Try a different date range with available data"
            ]
        )

    @classmethod
    def timeframe_incompatible(cls, chart_tf: str, required_tf: str) -> 'DataLoadError':
        """Create error for incompatible timeframes."""
        return cls(
            f"Cannot downsample {chart_tf} data to {required_tf}",
            details={
                "Chart Timeframe": chart_tf,
                "Required Timeframe": required_tf,
                "Problem": "Downsampling (converting higher TF to lower TF) is not possible"
            },
            suggestions=[
                f"Load chart with {required_tf} or 1m timeframe",
                f"Use a strategy that requires only {chart_tf} or higher timeframes",
                "Let system load data from Database/API (close chart, reopen Entry Analyzer)",
                "Modify strategy to use compatible indicator timeframes"
            ]
        )


class ConfigurationError(BacktestError):
    """Error in strategy configuration."""

    @classmethod
    def invalid_config(cls, error_details: str) -> 'ConfigurationError':
        """Create error for invalid configuration."""
        return cls(
            "Invalid strategy configuration",
            details={"Error": error_details},
            suggestions=[
                "Check JSON schema validation",
                "Verify all required fields are present",
                "Ensure indicator/regime/strategy IDs are unique",
                "Check parameter types match schema"
            ]
        )

    @classmethod
    def missing_indicator(cls, indicator_id: str, referenced_by: str) -> 'ConfigurationError':
        """Create error for missing indicator reference."""
        return cls(
            f"Indicator '{indicator_id}' not found",
            details={
                "Indicator ID": indicator_id,
                "Referenced By": referenced_by
            },
            suggestions=[
                f"Add indicator with ID '{indicator_id}' to config.indicators",
                "Check for typos in indicator ID",
                "Verify indicator is defined before being referenced"
            ]
        )

    @classmethod
    def no_strategy_matched(cls, active_regimes: list[str]) -> 'ConfigurationError':
        """Create error when no strategy matches current regime."""
        return cls(
            "No strategy matched current market regime",
            details={
                "Active Regimes": ", ".join(active_regimes) if active_regimes else "None",
                "Problem": "No routing rule matches the active regime combination"
            },
            suggestions=[
                "Add a default routing rule (no regime requirements)",
                "Expand regime definitions to cover more market conditions",
                "Check routing rules match expected regime combinations",
                "Use fallback RegimeEngine if no JSON regimes defined"
            ]
        )


class IndicatorError(BacktestError):
    """Error calculating indicators."""

    @classmethod
    def calculation_failed(cls, indicator_id: str, indicator_type: str, error_msg: str) -> 'IndicatorError':
        """Create error for indicator calculation failure."""
        return cls(
            f"Failed to calculate indicator '{indicator_id}'",
            details={
                "Indicator ID": indicator_id,
                "Indicator Type": indicator_type,
                "Error": error_msg
            },
            suggestions=[
                "Check if required data columns (OHLCV) are present",
                "Verify indicator parameters are valid",
                "Ensure sufficient data points for calculation",
                "Check pandas_ta documentation for parameter requirements"
            ]
        )


class ExecutionError(BacktestError):
    """Error during backtest execution."""

    @classmethod
    def insufficient_data(cls, required: int, available: int) -> 'ExecutionError':
        """Create error for insufficient data."""
        return cls(
            "Insufficient data for backtesting",
            details={
                "Required Candles": required,
                "Available Candles": available
            },
            suggestions=[
                "Load more historical data",
                "Reduce indicator lookback periods",
                "Adjust date range to include more data"
            ]
        )


def format_error_for_ui(error: Exception) -> str:
    """Format any exception for UI display.

    Args:
        error: Exception to format

    Returns:
        Formatted error message string
    """
    if isinstance(error, BacktestError):
        return error.format_error()
    else:
        # Generic formatting for unknown errors
        return (
            f"⚠️ Unexpected Error\n\n"
            f"Error Type: {type(error).__name__}\n"
            f"Message: {str(error)}\n\n"
            f"Suggestions:\n"
            f"  1. Check the logs for more details\n"
            f"  2. Verify all configuration parameters\n"
            f"  3. Report this error if it persists"
        )
