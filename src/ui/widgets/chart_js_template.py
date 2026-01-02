"""TradingView Lightweight Charts HTML/JavaScript Template."""

from __future__ import annotations

from pathlib import Path

from src.chart_marking.zones.zone_primitive_js import get_zone_javascript

_TEMPLATE_PATH = Path(__file__).with_name("chart_js_template.html")


def _load_chart_template() -> str:
    """Load the HTML/JS template from disk.

    Note: No caching to allow hot-reload during development.
    """
    return _TEMPLATE_PATH.read_text(encoding="utf-8")


# For backwards compatibility (though get_chart_html_template() should be preferred)
CHART_HTML_TEMPLATE = _load_chart_template()


def get_chart_html_template() -> str:
    """Get the complete chart HTML template with zone primitives injected.

    Returns:
        Complete HTML template string with all JavaScript included.
    """
    zone_js = get_zone_javascript()
    return _load_chart_template().replace(
        "// ZONE_PRIMITIVE_JS_PLACEHOLDER",
        zone_js
    )
