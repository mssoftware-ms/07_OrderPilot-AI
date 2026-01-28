"""
BotTabUIMixin - UI creation methods for BotTab

This mixin is part of the split BotTab implementation.
Contains methods extracted from bot_tab.py for better modularity.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import TYPE_CHECKING

import qasync
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, pyqtSlot
from PyQt6.QtGui import QColor, QTextCursor
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGroupBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QFrame,
    QProgressBar,
    QSplitter,
    QHeaderView,
    QMessageBox,
)

if TYPE_CHECKING:
    from src.core.broker.bitunix_paper_adapter import BitunixPaperAdapter
    from src.core.market_data.history_provider import HistoryManager

from src.core.trading_bot import (
    BotState,
    BotConfig,
    BotStatistics,
    SignalDirection,
    TradeSignal,
    MonitoredPosition,
    ExitResult,
    TradeLogEntry,
    MarketContext,
    RegimeType,
)

try:
    from src.ui.widgets.trading_status_panel import TradingStatusPanel
    HAS_STATUS_PANEL = True
except ImportError:
    HAS_STATUS_PANEL = False

try:
    from src.ui.widgets.trading_journal_widget import TradingJournalWidget
    HAS_JOURNAL = True
except ImportError:
    HAS_JOURNAL = False

logger = logging.getLogger(__name__)

BOT_SETTINGS_FILE = Path("config/bot_settings.json")


class BotTabUIMixin:
    """UI creation methods for BotTab"""

    def _setup_ui(self) -> None:
        """Erstellt das UI Layout."""
        print("DEBUG BotTab: _setup_ui() called")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(10)

        # --- Header: Bot Status ---
        header = self._create_header_section()
        layout.addWidget(header)
        print(f"DEBUG BotTab: Settings button created, enabled={self.settings_btn.isEnabled()}")

        # --- Phase 5: Trading Status Panel (Engine Results) ---
        if HAS_STATUS_PANEL:
            self._status_panel = TradingStatusPanel()
            self._status_panel.setVisible(False)  # Initial versteckt
            self._status_panel.refresh_requested.connect(self._on_status_panel_refresh)
            layout.addWidget(self._status_panel)
        else:
            self._status_panel = None

        # --- Phase 5.4: Trading Journal ---
        if HAS_JOURNAL:
            self._journal_widget = TradingJournalWidget()
            self._journal_widget.setVisible(False)  # Initial versteckt
            layout.addWidget(self._journal_widget)
        else:
            self._journal_widget = None

        # NOTE: WhatsApp Widget wurde in das ChartWindow Trading Bot Panel verschoben

        # --- Splitter für Signal/Position und Log ---
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Top Section: Signal + Position + Stats
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Signal Section
        top_layout.addWidget(self._create_signal_section())

        # Position Section
        top_layout.addWidget(self._create_position_section())

        # Statistics Section
        top_layout.addWidget(self._create_stats_section())

        splitter.addWidget(top_widget)

        # Bottom Section: Log
        splitter.addWidget(self._create_log_section())
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)

    def _create_header_section(self) -> QWidget:
        """Erstellt Header mit Status und Buttons."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-radius: 8px;
                padding: 8px;
            }
        """)
        layout = QHBoxLayout(frame)

        # Bot Icon und Status
        self.status_icon = QLabel("🤖")
        self.status_icon.setStyleSheet("font-size: 24px;")
        layout.addWidget(self.status_icon)

        status_layout = QVBoxLayout()
        self.status_label = QLabel("IDLE")
        self.status_label.setStyleSheet("""
            font-size: 16px;
            font-weight: bold;
            color: #888;
        """)
        status_layout.addWidget(self.status_label)

        self.status_detail = QLabel("Bot ist gestoppt")
        self.status_detail.setStyleSheet("color: #666; font-size: 11px;")
        status_layout.addWidget(self.status_detail)
        layout.addLayout(status_layout)

        layout.addStretch()

        # Buttons
        self.start_btn = QPushButton("▶ Start Bot")
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.start_btn.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_btn)

        # JSON Entry Button (NEU)
        self.start_btn_json = QPushButton("▶ Start Bot (JSON Entry)")
        self.start_btn_json.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.start_btn_json.setToolTip(
            "Startet Bot mit JSON-basierter Entry-Logik\n"
            "Nutzt CEL Expression aus Regime + Indicator JSON\n"
            "SL/TP/Trailing Stop aus UI-Feldern"
        )
        self.start_btn_json.clicked.connect(self._control.on_start_json_clicked)
        layout.addWidget(self.start_btn_json)

        self.stop_btn = QPushButton("⏹ Stop Bot")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #d32f2f; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        layout.addWidget(self.stop_btn)

        # Phase 5: Toggle für Status Panel
        self.status_panel_btn = QPushButton("📊")
        self.status_panel_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:checked { background-color: #1565C0; }
        """)
        self.status_panel_btn.setToolTip("Engine Status Panel ein/ausblenden")
        self.status_panel_btn.setCheckable(True)
        self.status_panel_btn.clicked.connect(self._toggle_status_panel)
        layout.addWidget(self.status_panel_btn)

        # Phase 5.4: Toggle für Journal
        self.journal_btn = QPushButton("📔")
        self.journal_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
            QPushButton:checked { background-color: #6A1B9A; }
        """)
        self.journal_btn.setToolTip("Trading Journal ein/ausblenden")
        self.journal_btn.setCheckable(True)
        self.journal_btn.clicked.connect(self._toggle_journal)
        layout.addWidget(self.journal_btn)

        # NOTE: WhatsApp Button wurde in das ChartWindow Trading Bot Panel verschoben

        self.settings_btn = QPushButton("⚙")
        self.settings_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #666; }
        """)
        self.settings_btn.setToolTip("Bot Settings")
        self.settings_btn.setEnabled(True)
        self.settings_btn.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        print(f"DEBUG: Connecting settings button clicked signal...")
        self.settings_btn.clicked.connect(lambda checked=False: self._handle_settings_click())
        receiver_count = self.settings_btn.receivers(self.settings_btn.clicked)
        print(f"DEBUG: Settings button has {receiver_count} receivers connected")

        layout.addWidget(self.settings_btn)

        return frame

    def _create_signal_section(self) -> QGroupBox:
        """Erstellt Signal-Anzeige Sektion."""
        group = QGroupBox("📊 Aktuelles Signal")
        layout = QVBoxLayout(group)

        # Direction und Confidence
        row1 = QHBoxLayout()

        self.signal_direction = QLabel("—")
        self.signal_direction.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            padding: 5px 15px;
            border-radius: 4px;
            background-color: #333;
        """)
        row1.addWidget(self.signal_direction)

        row1.addWidget(QLabel("Confluence:"))
        self.signal_confluence = QLabel("—")
        self.signal_confluence.setStyleSheet("font-weight: bold;")
        row1.addWidget(self.signal_confluence)

        row1.addStretch()

        self.signal_regime = QLabel("Regime: —")
        self.signal_regime.setStyleSheet("color: #888;")
        row1.addWidget(self.signal_regime)

        layout.addLayout(row1)

        # Conditions
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Conditions:"))
        self.signal_conditions = QLabel("—")
        self.signal_conditions.setWordWrap(True)
        self.signal_conditions.setStyleSheet("color: #aaa; font-size: 11px;")
        row2.addWidget(self.signal_conditions, 1)
        layout.addLayout(row2)

        # SL/TP Visual Bar (nur sichtbar wenn Position offen)
        self.sltp_container = QWidget()
        sltp_layout = QVBoxLayout(self.sltp_container)
        sltp_layout.setContentsMargins(0, 10, 0, 0)

        # Labels für SL / Current / TP
        sltp_labels_row = QHBoxLayout()
        self.sltp_sl_label = QLabel("SL: —")
        self.sltp_sl_label.setStyleSheet("color: #ef5350; font-weight: bold; font-size: 11px;")
        sltp_labels_row.addWidget(self.sltp_sl_label)
        sltp_labels_row.addStretch()
        self.sltp_current_label = QLabel("—")
        self.sltp_current_label.setStyleSheet("color: #fff; font-weight: bold; font-size: 12px;")
        sltp_labels_row.addWidget(self.sltp_current_label)
        sltp_labels_row.addStretch()
        self.sltp_tp_label = QLabel("TP: —")
        self.sltp_tp_label.setStyleSheet("color: #26a69a; font-weight: bold; font-size: 11px;")
        sltp_labels_row.addWidget(self.sltp_tp_label)
        sltp_layout.addLayout(sltp_labels_row)

        # Progress Bar (simuliert Balken zwischen SL und TP)
        self.sltp_bar = QProgressBar()
        self.sltp_bar.setTextVisible(False)
        self.sltp_bar.setMinimum(0)
        self.sltp_bar.setMaximum(100)
        self.sltp_bar.setValue(50)  # Default: Mitte
        self.sltp_bar.setMaximumHeight(20)
        # Grün-Rot Gradient: Rot=0% (SL), Grün=100% (TP)
        self.sltp_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #444;
                border-radius: 3px;
                background-color: #222;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #ef5350, stop:0.5 #ffa726, stop:1 #26a69a);
                border-radius: 2px;
            }
        """)
        sltp_layout.addWidget(self.sltp_bar)

        # P&L Display unter dem Balken
        self.sltp_pnl_label = QLabel("P&L: —")
        self.sltp_pnl_label.setStyleSheet("color: #888; font-size: 11px; margin-top: 5px;")
        self.sltp_pnl_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sltp_layout.addWidget(self.sltp_pnl_label)

        layout.addWidget(self.sltp_container)
        self.sltp_container.setVisible(True)  # Immer sichtbar, zeigt "keine Position" wenn nicht aktiv

        # Last Update
        row3 = QHBoxLayout()
        self.signal_timestamp = QLabel("Letztes Update: —")
        self.signal_timestamp.setStyleSheet("color: #666; font-size: 10px;")
        row3.addWidget(self.signal_timestamp)
        row3.addStretch()
        layout.addLayout(row3)

        return group

    def _create_position_section(self) -> QGroupBox:
        """Erstellt Position-Anzeige Sektion."""
        group = QGroupBox("📈 Aktive Position")
        layout = QVBoxLayout(group)

        # Position Details Grid
        details_layout = QHBoxLayout()

        # Left Column
        left = QVBoxLayout()

        side_row = QHBoxLayout()
        side_row.addWidget(QLabel("Richtung:"))
        self.pos_side = QLabel("—")
        self.pos_side.setStyleSheet("font-weight: bold;")
        side_row.addWidget(self.pos_side)
        side_row.addStretch()
        left.addLayout(side_row)

        entry_row = QHBoxLayout()
        entry_row.addWidget(QLabel("Entry:"))
        self.pos_entry = QLabel("—")
        entry_row.addWidget(self.pos_entry)
        entry_row.addStretch()
        left.addLayout(entry_row)

        current_row = QHBoxLayout()
        current_row.addWidget(QLabel("Aktuell:"))
        self.pos_current = QLabel("—")
        self.pos_current.setStyleSheet("font-weight: bold;")
        current_row.addWidget(self.pos_current)
        current_row.addStretch()
        left.addLayout(current_row)

        details_layout.addLayout(left)

        # Right Column
        right = QVBoxLayout()

        sl_row = QHBoxLayout()
        sl_row.addWidget(QLabel("SL:"))
        self.pos_sl = QLabel("—")
        self.pos_sl.setStyleSheet("color: #f44336;")
        sl_row.addWidget(self.pos_sl)
        sl_row.addStretch()
        right.addLayout(sl_row)

        tp_row = QHBoxLayout()
        tp_row.addWidget(QLabel("TP:"))
        self.pos_tp = QLabel("—")
        self.pos_tp.setStyleSheet("color: #4CAF50;")
        tp_row.addWidget(self.pos_tp)
        tp_row.addStretch()
        right.addLayout(tp_row)

        pnl_row = QHBoxLayout()
        pnl_row.addWidget(QLabel("PnL:"))
        self.pos_pnl = QLabel("—")
        self.pos_pnl.setStyleSheet("font-weight: bold;")
        pnl_row.addWidget(self.pos_pnl)
        pnl_row.addStretch()
        right.addLayout(pnl_row)

        details_layout.addLayout(right)
        layout.addLayout(details_layout)

        # SL/TP Progress Bar
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("SL"))
        self.sl_tp_progress = QProgressBar()
        self.sl_tp_progress.setRange(0, 100)
        self.sl_tp_progress.setValue(50)
        self.sl_tp_progress.setTextVisible(False)
        self.sl_tp_progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #333;
                border-radius: 3px;
                background-color: #1a1a1a;
                height: 10px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 #f44336, stop:0.5 #FFC107, stop:1 #4CAF50
                );
            }
        """)
        progress_layout.addWidget(self.sl_tp_progress, 1)
        progress_layout.addWidget(QLabel("TP"))
        layout.addLayout(progress_layout)

        # Close Button
        self.close_position_btn = QPushButton("❌ Position schließen")
        self.close_position_btn.setStyleSheet("""
            QPushButton {
                background-color: #D32F2F;
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #B71C1C; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.close_position_btn.setEnabled(False)
        self.close_position_btn.clicked.connect(self._on_close_position_clicked)
        layout.addWidget(self.close_position_btn)

        return group

    def _create_stats_section(self) -> QGroupBox:
        """Erstellt Statistik-Anzeige."""
        group = QGroupBox("📊 Tagesstatistik")
        layout = QHBoxLayout(group)

        # Trades
        trades_layout = QVBoxLayout()
        self.stats_trades = QLabel("0")
        self.stats_trades.setStyleSheet("font-size: 18px; font-weight: bold;")
        trades_layout.addWidget(self.stats_trades, alignment=Qt.AlignmentFlag.AlignCenter)
        trades_layout.addWidget(QLabel("Trades"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(trades_layout)

        layout.addWidget(self._create_separator())

        # Win Rate
        wr_layout = QVBoxLayout()
        self.stats_winrate = QLabel("—%")
        self.stats_winrate.setStyleSheet("font-size: 18px; font-weight: bold; color: #4CAF50;")
        wr_layout.addWidget(self.stats_winrate, alignment=Qt.AlignmentFlag.AlignCenter)
        wr_layout.addWidget(QLabel("Win Rate"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(wr_layout)

        layout.addWidget(self._create_separator())

        # PnL
        pnl_layout = QVBoxLayout()
        self.stats_pnl = QLabel("$0.00")
        self.stats_pnl.setStyleSheet("font-size: 18px; font-weight: bold;")
        pnl_layout.addWidget(self.stats_pnl, alignment=Qt.AlignmentFlag.AlignCenter)
        pnl_layout.addWidget(QLabel("Daily PnL"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(pnl_layout)

        layout.addWidget(self._create_separator())

        # Max Drawdown
        dd_layout = QVBoxLayout()
        self.stats_drawdown = QLabel("$0.00")
        self.stats_drawdown.setStyleSheet("font-size: 18px; font-weight: bold; color: #f44336;")
        dd_layout.addWidget(self.stats_drawdown, alignment=Qt.AlignmentFlag.AlignCenter)
        dd_layout.addWidget(QLabel("Max DD"), alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addLayout(dd_layout)

        return group

    def _create_separator(self) -> QFrame:
        """Erstellt vertikalen Separator."""
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet("color: #333;")
        return sep

    def _create_log_section(self) -> QGroupBox:
        """Erstellt Log-Viewer."""
        group = QGroupBox("📝 Bot Log")
        layout = QVBoxLayout(group)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setStyleSheet("""
            QTextEdit {
                background-color: #0d0d0d;
                color: #aaa;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.log_text)

        # Clear Button
        clear_btn = QPushButton("🗑 Log löschen")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #333;
                color: #888;
                padding: 5px;
                border-radius: 3px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: #444; }
        """)
        clear_btn.clicked.connect(lambda: self.log_text.clear())
        layout.addWidget(clear_btn)

        return group

    def _setup_signals(self) -> None:
        """Verbindet interne Signals für Thread-sichere Updates."""
        self.status_changed.connect(self._update_status_display)
        self.signal_updated.connect(self._update_signal_display)
        self.position_updated.connect(self._update_position_display)
        self.stats_updated.connect(self._update_stats_display)
        self.log_message.connect(self._append_log)

    def _setup_timers(self) -> None:
        """Erstellt Timer für periodische Updates."""
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self._periodic_update)
        self.update_timer.setInterval(1000)  # 1 Sekunde