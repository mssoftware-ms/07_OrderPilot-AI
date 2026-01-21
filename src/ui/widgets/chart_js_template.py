"""TradingView Lightweight Charts HTML/JavaScript Template."""

from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import QSettings

from src.chart_marking.zones.zone_primitive_js import get_zone_javascript

logger = logging.getLogger(__name__)

_TEMPLATE_PATH = Path(__file__).with_name("chart_js_template.html")


def _load_chart_template() -> str:
    """Load the HTML/JS template from disk."""
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


# For backwards compatibility (though get_chart_html_template() should be preferred)
CHART_HTML_TEMPLATE = _load_chart_template()


def get_background_image_style() -> str:
    """Get background image CSS style from QSettings (Issue #35).

    Returns:
        CSS style string for background image, or empty string if no image set.
    """
    settings = QSettings("OrderPilot", "TradingApp")

    # Get current theme to load theme-specific settings
    theme_name = settings.value("theme", "Dark Orange")
    t_key = theme_name.lower().replace(" ", "_")

    bg_image_path = settings.value(f"{t_key}_chart_background_image", "")
    bg_opacity = settings.value(f"{t_key}_chart_background_image_opacity", 30, type=int)

    if not bg_image_path:
        return ""

    # Convert Windows path to file:/// URL for WebView
    from pathlib import Path
    image_path = Path(bg_image_path).as_posix()
    file_url = f"file:///{image_path}"

    # Calculate opacity (0-100 -> 0.0-1.0)
    opacity_value = bg_opacity / 100.0

    css_style = f"""
        #chart-container::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: url('{file_url}');
            background-size: cover;
            background-position: center;
            background-repeat: no-repeat;
            opacity: {opacity_value};
            z-index: 0;
            pointer-events: none;
        }}
        #chart-container > * {{
            position: relative;
            z-index: 1;
        }}
    """

    logger.debug(f"Generated background image style: opacity={opacity_value}, path={bg_image_path}")
    return css_style


def get_chart_colors_config() -> dict:
    """Get chart colors from QSettings for JavaScript injection (Issues #34, #37).

    Returns:
        Dictionary with chart color configuration.
    """
    settings = QSettings("OrderPilot", "TradingApp")

    # Get current theme to load theme-specific colors
    theme_name = settings.value("theme", "Dark Orange")
    t_key = theme_name.lower().replace(" ", "_")

    # Default colors (fallback to standard theme)
    colors = {
        "background": "#0a0a0a",
        "upColor": "#26a69a",
        "downColor": "#ef5350",
        "wickUpColor": "#26a69a",
        "wickDownColor": "#ef5350",
    }

    # Load custom colors with theme prefix
    bullish = settings.value(f"{t_key}_chart_bullish_color", None)
    if bullish:
        colors["upColor"] = bullish
        colors["wickUpColor"] = bullish

    bearish = settings.value(f"{t_key}_chart_bearish_color", None)
    if bearish:
        colors["downColor"] = bearish
        colors["wickDownColor"] = bearish

    background = settings.value(f"{t_key}_chart_background_color", None)
    if background:
        colors["background"] = background

    logger.debug(f"Chart colors config for theme '{theme_name}': {colors}")
    return colors


def get_chart_html_template() -> str:
    """Get the complete chart HTML template with zone primitives injected.

    Issue #35: Injects background image CSS if configured.
    Issues #34, #37: Injects custom chart colors from settings.
    Issue #39: Injects candle border radius setting.

    Returns:
        Complete HTML template string with all JavaScript included.
    """
    zone_js = get_zone_javascript()
    template = _load_chart_template()

    # Replace zone primitive placeholder
    template = template.replace(
        "// ZONE_PRIMITIVE_JS_PLACEHOLDER",
        zone_js
    )

    # Issue #35: Inject background image CSS
    bg_image_style = get_background_image_style()
    if bg_image_style:
        # Inject before closing </style> tag
        template = template.replace(
            "</style>",
            f"{bg_image_style}\n    </style>"
        )

    # Issues #34, #37: Inject custom chart colors
    colors = get_chart_colors_config()

    # Replace hardcoded background color in layout
    template = template.replace(
        "background: { type: 'solid', color: '#0a0a0a' }",
        f"background: {{ type: 'solid', color: '{colors['background']}' }}"
    )

    # Replace hardcoded candle colors
    template = template.replace(
        "upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350'",
        f"upColor: '{colors['upColor']}', downColor: '{colors['downColor']}', borderVisible: false, wickUpColor: '{colors['wickUpColor']}', wickDownColor: '{colors['wickDownColor']}'"
    )

    # Issue #39: Inject candle border radius into JavaScript
    settings = QSettings("OrderPilot", "TradingApp")
    border_radius = settings.value("chart_candle_border_radius", 0, type=int)

    # Inject border radius and custom colors BEFORE window.chartAPI definition
    template = template.replace(
        "window.chartAPI = {",
        f"""// Issue #39: Border radius setting
                window._candleBorderRadius = {border_radius};

                // Issue #37/#40: Custom candle colors for overlay
                window._customCandleColors = {{ upColor: '{colors['upColor']}', downColor: '{colors['downColor']}' }};

                window.chartAPI = {{"""
    )

    logger.debug(f"Injected border radius: {border_radius}, colors: {colors}")
    return template
