"""Bitunix Trading Widget - Mirror Dock for Bitunix Futures Trading.

REFACTORED: Now uses BitunixTradingAPIWidget (compact) + SignalsTableMirror
instead of custom UI components. This widget mirrors the main TradingBotWindow
interface in a compact dock panel.

Features:
    - Mirrors BitunixTradingAPIWidget from TradingBotWindow
    - Shows compact signals table (11 columns)
    - Synchronized state via BitunixTradingStateManager
    - Full trading functionality (not read-only)

Public API:
    - set_master_widget(widget): Connect to master BitunixTradingAPIWidget
    - set_master_table(table): Connect to master signals table
    - set_state_manager(manager): Set central state manager
    - set_symbol(symbol): Set trading symbol
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from datetime import datetime, timedelta
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtWidgets import (
    QDockWidget,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QLabel,
    QFrame,
    QTableWidget,
    QPushButton,
    QGroupBox,
    QComboBox,
    QGridLayout,
)

if TYPE_CHECKING:
    from src.ui.widgets.bitunix_trading_api_widget import BitunixTradingAPIWidget
    from src.ui.widgets.bitunix_trading.bitunix_state_manager import BitunixTradingStateManager

logger = logging.getLogger(__name__)


class BitunixTradingWidget(QDockWidget):
    """Dockable mirror widget for Bitunix Futures trading.

    This widget provides a compact vertical interface that mirrors:
    1. BitunixTradingAPIWidget (compact layout) - for order entry
    2. SignalsTableMirror - 11 columns from the main signals table

    Architecture (Mirror Pattern):
    - Connects to BitunixTradingStateManager for state synchronization
    - All orders are coordinated through the state manager
    - Prevents duplicate order execution

    Signals:
        visibility_changed: Emitted when dock visibility changes
    """

    visibility_changed = pyqtSignal(bool)

    def __init__(
        self,
        state_manager: Optional["BitunixTradingStateManager"] = None,
        parent: QWidget = None
    ):
        """Initialize Bitunix trading dock widget.

        Args:
            state_manager: Central state manager for coordination
            parent: Parent widget
        """
        super().__init__("💱 Bitunix Trading", parent)
        self.setObjectName("bitunixTradingDock")

        # References
        self._state_manager = state_manager
        self._master_widget: Optional["BitunixTradingAPIWidget"] = None
        self._master_table: Optional[QTableWidget] = None

        # Child widgets (created in _setup_ui)
        self._api_widget: Optional["BitunixTradingAPIWidget"] = None
        self._signals_mirror = None

        # Guard against recursive statistics refresh
        self._stats_refresh_in_progress = False
        self._stats_refresh_pending = False

        # Throttle timer for statistics - 200ms debounce (statistics don't need instant updates)
        self._stats_timer = QTimer(self)
        self._stats_timer.setSingleShot(True)
        self._stats_timer.setInterval(200)  # 200ms debounce for stats
        self._stats_timer.timeout.connect(self._do_refresh_statistics)

        self._setup_ui()

        logger.info("BitunixTradingWidget initialized (Mirror mode)")

    def _setup_ui(self) -> None:
        """Set up the widget UI with compact mirror components."""
        self.setAllowedAreas(Qt.DockWidgetArea.RightDockWidgetArea)
        self.setMinimumWidth(320)
        # No maximum width - allow user to resize freely

        # Main container
        container = QWidget()
        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 1: BitunixTradingAPIWidget (compact vertical layout)
        # ─────────────────────────────────────────────────────────────────
        self._create_api_widget()
        if self._api_widget:
            main_layout.addWidget(self._api_widget)

        # Separator
        main_layout.addWidget(self._create_separator())

        # ─────────────────────────────────────────────────────────────────
        # SECTION 2: Bot Controls GroupBox (Start/Stop Bot + Status Label)
        # ─────────────────────────────────────────────────────────────────
        self._create_bot_controls()
        main_layout.addWidget(self._bot_controls_group)

        # ─────────────────────────────────────────────────────────────────
        # SECTION 3: Signals Table Mirror (compact 11-column table)
        # ─────────────────────────────────────────────────────────────────
        self._create_signals_mirror()
        if self._signals_mirror:
            main_layout.addWidget(self._signals_mirror, stretch=1)

        self.setWidget(container)

    def _create_api_widget(self) -> None:
        """Create the compact BitunixTradingAPIWidget."""
        try:
            from src.ui.widgets.bitunix_trading_api_widget import BitunixTradingAPIWidget

            self._api_widget = BitunixTradingAPIWidget(
                parent=self,
                is_mirror=True,
                state_manager=self._state_manager,
                compact_layout=True,
                title="Order Entry"
            )
            logger.debug("Created compact BitunixTradingAPIWidget for dock")

        except Exception as e:
            logger.error(f"Failed to create API widget: {e}", exc_info=True)
            # Fallback: show error label
            self._api_widget = QLabel(f"API Widget Error: {e}")
            self._api_widget.setStyleSheet("color: red;")

    def _create_signals_mirror(self) -> None:
        """Create the signals table mirror widget."""
        try:
            from src.ui.widgets.bitunix_trading.signals_table_mirror import (
                SignalsTableMirrorWidget
            )

            self._signals_mirror = SignalsTableMirrorWidget(
                master_table=self._master_table,
                title="📊 Recent Signals",
                parent=self
            )
            logger.debug("Created SignalsTableMirror for dock")

        except Exception as e:
            logger.error(f"Failed to create signals mirror: {e}", exc_info=True)
            # Fallback: show error label
            self._signals_mirror = QLabel(f"Signals Mirror Error: {e}")
            self._signals_mirror.setStyleSheet("color: red;")

    def _create_separator(self) -> QFrame:
        """Create a horizontal separator line."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #3a3a3a;")
        line.setFixedHeight(1)
        return line

    def _create_bot_controls(self) -> None:
        """Create bot controls GroupBox with Start/Stop button, status, and statistics."""
        self._bot_controls_group = QGroupBox("Trading Bot")
        main_layout = QVBoxLayout(self._bot_controls_group)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ── Row 1: Status + Start/Stop Button ──
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._bot_status_label = QLabel("Status: STOPPED")
        self._bot_status_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
        top_row.addWidget(self._bot_status_label)

        top_row.addStretch()

        self._start_bot_btn = QPushButton("▶ Start Bot")
        self._start_bot_btn.setFixedHeight(24)
        self._start_bot_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 12px; background-color: #ef5350; "
            "color: white; font-weight: bold;"
        )
        self._start_bot_btn.setToolTip(
            "Startet/Stoppt den Trading Bot\n"
            "Grün = Bot läuft\n"
            "Rot = Bot gestoppt"
        )
        self._start_bot_btn.clicked.connect(self._on_start_bot_clicked)
        top_row.addWidget(self._start_bot_btn)

        main_layout.addLayout(top_row)

        # ── Row 2: Time Filter + P&L Stats ──
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)

        # Time filter combo
        filter_label = QLabel("Zeitraum:")
        filter_label.setStyleSheet("color: #888; font-size: 10px;")
        stats_row.addWidget(filter_label)

        self._time_filter_combo = QComboBox()
        self._time_filter_combo.addItems(["Tag", "Woche", "Monat", "Kpl"])
        self._time_filter_combo.setCurrentText("Kpl")
        self._time_filter_combo.setFixedWidth(70)
        self._time_filter_combo.setStyleSheet("font-size: 10px;")
        self._time_filter_combo.currentTextChanged.connect(self._on_time_filter_changed)
        stats_row.addWidget(self._time_filter_combo)

        stats_row.addSpacing(10)

        # P&L % label
        self._pnl_pct_label = QLabel("P&L: 0.00%")
        self._pnl_pct_label.setStyleSheet("font-weight: bold; color: #9e9e9e; font-size: 11px;")
        stats_row.addWidget(self._pnl_pct_label)

        stats_row.addSpacing(10)

        # P&L USDT label
        self._pnl_usdt_label = QLabel("0.00 USDT")
        self._pnl_usdt_label.setStyleSheet("font-weight: bold; color: #9e9e9e; font-size: 11px;")
        stats_row.addWidget(self._pnl_usdt_label)

        stats_row.addStretch()
        main_layout.addLayout(stats_row)

        # ── Row 3: Top Strategy ──
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        top_label = QLabel("Top:")
        top_label.setStyleSheet("color: #26a69a; font-size: 10px; font-weight: bold;")
        top_row.addWidget(top_label)

        self._top_strategies_label = QLabel("-")
        self._top_strategies_label.setStyleSheet("color: #26a69a; font-size: 10px;")
        top_row.addWidget(self._top_strategies_label)

        top_row.addStretch()
        main_layout.addLayout(top_row)

        # ── Row 4: Worst Strategy ──
        worst_row = QHBoxLayout()
        worst_row.setSpacing(4)

        worst_label = QLabel("Worst:")
        worst_label.setStyleSheet("color: #ef5350; font-size: 10px; font-weight: bold;")
        worst_row.addWidget(worst_label)

        self._worst_strategies_label = QLabel("-")
        self._worst_strategies_label.setStyleSheet("color: #ef5350; font-size: 10px;")
        worst_row.addWidget(self._worst_strategies_label)

        worst_row.addStretch()
        main_layout.addLayout(worst_row)

    def _on_time_filter_changed(self, filter_text: str) -> None:
        """Handle time filter change - recalculate statistics."""
        self._refresh_statistics()

    def _refresh_statistics(self) -> None:
        """Schedule throttled statistics refresh from master signals table."""
        if not self._master_table:
            return

        # Guard against recursive refresh
        if self._stats_refresh_in_progress:
            return

        # Use timer-based debounce - don't refresh immediately
        self._stats_refresh_pending = True
        if not self._stats_timer.isActive():
            self._stats_timer.start()

    def _do_refresh_statistics(self) -> None:
        """Internal statistics refresh (called by debounce timer)."""
        if not self._master_table:
            return

        if self._stats_refresh_in_progress:
            # Reschedule if already running
            self._stats_timer.start()
            return

        self._stats_refresh_in_progress = True
        self._stats_refresh_pending = False

        try:
            self._calculate_statistics()
        finally:
            self._stats_refresh_in_progress = False

    def _calculate_statistics(self) -> None:
        """Calculate and display statistics from master table."""
        filter_text = self._time_filter_combo.currentText()
        now = datetime.now()

        # Determine cutoff date based on filter
        if filter_text == "Tag":
            cutoff = now - timedelta(days=1)
        elif filter_text == "Woche":
            cutoff = now - timedelta(weeks=1)
        elif filter_text == "Monat":
            cutoff = now - timedelta(days=30)
        else:  # "Kpl" - complete
            cutoff = None

        # Collect data from master table
        # Master columns: 0=Time, 2=Strategy, 12=P&L%, 13=P&L USDT
        total_pnl_pct = 0.0
        total_pnl_usdt = 0.0
        strategy_pnl_pct: dict[str, float] = {}  # strategy -> total P&L %
        valid_rows = 0

        for row in range(self._master_table.rowCount()):
            # Check time filter
            if cutoff:
                time_item = self._master_table.item(row, 0)
                if time_item:
                    try:
                        # Parse time - try common formats
                        time_str = time_item.text()
                        row_time = None
                        for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M"]:
                            try:
                                row_time = datetime.strptime(time_str, fmt)
                                break
                            except ValueError:
                                continue
                        if row_time and row_time < cutoff:
                            continue  # Skip rows outside time range
                    except Exception:
                        pass  # Include row if time parsing fails

            # Get P&L % (column 12)
            pnl_pct = 0.0
            pnl_pct_item = self._master_table.item(row, 12)
            if pnl_pct_item:
                try:
                    pnl_pct_text = pnl_pct_item.text().replace("%", "").replace(",", ".").strip()
                    if pnl_pct_text and pnl_pct_text != "-":
                        pnl_pct = float(pnl_pct_text)
                        total_pnl_pct += pnl_pct
                except (ValueError, AttributeError):
                    pass

            # Get P&L USDT (column 13)
            pnl_usdt_item = self._master_table.item(row, 13)
            if pnl_usdt_item:
                try:
                    pnl_text = pnl_usdt_item.text().replace("USDT", "").replace(",", ".").strip()
                    if pnl_text and pnl_text != "-":
                        total_pnl_usdt += float(pnl_text)
                except (ValueError, AttributeError):
                    pass

            # Get Strategy (column 2) for ranking by P&L %
            strategy_item = self._master_table.item(row, 2)
            if strategy_item and pnl_pct != 0:
                strategy_name = strategy_item.text().strip()
                if strategy_name and strategy_name != "-":
                    strategy_pnl_pct[strategy_name] = strategy_pnl_pct.get(strategy_name, 0.0) + pnl_pct

            valid_rows += 1

        # Update P&L labels
        pnl_pct_color = "#26a69a" if total_pnl_pct >= 0 else "#ef5350"
        pnl_usdt_color = "#26a69a" if total_pnl_usdt >= 0 else "#ef5350"

        self._pnl_pct_label.setText(f"P&L: {total_pnl_pct:+.2f}%")
        self._pnl_pct_label.setStyleSheet(f"font-weight: bold; color: {pnl_pct_color}; font-size: 11px;")

        self._pnl_usdt_label.setText(f"{total_pnl_usdt:+.2f} USDT")
        self._pnl_usdt_label.setStyleSheet(f"font-weight: bold; color: {pnl_usdt_color}; font-size: 11px;")

        # Update strategy rankings (Top 1 and Worst 1 with P&L %)
        if strategy_pnl_pct:
            sorted_strategies = sorted(strategy_pnl_pct.items(), key=lambda x: x[1], reverse=True)

            # Top (best performer)
            if sorted_strategies:
                top_name, top_pct = sorted_strategies[0]
                self._top_strategies_label.setText(f"{top_name} {top_pct:+.2f}%")
            else:
                self._top_strategies_label.setText("-")

            # Worst (worst performer)
            if sorted_strategies:
                worst_name, worst_pct = sorted_strategies[-1]
                # Only show if it's actually negative or different from top
                if worst_pct < 0 or len(sorted_strategies) > 1:
                    self._worst_strategies_label.setText(f"{worst_name} {worst_pct:+.2f}%")
                else:
                    self._worst_strategies_label.setText("-")
            else:
                self._worst_strategies_label.setText("-")
        else:
            self._top_strategies_label.setText("-")
            self._worst_strategies_label.setText("-")

    def _on_start_bot_clicked(self) -> None:
        """Handle Start/Stop Bot button click - delegates to master."""
        # Find the ChartWindow (parent of dock) and call its bot toggle
        parent = self.parent()
        if parent and hasattr(parent, '_on_signals_tab_bot_toggle_clicked'):
            parent._on_signals_tab_bot_toggle_clicked()
        else:
            logger.warning("Cannot find _on_signals_tab_bot_toggle_clicked on parent")

    def _update_bot_button_state(self, running: bool) -> None:
        """Update the bot button appearance based on running state.

        Args:
            running: True if bot is running (green), False if stopped (red)
        """
        if running:
            self._start_bot_btn.setText("⏹ Stop Bot")
            self._start_bot_btn.setStyleSheet(
                "font-size: 10px; padding: 2px 12px; background-color: #26a69a; "
                "color: white; font-weight: bold;"
            )
            self._bot_status_label.setText("Status: RUNNING")
            self._bot_status_label.setStyleSheet("font-weight: bold; color: #26a69a;")
        else:
            self._start_bot_btn.setText("▶ Start Bot")
            self._start_bot_btn.setStyleSheet(
                "font-size: 10px; padding: 2px 12px; background-color: #ef5350; "
                "color: white; font-weight: bold;"
            )
            self._bot_status_label.setText("Status: STOPPED")
            self._bot_status_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")

    # ─────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────

    def set_state_manager(self, state_manager: "BitunixTradingStateManager") -> None:
        """Set the central state manager for coordination.

        Args:
            state_manager: BitunixTradingStateManager instance
        """
        self._state_manager = state_manager

        # Update API widget if it exists
        if self._api_widget and hasattr(self._api_widget, 'setup_as_mirror'):
            self._api_widget.setup_as_mirror(
                master_widget=self._master_widget,
                state_manager=state_manager,
                readonly=False
            )

        logger.info("State manager set for BitunixTradingWidget")

    def set_master_widget(self, master_widget: "BitunixTradingAPIWidget") -> None:
        """Connect to the master BitunixTradingAPIWidget for synchronization.

        Args:
            master_widget: The master widget in TradingBotWindow
        """
        self._master_widget = master_widget

        # Connect signals for direct synchronization (backup to state manager)
        if master_widget:
            if hasattr(master_widget, 'order_placed'):
                master_widget.order_placed.connect(self._on_master_order_placed)

        logger.info("Master widget connected to BitunixTradingWidget")

    def set_master_table(self, master_table: QTableWidget) -> None:
        """Connect to the master signals table for mirroring.

        Args:
            master_table: The main signals table (25 columns)
        """
        self._master_table = master_table

        # Update signals mirror
        if self._signals_mirror and hasattr(self._signals_mirror, 'set_master_table'):
            self._signals_mirror.set_master_table(master_table)

        # Connect to model signals for auto-refresh statistics
        if master_table:
            model = master_table.model()
            if model:
                model.dataChanged.connect(self._on_table_data_changed)
                model.rowsInserted.connect(self._on_table_data_changed)
                model.rowsRemoved.connect(self._on_table_data_changed)

        # Initial statistics refresh
        self._refresh_statistics()

        logger.info("Master signals table connected to BitunixTradingWidget")

    def set_symbol(self, symbol: str) -> None:
        """Set the current trading symbol.

        Args:
            symbol: Trading symbol (e.g., "BTCUSDT")
        """
        if self._api_widget and hasattr(self._api_widget, 'set_symbol'):
            self._api_widget.set_symbol(symbol)

        logger.debug(f"Symbol set to {symbol}")

    def set_price(self, price: float) -> None:
        """Update the current price display.

        Args:
            price: Current market price
        """
        if self._api_widget and hasattr(self._api_widget, 'set_price'):
            self._api_widget.set_price(price)

    def set_adapter(self, adapter) -> None:
        """Set the trading adapter.

        Args:
            adapter: BitunixAdapter or BitunixPaperAdapter
        """
        if self._api_widget and hasattr(self._api_widget, 'set_adapter'):
            self._api_widget.set_adapter(adapter)

    def set_bot_running(self, running: bool) -> None:
        """Update bot button and status label to reflect running state.

        Called by ChartWindow when bot state changes to keep dock in sync.

        Args:
            running: True if bot is running, False if stopped
        """
        self._update_bot_button_state(running)

    def refresh_statistics(self) -> None:
        """Public method to refresh statistics display."""
        self._refresh_statistics()

    # ─────────────────────────────────────────────────────────────────────
    # Signal Handlers
    # ─────────────────────────────────────────────────────────────────────

    def _on_table_data_changed(self, *args) -> None:
        """Handle master table data changes - refresh statistics."""
        self._refresh_statistics()

    def _on_master_order_placed(self, order_id: str) -> None:
        """Handle order placed in master widget."""
        logger.debug(f"Master order placed: {order_id}")
        # Could show notification or update UI

    # ─────────────────────────────────────────────────────────────────────
    # Lifecycle
    # ─────────────────────────────────────────────────────────────────────

    def showEvent(self, event) -> None:
        """Handle show event."""
        super().showEvent(event)
        self.visibility_changed.emit(True)

        # Refresh signals mirror when shown
        if self._signals_mirror and hasattr(self._signals_mirror, 'table'):
            self._signals_mirror.table.refresh()

        # Refresh statistics when shown
        self._refresh_statistics()

    def hideEvent(self, event) -> None:
        """Handle hide event."""
        super().hideEvent(event)
        self.visibility_changed.emit(False)

    def closeEvent(self, event) -> None:
        """Handle close event."""
        # Clean up mirror connections
        if self._api_widget and hasattr(self._api_widget, 'cleanup_mirror'):
            self._api_widget.cleanup_mirror()

        super().closeEvent(event)


# Backward compatibility exports
__all__ = ["BitunixTradingWidget"]
