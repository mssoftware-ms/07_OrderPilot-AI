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
    # Moving Averages
    "SMA": IndicatorDefinition(
        IndicatorType.SMA, {'period': 20}, "SMA(20)"
    ),
    "EMA": IndicatorDefinition(
        IndicatorType.EMA, {'period': 20}, "EMA(20)"
    ),
    "WMA": IndicatorDefinition(
        IndicatorType.WMA, {'period': 20}, "WMA(20)"
    ),
    "VWMA": IndicatorDefinition(
        IndicatorType.VWMA, {'period': 20}, "VWMA(20)"
    ),
    # Bands & Channels
    "BB": IndicatorDefinition(
        IndicatorType.BB, {'period': 20, 'std': 2}, "BB(20,2)"
    ),
    "KC": IndicatorDefinition(
        IndicatorType.KC, {'period': 20, 'mult': 1.5}, "KC(20,1.5)"
    ),
    # Trend Following
    "PSAR": IndicatorDefinition(
        IndicatorType.PSAR, {'af': 0.02, 'max_af': 0.2}, "PSAR"
    ),
    "ICHIMOKU": IndicatorDefinition(
        IndicatorType.ICHIMOKU, {'tenkan': 9, 'kijun': 26, 'senkou': 52}, "Ichimoku"
    ),
    # Volume Overlay
    "VWAP": IndicatorDefinition(
        IndicatorType.VWAP, {}, "VWAP"
    ),
}

# Oscillator Indicators (plotted in separate panels)
OSCILLATOR_INDICATORS: Dict[str, IndicatorDefinition] = {
    # Momentum Indicators
    "RSI": IndicatorDefinition(
        IndicatorType.RSI, {'period': 14}, "RSI(14)", 0, 100
    ),
    "MACD": IndicatorDefinition(
        IndicatorType.MACD, {'fast': 12, 'slow': 26, 'signal': 9}, "MACD(12,26,9)"
    ),
    "STOCH": IndicatorDefinition(
        IndicatorType.STOCH, {'k_period': 14, 'd_period': 3}, "STOCH(14,3)", 0, 100
    ),
    "CCI": IndicatorDefinition(
        IndicatorType.CCI, {'period': 20}, "CCI(20)", -200, 200
    ),
    "MFI": IndicatorDefinition(
        IndicatorType.MFI, {'period': 14}, "MFI(14)", 0, 100
    ),
    "MOM": IndicatorDefinition(
        IndicatorType.MOM, {'period': 10}, "MOM(10)", None, None
    ),
    "ROC": IndicatorDefinition(
        IndicatorType.ROC, {'period': 10}, "ROC(10)", None, None
    ),
    "WILLR": IndicatorDefinition(
        IndicatorType.WILLR, {'period': 14}, "Williams %R(14)", -100, 0
    ),
    # Trend Strength
    "ADX": IndicatorDefinition(
        IndicatorType.ADX, {'period': 14}, "ADX(14)", 0, 100
    ),
    # Volatility Indicators
    "ATR": IndicatorDefinition(
        IndicatorType.ATR, {'period': 14}, "ATR(14)", 0, None
    ),
    "NATR": IndicatorDefinition(
        IndicatorType.NATR, {'period': 14}, "NATR(14)", 0, None
    ),
    "STD": IndicatorDefinition(
        IndicatorType.STD, {'period': 20}, "StdDev(20)", 0, None
    ),
    "BB_WIDTH": IndicatorDefinition(
        IndicatorType.BB_WIDTH, {'period': 20, 'std': 2}, "BB Width", 0, None
    ),
    "BB_PERCENT": IndicatorDefinition(
        IndicatorType.BB_PERCENT, {'period': 20, 'std': 2}, "%B", 0, 1.2
    ),
    # Volume Indicators
    "OBV": IndicatorDefinition(
        IndicatorType.OBV, {}, "OBV", None, None
    ),
    "CMF": IndicatorDefinition(
        IndicatorType.CMF, {'period': 20}, "CMF(20)", -1, 1
    ),
    "AD": IndicatorDefinition(
        IndicatorType.AD, {}, "A/D Line", None, None
    ),
    "FI": IndicatorDefinition(
        IndicatorType.FI, {'period': 13}, "Force Index(13)", None, None
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
