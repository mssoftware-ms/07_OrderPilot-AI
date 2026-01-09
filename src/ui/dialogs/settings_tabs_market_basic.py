"""Settings Tabs - Market Data Basic Providers.

Refactored from 820 LOC monolith using composition pattern.

Module 2/7 of settings_tabs_mixin.py split.

Contains:
- _build_alpha_tab(): Alpha Vantage settings
- _build_finnhub_tab(): Finnhub settings
- _build_yahoo_tab(): Yahoo Finance settings
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
)


class SettingsTabsMarketBasic:
    """Helper für Market Data Basic Tabs (Alpha, Finnhub, Yahoo)."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent

    def build_alpha_tab(self) -> QWidget:
        """Build Alpha Vantage settings tab."""
        alpha_tab = QWidget()
        alpha_layout = QFormLayout(alpha_tab)

        self.parent.alpha_enabled = QCheckBox("Enable Alpha Vantage provider")
        alpha_layout.addRow(self.parent.alpha_enabled)

        self.parent.alpha_api_key = QLineEdit()
        self.parent.alpha_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.alpha_api_key.setPlaceholderText("Enter Alpha Vantage API key")
        alpha_layout.addRow("API Key:", self.parent.alpha_api_key)

        alpha_info = QLabel(
            "Alpha Vantage free tier allows up to 5 requests per minute. "
            "Enable only if you entered a valid API key."
        )
        alpha_info.setWordWrap(True)
        alpha_layout.addRow(alpha_info)
        return alpha_tab

    def build_finnhub_tab(self) -> QWidget:
        """Build Finnhub settings tab."""
        finnhub_tab = QWidget()
        finnhub_layout = QFormLayout(finnhub_tab)

        self.parent.finnhub_enabled = QCheckBox("Enable Finnhub provider")
        finnhub_layout.addRow(self.parent.finnhub_enabled)

        self.parent.finnhub_api_key = QLineEdit()
        self.parent.finnhub_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.finnhub_api_key.setPlaceholderText("Enter Finnhub API key")
        finnhub_layout.addRow("API Key:", self.parent.finnhub_api_key)

        finnhub_info = QLabel(
            "Finnhub offers real-time and historical market data. "
            "Free plans provide limited intraday history."
        )
        finnhub_info.setWordWrap(True)
        finnhub_layout.addRow(finnhub_info)
        return finnhub_tab

    def build_yahoo_tab(self) -> QWidget:
        """Build Yahoo Finance settings tab."""
        yahoo_tab = QWidget()
        yahoo_layout = QFormLayout(yahoo_tab)

        self.parent.yahoo_enabled = QCheckBox("Enable Yahoo Finance provider")
        yahoo_layout.addRow(self.parent.yahoo_enabled)

        yahoo_info = QLabel(
            "Yahoo Finance data is fetched anonymously via public endpoints. " "No API key required."
        )
        yahoo_info.setWordWrap(True)
        yahoo_layout.addRow(yahoo_info)
        return yahoo_tab
