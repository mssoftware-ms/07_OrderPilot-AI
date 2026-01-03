from __future__ import annotations


from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from .chart_js_template import get_chart_html_template
from .embedded_tradingview_bridge import ChartBridge

class EmbeddedTradingViewChartUIMixin:
    """EmbeddedTradingViewChartUIMixin extracted from EmbeddedTradingViewChart."""
    def _show_error_ui(self):
        """Show error message if WebEngine not available."""
        layout = QVBoxLayout(self)
        error_label = QLabel(
            "⚠️ PyQt6-WebEngine not installed\n\n"
            "Run: pip install PyQt6-WebEngine"
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14pt;")
        layout.addWidget(error_label)
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar (from ToolbarMixin) - Two rows
        toolbar1, toolbar2 = self._create_toolbar()
        layout.addWidget(toolbar1)
        layout.addWidget(toolbar2)

        # Web view for chart
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_page_loaded)
        self.web_view.setHtml(get_chart_html_template())
        layout.addWidget(self.web_view, stretch=1)

        # Setup WebChannel for JavaScript to Python communication
        self._chart_bridge = ChartBridge(self)
        self._chart_bridge.stop_line_moved.connect(self._on_bridge_stop_line_moved)
        self._web_channel = QWebChannel(self.web_view.page())
        self._web_channel.registerObject("pyBridge", self._chart_bridge)
        self.web_view.page().setWebChannel(self._web_channel)

        # Info panel
        info_layout = QHBoxLayout()
        self.info_label = QLabel("Select a symbol to begin")
        self.info_label.setStyleSheet("color: #aaa; font-family: monospace; padding: 5px;")
        info_layout.addWidget(self.info_label)
        layout.addLayout(info_layout)

        # Setup context menu for chart markings
        self._setup_context_menu()
    def _setup_context_menu(self):
        """Setup context menu for chart marking operations."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtCore import Qt

        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.web_view.customContextMenuRequested.connect(self._show_marking_context_menu)
    def _show_marking_context_menu(self, pos):
        """Show context menu for chart markings."""
        from PyQt6.QtWidgets import QMenu, QInputDialog
        from PyQt6.QtGui import QAction
        import time

        menu = QMenu(self)

        zones_at_price = self._get_zones_at_price()
        if zones_at_price:
            self._add_zone_management_menu(menu, zones_at_price)

        self._add_entry_menu(menu)
        self._add_zone_menu(menu)
        self._add_structure_menu(menu)
        self._add_lines_menu(menu)
        self._add_clear_actions(menu)

        # Chart Markings Manager
        menu.addSeparator()
        manager_action = QAction("📋 Manage All Markings...", self)
        manager_action.triggered.connect(self._show_markings_manager)
        menu.addAction(manager_action)

        menu.exec(self.web_view.mapToGlobal(pos))

    def _get_zones_at_price(self):
        if hasattr(self, "_last_price") and self._last_price is not None:
            return self._zones.get_zones_at_price(self._last_price)
        return []

    def _add_zone_management_menu(self, menu, zones_at_price):
        from PyQt6.QtGui import QAction

        zone_mgmt_menu = menu.addMenu(f"📍 Zones at Price ({len(zones_at_price)})")

        for zone in zones_at_price:
            zone_label = zone.label or zone.id
            zone_type_icon = {
                "support": "🟢",
                "resistance": "🔴",
                "demand": "🟢",
                "supply": "🔴",
            }.get(zone.zone_type.value, "📊")

            # Add lock indicator to submenu title
            lock_icon = "🔒" if zone.is_locked else "🔓"
            zone_submenu = zone_mgmt_menu.addMenu(f"{zone_type_icon} {lock_icon} {zone_label}")

            # Lock/Unlock action (first position)
            lock_action = QAction(
                f"{'🔓 Unlock' if zone.is_locked else '🔒 Lock'} Zone",
                self
            )
            lock_action.triggered.connect(lambda checked, z=zone: self._toggle_zone_lock(z))
            zone_submenu.addAction(lock_action)

            zone_submenu.addSeparator()

            # Edit action (disabled if locked)
            edit_action = QAction("✏️ Edit Zone...", self)
            edit_action.triggered.connect(lambda checked, z=zone: self._edit_zone(z))
            edit_action.setEnabled(not zone.is_locked)
            zone_submenu.addAction(edit_action)

            # Extend action (disabled if locked)
            extend_action = QAction("➡️ Extend to Now", self)
            extend_action.triggered.connect(lambda checked, z=zone: self._extend_zone_to_now(z))
            extend_action.setEnabled(not zone.is_locked)
            zone_submenu.addAction(extend_action)

            zone_submenu.addSeparator()

            # Delete action (NOT disabled - user wants only edit/move locked, not delete)
            delete_action = QAction("🗑️ Delete Zone", self)
            delete_action.triggered.connect(lambda checked, z=zone: self._delete_zone(z))
            zone_submenu.addAction(delete_action)

        menu.addSeparator()

    def _add_entry_menu(self, menu):
        from PyQt6.QtGui import QAction

        entry_menu = menu.addMenu("Add Entry Marker")
        long_action = QAction("Long Entry (Arrow Up)", self)
        long_action.triggered.connect(lambda: self._add_test_entry_marker("long"))
        entry_menu.addAction(long_action)

        short_action = QAction("Short Entry (Arrow Down)", self)
        short_action.triggered.connect(lambda: self._add_test_entry_marker("short"))
        entry_menu.addAction(short_action)

    def _add_zone_menu(self, menu):
        from PyQt6.QtGui import QAction

        zone_menu = menu.addMenu("Add Zone")
        support_action = QAction("🟢 Support Zone", self)
        support_action.triggered.connect(lambda: self._add_test_zone("support"))
        zone_menu.addAction(support_action)

        resistance_action = QAction("🔴 Resistance Zone", self)
        resistance_action.triggered.connect(lambda: self._add_test_zone("resistance"))
        zone_menu.addAction(resistance_action)

        zone_menu.addSeparator()

        demand_action = QAction("🟢 Demand Zone (Bullish)", self)
        demand_action.triggered.connect(lambda: self._add_test_zone("demand"))
        zone_menu.addAction(demand_action)

        supply_action = QAction("🔴 Supply Zone (Bearish)", self)
        supply_action.triggered.connect(lambda: self._add_test_zone("supply"))
        zone_menu.addAction(supply_action)

    def _add_structure_menu(self, menu):
        from PyQt6.QtGui import QAction

        structure_menu = menu.addMenu("Add Structure Break")
        bos_bull_action = QAction("BoS Bullish", self)
        bos_bull_action.triggered.connect(lambda: self._add_test_structure("bos", True))
        structure_menu.addAction(bos_bull_action)

        bos_bear_action = QAction("BoS Bearish", self)
        bos_bear_action.triggered.connect(lambda: self._add_test_structure("bos", False))
        structure_menu.addAction(bos_bear_action)

        choch_bull_action = QAction("CHoCH Bullish", self)
        choch_bull_action.triggered.connect(lambda: self._add_test_structure("choch", True))
        structure_menu.addAction(choch_bull_action)

        choch_bear_action = QAction("CHoCH Bearish", self)
        choch_bear_action.triggered.connect(lambda: self._add_test_structure("choch", False))
        structure_menu.addAction(choch_bear_action)

        structure_menu.addSeparator()

        msb_bull_action = QAction("⬆️ MSB Bullish", self)
        msb_bull_action.triggered.connect(lambda: self._add_test_structure("msb", True))
        structure_menu.addAction(msb_bull_action)

        msb_bear_action = QAction("⬇️ MSB Bearish", self)
        msb_bear_action.triggered.connect(lambda: self._add_test_structure("msb", False))
        structure_menu.addAction(msb_bear_action)

    def _add_lines_menu(self, menu):
        from PyQt6.QtGui import QAction

        lines_menu = menu.addMenu("📏 Add Line")
        sl_long_action = QAction("🔴 Stop Loss (Long Position)", self)
        sl_long_action.triggered.connect(lambda: self._add_test_line("sl", True))
        lines_menu.addAction(sl_long_action)

        sl_short_action = QAction("🔴 Stop Loss (Short Position)", self)
        sl_short_action.triggered.connect(lambda: self._add_test_line("sl", False))
        lines_menu.addAction(sl_short_action)

        lines_menu.addSeparator()

        tp_long_action = QAction("🟢 Take Profit (Long Position)", self)
        tp_long_action.triggered.connect(lambda: self._add_test_line("tp", True))
        lines_menu.addAction(tp_long_action)

        tp_short_action = QAction("🟢 Take Profit (Short Position)", self)
        tp_short_action.triggered.connect(lambda: self._add_test_line("tp", False))
        lines_menu.addAction(tp_short_action)

        lines_menu.addSeparator()

        entry_long_action = QAction("🔵 Entry Line (Long)", self)
        entry_long_action.triggered.connect(lambda: self._add_test_line("entry", True))
        lines_menu.addAction(entry_long_action)

        entry_short_action = QAction("🔵 Entry Line (Short)", self)
        entry_short_action.triggered.connect(lambda: self._add_test_line("entry", False))
        lines_menu.addAction(entry_short_action)

        lines_menu.addSeparator()

        trailing_action = QAction("🟡 Trailing Stop", self)
        trailing_action.triggered.connect(lambda: self._add_test_line("trailing", True))
        lines_menu.addAction(trailing_action)

    def _add_clear_actions(self, menu):
        from PyQt6.QtGui import QAction

        menu.addSeparator()
        clear_markers_action = QAction("Clear All Markers", self)
        clear_markers_action.triggered.connect(self._clear_all_markers)
        menu.addAction(clear_markers_action)

        clear_zones_action = QAction("Clear All Zones", self)
        clear_zones_action.triggered.connect(self.clear_zones)
        menu.addAction(clear_zones_action)

        clear_lines_action = QAction("Clear All Lines", self)
        clear_lines_action.triggered.connect(self.clear_stop_loss_lines)
        menu.addAction(clear_lines_action)

        clear_all_action = QAction("Clear Everything", self)
        clear_all_action.triggered.connect(self._clear_all_markings)
        menu.addAction(clear_all_action)

    def _show_markings_manager(self):
        """Show the Chart Markings Manager dialog."""
        from src.ui.dialogs import ChartMarkingsManagerDialog

        dialog = ChartMarkingsManagerDialog(self, self)
        dialog.exec()
