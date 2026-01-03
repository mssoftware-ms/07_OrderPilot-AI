from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QThread, Qt, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QDialog,
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QStyledItemDelegate,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtCore import QSettings

# Import AnalysisWorker here to avoid NameError
from .chart_chat_worker import AnalysisWorker

if TYPE_CHECKING:
    from .chat_service import ChartChatService
    from .models import ChartAnalysisResult, QuickAnswerResult

logger = logging.getLogger(__name__)


class ColorCellDelegate(QStyledItemDelegate):
    """Custom delegate for color cells that doesn't show selection highlight."""

    def paint(self, painter, option, index):
        """Paint the color cell without selection highlight."""
        # Get the color from item data
        color_code = index.data(Qt.ItemDataRole.UserRole)
        if not color_code:
            color_code = "#0d6efd55"

        # Fill the cell with the color
        painter.fillRect(option.rect, QColor(color_code))

        # Don't call super().paint() to avoid selection highlight


class ChartChatActionsMixin:
    """ChartChatActionsMixin extracted from ChartChatWidget."""
    def _on_quick_action(self) -> None:
        """Handle quick action button click."""
        button = self.sender()
        if not button:
            return

        action_type = button.property("action_type")
        question = button.property("question")

        if action_type == "full_analysis":
            self._on_full_analysis()
        elif action_type == "ask" and question:
            self._input_field.setText(question)
            self._on_send()
    def _on_send(self) -> None:
        """Handle send button click."""
        question = self._input_field.text().strip()
        if not question:
            return

        self._input_field.clear()
        self._append_message("user", question)
        self._start_analysis("ask", question)
    def _on_full_analysis(self) -> None:
        """Handle full analysis button click."""
        self._append_message(
            "user",
            f"[Vollständige Chartanalyse angefordert]"
        )
        self._start_analysis("full_analysis")
        # Emit signal with action type (signal expects str argument)
        if hasattr(self, 'analysis_requested'):
            self.analysis_requested.emit("full_analysis")
    def _start_analysis(
        self, action: str, question: str | None = None
    ) -> None:
        """Start background analysis.

        Args:
            action: 'full_analysis' or 'ask'
            question: Optional question for 'ask' action
        """
        # Check if a worker is already running
        if self._worker and self._worker.isRunning():
            logger.warning("Analysis already in progress, ignoring new request")
            self._append_message(
                "assistant",
                "⏳ Bitte warte, bis die aktuelle Anfrage abgeschlossen ist."
            )
            return

        # Check if AI service is available
        if not self.service.ai_service:
            self._append_message(
                "assistant",
                "⚠️ **AI Service nicht verfügbar!**\n\n"
                "Bitte konfiguriere einen AI-Provider:\n"
                "1. Gehe zu File → Settings → AI Tab\n"
                "2. Wähle OpenAI, Anthropic oder Gemini\n"
                "3. Setze den entsprechenden API-Key\n\n"
                "Alternativ kannst du eine Umgebungsvariable setzen:\n"
                "• OPENAI_API_KEY\n"
                "• ANTHROPIC_API_KEY\n"
                "• GEMINI_API_KEY"
            )
            return

        # Check if AI service has required methods
        ai_service = self.service.ai_service
        has_methods = (
            hasattr(ai_service, "complete") or
            hasattr(ai_service, "chat_completion") or
            hasattr(ai_service, "generate")
        )
        if not has_methods:
            self._append_message(
                "assistant",
                f"⚠️ **AI Service fehlerhaft!**\n\n"
                f"Der AI-Service ({type(ai_service).__name__}) unterstützt keine "
                f"bekannte Completion-Methode.\n\n"
                f"Bitte überprüfe deine AI-Konfiguration."
            )
            return

        self._set_loading(True)

        self._worker = AnalysisWorker(self.service, action, question)
        self._worker.finished.connect(self._on_analysis_complete)
        self._worker.error.connect(self._on_analysis_error)
        self._worker.start()
    def _on_analysis_complete(self, result: Any) -> None:
        """Handle completed analysis.

        Args:
            result: ChartAnalysisResult or QuickAnswerResult
        """
        self._set_loading(False)

        # Clean up worker reference
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

        # Format response based on type
        is_new_analysis = False
        if hasattr(result, "to_markdown"):
            # ChartAnalysisResult
            content = result.to_markdown()
            is_new_analysis = True
        elif hasattr(result, "answer"):
            # QuickAnswerResult
            content = result.answer
            is_new_analysis = True
            if result.follow_up_suggestions:
                content += "\n\n**Weitere Fragen:**\n"
                for suggestion in result.follow_up_suggestions:
                    content += f"- {suggestion}\n"
        else:
            content = str(result)

        self._append_message("assistant", content)

        # Auswertung nur bei neuer Analyse und wenn Checkbox aktiv
        try:
            checkbox = getattr(self, "_evaluate_checkbox", None)
            if checkbox and checkbox.isChecked() and is_new_analysis:
                logger.info("Auto-opening evaluation popup (new analysis)")
                self._show_evaluation_popup(content=content)
        except Exception as e:
            logger.warning("Evaluation popup failed: %s", e, exc_info=True)
    def _on_analysis_error(self, error: str) -> None:
        """Handle analysis error.

        Args:
            error: Error message
        """
        self._set_loading(False)

        # Clean up worker reference
        if self._worker:
            self._worker.deleteLater()
            self._worker = None

        self._append_message(
            "assistant",
            f"⚠️ **Fehler:** {error}"
        )
    def _set_loading(self, loading: bool) -> None:
        """Set loading state.

        Args:
            loading: True if loading
        """
        self._progress_bar.setVisible(loading)
        self._send_button.setEnabled(not loading)
        if hasattr(self, "_analyze_button") and self._analyze_button:
            self._analyze_button.setEnabled(not loading)
        self._input_field.setEnabled(not loading)

    def _on_open_evaluation_popup(self):
        """Open last evaluation table if available."""
        if not getattr(self, "_last_eval_entries", None):
            QMessageBox.information(self, "Auswertung", "Keine Auswertung vorhanden.")
            return
        self._show_evaluation_popup(entries=self._last_eval_entries)

    def _show_evaluation_popup(self, content: str | None = None, entries: list | None = None) -> None:
        """Parse variable lines and show them in a table popup.

        - Only lines like "[#Label; value]" are accepted.
        - "value" must be either a single Zahl oder "zahl-zahl".
        - Optional drittes Feld (Kommentar) landet in Spalte "Info".
        - Bei ungültigen Werten erscheint eine Fehlermeldung und der Eintrag wird übersprungen.
        """
        import re

        logger.debug(f"_show_evaluation_popup called with content={'present' if content else 'None'}, entries={'present' if entries else 'None'}")

        var_pattern = re.compile(r"^\[#(.+?)\]$")
        numeric_pattern = re.compile(r"^-?\d+(?:\.\d+)?(?:-?\d+(?:\.\d+)?)?$")

        parsed_entries = []
        invalid = []

        source_lines = []
        if entries is not None:
            # entries already provided as list of tuples
            for e in entries:
                if len(e) >= 4:
                    parsed_entries.append((e[0], e[1], e[2], e[3]))
                elif len(e) == 3:
                    parsed_entries.append((e[0], e[1], e[2], "#0d6efd55"))
                else:
                    continue
        elif content:
            source_lines = content.splitlines()
            for line in source_lines:
                stripped = line.strip()
                if not stripped.startswith("[#") or not stripped.endswith("]"):
                    continue
                m = var_pattern.match(stripped)
                if not m:
                    continue
                inner = m.group(1)
                parts = [p.strip() for p in inner.split(";")]
                if len(parts) < 2:
                    continue
                label = parts[0]
                value = parts[1]
                info = parts[2] if len(parts) > 2 else ""
                color = parts[3] if len(parts) > 3 else "#0d6efd55"
                if not numeric_pattern.match(value):
                    invalid.append(stripped)
                    continue
                parsed_entries.append((label, value, info, color))

        if invalid:
            QMessageBox.warning(
                self,
                "Auswertung fehlerhaft",
                "Einige Werte sind nicht numerisch und wurden übersprungen:\n\n"
                + "\n".join(invalid),
            )

        if not parsed_entries:
            # Show warning if checkbox is checked but no data found
            if getattr(self, "_evaluate_checkbox", None) and self._evaluate_checkbox.isChecked():
                QMessageBox.information(
                    self,
                    "Keine Auswertung",
                    "Die Checkbox 'Auswertung' ist aktiviert, aber es konnten keine "
                    "Auswertungsdaten im Format [#Label; Wert] extrahiert werden.\n\n"
                    "Beispiel: [#Support Zone; 87450-87850]"
                )
            logger.debug("No evaluation entries found in content")
            return

        # persist for reopening
        self._last_eval_entries = [tuple(e) for e in parsed_entries]

        # Ensure only one evaluation dialog at a time
        try:
            if getattr(self, "_eval_dialog", None):
                self._eval_dialog.close()
        except Exception:
            pass

        dlg = QDialog(self)
        dlg.setWindowTitle("Auswertung")
        dlg.setModal(False)
        dlg.setWindowModality(Qt.WindowModality.NonModal)
        dlg.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self._eval_dialog = dlg
        dlg.destroyed.connect(lambda: setattr(self, "_eval_dialog", None))
        dlg_layout = QVBoxLayout(dlg)

        table = QTableWidget(len(parsed_entries), 4, dlg)
        table.setHorizontalHeaderLabels(["Name", "Wert", "Info", "Farbe"])
        table.verticalHeader().setVisible(False)
        table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)
        table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        table.setWordWrap(True)
        table.setColumnWidth(0, 180)
        table.setColumnWidth(1, 130)
        table.setColumnWidth(2, 160)
        table.setColumnWidth(3, 50)
        table.horizontalHeader().setStretchLastSection(False)
        # Make Info column (index 2) stretchable instead of the last column
        table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)

        # Set custom delegate for color column to prevent selection highlight
        table.setItemDelegateForColumn(3, ColorCellDelegate(table))

        # Track changes for save button state
        has_changes = [False]
        settings = QSettings("OrderPilot", "TradingApp")
        default_color_rules = {
            "stop": "#ef5350",
            "take profit": "#26a69a",
            "target": "#26a69a",
            "tp": "#26a69a",
            "support": "#2ca8b1",
            "demand": "#2ca8b1",
            "resistance": "#f39c12",
            "supply": "#f39c12",
            "entry long": "#0d6efd",
            "entry short": "#c2185b",
            "sma": "#9e9e9e",
            "ema": "#9e9e9e",
            "vwap": "#9e9e9e",
        }
        stored = settings.value("eval_color_rules", None)
        if isinstance(stored, dict):
            color_rules = {**default_color_rules, **stored}
        else:
            color_rules = default_color_rules.copy()

        def mark_changed():
            """Mark table as changed."""
            has_changes[0] = True

        def _apply_color(row, color_code):
            item = table.item(row, 3)
            if item is None:
                item = QTableWidgetItem("")
                table.setItem(row, 3, item)
            item.setText("")  # hide code, show swatch
            item.setData(Qt.ItemDataRole.UserRole, color_code)  # store color code in data
            item.setBackground(QColor(color_code))
            item.setToolTip(color_code)
            # Make color cell non-editable
            item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        table.blockSignals(True)
        for row, (label, value, info, color) in enumerate(parsed_entries):
            table.setItem(row, 0, QTableWidgetItem(label))
            table.setItem(row, 1, QTableWidgetItem(value))
            info_item = QTableWidgetItem(info)
            info_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
            table.setItem(row, 2, info_item)
            table.setItem(row, 3, QTableWidgetItem(color))
            _apply_color(row, color)
        table.blockSignals(False)
        table.resizeRowsToContents()
        has_changes[0] = False  # ensure clean state on open

        def on_color_double_click(row, col):
            if col != 3:
                return
            item = table.item(row, 3)
            current = item.data(Qt.ItemDataRole.UserRole) if item else "#0d6efd55"
            if not current:
                current = "#0d6efd55"
            chosen = QColorDialog.getColor(QColor(current), self, "Farbe wählen")
            if chosen.isValid():
                _apply_color(row, chosen.name())
                mark_changed()
                save_btn.setDisabled(False)

        table.cellDoubleClicked.connect(on_color_double_click)

        dlg_layout.addWidget(table)

        # Buttons: Save, Delete selected, Clear, Close
        btn_row = QHBoxLayout()

        def enable_save():
            """Enable save button when changes are made."""
            mark_changed()
            save_btn.setDisabled(False)

        def auto_assign_colors():
            """Assign standard colors based on label keywords."""
            def pick_color(label: str) -> str:
                lbl = label.lower()
                for key, clr in color_rules.items():
                    if key in lbl:
                        return clr
                # fallback: alternate palette to avoid transparent default
                fallback_palette = ["#7e57c2", "#ffca28", "#00897b", "#5c6bc0"]
                return fallback_palette[hash(lbl) % len(fallback_palette)]

            for r in range(table.rowCount()):
                label_item = table.item(r, 0)
                if not label_item:
                    continue
                color = pick_color(label_item.text())
                _apply_color(r, color)
            mark_changed()
            save_btn.setDisabled(False)

        def open_palette_dialog():
            dlg_pal = QDialog(dlg)
            dlg_pal.setWindowTitle("Farben zuordnen")
            layout = QVBoxLayout(dlg_pal)

            buttons = {}
            for key, clr in color_rules.items():
                row_layout = QHBoxLayout()
                lbl = QLabel(key)
                btn = QPushButton(" ")
                btn.setFixedWidth(32)
                btn.setStyleSheet(f"background:{clr};")
                def make_handler(k, b):
                    def handler():
                        chosen = QColorDialog.getColor(QColor(color_rules[k]), dlg_pal, f"Farbe für {k}")
                        if chosen.isValid():
                            color_rules[k] = chosen.name()
                            b.setStyleSheet(f"background:{chosen.name()};")
                    return handler
                btn.clicked.connect(make_handler(key, btn))
                row_layout.addWidget(lbl)
                row_layout.addStretch()
                row_layout.addWidget(btn)
                layout.addLayout(row_layout)

            apply_btn = QPushButton("Übernehmen")
            def save_and_close():
                settings.setValue("eval_color_rules", color_rules)
                settings.sync()
                dlg_pal.accept()
            apply_btn.clicked.connect(save_and_close)
            layout.addWidget(apply_btn)
            dlg_pal.exec()

        def save_entries():
            new_entries = []
            invalid_rows = []
            for r in range(table.rowCount()):
                label_item = table.item(r, 0)
                value_item = table.item(r, 1)
                info_item = table.item(r, 2)
                color_item = table.item(r, 3)
                label = label_item.text().strip() if label_item else ""
                value = value_item.text().strip() if value_item else ""
                info = info_item.text().strip() if info_item else ""
                color = color_item.data(Qt.ItemDataRole.UserRole) if color_item else "#0d6efd55"
                if not color:
                    color = "#0d6efd55"
                if not numeric_pattern.match(value):
                    invalid_rows.append(r + 1)
                    continue
                new_entries.append((label, value, info, color))

            if invalid_rows:
                QMessageBox.warning(
                    self,
                    "Speichern fehlgeschlagen",
                    "Ungültige Werte in Zeile(n): " + ", ".join(map(str, invalid_rows))
                    + "\nErlaubt sind nur Zahlen oder zahl-zahl.",
                )
                return

            self._last_eval_entries = new_entries
            has_changes[0] = False
            save_btn.setDisabled(True)
            QMessageBox.information(self, "Gespeichert", "Auswertung gespeichert.")

        def draw_selected():
            def draw_row(row: int):
                label_item = table.item(row, 0)
                value_item = table.item(row, 1)
                info_item = table.item(row, 2)
                color_item = table.item(row, 3)
                if not value_item or not label_item:
                    return
                label = (label_item.text().strip() if label_item else "").replace("'", "\\'")
                info = info_item.text().strip() if info_item else ""
                full_label = f"{label}" + (f" | {info}" if info else "")
                val = value_item.text().strip() if value_item else ""
                color = color_item.data(Qt.ItemDataRole.UserRole) if color_item else "#0d6efd55"
                if not color:
                    color = "#0d6efd55"
                # ensure transparency
                def ensure_alpha(c: str) -> str:
                    c = c.strip()
                    if c.startswith("#"):
                        if len(c) == 7:  # #RRGGBB -> add alpha 0x55
                            return c + "55"
                        return c
                    if c.lower().startswith("rgba"):
                        return c
                    return "#0d6efd55"
                chart = getattr(self.service, "chart_widget", None)
                if not chart:
                    return
                if "-" in val:
                    try:
                        parts = val.split("-")
                        low = float(parts[0])
                        high = float(parts[1])
                    except Exception:
                        return
                    color_rect = ensure_alpha(color)
                    if hasattr(chart, "add_rect_range"):
                        chart.add_rect_range(low, high, full_label, color_rect)
                    elif hasattr(chart, "web_view"):
                        js = (
                            "window.chartAPI && window.chartAPI.addRectRange("
                            f"{low}, {high}, '{color_rect}', '{full_label}');"
                        )
                        chart.web_view.page().runJavaScript(js)
                else:
                    try:
                        price = float(val)
                    except Exception:
                        return
                    color_line = color.strip() or "#0d6efd"
                    if hasattr(chart, "add_horizontal_line"):
                        chart.add_horizontal_line(price, full_label, color_line)
                    elif hasattr(chart, "web_view"):
                        js = (
                            "window.chartAPI && window.chartAPI.addHorizontalLine("
                            f"{price}, '{color_line}', '{full_label}');"
                        )
                        chart.web_view.page().runJavaScript(js)

            if all_draw_cb.isChecked():
                for r in range(table.rowCount()):
                    draw_row(r)
                return

            row = table.currentRow()
            if row < 0:
                QMessageBox.information(self, "Auswertung", "Bitte eine Zeile auswählen.")
                return
            draw_row(row)

        def delete_selected():
            selected = table.currentRow()
            if selected < 0:
                return
            table.removeRow(selected)
            enable_save()

        def clear_all():
            table.setRowCount(0)
            self._last_eval_entries = []
            enable_save()

        all_draw_cb = QCheckBox("Alle zeichnen", dlg)
        all_draw_cb.setChecked(False)

        save_btn = QPushButton("Speichern", dlg)
        save_btn.setDisabled(True)  # Initially disabled until changes are made
        save_btn.clicked.connect(save_entries)
        auto_color_btn = QPushButton("Farben setzen", dlg)
        auto_color_btn.clicked.connect(auto_assign_colors)
        palette_btn = QPushButton("🎨", dlg)
        palette_btn.setToolTip("Farbregeln bearbeiten")
        palette_btn.clicked.connect(open_palette_dialog)
        draw_btn = QPushButton("In Chart zeichnen", dlg)
        draw_btn.clicked.connect(draw_selected)
        del_btn = QPushButton("Löschen", dlg)
        del_btn.clicked.connect(delete_selected)
        clear_btn = QPushButton("Leeren", dlg)
        clear_btn.clicked.connect(clear_all)
        close_btn = QPushButton("Schließen", dlg)
        close_btn.clicked.connect(dlg.accept)

        # Connect table change events to enable save button
        table.cellChanged.connect(enable_save)
        has_changes[0] = False
        save_btn.setDisabled(True)

        # Warn on close if unsaved changes
        def on_close():
            if has_changes[0]:
                res = QMessageBox.question(
                    self,
                    "Auswertung",
                    "Sollen die Änderungen gespeichert werden?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Yes,
                )
                if res == QMessageBox.StandardButton.Yes:
                    save_entries()
                elif res == QMessageBox.StandardButton.Cancel:
                    return  # abort close
            dlg.accept()

        close_btn.clicked.disconnect()
        close_btn.clicked.connect(on_close)
        dlg.rejected.connect(lambda: None)

        btn_row.addWidget(save_btn)
        btn_row.addWidget(all_draw_cb)
        btn_row.addWidget(draw_btn)
        btn_row.addWidget(del_btn)
        btn_row.addWidget(clear_btn)
        btn_row.addWidget(auto_color_btn)  # nach "Leeren"
        btn_row.addWidget(palette_btn)
        btn_row.addStretch()
        btn_row.addWidget(close_btn)
        dlg_layout.addLayout(btn_row)

        dlg.resize(int(self.width() * 1.5), int(self.height() * 0.5))
        dlg.show()
