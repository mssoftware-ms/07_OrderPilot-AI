"""Bitunix Trading Mode Manager - Live/Paper Mode Switching.

Refactored from 1,108 LOC monolith using composition pattern.

Module 1/4 of bitunix_trading_widget.py split.

Contains:
- Mode switching logic (_toggle_mode, _update_mode_ui)
- Paper account reset (_reset_paper_account)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BitunixTradingModeManager:
    """Helper für Live/Paper Mode Switching."""

    def __init__(self, parent):
        """
        Args:
            parent: BitunixTradingWidget Instanz
        """
        self.parent = parent

    def toggle_mode(self, is_paper: bool) -> None:
        """Switch between Live and Paper adapters.

        Args:
            is_paper: True = Paper mode, False = Live mode
        """
        self.parent.is_paper_mode = is_paper

        if is_paper:
            self.parent.adapter = self.parent.paper_adapter
        else:
            self.parent.adapter = self.parent.live_adapter

        self.update_mode_ui()

        # Trigger immediate refresh
        self.parent._load_account_info()
        self.parent._positions_manager._load_positions()
        self.parent._order_handler._update_button_states()

    def update_mode_ui(self) -> None:
        """Update banner and colors based on mode."""
        if self.parent.is_paper_mode:
            self.parent.mode_banner.setText("PAPER TRADING - SIMULATION")
            self.parent.mode_banner.setStyleSheet("""
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            """)
            self.parent.reset_btn.setVisible(True)
        else:
            self.parent.mode_banner.setText("⚠️ LIVE TRADING - REAL MONEY ⚠️")
            self.parent.mode_banner.setStyleSheet("""
                background-color: #D32F2F;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            """)
            self.parent.reset_btn.setVisible(False)

    def reset_paper_account(self) -> None:
        """Reset paper trading balance to 10,000 USDT."""
        if not self.parent.is_paper_mode:
            return

        confirm = QMessageBox.question(
            self.parent,
            "Reset Simulation",
            "Reset paper balance to 10,000 USDT?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.parent.paper_adapter.reset_account()
            self.parent._load_account_info()
            self.parent._positions_manager._load_positions()
