"""ChartSetDialog - Dialog for opening chart sets.

Provides a UI for selecting and opening predefined chart layouts
for pre-trade analysis.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QComboBox,
    QGroupBox,
    QFormLayout,
    QTextEdit,
    QMessageBox,
    QSpinBox,
    QCheckBox,
    QWidget,
)

if TYPE_CHECKING:
    from .layout_manager import ChartLayoutManager, ChartLayoutConfig

logger = logging.getLogger(__name__)


class ChartSetDialog(QDialog):
    """Dialog for opening and managing chart sets.

    This is the main UI for:
    - Opening pre-trade analysis with multiple timeframes
    - Selecting predefined layouts
    - Managing saved layouts
    """

    layout_selected = pyqtSignal(str, str)  # layout_name, symbol

    def __init__(
        self,
        layout_manager: "ChartLayoutManager",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self._layout_manager = layout_manager
        self._setup_ui()
        self._load_layouts()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("📊 Chart-Set öffnen (Pre-Trade Analyse)")
        self.setMinimumSize(700, 500)
        self._apply_styles()

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        layout.addWidget(self._build_header())
        layout.addLayout(self._build_content())
        layout.addWidget(self._build_quick_group())
        layout.addLayout(self._build_bottom_buttons())

    def _apply_styles(self) -> None:
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #e0e0e0;
            }
            QGroupBox {
                color: #4CAF50;
                font-weight: bold;
                border: 1px solid #555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QListWidget {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #3a3a3a;
            }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 5px;
            }
            QTextEdit {
                background-color: #2a2a2a;
                color: #888;
                border: 1px solid #555;
                border-radius: 3px;
            }
            QPushButton {
                background-color: #2a2a2a;
                color: #e0e0e0;
                border: 1px solid #555;
                border-radius: 3px;
                padding: 8px 15px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
            }
            QPushButton:pressed {
                background-color: #444;
            }
            QPushButton#openButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
            }
            QPushButton#openButton:hover {
                background-color: #45a049;
            }
            QCheckBox {
                color: #e0e0e0;
            }
        """
        )

    def _build_header(self) -> QLabel:
        header = QLabel("🎯 Wähle ein Chart-Layout für die Trend-Analyse")
        header.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #4CAF50; padding: 10px;"
        )
        return header

    def _build_content(self) -> QHBoxLayout:
        content = QHBoxLayout()
        content.setSpacing(15)
        content.addWidget(self._build_left_group(), 1)
        content.addWidget(self._build_right_group(), 1)
        return content

    def _build_left_group(self) -> QGroupBox:
        left_group = QGroupBox("Verfügbare Layouts")
        left_layout = QVBoxLayout(left_group)

        self.layout_list = QListWidget()
        self.layout_list.currentItemChanged.connect(self._on_layout_selected)
        left_layout.addWidget(self.layout_list)

        layout_actions = QHBoxLayout()
        self.delete_btn = QPushButton("🗑️ Löschen")
        self.delete_btn.clicked.connect(self._delete_layout)
        layout_actions.addWidget(self.delete_btn)
        layout_actions.addStretch()
        left_layout.addLayout(layout_actions)
        return left_group

    def _build_right_group(self) -> QGroupBox:
        right_group = QGroupBox("Einstellungen")
        right_layout = QVBoxLayout(right_group)

        form = QFormLayout()
        self.symbol_combo = QComboBox()
        self.symbol_combo.setEditable(True)
        self.symbol_combo.addItems(
            [
                "BTC/USD", "ETH/USD", "SOL/USD", "DOGE/USD",
                "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY", "QQQ",
            ]
        )
        form.addRow("Symbol:", self.symbol_combo)
        right_layout.addLayout(form)

        desc_label = QLabel("Beschreibung:")
        right_layout.addWidget(desc_label)

        self.description_text = QTextEdit()
        self.description_text.setReadOnly(True)
        self.description_text.setMaximumHeight(80)
        right_layout.addWidget(self.description_text)

        windows_label = QLabel("Chart-Fenster:")
        right_layout.addWidget(windows_label)

        self.windows_text = QTextEdit()
        self.windows_text.setReadOnly(True)
        right_layout.addWidget(self.windows_text)

        monitor_info = QLabel(self._get_monitor_info())
        monitor_info.setStyleSheet("color: #888; font-size: 11px;")
        right_layout.addWidget(monitor_info)
        return right_group

    def _build_quick_group(self) -> QGroupBox:
        quick_group = QGroupBox("Schnell-Analyse")
        quick_layout = QHBoxLayout(quick_group)

        quick_label = QLabel("Sofort öffnen:")
        quick_layout.addWidget(quick_label)

        self.quick_symbol = QComboBox()
        self.quick_symbol.setEditable(True)
        self.quick_symbol.addItems(["BTC/USD", "ETH/USD", "AAPL", "SPY"])
        self.quick_symbol.setMinimumWidth(120)
        quick_layout.addWidget(self.quick_symbol)

        mtf_btn = QPushButton("📈 Multi-TF Analyse")
        mtf_btn.setToolTip(
            "Öffnet 3 Charts (Tag, Stunde, 5min) für den ausgewählten Symbol"
        )
        mtf_btn.clicked.connect(self._quick_mtf_analysis)
        quick_layout.addWidget(mtf_btn)
        quick_layout.addStretch()
        return quick_group

    def _build_bottom_buttons(self) -> QHBoxLayout:
        buttons = QHBoxLayout()
        buttons.addStretch()

        cancel_btn = QPushButton("Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(cancel_btn)

        self.open_btn = QPushButton("📊 Layout öffnen")
        self.open_btn.setObjectName("openButton")
        self.open_btn.clicked.connect(self._open_layout)
        buttons.addWidget(self.open_btn)
        return buttons

    def _get_monitor_info(self) -> str:
        """Get info about available monitors."""
        monitors = self._layout_manager.get_available_monitors()
        if len(monitors) == 1:
            return f"ℹ️ 1 Monitor verfügbar: {monitors[0]['width']}x{monitors[0]['height']}"
        else:
            lines = [f"ℹ️ {len(monitors)} Monitore verfügbar:"]
            for m in monitors:
                primary = " (Primary)" if m['is_primary'] else ""
                lines.append(f"  • Monitor {m['index']}: {m['width']}x{m['height']}{primary}")
            return "\n".join(lines)

    def _load_layouts(self) -> None:
        """Load available layouts into the list."""
        self.layout_list.clear()

        layouts = self._layout_manager.get_available_layouts()
        for name in layouts:
            item = QListWidgetItem(name)
            item.setData(Qt.ItemDataRole.UserRole, name)
            self.layout_list.addItem(item)

        # Select first item
        if self.layout_list.count() > 0:
            self.layout_list.setCurrentRow(0)

    def _on_layout_selected(self, current: QListWidgetItem | None, previous: QListWidgetItem | None) -> None:
        """Handle layout selection change."""
        if not current:
            self.description_text.clear()
            self.windows_text.clear()
            return

        name = current.data(Qt.ItemDataRole.UserRole)
        layout = self._layout_manager.load_layout(name)

        if layout:
            self.description_text.setPlainText(layout.description or "Keine Beschreibung")

            # Build windows preview
            lines = []
            for i, win in enumerate(layout.windows, 1):
                indicators = ", ".join(win.indicators) if win.indicators else "Keine"
                stream = "🟢 Live" if win.auto_stream else ""
                lines.append(
                    f"{i}. {win.symbol} @ {win.timeframe} "
                    f"(Monitor {win.monitor}) {stream}\n"
                    f"   Indikatoren: {indicators}"
                )

            self.windows_text.setPlainText("\n".join(lines))

    def _open_layout(self) -> None:
        """Open the selected layout."""
        current = self.layout_list.currentItem()
        if not current:
            QMessageBox.warning(self, "Kein Layout", "Bitte wähle ein Layout aus.")
            return

        layout_name = current.data(Qt.ItemDataRole.UserRole)
        symbol = self.symbol_combo.currentText().strip()

        if not symbol:
            QMessageBox.warning(self, "Kein Symbol", "Bitte gib ein Symbol ein.")
            return

        # Load and open the layout
        layout = self._layout_manager.load_layout(layout_name)
        if layout:
            self._layout_manager.open_layout(layout, symbol=symbol)
            self.layout_selected.emit(layout_name, symbol)
            self.accept()
        else:
            QMessageBox.critical(self, "Fehler", f"Layout '{layout_name}' konnte nicht geladen werden.")

    def _quick_mtf_analysis(self) -> None:
        """Open quick multi-timeframe analysis."""
        symbol = self.quick_symbol.currentText().strip()
        if not symbol:
            QMessageBox.warning(self, "Kein Symbol", "Bitte gib ein Symbol ein.")
            return

        windows = self._layout_manager.open_pre_trade_analysis(symbol)
        if windows:
            self.layout_selected.emit("Multi-Timeframe-Analyse", symbol)
            self.accept()
        else:
            QMessageBox.critical(self, "Fehler", "Multi-Timeframe Layout konnte nicht geöffnet werden.")

    def _delete_layout(self) -> None:
        """Delete the selected layout."""
        current = self.layout_list.currentItem()
        if not current:
            return

        name = current.data(Qt.ItemDataRole.UserRole)

        reply = QMessageBox.question(
            self,
            "Layout löschen",
            f"Layout '{name}' wirklich löschen?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._layout_manager.delete_layout(name):
                self._load_layouts()
            else:
                QMessageBox.warning(self, "Fehler", "Layout konnte nicht gelöscht werden.")
