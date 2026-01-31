"""Bot Signals Status Mixin - Status display and signal table management.

This module handles:
- Current position widget (SL/TP progress bar, position details)
- Signals widget (trading table toolbar + table)
- Bot log widget (bot log + KI messages)
- Signals table setup (25 columns)
"""

from __future__ import annotations

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFormLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QPushButton, QTableWidget, QVBoxLayout, QWidget, QPlainTextEdit
)

from src.ui.icons import get_icon
from ..signals.widgets.sltp_progress_bar import SLTPProgressBar

logger = logging.getLogger(__name__)


class BotSignalsStatusMixin:
    """Mixin for status display and signal table management.

    This mixin provides:
    - Current position widget (_build_current_position_widget)
    - Position layout builders (_build_position_left/right_column)
    - Signals widget (_build_signals_widget) with toolbar
    - Signals table setup (_build_signals_table) - 25 columns
    - Bot log widget (_build_bot_log_widget) - bot log + KI messages
    """

    # ==========================================
    # Current Position Widget
    # ==========================================

    def _build_current_position_widget(self) -> QWidget:
        """Build current position widget with SL/TP progress bar and position details.

        Structure:
        - GroupBox "Current Position"
          - SL/TP Progress Bar (top)
          - Position details (horizontal layout)
            - Left column (side, entry, size, P&L, etc.)
            - Right column (score, TR price, derivat info)

        Returns:
            QWidget: Complete position widget
        """
        position_widget = QWidget()
        position_layout = QVBoxLayout(position_widget)
        position_layout.setContentsMargins(0, 0, 0, 0)
        position_layout.setSpacing(0)

        position_group = QGroupBox("Current Position")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(6, 6, 6, 6)
        group_layout.setSpacing(4)

        # Add SL/TP Progress Bar at the top
        self.sltp_progress_bar = SLTPProgressBar()
        self.sltp_progress_bar.reset_bar()
        group_layout.addWidget(self.sltp_progress_bar)

        # Add position details
        details_widget = QWidget()
        details_widget.setLayout(self._build_position_layout())
        group_layout.addWidget(details_widget)

        position_group.setLayout(group_layout)
        position_group.setMaximumHeight(220)
        position_layout.addWidget(position_group)
        return position_widget

    def _build_position_layout(self) -> QHBoxLayout:
        """Build horizontal layout for position details (left + right columns).

        Returns:
            QHBoxLayout: Layout with left and right columns
        """
        position_h_layout = QHBoxLayout()
        position_h_layout.setContentsMargins(8, 8, 8, 8)
        position_h_layout.setSpacing(20)

        position_h_layout.addWidget(self._build_position_left_column())
        position_h_layout.addWidget(self._build_position_right_column())
        position_h_layout.addStretch()
        return position_h_layout

    def _build_position_left_column(self) -> QWidget:
        """Build left column of position details.

        Contains:
        - Side (LONG/SHORT/FLAT)
        - Strategy
        - Entry price
        - Size
        - Invested amount
        - Stop price
        - Current price
        - P&L
        - Bars held

        Returns:
            QWidget: Left column widget with labels
        """
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
        """Build right column of position details.

        Contains:
        - Score
        - TR Kurs (Trailing Stop price)
        - Derivat section (separator)
          - WKN
          - Hebel (leverage)
          - Spread
          - Ask price
          - D P&L (derivat P&L)

        Returns:
            QWidget: Right column widget with labels
        """
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

    # ==========================================
    # Signals Widget (Trading Table)
    # ==========================================

    def _build_signals_widget(self) -> QWidget:
        """Build signals widget with toolbar and trading table.

        Toolbar buttons:
        - 🗑️ Zeile löschen (delete selected)
        - 🧹 Alle löschen (delete all)
        - 💰 Sofort verkaufen (sell position - Issue #11)
        - 📊 Chart-Elemente (draw chart elements - Issue #18)
        - 📤 XLSX exportieren (export signals - Issue #4)
        - ▶ Start Bot (toggle bot - Issue #9)
        - ⚙️ Settings

        Returns:
            QWidget: Signals widget with toolbar and table
        """
        signals_widget = QWidget()
        signals_layout = QVBoxLayout(signals_widget)
        signals_layout.setContentsMargins(0, 0, 0, 0)

        signals_group = QGroupBox("Trading Table")
        signals_inner = QVBoxLayout()

        # TOOLBAR with action buttons
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

        # Issue #11: Sell position button
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

        # Issue #18: Chart elements button
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

        # Issue #4: XLSX export
        export_btn = QPushButton("📤 XLSX exportieren")
        export_btn.setFixedHeight(24)
        export_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 8px; background-color: #4caf50; color: white;"
        )
        export_btn.setToolTip("Exportiert die Trading-Tabelle als XLSX")
        export_btn.clicked.connect(self._on_export_signals_clicked)
        toolbar.addWidget(export_btn)

        # Issue #9: Start Bot button (same function as in Bot tab)
        self.signals_tab_start_bot_btn = QPushButton("▶ Start Bot")
        self.signals_tab_start_bot_btn.setFixedHeight(24)
        self.signals_tab_start_bot_btn.setStyleSheet(
            "font-size: 10px; padding: 2px 12px; background-color: #ef5350; color: white; font-weight: bold;"
        )
        self.signals_tab_start_bot_btn.setToolTip(
            "Startet/Stoppt den Trading Bot\n"
            "Grün = Bot läuft\n"
            "Rot = Bot gestoppt"
        )
        self.signals_tab_start_bot_btn.clicked.connect(self._on_signals_tab_bot_toggle_clicked)
        toolbar.addWidget(self.signals_tab_start_bot_btn)

        # Issue #8: Settings button next to Start/Stop Bot
        self.signals_tab_settings_btn = QPushButton()
        self.signals_tab_settings_btn.setIcon(get_icon("settings"))
        self.signals_tab_settings_btn.setFixedHeight(24)
        self.signals_tab_settings_btn.setFixedWidth(28)
        self.signals_tab_settings_btn.setToolTip("Settings öffnen")
        self.signals_tab_settings_btn.setStyleSheet(
            "padding: 0px; background-color: #2a2a2a; border: 1px solid #555; border-radius: 3px;"
        )
        self.signals_tab_settings_btn.clicked.connect(self._open_main_settings_dialog)
        toolbar.addWidget(self.signals_tab_settings_btn)

        toolbar.addStretch()

        signals_inner.addLayout(toolbar)
        self._build_signals_table()
        signals_inner.addWidget(self.signals_table)
        signals_group.setLayout(signals_inner)
        signals_layout.addWidget(signals_group)
        return signals_widget

    # ==========================================
    # Signals Table Setup (25 Columns)
    # ==========================================

    def _build_signals_table(self) -> None:
        """Build signals table with 25 columns and configure column widths.

        Columns (Issue #19: P&L % before P&L USDT):
        0: Time          11: Current      21: WKN (hidden)
        1: Type          12: P&L %        22: Score (hidden)
        2: Strategy      13: P&L USDT     23: TR Stop
        3: Side          14: Trading fees % 24: Liquidation
        4: Entry         15: Trading fees
        5: Stop          16: Invest (Issue #18)
        6: SL%           17: Stück
        7: TR%           18: D P&L € (hidden)
        8: TRA%          19: D P&L % (hidden)
        9: TR Lock       20: Hebel (visible - Issue #3)
        10: Status

        Hidden columns: D P&L € (18), D P&L % (19), WKN (21), Score (22)
        Issue #3: Hebel (20) is VISIBLE (was hidden before)
        """
        self.signals_table = QTableWidget()
        # Issue #3: Updated layout - P&L % before P&L USDT, renamed columns
        self.signals_table.setColumnCount(25)
        self.signals_table.setHorizontalHeaderLabels(
            [
                "Time", "Type", "Strategy", "Side", "Entry", "Stop", "SL%", "TR%",
                "TRA%", "TR Lock", "Status", "Current", "P&L %", "P&L USDT",  # Issue #19: P&L % before P&L USDT
                "Trading fees %", "Trading fees", "Invest", "Stück",  # Issue #18: "Fees €" -> "Invest"
                "D P&L €", "D P&L %", "Hebel", "WKN", "Score", "TR Stop", "Liquidation",
            ]
        )
        # Hidden columns: D P&L € (18), D P&L % (19), WKN (21), Score (22)
        # Issue #3: Hebel (20) is now VISIBLE
        for col in [18, 19, 21]:
            self.signals_table.setColumnHidden(col, True)
        self.signals_table.setColumnHidden(22, True)

        header = self.signals_table.horizontalHeader()
        # Narrow columns (approx 6 chars) for compact view (Issue #4)
        narrow_cols = [1, 3, 6, 7, 8, 9, 10]
        for col in narrow_cols:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)

        # Issue #3: Time fixed width 140px (was 70px)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(0, 140)

        # Strategy can stretch but keep moderate size
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Issue #3: Entry (4), Stop (5), Current (11) fixed at 110px
        for col in [4, 5, 11]:
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.Fixed)
            header.resizeSection(col, 110)

        # Issue #19: P&L % (12) fixed at 90px (before P&L USDT)
        header.setSectionResizeMode(12, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(12, 90)

        # Issue #19: P&L USDT (13) fixed at 120px
        header.setSectionResizeMode(13, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(13, 120)

        # Issue #5: Trading fees % (14) fixed at 90px
        header.setSectionResizeMode(14, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(14, 90)

        # Issue #4: Trading fees (15) fixed at 120px
        header.setSectionResizeMode(15, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(15, 120)

        # Issue #18: Invest (16) fixed at 100px
        header.setSectionResizeMode(16, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(16, 100)

        # Issue #3: Hebel column (20) fixed at 90px and VISIBLE
        header.setSectionResizeMode(20, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(20, 90)

        # Liquidation (24) fixed at 110px
        header.setSectionResizeMode(24, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(24, 110)

        # Stretch remaining numeric/value columns
        for col in [17, 23]:
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

    # ==========================================
    # Bot Log Widget (Issue #2 & #23)
    # ==========================================

    def _build_bot_log_widget(self) -> QWidget:
        """Create combined Bot Log + KI Nachrichten (Issue #2 & #23).

        Structure (horizontal layout):
        - Left: Bot Log
          - Status label (RUNNING/STOPPED)
          - Log text widget
          - Save/Clear buttons
        - Right: KI Messages
          - Info label
          - Messages text widget (dark green theme)
          - Prompt management / Save / Clear buttons

        Returns:
            QWidget: Combined bot log widget
        """
        container = QWidget()
        main_layout = QHBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(8)

        # Left: Bot log
        bot_group = QGroupBox("Log Trading Bot")
        bot_layout = QVBoxLayout(bot_group)
        bot_layout.setContentsMargins(6, 6, 6, 6)
        bot_layout.setSpacing(6)

        status_row = QHBoxLayout()
        self.bot_run_status_label = QLabel("Status: STOPPED")
        self.bot_run_status_label.setStyleSheet("font-weight: bold; color: #9e9e9e;")
        status_row.addWidget(self.bot_run_status_label)
        status_row.addStretch()
        bot_layout.addLayout(status_row)

        self.bot_log_text = QPlainTextEdit()
        self.bot_log_text.setReadOnly(True)
        self.bot_log_text.setPlaceholderText("Bot-Aktivitäten, Status und Fehler werden hier protokolliert...")
        self.bot_log_text.setMinimumHeight(140)
        bot_layout.addWidget(self.bot_log_text)

        bot_btn_row = QHBoxLayout()
        self.bot_log_save_btn = QPushButton("💾 Speichern")
        self.bot_log_save_btn.clicked.connect(self._save_bot_log)
        bot_btn_row.addWidget(self.bot_log_save_btn)

        self.bot_log_clear_btn = QPushButton("🧹 Leeren")
        self.bot_log_clear_btn.clicked.connect(self._clear_bot_log)
        bot_btn_row.addWidget(self.bot_log_clear_btn)
        bot_btn_row.addStretch()
        bot_layout.addLayout(bot_btn_row)

        # Right: KI messages + prompt management
        ki_group = QGroupBox("KI Nachrichten")
        ki_layout = QVBoxLayout(ki_group)
        ki_layout.setContentsMargins(6, 6, 6, 6)
        ki_layout.setSpacing(6)

        info_row = QHBoxLayout()
        info_label = QLabel("Ungefilterte Ausgaben des Trading Bots")
        info_label.setStyleSheet("color: #888; font-size: 10px;")
        info_row.addWidget(info_label)
        info_row.addStretch()
        ki_layout.addLayout(info_row)

        self.ki_messages_text = QPlainTextEdit()
        self.ki_messages_text.setReadOnly(True)
        self.ki_messages_text.setPlaceholderText("Ungefilterte KI-Ausgaben erscheinen hier...")
        self.ki_messages_text.setMinimumHeight(140)
        self.ki_messages_text.setStyleSheet("""
            QPlainTextEdit { background-color: #0d0d0d; color: #4CAF50; font-family: Consolas, monospace; font-size: 10px; }
        """)
        ki_layout.addWidget(self.ki_messages_text)

        ki_btn_row = QHBoxLayout()
        self.prompt_mgmt_btn = QPushButton("⚙️ Prompts verwalten")
        self.prompt_mgmt_btn.setToolTip("Öffnet Dialog zur Verwaltung und Bearbeitung der Bot-Prompts")
        self.prompt_mgmt_btn.clicked.connect(self._open_prompt_management)
        ki_btn_row.addWidget(self.prompt_mgmt_btn)

        self.ki_messages_save_btn = QPushButton("💾 Speichern")
        self.ki_messages_save_btn.clicked.connect(self._save_ki_messages)
        ki_btn_row.addWidget(self.ki_messages_save_btn)

        self.ki_messages_clear_btn = QPushButton("🧹 Leeren")
        self.ki_messages_clear_btn.clicked.connect(self._clear_ki_messages)
        ki_btn_row.addWidget(self.ki_messages_clear_btn)
        ki_btn_row.addStretch()
        ki_layout.addLayout(ki_btn_row)

        main_layout.addWidget(bot_group, stretch=1)
        main_layout.addWidget(ki_group, stretch=1)
        return container
