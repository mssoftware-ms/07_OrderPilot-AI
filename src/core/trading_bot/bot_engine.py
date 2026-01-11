"""
Trading Bot Engine - Zentrale State Machine und Orchestrierung (REFACTORED)

Die Haupt-Engine des Trading Bots. Koordiniert:
- State Machine (IDLE → ANALYZING → IN_POSITION)
- Signal-Generierung
- Risk Management
- Position Monitoring
- AI Validation
- Trade Logging

Nutzt Composition Pattern mit 5 Helper-Klassen:
- BotEngineLifecycle: start/stop + analysis loop
- BotEngineCallbacks: callback management + state/log
- BotEngineStatistics: daily reset + trade statistics
- BotEnginePersistence: save/load position to JSON
- BotEngineStatus: properties + status queries

WICHTIG: Arbeitet NUR im Paper-Modus!
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pandas as pd

if TYPE_CHECKING:
    from PyQt6.QtCore import pyqtSignal

    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
    from src.core.broker.broker_types import OrderRequest, OrderResponse, Position

from .ai_validator import AISignalValidator, AIValidation
from .bot_config import BotConfig
from .bot_engine_callbacks import BotEngineCallbacks
from .bot_engine_lifecycle import BotEngineLifecycle
from .bot_engine_persistence import BotEnginePersistence
from .bot_engine_statistics import BotEngineStatistics
from .bot_engine_status import BotEngineStatus
from .bot_market_analyzer import BotMarketAnalyzer
from .bot_trade_handler import BotTradeHandler
from .bot_types import BotState, BotStatistics
from .position_monitor import (
    ExitResult,
    ExitTrigger,
    MonitoredPosition,
    PositionMonitor,
)
from .risk_manager import RiskCalculation, RiskManager
from .signal_generator import SignalDirection, SignalGenerator, TradeSignal
from .strategy_config import StrategyConfig, get_strategy_config
from .trade_logger import (
    ExitReason,
    IndicatorSnapshot,
    MarketContext,
    SignalDetails,
    TradeLogEntry,
    TradeLogger,
    TradeOutcome,
)

logger = logging.getLogger(__name__)


class TradingBotEngine:
    """
    Haupt-Engine des Trading Bots (REFACTORED via Composition).

    Koordiniert alle Komponenten und verwaltet den Bot-Lebenszyklus.
    Delegiert spezifische Aufgaben an Helper-Klassen.

    SICHERHEIT: Arbeitet NUR mit BitunixPaperAdapter!
    """

    def __init__(
        self,
        adapter: "BitunixPaperAdapter",
        config: BotConfig | None = None,
        strategy_config_path: Path | str | None = None,
    ):
        """
        Args:
            adapter: BitunixPaperAdapter (NUR PAPER!)
            config: Bot-Konfiguration
            strategy_config_path: Pfad zur JSON Strategie-Konfiguration
        """
        # SICHERHEITS-CHECK: Nur Paper-Adapter erlaubt!
        adapter_class = type(adapter).__name__
        if "Paper" not in adapter_class:
            raise ValueError(
                f"SICHERHEITSFEHLER: TradingBotEngine akzeptiert NUR Paper-Adapter! "
                f"Erhalten: {adapter_class}"
            )

        self.adapter = adapter
        self.config = config or BotConfig()
        self.strategy_config = get_strategy_config(strategy_config_path)

        # Komponenten initialisieren
        self.signal_generator = SignalGenerator(
            min_confluence=self.strategy_config.min_confluence_long
        )
        self.risk_manager = RiskManager(
            config=self.config,
            strategy_config=self.strategy_config,
        )
        self.position_monitor = PositionMonitor(
            risk_manager=self.risk_manager,
            check_interval_ms=self.config.position_check_interval_ms,
        )
        # AISignalValidator - Provider und Model kommen aus QSettings (File -> Settings -> AI)!
        self.ai_validator = AISignalValidator(
            enabled=self.strategy_config.ai_config.enabled,
            confidence_threshold_trade=self.strategy_config.ai_config.confidence_threshold_trade,
            confidence_threshold_deep=self.strategy_config.ai_config.confidence_threshold_deep,
            deep_analysis_enabled=self.strategy_config.ai_config.deep_analysis_enabled,
            fallback_to_technical=self.strategy_config.ai_config.fallback_to_technical,
        )
        self.trade_logger = TradeLogger(
            log_directory=self.config.logging.log_directory,
            log_format=self.config.logging.log_format,
        )

        # Helper-Klassen initialisieren
        self.market_analyzer = BotMarketAnalyzer(self)
        self.trade_handler = BotTradeHandler(self)

        # State
        self._state = BotState.IDLE
        self._running = False
        self._current_trade_log: TradeLogEntry | None = None
        self._last_signal: TradeSignal | None = None
        self._last_analysis_time: datetime | None = None
        self._last_error: str | None = None

        # Statistics
        self._stats = BotStatistics(
            date=datetime.now(timezone.utc).strftime("%Y-%m-%d")
        )

        # Callbacks für UI
        self._on_state_changed: Callable[[BotState], None] | None = None
        self._on_signal_generated: Callable[[TradeSignal], None] | None = None
        self._on_position_opened: Callable[[MonitoredPosition], None] | None = None
        self._on_position_closed: Callable[[TradeLogEntry], None] | None = None
        self._on_error: Callable[[str], None] | None = None
        self._on_log: Callable[[str], None] | None = None

        # Timer/Task
        self._analysis_task: asyncio.Task | None = None

        # Composition Pattern: Create helper instances
        self._lifecycle = BotEngineLifecycle(self)
        self._callbacks = BotEngineCallbacks(self)
        self._statistics = BotEngineStatistics(self)
        self._persistence = BotEnginePersistence(self)
        self._status = BotEngineStatus(self)

        # Setup Position Monitor Callbacks
        self.position_monitor.set_exit_callback(self.trade_handler.on_exit_triggered)
        self.position_monitor.set_trailing_callback(self.trade_handler.on_trailing_updated)
        self.position_monitor.set_price_callback(self.trade_handler.on_price_updated)

        logger.info(
            f"TradingBotEngine initialized (REFACTORED). "
            f"Symbol: {self.config.symbol}, "
            f"Leverage: {self.strategy_config.risk_config.leverage}x, "
            f"AI: {'Enabled' if self.ai_validator.enabled else 'Disabled'}"
        )

    # =========================================================================
    # PROPERTIES (delegiert an Status Helper)
    # =========================================================================

    @property
    def state(self) -> BotState:
        """Aktueller Bot-Zustand."""
        return self._status.state

    @property
    def is_running(self) -> bool:
        """Bot läuft?"""
        return self._status.is_running

    @property
    def has_position(self) -> bool:
        """Position offen?"""
        return self._status.has_position

    @property
    def statistics(self) -> BotStatistics:
        """Aktuelle Statistiken."""
        return self._status.statistics

    # =========================================================================
    # CHART DATA INTERFACE (delegiert an Market Analyzer)
    # =========================================================================

    def set_chart_data(
        self,
        data: pd.DataFrame,
        symbol: str,
        timeframe: str,
    ) -> None:
        """Setzt Chart-Daten (delegiert)."""
        self.market_analyzer.set_chart_data(data, symbol, timeframe)

    def clear_chart_data(self) -> None:
        """Löscht Chart-Daten (delegiert)."""
        self.market_analyzer.clear_chart_data()

    @property
    def has_chart_data(self) -> bool:
        """Sind Chart-Daten verfügbar? (delegiert)."""
        return self.market_analyzer.has_chart_data

    # =========================================================================
    # LIFECYCLE (delegiert an Lifecycle Helper)
    # =========================================================================

    async def start(self) -> None:
        """Startet den Bot (delegiert)."""
        await self._lifecycle.start()

    async def stop(self, close_position: bool = False) -> None:
        """Stoppt den Bot (delegiert)."""
        await self._lifecycle.stop(close_position)

    # =========================================================================
    # PUBLIC STATUS (delegiert an Status Helper)
    # =========================================================================

    def get_current_status(self) -> dict:
        """Gibt aktuellen Bot-Status zurück (delegiert)."""
        return self._status.get_current_status()

    # =========================================================================
    # CALLBACKS (delegiert an Callbacks Helper)
    # =========================================================================

    def set_state_callback(self, callback: Callable[[BotState], None]) -> None:
        """Setzt Callback für State-Änderungen (delegiert)."""
        self._callbacks.set_state_callback(callback)

    def set_signal_callback(self, callback: Callable[[TradeSignal], None]) -> None:
        """Setzt Callback für neue Signale (delegiert)."""
        self._callbacks.set_signal_callback(callback)

    def set_position_opened_callback(
        self, callback: Callable[[MonitoredPosition], None]
    ) -> None:
        """Setzt Callback für Position-Öffnung (delegiert)."""
        self._callbacks.set_position_opened_callback(callback)

    def set_position_closed_callback(
        self, callback: Callable[[TradeLogEntry], None]
    ) -> None:
        """Setzt Callback für Position-Schließung (delegiert)."""
        self._callbacks.set_position_closed_callback(callback)

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Fehler (delegiert)."""
        self._callbacks.set_error_callback(callback)

    def set_log_callback(self, callback: Callable[[str], None]) -> None:
        """Setzt Callback für Log-Nachrichten (delegiert)."""
        self._callbacks.set_log_callback(callback)

    # =========================================================================
    # MANUAL CONTROLS (delegiert an Trade Handler)
    # =========================================================================

    async def manual_close_position(self) -> None:
        """Schließt Position manuell (delegiert)."""
        await self.trade_handler.manual_close_position()

    async def on_price_update(self, price: Decimal) -> None:
        """Preis-Update von außen (delegiert)."""
        await self.trade_handler.on_price_update(price)

    # =========================================================================
    # CONFIG UPDATE
    # =========================================================================

    def update_config(self, config: BotConfig) -> None:
        """
        Aktualisiert die Bot-Konfiguration.

        Einige Änderungen werden erst nach Neustart wirksam.
        """
        self.config = config
        self.risk_manager.update_config(config)
        self.ai_validator.update_config(
            enabled=config.ai.enabled,
            confidence_threshold=config.ai.confidence_threshold,
        )
        if config.logging.enabled:
            config.logging.log_directory.mkdir(parents=True, exist_ok=True)
        self._callbacks._log(
            f"Config aktualisiert: Risk={config.risk_per_trade_percent}%, "
            f"SL={config.sl_atr_multiplier}x ATR"
        )
        logger.info("Bot config updated")

    def update_indicator_config(
        self,
        indicator_updates: dict,
        save: bool = True,
    ) -> None:
        """
        Aktualisiert Indikator-Konfiguration (für Strategy Bridge).

        Ermöglicht das Übernehmen von optimierten Parametern aus dem
        Strategy Simulator in die aktive Trading-Strategie.

        Args:
            indicator_updates: Dict mit Indikator-Parametern
                Format: {"rsi_period": 14, "adx_threshold": 25, ...}
            save: Ob Konfiguration gespeichert werden soll
        """
        self.strategy_config.update_indicator_config(indicator_updates, save)
        self._callbacks._log(
            f"Indicator config updated: {list(indicator_updates.keys())}"
        )
        logger.info(f"Indicator config updated via Strategy Bridge: {indicator_updates}")
