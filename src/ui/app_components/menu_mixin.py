"""Menu Bar Mixin for TradingApplication.

Contains menu creation and menu action handlers.
"""

from PyQt6.QtGui import QAction


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
