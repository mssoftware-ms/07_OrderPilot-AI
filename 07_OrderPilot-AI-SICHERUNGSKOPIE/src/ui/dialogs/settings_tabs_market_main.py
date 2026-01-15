"""Settings Tabs - Market Data Main Tab.

Refactored from 820 LOC monolith using composition pattern.

Module 5/7 of settings_tabs_mixin.py split.

Contains:
- _create_market_data_tab(): Main Market Data tab with provider tabs
- _add_market_provider_tabs(): Adds all 5 provider tabs to QTabWidget
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)


class SettingsTabsMarketMain:
    """Helper für Market Data Main Tab mit Provider-Tabs."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent

    def create_market_data_tab(self) -> QWidget:
        """Create market data settings tab with provider sub-tabs."""
        tab = QWidget()
        layout = QVBoxLayout(tab)

        # Create tab widget for different providers
        self.parent.market_tabs = QTabWidget()
        layout.addWidget(self.parent.market_tabs)

        # Add all provider tabs (delegates to helper modules)
        self._add_market_provider_tabs()

        # Preferred data source behavior
        self.parent.prefer_live_broker = QCheckBox(
            "Prefer live broker market data when connected"
        )
        layout.addWidget(self.parent.prefer_live_broker)

        # Live data in paper mode
        self.parent.enable_live_data_paper = QCheckBox(
            "Enable live market data in paper trading mode"
        )
        self.parent.enable_live_data_paper.setToolTip(
            "When enabled, live market data from configured providers "
            "will be used even in paper trading mode"
        )
        layout.addWidget(self.parent.enable_live_data_paper)

        layout.addStretch()

        return tab

    def _add_market_provider_tabs(self) -> None:
        """Add all market data provider tabs to the tab widget."""
        # Delegate to respective helper modules for tab creation
        self.parent.market_tabs.addTab(
            self.parent._market_basic_helper.build_alpha_tab(),
            "Alpha Vantage"
        )
        self.parent.market_tabs.addTab(
            self.parent._market_basic_helper.build_finnhub_tab(),
            "Finnhub"
        )
        self.parent.market_tabs.addTab(
            self.parent._market_basic_helper.build_yahoo_tab(),
            "Yahoo Finance"
        )
        self.parent.market_tabs.addTab(
            self.parent._alpaca_helper.build_alpaca_tab(),
            "Alpaca"
        )
        self.parent.market_tabs.addTab(
            self.parent._bitunix_helper.build_bitunix_tab(),
            "Bitunix"
        )
