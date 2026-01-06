"""Central Registry for Technical Indicator Configurations.

Decouples UI indicator definitions from implementation logic.
"""

from typing import Dict, Tuple, Optional, Any
from dataclasses import dataclass

from src.core.indicators.engine import IndicatorType

@dataclass
class IndicatorDefinition:
    """Definition of a UI-accessible indicator."""
    type: IndicatorType
    default_params: Dict[str, Any]
    display_name_template: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None

# Overlay Indicators (plotted on top of price)
OVERLAY_INDICATORS: Dict[str, IndicatorDefinition] = {
    "SMA": IndicatorDefinition(
        IndicatorType.SMA, {'period': 20}, "SMA(20)"
    ),
    "EMA": IndicatorDefinition(
        IndicatorType.EMA, {'period': 20}, "EMA(20)"
    ),
    "BB": IndicatorDefinition(
        IndicatorType.BB, {'period': 20, 'std': 2}, "BB(20,2)"
    ),
}

# Oscillator Indicators (plotted in separate panels)
OSCILLATOR_INDICATORS: Dict[str, IndicatorDefinition] = {
    "RSI": IndicatorDefinition(
        IndicatorType.RSI, {'period': 14}, "RSI(14)", 0, 100
    ),
    "MACD": IndicatorDefinition(
        IndicatorType.MACD, {'fast': 12, 'slow': 26, 'signal': 9}, "MACD(12,26,9)"
    ),
    "STOCH": IndicatorDefinition(
        IndicatorType.STOCH, {'k_period': 14, 'd_period': 3}, "STOCH(14,3)", 0, 100
    ),
    "ATR": IndicatorDefinition(
        IndicatorType.ATR, {'period': 14}, "ATR(14)", 0, None
    ),
    "ADX": IndicatorDefinition(
        IndicatorType.ADX, {'period': 14}, "ADX(14)", 0, 100
    ),
    "CCI": IndicatorDefinition(
        IndicatorType.CCI, {'period': 20}, "CCI(20)", -100, 100
    ),
    "MFI": IndicatorDefinition(
        IndicatorType.MFI, {'period': 14}, "MFI(14)", 0, 100
    ),
    "BB_WIDTH": IndicatorDefinition(
        IndicatorType.BB_WIDTH, {'period': 20, 'std': 2}, "BB Width", 0, None
    ),
    "BB_PERCENT": IndicatorDefinition(
        IndicatorType.BB_PERCENT, {'period': 20, 'std': 2}, "%B", 0, 1.2
    ),
}

def get_overlay_configs() -> Dict[str, Tuple[IndicatorType, Dict, str, None, None]]:
    """Get overlay configs in legacy format for compatibility."""
    return {
        key: (d.type, d.default_params, d.display_name_template, d.min_value, d.max_value)
        for key, d in OVERLAY_INDICATORS.items()
    }

def get_oscillator_configs() -> Dict[str, Tuple[IndicatorType, Dict, str, Optional[float], Optional[float]]]:
    """Get oscillator configs in legacy format for compatibility."""
    return {
        key: (d.type, d.default_params, d.display_name_template, d.min_value, d.max_value)
        for key, d in OSCILLATOR_INDICATORS.items()
    }
