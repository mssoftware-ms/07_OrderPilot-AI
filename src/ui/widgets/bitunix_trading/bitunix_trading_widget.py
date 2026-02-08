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

# Import design system for theme-consistent colors
from src.ui.design_system import THEMES, ColorPalette, theme_service

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

        # Get theme palette for consistent styling
        self._palette = self._get_theme_palette()

        self._setup_ui()

        # Subscribe to theme changes for live updates
        theme_service.subscribe(self._on_theme_changed)

        logger.info("BitunixTradingWidget initialized (Mirror mode)")

    def _get_theme_palette(self) -> ColorPalette:
        """Get the current theme palette from app settings or default."""
        try:
            from PyQt6.QtCore import QSettings
            settings = QSettings("OrderPilot", "TradingApp")
            theme_name = settings.value("theme/name", "Dark Orange")
            key = theme_name.lower().replace(" ", "_")
            return THEMES.get(key, THEMES["dark_orange"])
        except Exception:
            return THEMES["dark_orange"]

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
        """Create a horizontal separator line using theme colors."""
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        # Use theme border color
        line.setStyleSheet(f"background-color: {self._palette.border_main};")
        line.setFixedHeight(1)
        return line

    def _create_bot_controls(self) -> None:
        """Create bot controls GroupBox with Start/Stop button, status, and statistics."""
        p = self._palette  # Shorthand for theme palette

        self._bot_controls_group = QGroupBox("Trading Bot")
        main_layout = QVBoxLayout(self._bot_controls_group)
        main_layout.setContentsMargins(6, 6, 6, 6)
        main_layout.setSpacing(6)

        # ── Row 1: Status + Start/Stop Button ──
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._bot_status_label = QLabel("Status: STOPPED")
        self._bot_status_label.setStyleSheet(f"font-weight: bold; color: {p.text_secondary};")
        top_row.addWidget(self._bot_status_label)

        top_row.addStretch()

        self._start_bot_btn = QPushButton("▶ Start Bot")
        self._start_bot_btn.setFixedHeight(24)
        self._start_bot_btn.setProperty("class", "danger")  # Use theme class
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
        filter_label.setProperty("class", "info-label")  # Use theme class
        stats_row.addWidget(filter_label)

        self._time_filter_combo = QComboBox()
        self._time_filter_combo.addItems(["Tag", "Woche", "Monat", "Kpl"])
        self._time_filter_combo.setCurrentText("Kpl")
        self._time_filter_combo.setFixedWidth(70)
        self._time_filter_combo.currentTextChanged.connect(self._on_time_filter_changed)
        stats_row.addWidget(self._time_filter_combo)

        stats_row.addSpacing(10)

        # P&L % label
        self._pnl_pct_label = QLabel("P&L: 0.00%")
        self._pnl_pct_label.setStyleSheet(f"font-weight: bold; color: {p.text_secondary};")
        stats_row.addWidget(self._pnl_pct_label)

        stats_row.addSpacing(10)

        # P&L USDT label
        self._pnl_usdt_label = QLabel("0.00 USDT")
        self._pnl_usdt_label.setStyleSheet(f"font-weight: bold; color: {p.text_secondary};")
        stats_row.addWidget(self._pnl_usdt_label)

        stats_row.addStretch()
        main_layout.addLayout(stats_row)

        # ── Row 3: Top Strategy ──
        strategy_top_row = QHBoxLayout()
        strategy_top_row.setSpacing(4)

        top_label = QLabel("Top:")
        top_label.setStyleSheet(f"color: {p.success}; font-weight: bold;")
        strategy_top_row.addWidget(top_label)

        self._top_strategies_label = QLabel("-")
        self._top_strategies_label.setStyleSheet(f"color: {p.success};")
        strategy_top_row.addWidget(self._top_strategies_label)

        strategy_top_row.addStretch()
        main_layout.addLayout(strategy_top_row)

        # ── Row 4: Worst Strategy ──
        worst_row = QHBoxLayout()
        worst_row.setSpacing(4)

        worst_label = QLabel("Worst:")
        worst_label.setStyleSheet(f"color: {p.error}; font-weight: bold;")
        worst_row.addWidget(worst_label)

        self._worst_strategies_label = QLabel("-")
        self._worst_strategies_label.setStyleSheet(f"color: {p.error};")
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

        def _parse_row_time(time_str: str) -> Optional[datetime]:
            time_str = time_str.strip()
            if not time_str:
                return None
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M"]:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
            for fmt in ["%H:%M:%S", "%H:%M"]:
                try:
                    parsed_time = datetime.strptime(time_str, fmt).time()
                    return datetime.combine(now.date(), parsed_time)
                except ValueError:
                    continue
            return None

        # Determine cutoff date based on filter
        # "Tag" = from midnight today (00:00), not last 24 hours
        if filter_text == "Tag":
            cutoff = datetime.combine(now.date(), datetime.min.time())  # Today 00:00:00
        elif filter_text == "Woche":
            # Start of current week (Monday 00:00)
            days_since_monday = now.weekday()
            week_start = now.date() - timedelta(days=days_since_monday)
            cutoff = datetime.combine(week_start, datetime.min.time())
        elif filter_text == "Monat":
            # Start of current month (1st day 00:00)
            cutoff = datetime.combine(now.date().replace(day=1), datetime.min.time())
        else:  # "Kpl" - complete
            cutoff = None

        # Collect data from master table
        # Master columns: 0=Time, 2=Strategy, 12=P&L%, 13=P&L USDT, 16=Invested
        total_pnl_usdt = 0.0
        total_invested = 0.0
        strategy_pnl: dict[str, dict] = {}  # strategy -> {"pnl_usdt": float, "invested": float}
        valid_rows = 0

        for row in range(self._master_table.rowCount()):
            # Check time filter
            if cutoff:
                time_item = self._master_table.item(row, 0)
                row_time = _parse_row_time(time_item.text()) if time_item else None
                if not row_time:
                    continue  # Skip rows if time cannot be parsed when filtering
                if row_time < cutoff:
                    continue  # Skip rows outside time range

            # Get Invested amount (column 16) for weighted P&L% calculation
            invested = 0.0
            invested_item = self._master_table.item(row, 16)
            if invested_item:
                try:
                    invested_text = invested_item.text().replace("USDT", "").replace(",", ".").strip()
                    if invested_text and invested_text != "-":
                        invested = float(invested_text)
                        total_invested += invested
                except (ValueError, AttributeError):
                    pass

            # Get P&L USDT (column 13)
            pnl_usdt = 0.0
            pnl_usdt_item = self._master_table.item(row, 13)
            if pnl_usdt_item:
                try:
                    pnl_text = pnl_usdt_item.text().replace("USDT", "").replace(",", ".").strip()
                    if pnl_text and pnl_text != "-":
                        pnl_usdt = float(pnl_text)
                        total_pnl_usdt += pnl_usdt
                except (ValueError, AttributeError):
                    pass

            # Get Strategy (column 2) for ranking
            strategy_item = self._master_table.item(row, 2)
            if strategy_item and (pnl_usdt != 0 or invested > 0):
                strategy_name = strategy_item.text().strip()
                base_strategy = strategy_name.split(" | ", 1)[0].strip()
                if base_strategy and base_strategy != "-":
                    if base_strategy not in strategy_pnl:
                        strategy_pnl[base_strategy] = {"pnl_usdt": 0.0, "invested": 0.0}
                    strategy_pnl[base_strategy]["pnl_usdt"] += pnl_usdt
                    strategy_pnl[base_strategy]["invested"] += invested

            valid_rows += 1

        # Calculate weighted P&L% = (Total P&L USDT / Total Invested) * 100
        if total_invested > 0:
            total_pnl_pct = (total_pnl_usdt / total_invested) * 100
        else:
            total_pnl_pct = 0.0

        # Calculate strategy P&L percentages (weighted)
        strategy_pnl_pct: dict[str, float] = {}
        for strat_name, data in strategy_pnl.items():
            if data["invested"] > 0:
                strategy_pnl_pct[strat_name] = (data["pnl_usdt"] / data["invested"]) * 100
            elif data["pnl_usdt"] != 0:
                # Fallback: if no invested but has P&L, show as-is (shouldn't happen normally)
                strategy_pnl_pct[strat_name] = data["pnl_usdt"]

        # Update P&L labels using theme colors
        pnl_pct_color = self._palette.success if total_pnl_pct >= 0 else self._palette.error
        pnl_usdt_color = self._palette.success if total_pnl_usdt >= 0 else self._palette.error

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
                f"font-size: 10px; padding: 2px 12px; background-color: {self._palette.success}; "
                f"color: {self._palette.text_inverse}; font-weight: bold;"
            )
            self._bot_status_label.setText("Status: RUNNING")
            self._bot_status_label.setStyleSheet(f"font-weight: bold; color: {self._palette.success};")
        else:
            self._start_bot_btn.setText("▶ Start Bot")
            self._start_bot_btn.setStyleSheet(
                f"font-size: 10px; padding: 2px 12px; background-color: {self._palette.error}; "
                f"color: {self._palette.text_inverse}; font-weight: bold;"
            )
            self._bot_status_label.setText("Status: STOPPED")
            self._bot_status_label.setStyleSheet(f"font-weight: bold; color: {self._palette.text_secondary};")

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

    def _on_theme_changed(self, new_palette: ColorPalette) -> None:
        """Handle theme change - update all styled components.

        Args:
            new_palette: The new ColorPalette to apply.
        """
        self._palette = new_palette
        logger.debug(f"BitunixTradingWidget theme changed to: {new_palette.name}")

        # Update bot controls styling
        p = self._palette

        # Update status label color
        if hasattr(self, '_bot_status_label'):
            # Preserve current running state
            is_running = "RUNNING" in self._bot_status_label.text()
            if is_running:
                self._bot_status_label.setStyleSheet(f"font-weight: bold; color: {p.success};")
            else:
                self._bot_status_label.setStyleSheet(f"font-weight: bold; color: {p.text_secondary};")

        # Update P&L labels
        if hasattr(self, '_pnl_pct_label'):
            # Re-apply colors based on current value
            self._do_refresh_statistics()

        # Update strategy labels
        if hasattr(self, '_top_strategies_label'):
            self._top_strategies_label.setStyleSheet(f"color: {p.success};")
        if hasattr(self, '_worst_strategies_label'):
            self._worst_strategies_label.setStyleSheet(f"color: {p.error};")

        # Update separator lines if they exist
        for child in self.findChildren(QFrame):
            if child.frameShape() == QFrame.Shape.HLine:
                child.setStyleSheet(f"background-color: {p.border_main};")

        # Update signals mirror table styling
        if self._signals_mirror and hasattr(self._signals_mirror, 'table'):
            self._signals_mirror.table._palette = new_palette
            self._signals_mirror.table._setup_ui()  # Re-apply styling

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
        # Unsubscribe from theme changes
        theme_service.unsubscribe(self._on_theme_changed)

        # Clean up mirror connections
        if self._api_widget and hasattr(self._api_widget, 'cleanup_mirror'):
            self._api_widget.cleanup_mirror()

        super().closeEvent(event)


# Backward compatibility exports
__all__ = ["BitunixTradingWidget"]
