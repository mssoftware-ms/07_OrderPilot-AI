"""Theme utilities for chart widgets.

This module provides centralized theme management for all chart implementations.
Previously, theme colors were hardcoded in multiple locations.

IMPORTANT: This is now the SINGLE SOURCE OF TRUTH for chart themes.
"""

import logging
from typing import Dict, Any, Optional

from .constants import THEME_COLORS, DEFAULT_THEME

logger = logging.getLogger(__name__)


def get_theme_colors(theme: str = DEFAULT_THEME) -> Dict[str, str]:
    """Get color palette for a specific theme.

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Dictionary of color values for the theme

    Example:
        >>> colors = get_theme_colors('dark')
        >>> colors['background']
        '#0a0a0a'
    """
    if theme not in THEME_COLORS:
        logger.warning(f"Unknown theme '{theme}', falling back to '{DEFAULT_THEME}'")
        theme = DEFAULT_THEME

    return THEME_COLORS[theme].copy()


def get_candle_colors(theme: str = DEFAULT_THEME) -> Dict[str, str]:
    """Get candlestick colors for a specific theme.

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Dictionary with up/down candle and wick colors
    """
    colors = get_theme_colors(theme)
    return {
        'up': colors['up_candle'],
        'down': colors['down_candle'],
        'up_wick': colors['up_wick'],
        'down_wick': colors['down_wick'],
    }


def get_volume_colors(theme: str = DEFAULT_THEME) -> Dict[str, str]:
    """Get volume bar colors for a specific theme.

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Dictionary with up/down volume colors
    """
    colors = get_theme_colors(theme)
    return {
        'up': colors['volume_up'],
        'down': colors['volume_down'],
    }


def apply_theme_to_chart(
    chart_options: Dict[str, Any],
    theme: str = DEFAULT_THEME
) -> Dict[str, Any]:
    """Apply theme colors to chart options dictionary.

    This function modifies a chart configuration dictionary
    to use the specified theme colors.

    Args:
        chart_options: Chart configuration dictionary
        theme: Theme name ('dark' or 'light')

    Returns:
        Modified chart options with theme colors applied
    """
    colors = get_theme_colors(theme)

    # Apply layout colors
    if 'layout' not in chart_options:
        chart_options['layout'] = {}

    chart_options['layout']['background'] = {
        'type': 'solid',
        'color': colors['background']
    }
    chart_options['layout']['textColor'] = colors['text']

    # Apply grid colors
    if 'grid' not in chart_options:
        chart_options['grid'] = {}

    chart_options['grid']['vertLines'] = {'color': colors['grid']}
    chart_options['grid']['horzLines'] = {'color': colors['grid']}

    # Apply crosshair colors
    if 'crosshair' not in chart_options:
        chart_options['crosshair'] = {}

    chart_options['crosshair']['vertLine'] = {
        'color': colors['crosshair'],
        'labelBackgroundColor': colors['panel_background']
    }
    chart_options['crosshair']['horzLine'] = {
        'color': colors['crosshair'],
        'labelBackgroundColor': colors['panel_background']
    }

    # Apply price scale colors
    if 'rightPriceScale' not in chart_options:
        chart_options['rightPriceScale'] = {}

    chart_options['rightPriceScale']['borderColor'] = colors['scale_border']

    # Apply time scale colors
    if 'timeScale' not in chart_options:
        chart_options['timeScale'] = {}

    chart_options['timeScale']['borderColor'] = colors['scale_border']

    return chart_options


def get_pyqtgraph_theme(theme: str = DEFAULT_THEME) -> Dict[str, Any]:
    """Get PyQtGraph-specific theme configuration.

    Used for PyQtGraph-based charts (chart.py, chart_view.py).

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Dictionary with PyQtGraph configuration
    """
    colors = get_theme_colors(theme)

    return {
        'background': colors['background'],
        'foreground': colors['text'],
        'grid_alpha': 0.3,
        'candle_up': colors['up_candle'],
        'candle_down': colors['down_candle'],
    }


