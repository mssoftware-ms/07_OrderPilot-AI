"""Settings Tabs - Basic Settings (General, Trading, Broker).

Refactored from 820 LOC monolith using composition pattern.

Module 1/7 of settings_tabs_mixin.py split.

Contains:
- _create_general_tab(): Theme, auto-connect, default broker
- _create_trading_tab(): Order approval, max size, risk tolerance
- _create_broker_tab(): IBKR, Trade Republic, Bitunix broker settings
"""

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QWidget,
)


class SettingsTabsBasic:
    """Helper für Basic Settings Tabs (General, Trading, Broker)."""

    def __init__(self, parent):
        """
        Args:
            parent: SettingsDialog Instanz
        """
        self.parent = parent

    def create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.parent.theme_combo = QComboBox()
        self.parent.theme_combo.addItems(["Dark", "Light"])
        layout.addRow("Theme:", self.parent.theme_combo)

        # Auto-connect broker
        self.parent.auto_connect_check = QCheckBox("Auto-connect to broker on startup")
        layout.addRow(self.parent.auto_connect_check)

        # Default broker
        self.parent.default_broker_combo = QComboBox()
        self.parent.default_broker_combo.addItems(["Mock Broker", "Interactive Brokers", "Trade Republic"])
        layout.addRow("Default Broker:", self.parent.default_broker_combo)

        return tab

    def create_trading_tab(self) -> QWidget:
        """Create trading settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        self.parent.manual_approval = QCheckBox("Require manual approval for orders")
        self.parent.manual_approval.setChecked(True)
        layout.addRow(self.parent.manual_approval)

        self.parent.confirm_cancel = QCheckBox("Confirm before canceling orders")
        self.parent.confirm_cancel.setChecked(True)
        layout.addRow(self.parent.confirm_cancel)

        # Max order size
        self.parent.max_order_size = QDoubleSpinBox()
        self.parent.max_order_size.setRange(100, 100000)
        self.parent.max_order_size.setValue(10000)
        self.parent.max_order_size.setPrefix("€")
        layout.addRow("Max Order Size:", self.parent.max_order_size)

        # Risk tolerance
        self.parent.risk_combo = QComboBox()
        self.parent.risk_combo.addItems(["Conservative", "Moderate", "Aggressive"])
        layout.addRow("Risk Tolerance:", self.parent.risk_combo)

        return tab

    def create_broker_tab(self) -> QWidget:
        """Create broker settings tab."""
        tab = QWidget()
        layout = QFormLayout(tab)

        # IBKR Settings
        layout.addRow(QLabel("<b>Interactive Brokers (IBKR)</b>"))

        self.parent.ibkr_host = QLineEdit()
        self.parent.ibkr_host.setPlaceholderText("localhost or IP address")
        layout.addRow("IBKR Host:", self.parent.ibkr_host)

        self.parent.ibkr_port = QComboBox()
        self.parent.ibkr_port.addItems(["7497 (Paper)", "7496 (Live)"])
        layout.addRow("IBKR Port:", self.parent.ibkr_port)

        self.parent.ibkr_client_id = QComboBox()
        self.parent.ibkr_client_id.addItems(["1", "2", "3", "4", "5"])
        layout.addRow("IBKR Client ID:", self.parent.ibkr_client_id)

        # Trade Republic Settings
        layout.addRow(QLabel("<b>Trade Republic</b>"))

        self.parent.tr_phone = QLineEdit()
        self.parent.tr_phone.setPlaceholderText("+49...")
        layout.addRow("Phone Number:", self.parent.tr_phone)

        self.parent.tr_pin = QLineEdit()
        self.parent.tr_pin.setEchoMode(QLineEdit.EchoMode.Password)
        self.parent.tr_pin.setPlaceholderText("4-digit PIN")
        self.parent.tr_pin.setMaxLength(4)
        layout.addRow("PIN:", self.parent.tr_pin)

        # Bitunix Settings
        layout.addRow(QLabel(""))  # Spacer
        layout.addRow(QLabel("<b>Bitunix Futures</b>"))

        self.parent.bitunix_broker_enabled = QCheckBox("Enable Bitunix for trading")
        layout.addRow(self.parent.bitunix_broker_enabled)

        bitunix_note = QLabel("<i>Note: Configure API keys in Market Data → Bitunix tab</i>")
        bitunix_note.setWordWrap(True)
        layout.addRow(bitunix_note)

        return tab
