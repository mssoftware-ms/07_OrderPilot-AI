"""
Bot Tab UI - UI Creation and Layout for Bot Trading Tab

Module 1/3 of bot_tab.py split (~800 LOC)

Responsibilities:
- Header section (status, buttons)
- Signal section (direction, confidence, SL/TP bar)
- Position section (entry, current, SL/TP, P&L)
- Statistics section (trades, win rate, PnL, DD)
- Log section

All UI widgets are created here and referenced by main BotTab class.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTextEdit, QFrame, QProgressBar, QSplitter,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget as QWidgetType

import logging
logger = logging.getLogger(__name__)


class BotTabUI:
    """UI Manager for Bot Trading Tab.

    Creates all UI sections and widgets.
    """

    def __init__(self, parent: "QWidgetType"):
        """Initialize UI manager.

        Args:
            parent: The BotTab widget
        """
        self.parent = parent

    def setup_ui(self) -> None:
        """Creates the complete UI layout."""
        layout = QVBoxLayout(self.parent)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # Header: Bot Status
        header = self.create_header_section()
        layout.addWidget(header)

        # Status Panel (if available)
        if hasattr(self.parent, '_status_panel') and self.parent._status_panel:
            self.parent._status_panel.setVisible(False)
            layout.addWidget(self.parent._status_panel)

        # Journal Widget (if available)
        if hasattr(self.parent, '_journal_widget') and self.parent._journal_widget:
            self.parent._journal_widget.setVisible(False)
            layout.addWidget(self.parent._journal_widget)

        # Splitter for Signal/Position and Log
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top Section
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.create_signal_section())
        top_layout.addWidget(self.create_position_section())
        top_layout.addWidget(self.create_stats_section())

        splitter.addWidget(top_widget)
        splitter.addWidget(self.create_log_section())
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

    def create_header_section(self) -> QWidget:
        """Creates header with status and buttons."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame { background-color: #1a1a2e; border-radius: 8px; padding: 8px; }
        """)
        layout = QHBoxLayout(frame)

        # Bot Icon and Status
        self.parent.status_icon = QLabel("🤖")
        self.parent.status_icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.parent.status_icon)

        status_layout = QVBoxLayout()
        self.parent.status_label = QLabel("IDLE")
        self.parent.status_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #888;")
        status_layout.addWidget(self.parent.status_label)

        self.parent.status_detail = QLabel("Bot ist gestoppt")
        self.parent.status_detail.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.parent.status_detail)
        layout.addLayout(status_layout)

        layout.addStretch()

        # Buttons
        self.parent.start_btn = QPushButton("▶ Start Bot")
        self.parent.start_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; font-weight: bold;
                          padding: 10px 20px; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        layout.addWidget(self.parent.start_btn)

        self.parent.stop_btn = QPushButton("⏹ Stop Bot")
        self.parent.stop_btn.setStyleSheet("""
            QPushButton { background-color: #f44336; color: white; font-weight: bold;
                          padding: 10px 20px; border-radius: 5px; font-size: 13px; }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.parent.stop_btn.setEnabled(False)
        layout.addWidget(self.parent.stop_btn)

        # Status Panel Toggle
        self.parent.status_panel_btn = QPushButton("📊")
        self.parent.status_panel_btn.setStyleSheet("""
            QPushButton { background-color: #2196F3; color: white; padding: 10px 15px;
                          border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:checked { background-color: #1565C0; }
        """)
        self.parent.status_panel_btn.setToolTip("Engine Status Panel ein/ausblenden")
        self.parent.status_panel_btn.setCheckable(True)
        layout.addWidget(self.parent.status_panel_btn)

        # Journal Toggle
        self.parent.journal_btn = QPushButton("📔")
        self.parent.journal_btn.setStyleSheet("""
            QPushButton { background-color: #9C27B0; color: white; padding: 10px 15px;
                          border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:checked { background-color: #6A1B9A; }
        """)
        self.parent.journal_btn.setToolTip("Trading Journal ein/ausblenden")
        self.parent.journal_btn.setCheckable(True)
        layout.addWidget(self.parent.journal_btn)

        # Settings Button
        self.parent.settings_btn = QPushButton("⚙")
        self.parent.settings_btn.setStyleSheet("""
            QPushButton { background-color: #555; color: white; padding: 10px 15px;
                          border-radius: 5px; font-size: 14px; }
            QPushButton:hover { background-color: #666; }
        """)
        self.parent.settings_btn.setToolTip("Bot Settings")
        self.parent.settings_btn.setEnabled(True)
        layout.addWidget(self.parent.settings_btn)

        return frame

    def create_signal_section(self) -> QGroupBox:
        """Creates signal display section."""
        group = QGroupBox("📊 Aktuelles Signal")
        layout = QVBoxLayout(group)

        # Direction and Confidence
        row1 = QHBoxLayout()
        self.parent.signal_direction = QLabel("—")
        self.parent.signal_direction.setStyleSheet("""
            font-size: 18px; font-weight: bold; padding: 5px 15px;
            border-radius: 4px; background-color: #333;
        """)
        row1.addWidget(self.parent.signal_direction)

        row1.addWidget(QLabel("Confluence:"))
        self.parent.signal_confluence = QLabel("—")
        self.parent.signal_confluence.setStyleSheet("font-weight: bold;")
        row1.addWidget(self.parent.signal_confluence)
        row1.addStretch()

        self.parent.signal_regime = QLabel("Regime: —")
        self.parent.signal_regime.setStyleSheet("color: #888;")
        row1.addWidget(self.parent.signal_regime)
        layout.addLayout(row1)

        # Conditions
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Conditions:"))
        self.parent.signal_conditions = QLabel("—")
        self.parent.signal_conditions.setWordWrap(True)
        self.parent.signal_conditions.setStyleSheet("color: #aaa; font-size: 11px;")
        row2.addWidget(self.parent.signal_conditions, 1)
        layout.addLayout(row2)

        # SL/TP Visual Bar
        self.parent.sltp_container = QWidget()
        sltp_layout = QVBoxLayout(self.parent.sltp_container)
        sltp_layout.setContentsMargins(0, 10, 0, 0)

        sltp_labels_row = QHBoxLayout()
        self.parent.sltp_sl_label = QLabel("SL: —")
        self.parent.sltp_sl_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 11px;")
        sltp_labels_row.addWidget(self.parent.sltp_sl_label)
        sltp_labels_row.addStretch()
        self.parent.sltp_current_label = QLabel("—")
        self.parent.sltp_current_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 12px;")
        sltp_labels_row.addWidget(self.parent.sltp_current_label)
        sltp_labels_row.addStretch()
        self.parent.sltp_tp_label = QLabel("TP: —")
        self.parent.sltp_tp_label.setStyleSheet("color: #26a69a; font-weight: bold; font-size: 11px;")
        sltp_labels_row.addWidget(self.parent.sltp_tp_label)
        sltp_layout.addLayout(sltp_labels_row)

        self.parent.sltp_bar = QProgressBar()
        self.parent.sltp_bar.setTextVisible(False)
        self.parent.sltp_bar.setMinimum(0)
        self.parent.sltp_bar.setMaximum(100)
        self.parent.sltp_bar.setValue(50)
        self.parent.sltp_bar.setMaximumHeight(20)
        self.parent.sltp_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #444; border-radius: 3px; background-color: #222; }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef5350, stop:0.5 #ffa726, stop:1 #26a69a);
                border-radius: 2px;
            }
        """)
        sltp_layout.addWidget(self.parent.sltp_bar)

        self.parent.sltp_pnl_label = QLabel("P&L: —")
        self.parent.sltp_pnl_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        self.parent.sltp_pnl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sltp_layout.addWidget(self.parent.sltp_pnl_label)

        layout.addWidget(self.parent.sltp_container)
        self.parent.sltp_container.setVisible(True)

        # Last Update
        row3 = QHBoxLayout()
        self.parent.signal_timestamp = QLabel("Letztes Update: —")
        self.parent.signal_timestamp.setStyleSheet("color: #666; font-size: 10px;")
        row3.addWidget(self.parent.signal_timestamp)
        row3.addStretch()
        layout.addLayout(row3)

        return group

    def create_position_section(self) -> QGroupBox:
        """Creates position display section."""
        group = QGroupBox("📈 Aktive Position")
        layout = QVBoxLayout(group)

        # Position Details Grid
        details_layout = QHBoxLayout()

        # Left Column
        left = QVBoxLayout()
        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("Richtung:"))
        self.parent.pos_side = QLabel("—")
        self.parent.pos_side.setStyleSheet("font-weight: bold;")
        side_row.addWidget(self.parent.pos_side)
        side_row.addStretch()
        left.addLayout(side_row)

        entry_row = QHBoxLayout()
        entry_row.addWidget(QLabel("Entry:"))
        self.parent.pos_entry = QLabel("—")
        entry_row.addWidget(self.parent.pos_entry)
        entry_row.addStretch()
        left.addLayout(entry_row)

        current_row = QHBoxLayout()
        current_row.addWidget(QLabel("Aktuell:"))
        self.parent.pos_current = QLabel("—")
        self.parent.pos_current.setStyleSheet("font-weight: bold;")
        current_row.addWidget(self.parent.pos_current)
        current_row.addStretch()
        left.addLayout(current_row)

        details_layout.addLayout(left)

        # Right Column
        right = QVBoxLayout()
        sl_row = QHBoxLayout()
        sl_row.addWidget(QLabel("SL:"))
        self.parent.pos_sl = QLabel("—")
        self.parent.pos_sl.setStyleSheet("color: #f44336;")
        sl_row.addWidget(self.parent.pos_sl)
        sl_row.addStretch()
        right.addLayout(sl_row)

        tp_row = QHBoxLayout()
        tp_row.addWidget(QLabel("TP:"))
        self.parent.pos_tp = QLabel("—")
        self.parent.pos_tp.setStyleSheet("color: #4CAF50;")
        tp_row.addWidget(self.parent.pos_tp)
        tp_row.addStretch()
        right.addLayout(tp_row)

        pnl_row = QHBoxLayout()
        pnl_row.addWidget(QLabel("PnL:"))
        self.parent.pos_pnl = QLabel("—")
        self.parent.pos_pnl.setStyleSheet("font-weight: bold;")
        pnl_row.addWidget(self.parent.pos_pnl)
        pnl_row.addStretch()
        right.addLayout(pnl_row)

        details_layout.addLayout(right)
        layout.addLayout(details_layout)

        # SL/TP Progress Bar
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("SL"))
        self.parent.sl_tp_progress = QProgressBar()
        self.parent.sl_tp_progress.setRange(0, 100)
        self.parent.sl_tp_progress.setValue(50)
        self.parent.sl_tp_progress.setTextVisible(False)
        self.parent.sl_tp_progress.setStyleSheet("""
            QProgressBar { border: 1px solid #333; border-radius: 3px;
                           background-color: #1a1a1a; height: 10px; }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f44336, stop:0.5 #FFC107, stop:1 #4CAF50);
            }
        """)
        progress_layout.addWidget(self.parent.sl_tp_progress, 1)
        progress_layout.addWidget(QLabel("TP"))
        layout.addLayout(progress_layout)

        # Close Button
        self.parent.close_position_btn = QPushButton("❌ Position schließen")
        self.parent.close_position_btn.setStyleSheet("""
            QPushButton { background-color: #D32F2F; color: white; padding: 8px; border-radius: 4px; }
            QPushButton:hover { background-color: #B71C1C; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.parent.close_position_btn.setEnabled(False)
        layout.addWidget(self.parent.close_position_btn)

        return group

    def create_stats_section(self) -> QGroupBox:
        """Creates statistics display."""
        group = QGroupBox("📊 Tagesstatistik")
        layout = QHBoxLayout(group)

        # Trades
        trades_layout = QVBoxLayout()
        self.parent.stats_trades = QLabel("0")
        self.parent.stats_trades.setStyleSheet("font-size: 18px; font-weight: bold;")
        trades_layout.addWidget(self.parent.stats_trades, alignment=Qt.AlignmentFlag.AlignCenter)
        trades_layout.addWidget(QLabel("Trades"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(trades_layout)

        layout.addWidget(self._create_separator())

        # Win Rate
        wr_layout = QVBoxLayout()
        self.parent.stats_winrate = QLabel("—%")
        self.parent.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        wr_layout.addWidget(self.parent.stats_winrate, alignment=Qt.AlignmentFlag.AlignCenter)
        wr_layout.addWidget(QLabel("Win Rate"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(wr_layout)

        layout.addWidget(self._create_separator())

        # PnL
        pnl_layout = QVBoxLayout()
        self.parent.stats_pnl = QLabel("$0.00")
        self.parent.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold;")
        pnl_layout.addWidget(self.parent.stats_pnl, alignment=Qt.AlignmentFlag.AlignCenter)
        pnl_layout.addWidget(QLabel("Daily PnL"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(pnl_layout)

        layout.addWidget(self._create_separator())

        # Max Drawdown
        dd_layout = QVBoxLayout()
        self.parent.stats_drawdown = QLabel("$0.00")
        self.parent.stats_drawdown.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")
        dd_layout.addWidget(self.parent.stats_drawdown, alignment=Qt.AlignmentFlag.AlignCenter)
        dd_layout.addWidget(QLabel("Max DD"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(dd_layout)

        return group

    def _create_separator(self) -> QFrame:
        """Creates vertical separator."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #333;")
        return sep

    def create_log_section(self) -> QGroupBox:
        """Creates log viewer."""
        group = QGroupBox("📝 Bot Log")
        layout = QVBoxLayout(group)

        self.parent.log_text = QTextEdit()
        self.parent.log_text.setReadOnly(True)
        self.parent.log_text.setStyleSheet("""
            QTextEdit { background-color: #0d0d0d; color: #aaa;
                        font-family: 'Consolas', 'Monaco', monospace;
                        font-size: 11px; border: 1px solid #333; border-radius: 4px; }
        """)
        layout.addWidget(self.parent.log_text)

        # Clear Button
        clear_btn = QPushButton("🗑 Log löschen")
        clear_btn.setStyleSheet("""
            QPushButton { background-color: #333; color: #888; padding: 5px;
                          border-radius: 3px; font-size: 10px; }
            QPushButton:hover { background-color: #444; }
        """)
        clear_btn.clicked.connect(lambda: self.parent.log_text.clear())
        layout.addWidget(clear_btn)

        return group
