"""Menu Bar Mixin for TradingApplication.

Contains menu creation and menu action handlers.
"""

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QInputDialog, QMessageBox


class MenuMixin:
    """Mixin providing menu bar functionality for TradingApplication."""

    def create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File Menu
        file_menu = menubar.addMenu("&File")

        new_order_action = QAction("&New Order...", self)
        new_order_action.setShortcut("Ctrl+N")
        new_order_action.triggered.connect(self.show_order_dialog)
        file_menu.addAction(new_order_action)

        file_menu.addSeparator()

        settings_action = QAction("&Settings...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.triggered.connect(self.show_settings_dialog)
        file_menu.addAction(settings_action)

        file_menu.addSeparator()

        exit_action = QAction("&Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View Menu
        view_menu = menubar.addMenu("&View")

        theme_menu = view_menu.addMenu("&Theme")
        dark_theme_action = QAction("&Dark", self)
        dark_theme_action.triggered.connect(lambda: self.apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)

        light_theme_action = QAction("&Light", self)
        light_theme_action.triggered.connect(lambda: self.apply_theme("light"))
        theme_menu.addAction(light_theme_action)

        # Charts Menu (Multi-Chart Support)
        charts_menu = menubar.addMenu("&Charts")

        # PRE-TRADE ANALYSIS - THE KEY FEATURE
        pre_trade_action = QAction("🎯 &Pre-Trade Analyse...", self)
        pre_trade_action.setShortcut("Ctrl+Shift+T")
        pre_trade_action.setToolTip("Multi-Timeframe Charts für Trendanalyse VOR dem Trade öffnen")
        pre_trade_action.triggered.connect(self._on_open_pre_trade_analysis)
        charts_menu.addAction(pre_trade_action)

        charts_menu.addSeparator()

        new_chart_action = QAction("&New Chart Window...", self)
        new_chart_action.setShortcut("Ctrl+Shift+N")
        new_chart_action.triggered.connect(self._on_new_chart_window)
        charts_menu.addAction(new_chart_action)

        charts_menu.addSeparator()

        # Layouts Submenu
        layouts_menu = charts_menu.addMenu("&Layouts")

        save_layout_action = QAction("&Save Current Layout...", self)
        save_layout_action.triggered.connect(self._on_save_layout)
        layouts_menu.addAction(save_layout_action)

        layouts_menu.addSeparator()

        # Preset layouts
        single_layout_action = QAction("Single Chart", self)
        single_layout_action.triggered.connect(lambda: self._on_apply_layout("default_single"))
        layouts_menu.addAction(single_layout_action)

        dual_layout_action = QAction("Dual Charts (Side by Side)", self)
        dual_layout_action.triggered.connect(lambda: self._on_apply_layout("default_dual"))
        layouts_menu.addAction(dual_layout_action)

        mtf_layout_action = QAction("Multi-Timeframe (4 Charts)", self)
        mtf_layout_action.triggered.connect(lambda: self._on_apply_layout("default_mtf4"))
        layouts_menu.addAction(mtf_layout_action)

        layouts_menu.addSeparator()

        manage_layouts_action = QAction("&Manage Layouts...", self)
        manage_layouts_action.triggered.connect(self._on_manage_layouts)
        layouts_menu.addAction(manage_layouts_action)

        charts_menu.addSeparator()

        # Crosshair Sync
        self._crosshair_sync_action = QAction("&Sync Crosshairs", self)
        self._crosshair_sync_action.setCheckable(True)
        self._crosshair_sync_action.setChecked(False)
        self._crosshair_sync_action.triggered.connect(self._on_toggle_crosshair_sync)
        charts_menu.addAction(self._crosshair_sync_action)

        charts_menu.addSeparator()

        tile_charts_action = QAction("&Tile All Charts", self)
        tile_charts_action.triggered.connect(self._on_tile_charts)
        charts_menu.addAction(tile_charts_action)

        close_all_charts_action = QAction("Close &All Charts", self)
        close_all_charts_action.triggered.connect(self._on_close_all_charts)
        charts_menu.addAction(close_all_charts_action)

        # Trading Menu
        trading_menu = menubar.addMenu("&Trading")

        connect_broker_action = QAction("&Connect Broker", self)
        connect_broker_action.triggered.connect(self.connect_broker)
        trading_menu.addAction(connect_broker_action)

        disconnect_broker_action = QAction("&Disconnect Broker", self)
        disconnect_broker_action.triggered.connect(self.disconnect_broker)
        trading_menu.addAction(disconnect_broker_action)

        trading_menu.addSeparator()

        backtest_action = QAction("&Run Backtest...", self)
        backtest_action.triggered.connect(self.show_backtest_dialog)
        trading_menu.addAction(backtest_action)

        ai_backtest_action = QAction("&AI Backtest Analysis...", self)
        ai_backtest_action.setShortcut("Ctrl+Shift+B")
        ai_backtest_action.triggered.connect(self.show_ai_backtest_dialog)
        trading_menu.addAction(ai_backtest_action)

        trading_menu.addSeparator()

        param_opt_action = QAction("&Parameter Optimization...", self)
        param_opt_action.setShortcut("Ctrl+Shift+P")
        param_opt_action.triggered.connect(self.show_parameter_optimization_dialog)
        trading_menu.addAction(param_opt_action)

        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")

        # Chart Analysis Section
        chart_analysis_action = QAction("📊 &Chart Analysis...", self)
        chart_analysis_action.setShortcut("Ctrl+Shift+A")
        chart_analysis_action.setToolTip("Open AI-powered chart analysis for active chart")
        chart_analysis_action.triggered.connect(self._on_open_chart_analysis)
        tools_menu.addAction(chart_analysis_action)

        toggle_chat_action = QAction("💬 &Toggle Chat Widget", self)
        toggle_chat_action.setShortcut("Ctrl+Shift+C")
        toggle_chat_action.setToolTip("Show/hide the chart chat widget")
        toggle_chat_action.triggered.connect(self._on_toggle_chat_widget)
        tools_menu.addAction(toggle_chat_action)

        tools_menu.addSeparator()

        ai_monitor_action = QAction("&AI Usage Monitor", self)
        ai_monitor_action.triggered.connect(self.show_ai_monitor)
        tools_menu.addAction(ai_monitor_action)

        pattern_db_action = QAction("&Pattern Database...", self)
        pattern_db_action.setShortcut("Ctrl+Shift+D")
        pattern_db_action.setToolTip("Manage Qdrant pattern database for signal validation")
        pattern_db_action.triggered.connect(self.show_pattern_db_dialog)
        tools_menu.addAction(pattern_db_action)

        tools_menu.addSeparator()

        show_console_action = QAction("Show &Console Window", self)
        show_console_action.setToolTip("Show the hidden console output window")
        show_console_action.triggered.connect(self.show_console_window)
        tools_menu.addAction(show_console_action)

        reset_layout_action = QAction("&Reset Toolbars && Docks", self)
        reset_layout_action.setToolTip("Reset all toolbars and dock widgets to default positions")
        reset_layout_action.triggered.connect(self.reset_toolbars_and_docks)
        tools_menu.addAction(reset_layout_action)

        # Help Menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    # =========================================================================
    # Charts Menu Handlers
    # =========================================================================

    def _on_new_chart_window(self):
        """Open a new chart window."""
        symbol, ok = QInputDialog.getText(
            self, "New Chart", "Enter symbol (e.g., BTC/USD, AAPL):",
            text="BTC/USD"
        )
        if ok and symbol:
            self._open_chart_window(symbol.upper())

    def _on_save_layout(self):
        """Save the current window arrangement as a layout."""
        name, ok = QInputDialog.getText(
            self, "Save Layout", "Enter layout name:",
            text="My Layout"
        )
        if ok and name:
            if hasattr(self, "_multi_chart_manager"):
                layout = self._multi_chart_manager.save_current_layout(name)
                if layout:
                    QMessageBox.information(
                        self, "Layout Saved",
                        f"Layout '{name}' saved successfully."
                    )
                else:
                    QMessageBox.warning(
                        self, "No Charts",
                        "No chart windows to save."
                    )

    def _on_apply_layout(self, layout_id: str):
        """Apply a preset layout."""
        if hasattr(self, "_multi_chart_manager"):
            # Ensure default layouts exist
            self._multi_chart_manager.layout_manager.create_default_layouts()
            success = self._multi_chart_manager.apply_layout_by_id(layout_id)
            if not success:
                QMessageBox.warning(
                    self, "Layout Not Found",
                    f"Layout '{layout_id}' not found."
                )

    def _on_toggle_crosshair_sync(self, checked: bool):
        """Toggle crosshair synchronization."""
        if hasattr(self, "_multi_chart_manager"):
            self._multi_chart_manager.crosshair_sync.set_enabled(checked)

    def _on_tile_charts(self):
        """Tile all chart windows."""
        if hasattr(self, "_multi_chart_manager"):
            symbols = self._multi_chart_manager.get_open_symbols()
            if symbols:
                self._multi_chart_manager.tile_on_monitor(0, symbols)
            else:
                QMessageBox.information(
                    self, "No Charts",
                    "No chart windows to tile."
                )

    def _on_close_all_charts(self):
        """Close all chart windows."""
        if hasattr(self, "_multi_chart_manager"):
            count = self._multi_chart_manager.get_window_count()
            if count > 0:
                reply = QMessageBox.question(
                    self, "Close All Charts",
                    f"Close all {count} chart window(s)?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._multi_chart_manager.close_all()

    def _open_chart_window(self, symbol: str, timeframe: str = "1T"):
        """Open a chart window for a symbol.

        Args:
            symbol: Trading symbol
            timeframe: Chart timeframe
        """
        if hasattr(self, "_multi_chart_manager"):
            self._multi_chart_manager.open_chart(symbol, timeframe)

    def _on_manage_layouts(self):
        """Open the layout manager dialog."""
        if hasattr(self, "_multi_chart_manager"):
            from src.ui.dialogs.layout_manager_dialog import LayoutManagerDialog
            dialog = LayoutManagerDialog(
                layout_manager=self._multi_chart_manager.layout_manager,
                parent=self
            )
            dialog.exec()

    # =========================================================================
    # Chart Analysis Handlers
    # =========================================================================

    def _get_active_chart_window(self):
        """Get the currently active chart window.

        Returns:
            ChartWindow instance or None
        """
        if hasattr(self, "_multi_chart_manager"):
            # Get windows from manager
            windows = getattr(self._multi_chart_manager, "_windows", {})
            for window in windows.values():
                if window.isActiveWindow():
                    return window
            # Return first window if none active
            if windows:
                return next(iter(windows.values()))
        return None

    def _on_open_chart_analysis(self):
        """Open chart analysis for the active chart window."""
        active_chart = self._get_active_chart_window()
        if active_chart:
            if hasattr(active_chart, 'show_chat_widget'):
                active_chart.show_chat_widget()
            if hasattr(active_chart, 'request_chart_analysis'):
                active_chart.request_chart_analysis()
        else:
            QMessageBox.information(
                self, "No Chart",
                "Please open a chart window first.\n\n"
                "Use Charts → New Chart Window or double-click a symbol."
            )

    def _on_toggle_chat_widget(self):
        """Toggle the chat widget in the active chart window."""
        active_chart = self._get_active_chart_window()
        if active_chart and hasattr(active_chart, 'toggle_chat_widget'):
            active_chart.toggle_chat_widget()
        else:
            QMessageBox.information(
                self, "No Chart",
                "Please open a chart window first."
            )

    # =========================================================================
    # Pre-Trade Analysis Handler
    # =========================================================================

    def _on_open_pre_trade_analysis(self):
        """Open the Pre-Trade Analysis dialog.

        This opens a dialog to select and open multi-timeframe charts
        for analyzing the overarching trend BEFORE entering a trade.
        """
        try:
            from src.ui.multi_chart import ChartLayoutManager, ChartSetDialog

            # Get or create layout manager
            if not hasattr(self, '_chart_layout_manager'):
                self._chart_layout_manager = ChartLayoutManager(parent=self)
                # Set history manager for data loading
                if hasattr(self, 'history_manager'):
                    self._chart_layout_manager.set_history_manager(self.history_manager)

            # Open the dialog
            dialog = ChartSetDialog(
                layout_manager=self._chart_layout_manager,
                parent=self
            )
            dialog.exec()

        except ImportError as e:
            QMessageBox.critical(
                self, "Modul nicht gefunden",
                f"Pre-Trade Analyse Modul konnte nicht geladen werden:\n{e}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Fehler",
                f"Pre-Trade Analyse konnte nicht geöffnet werden:\n{e}"
            )
