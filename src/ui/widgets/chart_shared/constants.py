"""Shared constants for chart widgets.

This module centralizes all chart-related constants to ensure consistency
across different chart implementations. Previously, these values were
duplicated across:
- chart.py (symbols: line 50, timeframes: line 58)
- chart_view.py (symbols: line 203, timeframes: line 213)
- embedded_tradingview_chart.py (various locations)
- lightweight_chart.py (various locations)

IMPORTANT: This is now the SINGLE SOURCE OF TRUTH for chart constants.
"""

from typing import Dict, List, Any

# =============================================================================
# SYMBOL CONSTANTS
# =============================================================================

# Default symbols for stock trading
# Consolidated from:
# - chart.py line 50: ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "SPY", "QQQ"]
# - chart_view.py line 203: ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"]
DEFAULT_SYMBOLS: List[str] = [
    "AAPL",   # Apple Inc.
    "MSFT",   # Microsoft Corporation
    "GOOGL",  # Alphabet Inc.
    "AMZN",   # Amazon.com Inc.
    "TSLA",   # Tesla Inc.
    "SPY",    # SPDR S&P 500 ETF
    "QQQ",    # Invesco QQQ Trust (Nasdaq-100)
    "NVDA",   # NVIDIA Corporation
    "META",   # Meta Platforms Inc.
]

# Crypto symbols
DEFAULT_CRYPTO_SYMBOLS: List[str] = [
    "BTC/USD",
    "ETH/USD",
    "SOL/USD",
    "DOGE/USD",
]

# =============================================================================
# TIMEFRAME CONSTANTS
# =============================================================================

# Timeframe definitions - UNIFIED format
# Consolidated from:
# - chart.py line 58: ["1min", "5min", "15min", "1h", "1D"]
# - chart_view.py line 213: ["1T", "5T", "15T", "30T", "1H", "4H", "1D"]
#
# Format: display_name -> api_value
TIMEFRAMES: Dict[str, str] = {
    "1m": "1min",      # 1 minute (Alpaca: 1Min)
    "5m": "5min",      # 5 minutes (Alpaca: 5Min)
    "15m": "15min",    # 15 minutes (Alpaca: 15Min)
    "30m": "30min",    # 30 minutes (Alpaca: 30Min)
    "1H": "1hour",     # 1 hour (Alpaca: 1Hour)
    "4H": "4hour",     # 4 hours (Alpaca: 4Hour)
    "1D": "1day",      # 1 day (Alpaca: 1Day)
    "1W": "1week",     # 1 week (Alpaca: 1Week)
}

# Timeframe display names for UI
TIMEFRAME_DISPLAY_NAMES: Dict[str, str] = {
    "1m": "1 Minute",
    "5m": "5 Minutes",
    "15m": "15 Minutes",
    "30m": "30 Minutes",
    "1H": "1 Hour",
    "4H": "4 Hours",
    "1D": "1 Day",
    "1W": "1 Week",
}

# Default timeframe
DEFAULT_TIMEFRAME: str = "1D"

# =============================================================================
# INDICATOR DEFAULTS
# =============================================================================

# Indicator configuration defaults
# Consolidated from various chart implementations
INDICATOR_DEFAULTS: Dict[str, Dict[str, Any]] = {
    # Moving Averages
    "SMA": {
        "period": 20,
        "color": "#2196F3",  # Blue
        "line_width": 2,
    },
    "EMA": {
        "period": 20,
        "color": "#FF9800",  # Orange
        "line_width": 2,
    },
    "WMA": {
        "period": 20,
        "color": "#4CAF50",  # Green
        "line_width": 2,
    },

    # Bollinger Bands
    "BB": {
        "period": 20,
        "std_dev": 2.0,
        "color": "#9C27B0",  # Purple
        "fill_alpha": 0.1,
    },

    # Momentum Indicators
    "RSI": {
        "period": 14,
        "overbought": 70,
        "oversold": 30,
        "color": "#E91E63",  # Pink
    },
    "MACD": {
        "fast_period": 12,
        "slow_period": 26,
        "signal_period": 9,
        "macd_color": "#2196F3",  # Blue
        "signal_color": "#FF9800",  # Orange
        "histogram_up_color": "#26a69a",  # Green
        "histogram_down_color": "#ef5350",  # Red
    },
    "Stochastic": {
        "k_period": 14,
        "d_period": 3,
        "overbought": 80,
        "oversold": 20,
        "k_color": "#2196F3",
        "d_color": "#FF9800",
    },

    # Volatility Indicators
    "ATR": {
        "period": 14,
        "color": "#607D8B",  # Blue Grey
    },

    # Volume Indicators
    "VWAP": {
        "color": "#00BCD4",  # Cyan
        "line_width": 2,
    },
    "OBV": {
        "color": "#795548",  # Brown
    },
}

