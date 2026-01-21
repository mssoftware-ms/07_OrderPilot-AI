"""App UI Mixin for OrderPilot-AI - REFACTORED for Workspace Manager.

Phase 1: Workspace Manager Umbau
- Central Widget: Watchlist (statt 6-Tab Widget)
- Activity Log Dock entfernt (wird in ChartWindow integriert)
- Kompakte Fenstergröße (400x600 statt 1400x900)
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QLabel,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from ..app_resources import _load_app_icon
from ..widgets.watchlist import WatchlistWidget

logger = logging.getLogger(__name__)


class AppUIMixin:
    """AppUIMixin for Workspace Manager UI.
    
    REFACTORED: Simplified from 6-tab trading interface to compact
    Workspace Manager with Watchlist as central widget.
    
    Changes from original:
    - Removed: Dashboard, Positions, Orders, Performance, Indicators, Alerts tabs
    - Removed: Activity Log dock (moved to ChartWindow)
    - Changed: Watchlist from dock to central widget
    - Changed: Window size from 1400x900 to 400x600
    """
    
    def init_ui(self):
        """Initialize the Workspace Manager UI."""
        self.setWindowTitle("OrderPilot-AI - Workspace Manager")
        
        # Compact size for Workspace Manager
        self.setGeometry(100, 100, 400, 600)
        self.setMinimumSize(300, 400)
        
        self.setWindowIcon(_load_app_icon())

        # Create menu bar (from MenuMixin)
        self.create_menu_bar()

        # Create toolbar (from ToolbarMixin) - now single row
        self.create_toolbar()

        # Create central widget - WATCHLIST (not tabs)
        self.create_central_widget()

        # NO dock widgets in Workspace Manager
        # (Watchlist is central, Activity Log is in ChartWindow)

        # Create status bar
        self.create_status_bar()

        # Apply initial theme
        self.apply_theme("dark")
        
        logger.info("Workspace Manager UI initialized")
    
    def create_central_widget(self):
        """Create the central widget with Watchlist.
        
        REFACTORED: Replaced 6-tab widget with Watchlist as central widget.
        This makes the Workspace Manager focused on symbol selection.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Watchlist as main content (was in dock)
        self.watchlist_widget = WatchlistWidget()
        
        # Connect watchlist signals
        # Double-click opens popup chart window
        self.watchlist_widget.symbol_selected.connect(self.open_chart_popup)
        self.watchlist_widget.symbol_added.connect(self.on_watchlist_symbol_added)
        
        layout.addWidget(self.watchlist_widget)
        
        # Note: Dashboard, Positions, Orders, Performance, Indicators, Alerts
        # are NO LONGER part of the Workspace Manager.
        # These were removed per user decision (Option A in plan).
        
        logger.debug("Central widget created with Watchlist")
    
    def create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Add permanent widgets
        self.time_label = QLabel()
        self.status_bar.addPermanentWidget(self.time_label)

        self.market_status = QLabel("Market: Closed")
        self.status_bar.addPermanentWidget(self.market_status)

        self.account_info = QLabel("Account: --")
        self.status_bar.addPermanentWidget(self.account_info)

        # Show initial message
        self.status_bar.showMessage("Workspace Manager ready", 5000)
    
    # ========================================================================
    # Removed Methods (kept as stubs for backward compatibility)
    # ========================================================================
    
    def create_dock_widgets(self):
        """Create dock widgets - REMOVED in Workspace Manager.
        
        Watchlist is now central widget, not a dock.
        Activity Log is now in ChartWindow, not Workspace Manager.
        """
        # No dock widgets in Workspace Manager
        pass
    
    # ========================================================================
    # Compatibility Properties
    # ========================================================================
    
    @property
    def dashboard_widget(self):
        """Removed - raises deprecation warning."""
        logger.warning("dashboard_widget is deprecated in Workspace Manager")
        return None
    
    @property
    def positions_widget(self):
        """Removed - raises deprecation warning."""
        logger.warning("positions_widget is deprecated in Workspace Manager")
        return None
    
    @property
    def orders_widget(self):
        """Removed - raises deprecation warning."""
        logger.warning("orders_widget is deprecated in Workspace Manager")
        return None
    
    @property
    def performance_dashboard(self):
        """Removed - raises deprecation warning."""
        logger.warning("performance_dashboard is deprecated in Workspace Manager")
        return None
    
    @property
    def indicators_widget(self):
        """Removed - raises deprecation warning."""
        logger.warning("indicators_widget is deprecated in Workspace Manager")
        return None
    
    @property
    def alerts_widget(self):
        """Removed - raises deprecation warning."""
        logger.warning("alerts_widget is deprecated in Workspace Manager")
        return None