def get_tradingview_chart_options(theme: str = DEFAULT_THEME) -> Dict[str, Any]:
    """Get complete TradingView Lightweight Charts configuration.

    This returns the full configuration object for createChart().

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Complete chart configuration dictionary
    """
    colors = get_theme_colors(theme)

    return {
        'layout': {
            'background': {'type': 'solid', 'color': colors['background']},
            'textColor': colors['text'],
            'panes': {
                'separatorColor': colors['border'],
                'separatorHoverColor': colors['border_hover'],
                'enableResize': True,
            },
        },
        'grid': {
            'vertLines': {'color': colors['grid']},
            'horzLines': {'color': colors['grid']},
        },
        'crosshair': {
            'mode': 1,  # CrosshairMode.Normal
            'vertLine': {
                'color': colors['crosshair'],
                'labelBackgroundColor': colors['panel_background'],
            },
            'horzLine': {
                'color': colors['crosshair'],
                'labelBackgroundColor': colors['panel_background'],
            },
        },
        'rightPriceScale': {
            'borderColor': colors['scale_border'],
            'minimumWidth': 60,
            'autoScale': True,
            'scaleMargins': {'top': 0.15, 'bottom': 0.15},
        },
        'timeScale': {
            'timeVisible': True,
            'secondsVisible': False,
            'borderColor': colors['scale_border'],
        },
        'handleScroll': {
            'mouseWheel': False,
            'pressedMouseMove': True,
            'horzTouchDrag': True,
            'vertTouchDrag': True,
        },
        'handleScale': {
            'axisPressedMouseMove': {'time': True, 'price': True},
            'mouseWheel': True,
            'pinch': True,
        },
        'autoSize': True,
    }


def get_candlestick_series_options(theme: str = DEFAULT_THEME) -> Dict[str, Any]:
    """Get TradingView candlestick series options.

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Candlestick series configuration
    """
    colors = get_theme_colors(theme)

    return {
        'upColor': colors['up_candle'],
        'downColor': colors['down_candle'],
        'borderVisible': False,
        'wickUpColor': colors['up_wick'],
        'wickDownColor': colors['down_wick'],
    }


def get_volume_series_options(theme: str = DEFAULT_THEME) -> Dict[str, Any]:
    """Get TradingView volume series options.

    Args:
        theme: Theme name ('dark' or 'light')

    Returns:
        Volume series configuration
    """
    colors = get_theme_colors(theme)

    return {
        'color': colors['volume_up'],
        'priceFormat': {
            'type': 'volume',
        },
        'priceScaleId': '',
        'scaleMargins': {
            'top': 0.8,
            'bottom': 0,
        },
    }


def generate_indicator_color(
    indicator_type: str,
    index: int = 0
) -> str:
    """Generate a color for an indicator.

    If the indicator has a default color, use that.
    Otherwise, generate a color based on the index.

    Args:
        indicator_type: Type of indicator (e.g., 'SMA', 'EMA')
        index: Index for color cycling when multiple of same type

    Returns:
        Hex color string
    """
    from .constants import INDICATOR_DEFAULTS

    # Check if indicator has default color
    if indicator_type.upper() in INDICATOR_DEFAULTS:
        default = INDICATOR_DEFAULTS[indicator_type.upper()]
        if 'color' in default:
            return default['color']

    # Fallback color palette
    palette = [
        '#2196F3',  # Blue
        '#FF9800',  # Orange
        '#4CAF50',  # Green
        '#E91E63',  # Pink
        '#9C27B0',  # Purple
        '#00BCD4',  # Cyan
        '#FFEB3B',  # Yellow
        '#795548',  # Brown
        '#607D8B',  # Blue Grey
        '#F44336',  # Red
    ]

    return palette[index % len(palette)]