# =============================================================================
# THEME COLORS
# =============================================================================

# Chart theme colors
# Consolidated from embedded_tradingview_chart.py and other implementations
THEME_COLORS: Dict[str, Dict[str, str]] = {
    "dark": {
        # Background colors
        "background": "#0a0a0a",
        "chart_background": "#131722",
        "panel_background": "#1e222d",

        # Text colors
        "text": "#d1d4dc",
        "text_secondary": "#787b86",
        "text_muted": "#4c525e",

        # Grid colors
        "grid": "rgba(70, 70, 70, 0.35)",
        "grid_hover": "rgba(100, 100, 100, 0.5)",

        # Candlestick colors
        "up_candle": "#26a69a",      # Green (bullish)
        "down_candle": "#ef5350",     # Red (bearish)
        "up_wick": "#26a69a",
        "down_wick": "#ef5350",

        # Volume colors
        "volume_up": "rgba(38, 166, 154, 0.5)",
        "volume_down": "rgba(239, 83, 80, 0.5)",

        # Border colors
        "border": "#2a2a3c",
        "border_hover": "#3a3a4c",

        # Crosshair
        "crosshair": "#758696",

        # Scale colors
        "scale_border": "#485c7b",
    },

    "light": {
        # Background colors
        "background": "#ffffff",
        "chart_background": "#ffffff",
        "panel_background": "#f8f9fa",

        # Text colors
        "text": "#131722",
        "text_secondary": "#787b86",
        "text_muted": "#b2b5be",

        # Grid colors
        "grid": "rgba(200, 200, 200, 0.35)",
        "grid_hover": "rgba(180, 180, 180, 0.5)",

        # Candlestick colors (same for both themes)
        "up_candle": "#26a69a",
        "down_candle": "#ef5350",
        "up_wick": "#26a69a",
        "down_wick": "#ef5350",

        # Volume colors
        "volume_up": "rgba(38, 166, 154, 0.5)",
        "volume_down": "rgba(239, 83, 80, 0.5)",

        # Border colors
        "border": "#e0e3eb",
        "border_hover": "#c8ccd5",

        # Crosshair
        "crosshair": "#9598a1",

        # Scale colors
        "scale_border": "#b2b5be",
    },
}

# Default theme
DEFAULT_THEME: str = "dark"

# =============================================================================
# CHART CONFIGURATION
# =============================================================================

# Default chart configuration
DEFAULT_CHART_CONFIG: Dict[str, Any] = {
    "show_volume": True,
    "show_grid": True,
    "auto_scale": True,
    "crosshair_mode": "normal",
    "price_scale_position": "right",
    "time_scale_visible": True,
    "seconds_visible": False,
}

# Maximum bars to display
MAX_BARS_DISPLAY: int = 2000
MAX_BARS_HISTORY: int = 5000

# Update intervals (milliseconds)
UPDATE_INTERVAL_REALTIME: int = 1000
UPDATE_INTERVAL_BATCH: int = 5000

# =============================================================================
# DRAWING TOOLS
# =============================================================================

# Drawing tool types
DRAWING_TOOLS: Dict[str, Dict[str, Any]] = {
    "horizontal_line": {
        "name": "Horizontal Line",
        "icon": "horizontal_line",
        "color": "#2196F3",
    },
    "vertical_line": {
        "name": "Vertical Line",
        "icon": "vertical_line",
        "color": "#2196F3",
    },
    "trend_line": {
        "name": "Trend Line",
        "icon": "trend_line",
        "color": "#FF9800",
    },
    "rectangle": {
        "name": "Rectangle",
        "icon": "rectangle",
        "color": "#9C27B0",
        "fill_alpha": 0.2,
    },
    "fibonacci": {
        "name": "Fibonacci Retracement",
        "icon": "fibonacci",
        "levels": [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1],
    },
}
