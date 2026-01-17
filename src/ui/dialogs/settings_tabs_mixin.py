"""Settings Dialog Tab Creation Mixin - Refactored Orchestrator.

Refactored from 820 LOC monolith using composition pattern.

Module 7/7 - Main Orchestrator.

Delegates to 6 specialized helper modules:
- SettingsTabsBasic: General, Trading, Broker tabs
- SettingsTabsMarketBasic: Alpha Vantage, Finnhub, Yahoo Finance tabs
- SettingsTabsAlpaca: Alpaca API + Historical Download
- SettingsTabsBitunix: Bitunix API + Historical Download
- SettingsTabsMarketMain: Market Data tab orchestrator
- SettingsTabsAI: AI provider tabs (OpenAI, Anthropic, Gemini)

Provides:
- Tab creation delegation methods (_create_general_tab, _create_ai_tab, etc.)
- _create_notifications_tab(): Notifications settings (order fills, alerts, connections)
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QWidget,
)

from src.ui.dialogs.settings_tabs_basic import SettingsTabsBasic
from src.ui.dialogs.settings_tabs_market_basic import SettingsTabsMarketBasic
from src.ui.dialogs.settings_tabs_alpaca import SettingsTabsAlpaca
from src.ui.dialogs.settings_tabs_bitunix import SettingsTabsBitunix
from src.ui.dialogs.settings_tabs_market_main import SettingsTabsMarketMain
from src.ui.dialogs.settings_tabs_ai import SettingsTabsAI
from src.ui.dialogs.settings_tabs_data_quality import SettingsTabsDataQuality


class SettingsTabsMixin:
    """Mixin providing tab creation methods for SettingsDialog.

    Refactored using composition pattern with 6 specialized helpers.
    """

    def __init__(self, *args, **kwargs):
        """Initialize all helper modules for tab creation.

        Args:
            *args, **kwargs: Passed to next class in MRO (e.g., QDialog)
        """
        # Pass arguments to next class in MRO (cooperative multiple inheritance)
        super().__init__(*args, **kwargs)

        # Instantiate helper modules (composition pattern)
        self._basic_helper = SettingsTabsBasic(parent=self)
        self._market_basic_helper = SettingsTabsMarketBasic(parent=self)
        self._alpaca_helper = SettingsTabsAlpaca(parent=self)
        self._bitunix_helper = SettingsTabsBitunix(parent=self)
        self._market_main_helper = SettingsTabsMarketMain(parent=self)
        self._ai_helper = SettingsTabsAI(parent=self)
        self._data_quality_helper = SettingsTabsDataQuality(parent=self)

    # ========================================================================
    # Basic Settings Tabs (General, Trading, Broker)
    # ========================================================================

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab.

        Delegates to SettingsTabsBasic.create_general_tab().
        """
        return self._basic_helper.create_general_tab()

    def _create_trading_tab(self) -> QWidget:
        """Create trading settings tab.

        Delegates to SettingsTabsBasic.create_trading_tab().
        """
        return self._basic_helper.create_trading_tab()

    def _create_broker_tab(self) -> QWidget:
        """Create broker settings tab.

        Delegates to SettingsTabsBasic.create_broker_tab().
        """
        return self._basic_helper.create_broker_tab()

    # ========================================================================
    # Market Data Tab
    # ========================================================================

    def _create_market_data_tab(self) -> QWidget:
        """Create market data settings tab with provider sub-tabs.

        Delegates to SettingsTabsMarketMain.create_market_data_tab().
        """
        return self._market_main_helper.create_market_data_tab()

    # ========================================================================
    # AI Settings Tab
    # ========================================================================

    def _create_ai_tab(self) -> QWidget:
        """Create AI settings tab with provider sub-tabs.

        Delegates to SettingsTabsAI.create_ai_tab().
        """
        return self._ai_helper.create_ai_tab()

    # ========================================================================
    # Data Quality Tab
    # ========================================================================

    def _create_data_quality_tab(self) -> QWidget:
        """Create data quality tab.

        Delegates to SettingsTabsDataQuality.create_data_quality_tab().
        """
        return self._data_quality_helper.create_data_quality_tab()

    # ========================================================================
    # Notifications Tab
    # ========================================================================

    def _create_notifications_tab(self) -> QWidget:
        """Create notifications settings tab.

        Contains:
            - Order fills notifications
            - Alert notifications
            - Connection change notifications
        """
        tab = QWidget()
        layout = QFormLayout(tab)

        self.order_filled_notif = QCheckBox("Notify on order fills")
        self.order_filled_notif.setChecked(True)
        layout.addRow(self.order_filled_notif)

        self.alert_notif = QCheckBox("Notify on alerts")
        self.alert_notif.setChecked(True)
        layout.addRow(self.alert_notif)

        self.connection_notif = QCheckBox("Notify on connection changes")
        self.connection_notif.setChecked(False)
        layout.addRow(self.connection_notif)

        return tab

    # -------------------------------------------------------------------- #
    # AI slot delegates (backward compatibility for SettingsDialog)
    # -------------------------------------------------------------------- #
    def _on_openai_model_changed(self, model_text: str):
        """Forward model change events to the AI helper."""
        return self._ai_helper._on_openai_model_changed(model_text)

    def _on_openai_reasoning_changed(self, reasoning_effort: str):
        """Forward reasoning effort changes to the AI helper."""
        return self._ai_helper._on_openai_reasoning_changed(reasoning_effort)


# Re-export für backward compatibility
__all__ = ["SettingsTabsMixin"]
