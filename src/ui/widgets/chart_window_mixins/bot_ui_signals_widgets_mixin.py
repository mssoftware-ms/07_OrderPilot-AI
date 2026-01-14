from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from decimal import Decimal

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter, QLinearGradient
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QProgressBar, QPushButton, QSplitter, QTableWidget, QVBoxLayout, QWidget,
    QMessageBox, QPlainTextEdit, QFileDialog
)

from .bot_sltp_progressbar import SLTPProgressBar

logger = logging.getLogger(__name__)

class BotUISignalsWidgetsMixin:
    """UI widget creation for signals tab"""

    def _create_signals_tab(self) -> QWidget:
        """Create signals & trade management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Top row: Bitunix HEDGE (with integrated Status) + Current Position
        top_row_layout = QHBoxLayout()
        top_row_layout.setSpacing(8)

        # Bitunix HEDGE Execution Widget (takes remaining space)
        # Now includes all 4 GroupBoxes: Connection & Risk, Entry, TP/SL, Status
        bitunix_widget = self._build_bitunix_hedge_widget()
        top_row_layout.addWidget(bitunix_widget, stretch=1)

        # Current Position (fixed 420px width)
        position_widget = self._build_current_position_widget()
        position_widget.setMaximumWidth(420)
        position_widget.setMinimumWidth(420)
        top_row_layout.addWidget(position_widget, stretch=0)

        layout.addLayout(top_row_layout)

        # 20px Abstand vor Recent Signals
        layout.addSpacing(10) # Reduced spacing

        # Issue #68: Use QSplitter for Signals Table and Bot Log
        # "Log Trading Bot ... nach unten hin minimieren kann"
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(self._build_signals_widget())
        splitter.addWidget(self._build_bot_log_widget())
        splitter.setStretchFactor(0, 7) # Signals table gets more space
        splitter.setStretchFactor(1, 3) # Log gets less
        
        layout.addWidget(splitter)
        
        return widget

    def _build_bitunix_hedge_widget(self) -> QWidget:
        """Build Bitunix HEDGE Execution Widget.

        Uses the new BitunixHedgeExecutionWidget with 3-column layout.
        Based on: UI_Spezifikation_TradingBot_Signals_BitunixExecution.md
        """
        from src.ui.widgets.bitunix_hedge_execution_widget import BitunixHedgeExecutionWidget

        try:
            self.bitunix_hedge_widget = BitunixHedgeExecutionWidget(parent=self)

            # Wire up signals
            self.bitunix_hedge_widget.order_placed.connect(self._on_bitunix_order_placed)
            self.bitunix_hedge_widget.position_opened.connect(self._on_bitunix_position_opened)
            self.bitunix_hedge_widget.trade_closed.connect(self._on_bitunix_trade_closed)

            return self.bitunix_hedge_widget

        except Exception as e:
            logger.error(f"Failed to create Bitunix HEDGE widget: {e}")
            # Return placeholder on error
            error_widget = QLabel(f"Bitunix HEDGE: Initialization failed - {e}")
            error_widget.setStyleSheet("color: #ff5555; padding: 8px;")
            return error_widget

    def _on_bitunix_order_placed(self, order_id: str):
        """Handle Bitunix order placed event."""
        logger.info(f"Bitunix order placed: {order_id}")

    def _on_bitunix_position_opened(self, position_id: str):
        """Handle Bitunix position opened event."""
        logger.info(f"Bitunix position opened: {position_id}")

    def _on_bitunix_trade_closed(self):
        """Handle Bitunix trade closed event."""
        logger.info("Bitunix trade closed")

    def _build_status_widget_fallback(self) -> QWidget:
        """Build fallback Status GroupBox if Bitunix widget failed."""
        status_group = QGroupBox("Status")
        layout = QFormLayout()
        layout.setContentsMargins(8, 12, 8, 8)
        layout.setVerticalSpacing(8)

        self.state_label = QLabel("—")
        layout.addRow("State:", self.state_label)

        self.order_id_label = QLabel("—")
        layout.addRow("Order ID:", self.order_id_label)

        self.position_id_label = QLabel("—")
        layout.addRow("Position ID:", self.position_id_label)

        self.adaptive_label = QLabel("—")
        layout.addRow("Adaptive:", self.adaptive_label)

        kill_btn = QPushButton("KILL SWITCH")
        kill_btn.setStyleSheet(
            "background-color: #ff0000; color: white; font-weight: bold; padding: 8px;"
        )
        layout.addRow(kill_btn)

        status_group.setLayout(layout)
        status_group.setMinimumWidth(160)
        status_group.setMaximumWidth(200)

        return status_group

    def _build_current_position_widget(self) -> QWidget:
        position_widget = QWidget()
        position_layout = QVBoxLayout(position_widget)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.setSpacing(0)

        position_group = QGroupBox("Current Position")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(4)

        # Issue #68: Add Live Trading controls here
        if hasattr(self, 'bitunix_hedge_widget'):
            mode_layout = QHBoxLayout()
            mode_layout.setContentsMargins(0, 0, 0, 4)
            mode_layout.setSpacing(12)
            
            # Use widgets from bitunix widget that were initialized but not added to layout
            cb = self.bitunix_hedge_widget.live_mode_cb
            lbl = self.bitunix_hedge_widget.mode_indicator
            
            # Adjust label style (smaller font as requested)
            lbl.setStyleSheet(
                "background-color: #26a69a; color: white; "
                "font-weight: bold; font-size: 11px; " 
                "padding: 4px 8px; border-radius: 4px;"
                "min-width: 100px;"
            )
            
            mode_layout.addWidget(cb)
            mode_layout.addWidget(lbl)
            mode_layout.addStretch()
            
            group_layout.addLayout(mode_layout)

        # Add SL/TP Progress Bar at the top
        self.sltp_progress_bar = SLTPProgressBar()
        self.sltp_progress_bar.reset_bar()
        group_layout.addWidget(self.sltp_progress_bar)

        # Add position details
        details_widget = QWidget()
        details_widget.setLayout(self._build_position_layout())
        group_layout.addWidget(details_widget)

        position_group.setLayout(group_layout)
        # Removed setMaximumHeight - allow full vertical space
        position_layout.addWidget(position_group)
        return position_widget

    def _build_position_layout(self) -> QHBoxLayout:
        position_h_layout = QHBoxLayout()
        position_h_layout.setContentsMargins(8, 8, 8, 8)
        position_h_layout.setSpacing(20)

        position_h_layout.addWidget(self._build_position_left_column())
        position_h_layout.addWidget(self._build_position_right_column())
        position_h_layout.addStretch()
        return position_h_layout

    def _build_position_left_column(self) -> QWidget:
        left_widget = QWidget()
        left_widget.setMinimumWidth(180)
        left_widget.setMaximumWidth(220)
        left_form = QFormLayout(left_widget)
        left_form.setVerticalSpacing(2)
        left_form.setContentsMargins(0, 0, 0, 0)

        self.position_side_label = QLabel("FLAT")
        self.position_side_label.setStyleSheet("font-weight: bold;")
        left_form.addRow("Side:", self.position_side_label)

        self.position_strategy_label = QLabel("-")
        left_form.addRow("Strategy:", self.position_strategy_label)

        self.position_entry_label = QLabel("-")
        left_form.addRow("Entry:", self.position_entry_label)

        self.position_size_label = QLabel("-")
        left_form.addRow("Size:", self.position_size_label)

        self.position_invested_label = QLabel("-")
        self.position_invested_label.setStyleSheet("font-weight: bold;")
        left_form.addRow("Invested:", self.position_invested_label)

        self.position_stop_label = QLabel("-")
        left_form.addRow("Stop:", self.position_stop_label)

        self.position_current_label = QLabel("-")
        self.position_current_label.setStyleSheet("font-weight: bold;")
        left_form.addRow("Current:", self.position_current_label)

        self.position_pnl_label = QLabel("-")
        left_form.addRow("P&L:", self.position_pnl_label)

        self.position_bars_held_label = QLabel("-")
        left_form.addRow("Bars Held:", self.position_bars_held_label)
        return left_widget

    def _build_position_right_column(self) -> QWidget:
        right_widget = QWidget()
        right_widget.setMinimumWidth(160)
        right_form = QFormLayout(right_widget)
        right_form.setVerticalSpacing(2)
        right_form.setContentsMargins(0, 0, 0, 0)

        self.position_score_label = QLabel("-")
        self.position_score_label.setStyleSheet("font-weight: bold; color: #26a69a;")
        right_form.addRow("Score:", self.position_score_label)

        self.position_tr_price_label = QLabel("-")
        right_form.addRow("TR Kurs:", self.position_tr_price_label)

        self.deriv_separator = QLabel("── Derivat ──")
        self.deriv_separator.setStyleSheet("color: #ff5722; font-weight: bold;")
        right_form.addRow(self.deriv_separator)

        self.deriv_wkn_label = QLabel("-")
        self.deriv_wkn_label.setStyleSheet("font-weight: bold;")
        right_form.addRow("WKN:", self.deriv_wkn_label)

        self.deriv_leverage_label = QLabel("-")
        right_form.addRow("Hebel:", self.deriv_leverage_label)

        self.deriv_spread_label = QLabel("-")
        right_form.addRow("Spread:", self.deriv_spread_label)

        self.deriv_ask_label = QLabel("-")
        right_form.addRow("Ask:", self.deriv_ask_label)

        self.deriv_pnl_label = QLabel("-")
        self.deriv_pnl_label.setStyleSheet("font-weight: bold;")
        right_form.addRow("D P&L:", self.deriv_pnl_label)
        return right_widget

    def _build_signals_widget(self) -> QWidget:
        signals_widget = QWidget()
        signals_layout = QVBoxLayout(signals_widget)
        signals_layout.setContentsMargins(0, 0, 0, 0)

        signals_group = QGroupBox("Recent Signals")
        signals_inner = QVBoxLayout()

        # === TOOLBAR mit Clear-Buttons ===
        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(0, 0, 0, 4)

        self.clear_selected_btn = QPushButton("🗑️ Zeile löschen")
        self.clear_selected_btn.setFixedHeight(24)
        self.clear_selected_btn.setStyleSheet("font-size: 10px; padding: 2px 8px;")
        self.clear_selected_btn.setToolTip("Ausgewählte Zeile löschen")
        self.clear_selected_btn.clicked.connect(self._on_clear_selected_signal)
        toolbar.addWidget(self.clear_selected_btn)

        self.clear_all_signals_btn = QPushButton("🧹 Alle löschen")
        self.clear_all_signals_btn.setFixedHeight(24)
        self.clear_all_signals_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 8px; color: #ef5350;"
        )
        self.clear_all_signals_btn.setToolTip("Alle Signale aus der Tabelle löschen")
        self.clear_all_signals_btn.clicked.connect(self._on_clear_all_signals)
        toolbar.addWidget(self.clear_all_signals_btn)

        # Issue #11: Sofort Verkaufen Button
        self.sell_position_btn = QPushButton("💰 Sofort verkaufen")
        self.sell_position_btn.setFixedHeight(24)
        self.sell_position_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 8px; background-color: #ff5722; color: white; font-weight: bold;"
        )
        self.sell_position_btn.setToolTip(
            "Aktuelle Position mit Limit-Order verkaufen (0.05% unter aktuellem Kurs)"
        )
        self.sell_position_btn.clicked.connect(self._on_sell_position_clicked)
        self.sell_position_btn.setEnabled(False)  # Initially disabled
        toolbar.addWidget(self.sell_position_btn)

        # Issue #18: Chart-Elemente zeichnen Button
        self.draw_chart_elements_btn = QPushButton("📊 Chart-Elemente")
        self.draw_chart_elements_btn.setFixedHeight(24)
        self.draw_chart_elements_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 8px; background-color: #2196f3; color: white;"
        )
        self.draw_chart_elements_btn.setToolTip(
            "Zeichnet Entry, Stop-Loss und Trailing-Stop Linien für aktive Position im Chart.\n"
            "Linien können im Chart verschoben werden - Werte werden automatisch aktualisiert."
        )
        self.draw_chart_elements_btn.clicked.connect(self._on_draw_chart_elements_clicked)
        self.draw_chart_elements_btn.setEnabled(False)  # Initially disabled
        toolbar.addWidget(self.draw_chart_elements_btn)

        # Export to XLSX button (neben Chart-Elemente Button)
        self.export_signals_btn = QPushButton("📊 Export XLSX")
        self.export_signals_btn.setFixedHeight(24)
        self.export_signals_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 8px; background-color: #2196f3; color: white;"
        )
        self.export_signals_btn.setToolTip("Export signal table to Excel file")
        self.export_signals_btn.clicked.connect(self._export_signals_to_xlsx)
        toolbar.addWidget(self.export_signals_btn)

        toolbar.addStretch()

        signals_inner.addLayout(toolbar)
        self._build_signals_table()
        signals_inner.addWidget(self.signals_table)

        signals_group.setLayout(signals_inner)
        signals_layout.addWidget(signals_group)
        return signals_widget

    # =========================================================================
    # Trading Bot Log (Issue #23)
    # =========================================================================

    def _build_signals_table(self) -> None:
        self.signals_table = QTableWidget()
        self.signals_table.setColumnCount(22)  # Issue #5: Added "Stück" column (22 total)
        self.signals_table.setHorizontalHeaderLabels(
            [
                "Time", "Type", "Strategy", "Side", "Entry", "Stop", "SL%", "TR%",
                "TRA%", "TR Lock", "Status", "Current", "P&L %", "P&L USDT",
                "Fees USDT",  # Issue #6: BitUnix fees in USDT
                "Stück",  # Issue #5: Gekaufte Stückzahl
                "D P&L USDT", "D P&L %", "Heb", "WKN", "Score", "TR Stop",
            ]
        )
        # Hidden columns: D P&L USDT (16), D P&L % (17), Heb (18), WKN (19), Score (20)
        for col in [16, 17, 18, 19]:
            self.signals_table.setColumnHidden(col, True)
        self.signals_table.setColumnHidden(20, True)

        # Issue #4: Set column resize modes for optimal width usage
        header = self.signals_table.horizontalHeader()

        # Narrow columns (6-character width) - Issue #4
        narrow_cols = [1, 3, 6, 7, 8, 9, 10]  # Type, Side, SL%, TR%, TRA%, TR Lock, Status
        for col in narrow_cols:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # Medium-width columns with fixed pixel sizes for better control
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # Time
        header.resizeSection(0, 70)
        header.setSectionResizeMode(17, QHeaderView.ResizeMode.Fixed)  # Heb
        header.resizeSection(17, 50)
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Fixed)  # P&L %
        header.resizeSection(12, 70)

        # Stretch remaining columns (Strategy, Entry, Stop, Current, P&L USDT, Fees, Stück, TR Stop)
        stretch_cols = [2, 4, 5, 11, 13, 14, 15, 21]
        for col in stretch_cols:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Stretch)

        self.signals_table.setAlternatingRowColors(True)
        self.signals_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.signals_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)

        self.signals_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.signals_table.customContextMenuRequested.connect(
            self._show_signals_context_menu
        )
        self.signals_table.cellChanged.connect(self._on_signals_table_cell_changed)
        self.signals_table.itemSelectionChanged.connect(
            self._on_signals_table_selection_changed
        )
        self._signals_table_updating = False

    def _update_leverage_column_visibility(self) -> None:
        """Issue #1: Show/hide leverage column based on leverage override state."""
        if not hasattr(self, 'signals_table'):
            return

        show_leverage = False
        if hasattr(self, 'get_leverage_override'):
            override_enabled, _ = self.get_leverage_override()
            show_leverage = override_enabled

        # Column 18 is "Heb" (Leverage) - Issue #5: moved from 17
        self.signals_table.setColumnHidden(18, not show_leverage)

