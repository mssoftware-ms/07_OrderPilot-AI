"""Indicator Calculator Factory Pattern.

Refactored from indicator_optimization_thread._calculate_indicator() (CC=86).
Uses Factory Pattern to eliminate massive if-elif chain.

Structure:
- BaseIndicatorCalculator: Abstract base class
- IndicatorCalculatorFactory: Central registration and dispatch
- Momentum calculators: RSI, MACD, Stochastic, CCI
- Trend calculators: SMA, EMA, Ichimoku, VWAP
- Volume calculators: OBV, MFI, AD, CMF
- Volatility calculators: ATR, Bollinger Bands, Keltner Channels

Benefits:
- CC reduction: 86 → ~5 per calculator
- Single Responsibility Principle
- Easy to add new indicators
- Independent testing per calculator
- Clean separation of concerns
"""

from .base_calculator import BaseIndicatorCalculator
from .calculator_factory import IndicatorCalculatorFactory

__all__ = ['BaseIndicatorCalculator', 'IndicatorCalculatorFactory']
