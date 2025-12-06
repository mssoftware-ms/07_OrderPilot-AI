"""Configuration management for OrderPilot-AI.

This package provides configuration management with support for multiple
trading modes (Backtest, Paper, Live) and comprehensive safety validation.
"""

from src.config.loader import (
    AIConfig,
    AlertConfig,
    AppSettings,
    BacktestConfig,
    BrokerConfig,
    BrokerType,
    ConfigManager,
    DatabaseConfig,
    ExecutionConfig,
    MarketDataProviderConfig,
    MonitoringConfig,
    ProfileConfig,
    TradingConfig,
    TradingEnvironment,
    TradingMode,
    UIConfig,
    config_manager,
)

__all__ = [
    # Enums
    "TradingEnvironment",
    "TradingMode",
    "BrokerType",
    # Config classes
    "AIConfig",
    "AlertConfig",
    "AppSettings",
    "BacktestConfig",
    "BrokerConfig",
    "DatabaseConfig",
    "ExecutionConfig",
    "MarketDataProviderConfig",
    "MonitoringConfig",
    "ProfileConfig",
    "TradingConfig",
    "UIConfig",
    # Manager
    "ConfigManager",
    "config_manager",
]
