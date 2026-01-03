"""BitunixTradingMixin - Adds Bitunix trading functionality to ChartWindow.

Provides seamless integration of the Bitunix trading widget into chart windows
for crypto symbols only.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt

from src.core.market_data.types import AssetClass

if TYPE_CHECKING:
    from src.ui.widgets.embedded_tradingview_chart import EmbeddedTradingViewChart
    from src.core.broker.bitunix_adapter import BitunixAdapter

logger = logging.getLogger(__name__)


class BitunixTradingMixin:
    """Mixin that adds Bitunix trading functionality to a window.

    Usage:
        class ChartWindow(QMainWindow, BitunixTradingMixin):
            def __init__(self):
                super().__init__()
                self.setup_bitunix_trading(self.chart_widget)
    """

    _bitunix_widget: Any = None
    _bitunix_adapter: Any = None

    def setup_bitunix_trading(
        self,
        chart_widget: "EmbeddedTradingViewChart",
        adapter: "BitunixAdapter | None" = None,
    ) -> bool:
        """Set up the Bitunix trading functionality.

        Args:
            chart_widget: The chart widget to trade from
            adapter: Optional Bitunix adapter (auto-creates if None)

        Returns:
            True if setup successful, False otherwise
        """
        try:
            # Import here to avoid circular imports
            from src.ui.widgets.bitunix_trading.bitunix_trading_widget import BitunixTradingWidget

            logger.info("Setting up Bitunix trading...")

            # Get or create adapter
            adapter = self._resolve_bitunix_adapter(adapter)

            # Create trading widget
            self._bitunix_widget = BitunixTradingWidget(
                adapter=adapter,
                parent=self,  # type: ignore
            )

            # Set initial symbol if crypto
            if hasattr(chart_widget, 'current_symbol'):
                symbol = chart_widget.current_symbol
                asset_class = self._get_symbol_asset_class(symbol)
                if asset_class == AssetClass.CRYPTO:
                    self._bitunix_widget.set_symbol(symbol)

            # Add as dock widget (assumes self is QMainWindow)
            self._dock_bitunix_widget()

            # Connect chart change signal if available
            self._connect_bitunix_chart_signals(chart_widget)

            # Perform initial button visibility check
            self._update_bitunix_button_visibility(chart_widget)

            logger.info("✅ Bitunix trading setup complete")
            return True

        except ImportError as e:
            logger.error("Failed to import Bitunix trading modules: %s", e)
            self._bitunix_widget = None
            self._bitunix_adapter = None
            return False
        except Exception as e:
            logger.exception("Failed to setup Bitunix trading: %s", e)
            self._bitunix_widget = None
            self._bitunix_adapter = None
            return False

    def _resolve_bitunix_adapter(self, adapter: "BitunixAdapter | None") -> "BitunixAdapter | None":
        """Resolve Bitunix adapter from various sources.

        Args:
            adapter: Provided adapter (if any)

        Returns:
            Bitunix adapter or None
        """
        if adapter is not None:
            return adapter

        logger.info("No Bitunix adapter provided, attempting to create one...")
        adapter = self._get_or_create_bitunix_adapter()

        if adapter is None:
            logger.warning(
                "No Bitunix adapter available for trading. "
                "Check Settings -> Brokers tab for configuration."
            )

        return adapter

    def _dock_bitunix_widget(self) -> None:
        """Add Bitunix widget as dock widget."""
        if hasattr(self, "addDockWidget"):
            self.addDockWidget(  # type: ignore
                Qt.DockWidgetArea.RightDockWidgetArea,
                self._bitunix_widget,
            )
            self._bitunix_widget.hide()
            logger.info("Bitunix widget added as dock widget (initially hidden)")

    def _connect_bitunix_chart_signals(self, chart_widget: "EmbeddedTradingViewChart") -> None:
        """Connect to chart signals to update symbol.

        Args:
            chart_widget: Chart widget to monitor
        """
        if hasattr(chart_widget, "symbol_changed"):
            chart_widget.symbol_changed.connect(self._on_bitunix_chart_symbol_changed)

    def _get_or_create_bitunix_adapter(self) -> "BitunixAdapter | None":
        """Get or create a Bitunix adapter instance.

        Returns:
            Bitunix adapter instance or None
        """
        logger.info("🔍 _get_or_create_bitunix_adapter called...")

        # Try to get from self
        if hasattr(self, "bitunix_adapter") and self.bitunix_adapter is not None:
            logger.info("Using existing bitunix_adapter from self")
            return self.bitunix_adapter

        # Try to get from parent application
        app = self._get_parent_app()
        if app and hasattr(app, "bitunix_adapter") and app.bitunix_adapter is not None:
            logger.info("Using bitunix_adapter from parent app")
            return app.bitunix_adapter

        # Try to create from credentials
        logger.info("Attempting to create Bitunix adapter from credentials...")
        try:
            from src.core.broker.bitunix_adapter import BitunixAdapter
            from src.config.config_manager import config_manager

            api_key = config_manager.get_credential("bitunix_api_key")
            api_secret = config_manager.get_credential("bitunix_api_secret")
            use_testnet = config_manager.get_setting("bitunix_testnet", True)

            if not api_key or not api_secret:
                logger.warning("❌ Bitunix API credentials not found in config!")
                return None

            logger.info("Creating Bitunix adapter (testnet=%s)...", use_testnet)
            adapter = BitunixAdapter(
                api_key=api_key,
                api_secret=api_secret,
                use_testnet=use_testnet
            )

            # Store adapter - connection will be established when widget is shown
            logger.info("✅ Created Bitunix adapter (connection will be established on first use)")
            self._bitunix_adapter = adapter
            return adapter

        except ValueError as e:
            logger.error(f"❌ ValueError creating Bitunix adapter: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Exception creating Bitunix adapter: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            return None

    def _get_parent_app(self) -> Any | None:
        """Get the parent TradingApplication.

        Returns:
            TradingApplication instance or None
        """
        from PyQt6.QtWidgets import QApplication

        app = QApplication.instance()
        if app and hasattr(app, "main_window"):
            return app.main_window

        return None

    def _get_symbol_asset_class(self, symbol: str) -> AssetClass:
        """Determine asset class from symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Asset class (CRYPTO or STOCK)
        """
        # Simple heuristic: if symbol ends with USDT, USDC, USD, etc., it's crypto
        crypto_suffixes = ["USDT", "USDC", "USD", "BTC", "ETH"]
        for suffix in crypto_suffixes:
            if symbol.endswith(suffix):
                return AssetClass.CRYPTO

        return AssetClass.STOCK

    def _on_bitunix_chart_symbol_changed(self) -> None:
        """Handle chart symbol change."""
        if not self._bitunix_widget:
            return

        # Get new symbol from chart
        chart_widget = getattr(self, "chart_widget", None)
        if not chart_widget:
            return

        self._update_bitunix_button_visibility(chart_widget)

    def _update_bitunix_button_visibility(self, chart_widget: "EmbeddedTradingViewChart") -> None:
        """Update Bitunix button visibility based on current symbol.

        Args:
            chart_widget: The chart widget to check
        """
        if not hasattr(chart_widget, "current_symbol"):
            return

        symbol = chart_widget.current_symbol
        asset_class = self._get_symbol_asset_class(symbol)

        # Only show button and update widget for crypto symbols
        if asset_class == AssetClass.CRYPTO:
            if self._bitunix_widget:
                self._bitunix_widget.set_symbol(symbol)
                logger.info(f"Bitunix widget symbol updated to: {symbol}")

            # Show button for crypto
            if hasattr(chart_widget, "bitunix_trading_button"):
                chart_widget.bitunix_trading_button.setVisible(True)
        else:
            # Hide button for non-crypto
            if hasattr(chart_widget, "bitunix_trading_button"):
                chart_widget.bitunix_trading_button.setVisible(False)

    def toggle_bitunix_widget(self) -> None:
        """Toggle visibility of the Bitunix trading widget."""
        if self._bitunix_widget:
            if self._bitunix_widget.isVisible():
                self._bitunix_widget.hide()
            else:
                self._bitunix_widget.show()

    def show_bitunix_widget(self) -> None:
        """Show the Bitunix trading widget."""
        if self._bitunix_widget:
            self._bitunix_widget.show()
            self._bitunix_widget.raise_()

    def hide_bitunix_widget(self) -> None:
        """Hide the Bitunix trading widget."""
        if self._bitunix_widget:
            self._bitunix_widget.hide()

    @property
    def bitunix_widget(self) -> Any:
        """Get the Bitunix trading widget."""
        return self._bitunix_widget

    @property
    def bitunix_adapter(self) -> Any:
        """Get the Bitunix adapter."""
        return self._bitunix_adapter

    def cleanup_bitunix_trading(self) -> None:
        """Clean up Bitunix resources.

        Call this when closing the window.
        """
        if self._bitunix_adapter:
            import asyncio
            # Schedule disconnect task without blocking
            asyncio.create_task(self._bitunix_adapter.disconnect())

        if self._bitunix_widget:
            self._bitunix_widget.close()

        self._bitunix_widget = None
        self._bitunix_adapter = None
