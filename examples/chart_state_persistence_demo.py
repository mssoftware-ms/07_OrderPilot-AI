"""Demo: Chart State Persistence in OrderPilot-AI

This example demonstrates how to use the comprehensive chart state persistence
system to automatically save and restore:
- Zoom factors and pan positions
- Indicator configurations and their row heights
- Window geometry and layouts
- Pane layouts and splitter positions

Usage:
    python examples/chart_state_persistence_demo.py
"""

import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout, QLabel
from PyQt6.QtCore import Qt

from ui.widgets.enhanced_chart_window import get_chart_window_manager, EnhancedChartWindow
from ui.widgets.chart_factory import ChartType
from ui.widgets.chart_state_manager import get_chart_state_manager, IndicatorState, PaneLayout, ViewRange

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ChartStateDemoWindow(QMainWindow):
    """Demo window showing chart state persistence features."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("OrderPilot-AI Chart State Persistence Demo")
        self.setGeometry(100, 100, 400, 300)

        # Get managers
        self.chart_manager = get_chart_window_manager()
        self.state_manager = get_chart_state_manager()

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup demo UI."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # Title
        title = QLabel("📊 Chart State Persistence Demo")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 18pt; font-weight: bold; padding: 10px;")
        layout.addWidget(title)

        # Description
        desc = QLabel(
            "This demo shows how chart states are automatically saved and restored:\n"
            "• Zoom levels and pan positions\n"
            "• Indicator configurations and row heights\n"
            "• Window geometry and layouts\n"
            "• Pane layouts and splitter positions"
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("padding: 10px; background: #f0f0f0; border-radius: 5px;")
        layout.addWidget(desc)

        # Chart buttons
        chart_layout = QHBoxLayout()

        # Stock charts
        btn_aapl = QPushButton("Open AAPL Chart")
        btn_aapl.clicked.connect(lambda: self.open_chart("AAPL"))
        chart_layout.addWidget(btn_aapl)

        btn_googl = QPushButton("Open GOOGL Chart")
        btn_googl.clicked.connect(lambda: self.open_chart("GOOGL"))
        chart_layout.addWidget(btn_googl)

        btn_tsla = QPushButton("Open TSLA Chart")
        btn_tsla.clicked.connect(lambda: self.open_chart("TSLA"))
        chart_layout.addWidget(btn_tsla)

        layout.addLayout(chart_layout)

        # Crypto charts
        crypto_layout = QHBoxLayout()

        btn_btc = QPushButton("Open BTC/USD Chart")
        btn_btc.clicked.connect(lambda: self.open_chart("BTC/USD"))
        crypto_layout.addWidget(btn_btc)

        btn_eth = QPushButton("Open ETH/USD Chart")
        btn_eth.clicked.connect(lambda: self.open_chart("ETH/USD"))
        crypto_layout.addWidget(btn_eth)

        btn_sol = QPushButton("Open SOL/USD Chart")
        btn_sol.clicked.connect(lambda: self.open_chart("SOL/USD"))
        crypto_layout.addWidget(btn_sol)

        layout.addLayout(crypto_layout)

        # Action buttons
        action_layout = QHBoxLayout()

        btn_demo_states = QPushButton("🔧 Demo: Setup Example States")
        btn_demo_states.clicked.connect(self.create_demo_states)
        action_layout.addWidget(btn_demo_states)

        btn_show_states = QPushButton("📋 Show Saved States")
        btn_show_states.clicked.connect(self.show_saved_states)
        action_layout.addWidget(btn_show_states)

        layout.addLayout(action_layout)

        # Management buttons
        mgmt_layout = QHBoxLayout()

        btn_close_all = QPushButton("❌ Close All Charts")
        btn_close_all.clicked.connect(self.chart_manager.close_all_charts)
        mgmt_layout.addWidget(btn_close_all)

        btn_clear_states = QPushButton("🗑️ Clear All States")
        btn_clear_states.clicked.connect(self.clear_all_states)
        mgmt_layout.addWidget(btn_clear_states)

        layout.addLayout(mgmt_layout)

        # Status area
        self.status_label = QLabel("Ready. Open a chart and adjust zoom/indicators - they will be automatically saved!")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet("padding: 10px; background: #e8f5e8; border-radius: 5px;")
        layout.addWidget(self.status_label)

    def _connect_signals(self):
        """Connect signals for feedback."""
        self.state_manager.state_saved.connect(self._on_state_saved)
        self.state_manager.state_loaded.connect(self._on_state_loaded)

    def open_chart(self, symbol: str, chart_type: ChartType = ChartType.AUTO):
        """Open chart with automatic state restoration."""
        try:
            logger.info(f"Opening chart for {symbol}")

            # Check if we have saved state
            saved_symbols = self.state_manager.list_saved_symbols()
            has_saved_state = symbol in saved_symbols

            window = self.chart_manager.open_chart(symbol, chart_type)

            if has_saved_state:
                self.status_label.setText(f"✅ Opened {symbol} chart with restored state (zoom, indicators, layout)")
            else:
                self.status_label.setText(f"📊 Opened {symbol} chart (fresh state - adjust zoom/indicators and they'll be saved)")

        except Exception as e:
            logger.error(f"Failed to open chart for {symbol}: {e}")
            self.status_label.setText(f"❌ Error opening {symbol}: {e}")

    def create_demo_states(self):
        """Create example saved states to demonstrate restoration."""
        try:
            from ui.widgets.chart_state_manager import ChartState, IndicatorState, ViewRange, PaneLayout

            # Example state for AAPL
            aapl_indicators = [
                IndicatorState(type="SMA", alias="sma_20", params={"period": 20}, visible=True, pane_index=0),
                IndicatorState(type="RSI", alias="rsi_14", params={"period": 14}, visible=True, pane_index=1, row_height=0.3),
                IndicatorState(type="MACD", alias="macd", params={"fast": 12, "slow": 26, "signal": 9}, visible=True, pane_index=2, row_height=0.3)
            ]

            aapl_state = ChartState(
                symbol="AAPL",
                timeframe="1H",
                chart_type="tradingview",
                view_range=ViewRange(x_min=0, x_max=100, logical_range_from=80, logical_range_to=100),
                pane_layout=PaneLayout(pane_count=3, pane_heights=[0.4, 0.3, 0.3]),
                indicators=aapl_indicators,
                show_volume=True,
                show_crosshair=True
            )

            # Example state for BTC/USD
            btc_indicators = [
                IndicatorState(type="EMA", alias="ema_21", params={"period": 21}, visible=True, pane_index=0),
                IndicatorState(type="BBANDS", alias="bb_20", params={"period": 20, "deviation": 2}, visible=True, pane_index=0),
                IndicatorState(type="STOCH", alias="stoch", params={"k_period": 14, "d_period": 3}, visible=True, pane_index=1, row_height=0.25)
            ]

            btc_state = ChartState(
                symbol="BTC/USD",
                timeframe="4H",
                chart_type="tradingview",
                view_range=ViewRange(x_min=0, x_max=100, logical_range_from=60, logical_range_to=100),
                pane_layout=PaneLayout(pane_count=2, pane_heights=[0.75, 0.25]),
                indicators=btc_indicators,
                show_volume=True,
                show_crosshair=True
            )

            # Save states
            self.state_manager.save_chart_state("AAPL", aapl_state)
            self.state_manager.save_chart_state("BTC/USD", btc_state)

            self.status_label.setText("✅ Created demo states for AAPL and BTC/USD. Open these charts to see restoration!")
            logger.info("Created demo chart states")

        except Exception as e:
            logger.error(f"Failed to create demo states: {e}")
            self.status_label.setText(f"❌ Error creating demo states: {e}")

    def show_saved_states(self):
        """Show information about saved states."""
        try:
            saved_symbols = self.state_manager.list_saved_symbols()

            if not saved_symbols:
                self.status_label.setText("ℹ️ No saved chart states found. Open charts and adjust them to create states!")
                return

            # Get detailed state info
            state_info = []
            for symbol in saved_symbols:
                chart_state = self.state_manager.load_chart_state(symbol)
                if chart_state:
                    indicators = len(chart_state.indicators) if chart_state.indicators else 0
                    panes = chart_state.pane_layout.pane_count if chart_state.pane_layout else 1

                    state_info.append(f"{symbol} ({chart_state.timeframe}, {indicators} indicators, {panes} panes)")

            status_text = f"💾 Saved states ({len(saved_symbols)}): " + " | ".join(state_info)
            self.status_label.setText(status_text)

        except Exception as e:
            logger.error(f"Failed to show saved states: {e}")
            self.status_label.setText(f"❌ Error loading saved states: {e}")

    def clear_all_states(self):
        """Clear all saved chart states."""
        try:
            self.state_manager.clear_all_states()
            self.status_label.setText("🗑️ Cleared all saved chart states. Charts will start fresh now.")
            logger.info("Cleared all chart states")

        except Exception as e:
            logger.error(f"Failed to clear states: {e}")
            self.status_label.setText(f"❌ Error clearing states: {e}")

    def _on_state_saved(self, symbol: str):
        """Handle state saved signal."""
        self.status_label.setText(f"💾 Auto-saved chart state for {symbol}")

    def _on_state_loaded(self, symbol: str, state_dict: dict):
        """Handle state loaded signal."""
        self.status_label.setText(f"📂 Loaded saved chart state for {symbol}")


def main():
    """Run the chart state persistence demo."""
    app = QApplication(sys.argv)

    # Set application details for QSettings
    app.setOrganizationName("OrderPilot")
    app.setApplicationName("TradingApp")

    # Create and show demo window
    demo_window = ChartStateDemoWindow()
    demo_window.show()

    # Show usage instructions
    print("\n" + "="*60)
    print("📊 OrderPilot-AI Chart State Persistence Demo")
    print("="*60)
    print("\n🎯 Instructions:")
    print("1. Click 'Demo: Setup Example States' to create example configurations")
    print("2. Open AAPL or BTC/USD charts to see automatic state restoration")
    print("3. Open other charts and adjust zoom, indicators, and layout")
    print("4. Close and reopen charts - your settings will be preserved!")
    print("5. Use 'Show Saved States' to see what's been saved")
    print("\n💡 Features demonstrated:")
    print("• Automatic zoom and pan position saving")
    print("• Indicator configurations and row heights")
    print("• Window geometry and layout preservation")
    print("• Multi-pane layouts with custom heights")
    print("\n📁 State storage location:")

    # Get storage location
    from PyQt6.QtCore import QSettings
    settings = QSettings("OrderPilot", "TradingApp")
    print(f"• {settings.fileName()}")
    print("\n" + "="*60)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())