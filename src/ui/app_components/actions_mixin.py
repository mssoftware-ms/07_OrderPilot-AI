"""Actions Mixin for Main Application.

Contains dialog show methods and UI action handlers for TradingApplication.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDockWidget,
    QMessageBox,
    QToolBar,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QMainWindow

logger = logging.getLogger(__name__)


class ActionsMixin:
    """Mixin providing dialog and action methods for TradingApplication."""

    def show_order_dialog(self):
        """Show the order placement dialog."""
        from src.ui.dialogs.order_dialog import OrderDialog

        if not self.broker:
            QMessageBox.warning(self, "No Broker",
                              "Please connect to a broker first")
            return

        dialog = OrderDialog(self.broker, self.ai_service, self)
        dialog.order_placed.connect(self.on_order_placed)
        dialog.exec()

    def show_settings_dialog(self):
        """Show the settings dialog."""
        from src.ui.dialogs.settings_dialog import SettingsDialog

        dialog = SettingsDialog(self)
        if dialog.exec():
            # Reload settings if changed
            self.load_settings()

    def show_backtest_dialog(self):
        """Show the backtest dialog."""
        from src.ui.dialogs.backtest_dialog import BacktestDialog

        dialog = BacktestDialog(self.ai_service, self)
        dialog.exec()

    def show_ai_backtest_dialog(self):
        """Show the AI-powered backtest analysis dialog."""
        from src.ui.dialogs.ai_backtest_dialog import AIBacktestDialog

        current_symbol = None
        if hasattr(self, 'backtest_chart_manager'):
            current_symbol = self.backtest_chart_manager.get_active_symbol()

        dialog = AIBacktestDialog(self, current_symbol=current_symbol)
        dialog.exec()

    def show_parameter_optimization_dialog(self):
        """Show the parameter optimization dialog."""
        from src.ui.dialogs.parameter_optimization_dialog import ParameterOptimizationDialog

        current_symbol = None
        if hasattr(self, 'backtest_chart_manager'):
            current_symbol = self.backtest_chart_manager.get_active_symbol()

        dialog = ParameterOptimizationDialog(self, current_symbol=current_symbol)
        dialog.exec()

    def show_ai_monitor(self):
        """Show AI usage monitor."""
        if self.ai_service and hasattr(self.ai_service, 'cost_tracker'):
            try:
                cost = self.ai_service.cost_tracker.current_month_cost
                budget = self.ai_service.cost_tracker.monthly_budget

                QMessageBox.information(self, "AI Usage",
                                      f"Current Month Usage: €{cost:.2f}\n"
                                      f"Monthly Budget: €{budget:.2f}\n"
                                      f"Remaining: €{budget - cost:.2f}")
            except Exception as e:
                logger.error(f"Error showing AI monitor: {e}")
                QMessageBox.warning(self, "AI Usage",
                                   f"Error retrieving AI usage data: {e}")
        else:
            QMessageBox.information(self, "AI Usage", "AI service not initialized")

    def show_pattern_db_dialog(self):
        """Show the pattern database management dialog."""
        from src.ui.dialogs import PatternDatabaseDialog
        dialog = PatternDatabaseDialog(self)
        dialog.exec()

    def reset_toolbars_and_docks(self):
        """Reset all toolbars and dock widgets to their default positions."""
        try:
            reply = QMessageBox.question(
                self,
                "Reset Layout",
                "This will reset all toolbars and dock widgets to their default positions.\n\n"
                "Do you want to continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.settings.remove("windowState")
                self.settings.remove("geometry")

                for toolbar in self.findChildren(QToolBar):
                    toolbar.setVisible(True)
                    self.addToolBar(Qt.ToolBarArea.TopToolBarArea, toolbar)

                for dock in self.findChildren(QDockWidget):
                    dock.setVisible(True)
                    dock_name = dock.windowTitle()
                    if "Watchlist" in dock_name:
                        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, dock)
                    elif "Activity" in dock_name or "Log" in dock_name:
                        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, dock)

                self.setGeometry(100, 100, 1400, 900)
                self.status_bar.showMessage("Layout reset to defaults", 3000)
                logger.info("Toolbars and docks reset to default positions")

                QMessageBox.information(
                    self,
                    "Layout Reset",
                    "Toolbars and dock widgets have been reset to their default positions."
                )

        except Exception as e:
            logger.error(f"Failed to reset layout: {e}")
            QMessageBox.critical(self, "Reset Failed", f"Failed to reset layout:\n\n{str(e)}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(self, "About OrderPilot-AI",
                        "OrderPilot-AI Trading Application\n\n"
                        "Version 1.0.0\n\n"
                        "An AI-powered trading platform for retail investors.\n\n"
                        "© 2025 OrderPilot")
