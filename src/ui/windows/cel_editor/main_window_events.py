"""CEL Editor Window - Event Handlers Mixin.

This module contains all event handler methods for the CEL Editor main window.
Extracted from monolithic main_window.py (1798 LOC) as part of Phase 3 refactoring.

Responsibilities:
- Signal connections (_connect_signals)
- File operation handlers (new, open, save, export)
- RulePack handlers (load, save, rule selection)
- View mode switching
- Pattern canvas events
- AI generation events
- Help and about dialogs
- Window close event

Author: CODER-009 (Claude Sonnet 4.5)
Date: 2026-01-31
Task: 3.1.1 - Split cel_editor/main_window.py
"""

from PyQt6.QtWidgets import QMessageBox, QFileDialog, QLabel
from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QCloseEvent
import json
import logging
from pathlib import Path
from datetime import datetime

from src.core.tradingbot.cel.models import RulePack, Rule, RulePackMetadata
from .theme import STATUS_SUCCESS

logger = logging.getLogger(__name__)


class CelEditorWindowEventsMixin:
    """Mixin for CEL Editor window event handlers.

    This mixin provides all event handler methods for user interactions:
    - Signal connection setup
    - File operations (new, open, save, export)
    - RulePack editing
    - View mode switching
    - Pattern canvas interactions
    - AI code generation
    - Window lifecycle events

    Usage:
        class CelEditorWindow(CelEditorWindowEventsMixin, QMainWindow):
            def __init__(self):
                super().__init__()
                # ...
                self._connect_signals()
    """

    def _connect_signals(self):
        """Connect signals to slots."""
        # File actions
        self.action_new.triggered.connect(self._on_new_strategy)
        self.action_open.triggered.connect(self._on_open_strategy)
        self.action_save.triggered.connect(self._on_save_strategy)
        self.action_save_as.triggered.connect(self._on_save_as_strategy)
        self.action_open_rulepack.triggered.connect(self._on_open_rulepack)
        self.action_save_rulepack.triggered.connect(self._on_save_rulepack)
        self.action_save_rulepack_as.triggered.connect(self._on_save_rulepack_as)
        self.action_export_json.triggered.connect(self._on_export_json)
        self.action_close.triggered.connect(self.close)

        # Regime JSON actions
        self.action_open_regime.triggered.connect(self._on_open_regime)
        self.action_save_regime.triggered.connect(self._on_save_regime)
        self.regime_editor.config_modified.connect(self._on_regime_modified)
        self.regime_editor.config_saved.connect(self._on_regime_saved)

        # Edit actions
        self.action_undo.triggered.connect(self._on_undo)
        self.action_redo.triggered.connect(self._on_redo)
        self.action_clear.triggered.connect(self._on_clear_pattern)
        self.action_variables.triggered.connect(self._on_show_variables)

        # View actions
        self.action_view_pattern.triggered.connect(lambda: self._switch_view_mode("pattern"))
        self.action_view_code.triggered.connect(lambda: self._switch_view_mode("code"))
        self.action_view_chart.triggered.connect(lambda: self._switch_view_mode("chart"))
        self.action_view_split.triggered.connect(lambda: self._switch_view_mode("split"))

        # View mode Tabs
        self.central_tabs.currentChanged.connect(self._on_tab_changed)

        # Zoom actions
        self.action_zoom_in.triggered.connect(self._on_zoom_in)
        self.action_zoom_out.triggered.connect(self._on_zoom_out)
        self.action_zoom_fit.triggered.connect(self._on_zoom_fit)

        # Strategy Selector
        self.strategy_selector.currentIndexChanged.connect(self._on_strategy_selected)

        # Connect Code Editor changes to update status bar
        self.code_editor.strategy_changed.connect(self._on_code_strategy_changed)
        for workflow_type, editor in self.code_editor.cel_editors.items():
            editor.code_changed.connect(
                lambda code, wf=workflow_type: self._on_editor_code_changed(wf, code)
            )
            editor.ai_generation_requested.connect(self._on_ai_generation_requested)

        # Candle Toolbar signals (Phase 2.5)
        self.candle_toolbar.candle_add_requested.connect(self._on_toolbar_add_candle)
        self.candle_toolbar.candle_remove_requested.connect(self._on_toolbar_remove_candle)
        self.candle_toolbar.pattern_clear_requested.connect(self._on_clear_pattern)
        self.candle_toolbar.zoom_fit_requested.connect(self.pattern_canvas.zoom_to_fit_all)
        self.candle_toolbar.zoom_back_requested.connect(self.pattern_canvas.zoom_back_to_previous_view)

        # Properties Panel signals (Phase 2.6)
        # Panel → Canvas: Update candle when user applies changes
        self.properties_panel.values_changed.connect(self.pattern_canvas.update_candle_properties)

        # Canvas → Panel: Update panel when selection changes
        self.pattern_canvas.candle_selected.connect(self._on_candle_selected_for_properties)
        self.pattern_canvas.selection_cleared.connect(self._on_selection_cleared_for_properties)

        # Help actions
        self.action_help.triggered.connect(self._on_show_help)
        self.action_about.triggered.connect(self._on_show_about)

    def _on_strategy_selected(self, index: int):
        """Handle strategy selection change."""
        selection = self.strategy_selector.itemText(index)
        if "New Strategy" in selection:
            self._on_new_strategy()
        elif "Recent" not in selection:
            self.statusBar().showMessage(f"Loading {selection}...", 3000)
            # In a real app, this would load the JSON file
            self.strategy_name = selection.replace("📁 ", "").replace("📊 ", "")
            self.setWindowTitle(f"CEL Editor - {self.strategy_name}")

    def _on_code_strategy_changed(self, strategy_data: dict):
        """Update status bar when code strategy changes."""
        workflow = strategy_data.get("workflow", {})
        
        counts = {
            "entry": workflow.get("entry", {}).get("expression", "").count("&&") + 1 if workflow.get("entry", {}).get("expression", "") else 0,
            "exit": workflow.get("exit", {}).get("expression", "").count("&&") + 1 if workflow.get("exit", {}).get("expression", "") else 0,
            "risk": 0, # Placeholder
            "stop": workflow.get("update_stop", {}).get("expression", "").count("&&") + 1 if workflow.get("update_stop", {}).get("expression", "") else 0
        }
        
        self.rule_counts_label.setText(
            f"  {counts['entry']} Entry  |  {counts['exit']} Exit  |  {counts['risk']} Risk  |  {counts['stop']} Stop  "
        )

    def _on_editor_code_changed(self, workflow_type: str, code: str) -> None:
        """Update selected RulePack rule when editor changes."""
        if not self.rulepack_mode:
            return
        if self._rulepack_editor_loading:
            return
        if not self.current_rulepack or not self.selected_rule or not self.selected_pack_type:
            return

        pack_mapping = {
            "entry": "entry",
            "exit": "exit",
            "update_stop": "update_stop",
            "no_trade": "before_exit",
            "risk": "before_exit",
        }
        if pack_mapping.get(self.selected_pack_type) != workflow_type:
            return

        self.rulepack_panel.set_rule_expression(self.selected_pack_type, self.selected_rule.id, code)
        self.modified = True

    def _on_rulepack_rule_selected(self, pack_type: str, rule_id: str) -> None:
        """Load selected RulePack rule into editor."""
        if not self.current_rulepack:
            return
        rule = None
        pack = self.current_rulepack.get_pack(pack_type)
        if pack:
            for item in pack.rules:
                if item.id == rule_id:
                    rule = item
                    break
        if not rule:
            return

        self.selected_rule = rule
        self.selected_pack_type = pack_type

        pack_mapping = {
            "entry": "entry",
            "exit": "exit",
            "update_stop": "update_stop",
            "no_trade": "before_exit",
            "risk": "before_exit",
        }
        workflow_type = pack_mapping.get(pack_type, "entry")
        editor = self.code_editor.cel_editors.get(workflow_type)
        if not editor:
            return

        self._rulepack_editor_loading = True
        try:
            editor.set_code(rule.expression or "")
            for idx in range(self.code_editor.workflow_tabs.count()):
                tab_name = self.code_editor.workflow_tabs.tabText(idx).lower().replace(" ", "_")
                if tab_name == workflow_type:
                    self.code_editor.workflow_tabs.setCurrentIndex(idx)
                    break
        finally:
            self._rulepack_editor_loading = False

    def _on_rulepack_rule_updated(self, pack_type: str, rule_id: str) -> None:
        """Handle RulePack metadata updates."""
        self.modified = True
        self._update_rule_counts_from_rulepack()

    def _on_rulepack_rule_order_changed(self, pack_type: str) -> None:
        """Handle RulePack rule ordering updates."""
        self.modified = True

    def _on_ai_generation_requested(self, workflow_type: str) -> None:
        """Open AI assistant on Generate tab for the given workflow."""
        if hasattr(self, "ai_panel"):
            self.ai_panel.set_workflow(workflow_type)
            self.ai_panel.tabs.setCurrentIndex(0)

    def _on_ai_code_ready(self, workflow_type: str, code: str) -> None:
        """Insert AI generated code into the appropriate editor."""
        editor = self.code_editor.cel_editors.get(workflow_type)
        if not editor:
            return
        editor.set_code(code)

    def _on_ai_status_changed(self, status: str) -> None:
        """Update AI status label in status bar."""
        if hasattr(self, "ai_status_label"):
            self.ai_status_label.setText(f"🤖 {status}")

    def _on_functions_insert(self, name: str, code: str) -> None:
        """Insert code from Functions dock into active editor."""
        if not hasattr(self, "code_editor"):
            return
        current_index = self.code_editor.workflow_tabs.currentIndex()
        tab_name = self.code_editor.workflow_tabs.tabText(current_index).lower().replace(" ", "_")
        editor = self.code_editor.cel_editors.get(tab_name)
        if editor:
            editor.insert_text(code)

    def _on_new_strategy(self):
        """Create new strategy."""
        # Check for unsaved changes
        if self.modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Create new strategy anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Clear pattern canvas
        self.pattern_canvas.clear_pattern()

        # Clear all CEL editors
        for workflow, editor in self.code_editor.cel_editors.items():
            editor.set_code("")

        # Exit RulePack mode if active
        self.current_rulepack = None
        self.current_rulepack_file = None
        self._set_rulepack_mode(False)

        # Reset state
        self.current_file = None
        self.modified = False
        self.strategy_name = "Untitled Strategy"
        self.setWindowTitle(f"CEL Editor - {self.strategy_name}")

        self.statusBar().showMessage("New strategy created", 3000)

    def _on_open_strategy(self):
        """Open existing strategy from JSON file."""
        # Check for unsaved changes
        if self.modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Open strategy anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CEL Strategy",
            "03_JSON/Trading_Bot",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Load JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Validate version
            if data.get("version") != "1.0":
                QMessageBox.warning(
                    self, "Version Mismatch",
                    f"Strategy version {data.get('version')} may not be compatible."
                )

            # Load pattern data
            if "pattern" in data:
                self.pattern_canvas.load_pattern_data(data["pattern"])

            # Load workflow expressions
            workflows = data.get("workflows", {})
            for workflow_name, code in workflows.items():
                if workflow_name in self.code_editor.cel_editors:
                    self.code_editor.cel_editors[workflow_name].set_code(code)

            # Update state
            self.current_file = Path(file_path)
            self.modified = False
            self.strategy_name = data.get("name", self.current_file.stem)
            self.setWindowTitle(f"CEL Editor - {self.strategy_name}")
            self.current_rulepack = None
            self.current_rulepack_file = None
            self._set_rulepack_mode(False)

            self.statusBar().showMessage(
                f"Loaded strategy: {self.current_file.name}", 3000
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Load Error",
                f"Failed to load strategy:\n{str(e)}"
            )

    def _on_save_strategy(self):
        """Save current strategy to file."""
        if self.current_file:
            self._save_to_file(self.current_file)
        else:
            self._on_save_as_strategy()

    def _on_save_as_strategy(self):
        """Save strategy with new file name."""
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CEL Strategy",
            f"03_JSON/Trading_Bot/{self.strategy_name}.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        # Ensure .json extension
        file_path = Path(file_path)
        if file_path.suffix != ".json":
            file_path = file_path.with_suffix(".json")

        self._save_to_file(file_path)

    def _on_export_json(self):
        """Export strategy as JSON RulePack for trading bot."""
        # Show file dialog
        export_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CEL RulePack",
            f"03_JSON/Trading_Bot/{self.strategy_name}_rulepack.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if not export_path:
            return

        try:
            # Build RulePack format (only workflows, no pattern)
            workflows = {}
            for workflow_name, editor in self.code_editor.cel_editors.items():
                code = editor.get_code().strip()
                if code:  # Only include non-empty workflows
                    workflows[workflow_name] = code

            rulepack_data = {
                "version": "1.0",
                "name": self.strategy_name,
                "type": "cel_rulepack",
                "workflows": workflows,
                "metadata": {
                    "exported": datetime.now().isoformat(),
                    "source": "cel_editor"
                }
            }

            # Save to file
            export_path = Path(export_path)
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(rulepack_data, f, indent=2, ensure_ascii=False)

            self.statusBar().showMessage(
                f"Exported RulePack: {export_path.name}", 3000
            )

            QMessageBox.information(
                self, "Export Successful",
                f"RulePack exported to:\n{export_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Export Error",
                f"Failed to export RulePack:\n{str(e)}"
            )

    def _on_open_rulepack(self):
        """Open CEL RulePack JSON file."""
        # Check for unsaved changes
        if self.modified:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Open RulePack anyway?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                return

        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open CEL RulePack",
            "03_JSON/Trading_Bot",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        try:
            # Load JSON
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Detect file type
            if "rules_version" in data:
                # RulePack format
                self._load_rulepack(data, Path(file_path))
            elif "version" in data and "pattern" in data:
                # Strategy format - offer to convert
                reply = QMessageBox.question(
                    self, "Strategy File Detected",
                    "This appears to be a Strategy file, not a RulePack.\n\n"
                    "Do you want to open it as a Strategy instead?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self._on_open_strategy()  # Recursively call strategy loader
                return
            else:
                QMessageBox.warning(
                    self, "Unknown Format",
                    "File format not recognized.\n\n"
                    "Expected 'rules_version' field for RulePack or 'pattern' field for Strategy."
                )
                return

        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self, "JSON Error",
                f"Failed to parse JSON file:\n{str(e)}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Load Error",
                f"Failed to load RulePack:\n{str(e)}"
            )

    def _on_save_rulepack(self):
        """Save current RulePack to file."""
        if self.current_rulepack_file:
            self._save_rulepack_to_file(self.current_rulepack_file)
        else:
            self._on_save_rulepack_as()

    def _on_save_rulepack_as(self):
        """Save RulePack with new file name."""
        # Show file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save CEL RulePack",
            f"03_JSON/Trading_Bot/{self.strategy_name}_rulepack.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if not file_path:
            return

        # Ensure .json extension
        file_path = Path(file_path)
        if file_path.suffix != ".json":
            file_path = file_path.with_suffix(".json")

        self._save_rulepack_to_file(file_path)

    def _on_open_regime(self):
        """Open any JSON file in JSON Editor tab."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",
            "",  # Start from current directory
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            # Load into Regime Editor
            self.regime_editor.load_config(file_path)

            # Switch to Regime Editor tab
            regime_tab_index = self.central_tabs.indexOf(self.regime_editor)
            self.central_tabs.setCurrentIndex(regime_tab_index)

            # Enable save action
            self.action_save_regime.setEnabled(True)

            self.statusBar().showMessage(f"Loaded Regime: {Path(file_path).name}", 3000)

    def _on_save_regime(self):
        """Save current Regime JSON."""
        if self.regime_editor.current_file_path:
            self.regime_editor._on_save_file()
        else:
            self.regime_editor._on_save_file_as()

    def _on_regime_modified(self):
        """Handle Regime config modification."""
        self.action_save_regime.setEnabled(True)
        self.modified = True

    def _on_regime_saved(self, file_path: str):
        """Handle Regime config saved."""
        self.statusBar().showMessage(f"Saved Regime: {Path(file_path).name}", 3000)

    def _on_undo(self):
        """Undo last action."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.undo()
            undo_text = self.pattern_canvas.undo_stack.undoText()
            self.statusBar().showMessage(f"Undo: {undo_text}" if undo_text else "Undo", 2000)

    def _on_redo(self):
        """Redo last undone action."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.redo()
            redo_text = self.pattern_canvas.undo_stack.redoText()
            self.statusBar().showMessage(f"Redo: {redo_text}" if redo_text else "Redo", 2000)

    def _on_clear_pattern(self):
        """Clear all candles from pattern."""
        if hasattr(self, 'pattern_canvas'):
            # Show confirmation dialog
            reply = QMessageBox.question(
                self,
                "Clear Pattern",
                "Are you sure you want to clear all candles?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.pattern_canvas.clear_pattern()
                self.statusBar().showMessage("Pattern cleared", 2000)

    def _switch_view_mode(self, mode: str):
        """Switch between view modes via TabWidget."""
        self.current_view_mode = mode

        # Update menu checkboxes
        self.action_view_pattern.setChecked(mode == "pattern")
        self.action_view_code.setChecked(mode == "code")
        self.action_view_chart.setChecked(mode == "chart")
        self.action_view_split.setChecked(mode == "split")

        # Sync tab widget
        mode_index = {"pattern": 0, "code": 1, "chart": 2, "split": 3}
        self.central_tabs.blockSignals(True)
        self.central_tabs.setCurrentIndex(mode_index.get(mode, 0))
        self.central_tabs.blockSignals(False)

        # Emit signal
        self.view_mode_changed.emit(mode)

        # Update status
        self.statusBar().showMessage(f"Switched to {mode} view", 2000)

        # Show/hide sidebars based on mode
        is_pattern = mode in ["pattern", "split"]
        self.left_dock.setVisible(is_pattern)
        self.right_dock.setVisible(is_pattern)
        self.candle_toolbar.setVisible(is_pattern)

    def _on_tab_changed(self, index: int):
        """Handle view mode tab change."""
        modes = ["pattern", "code", "chart", "split"]
        if 0 <= index < len(modes):
            self._switch_view_mode(modes[index])

    def _on_view_mode_combo_changed(self, index: int):
        """Legacy handler for combo box (kept for compatibility during refactoring)."""
        pass

    def _on_zoom_in(self):
        """Zoom in on canvas."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.zoom_in()
            self.statusBar().showMessage("Zoomed in", 1000)

    def _on_zoom_out(self):
        """Zoom out on canvas."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.zoom_out()
            self.statusBar().showMessage("Zoomed out", 1000)

    def _on_zoom_fit(self):
        """Zoom to fit all candles."""
        if hasattr(self, 'pattern_canvas'):
            self.pattern_canvas.zoom_fit()
            self.statusBar().showMessage("Zoomed to fit", 1000)

    def _on_toolbar_add_candle(self, candle_type: str):
        """Handle add candle request from toolbar.

        Args:
            candle_type: Type of candle to add (bullish, bearish, doji, etc.)
        """
        if hasattr(self, 'pattern_canvas'):
            # Add candle at auto-positioned coordinates (canvas handles positioning)
            candle = self.pattern_canvas.add_candle(candle_type)

            # Update status bar
            self.statusBar().showMessage(
                f"Added {candle_type.replace('_', ' ').title()} candle",
                2000
            )

    def _on_toolbar_remove_candle(self):
        """Handle remove candle request from toolbar."""
        if hasattr(self, 'pattern_canvas'):
            # Remove selected candles
            self.pattern_canvas.remove_selected_candles()

            # Update status bar
            self.statusBar().showMessage("Removed selected candle(s)", 2000)

    def _on_ai_generate(self):
        """Generate CEL code from pattern."""
        # Get pattern data from canvas
        pattern_data = self.pattern_canvas.get_pattern_data()

        # Validate pattern
        is_valid, error_msg = self.translator.validate_pattern(pattern_data)
        if not is_valid:
            QMessageBox.warning(
                self, "Invalid Pattern",
                f"Cannot generate CEL code:\n{error_msg}"
            )
            return

        # Check if pattern has content
        if not pattern_data.get("candles"):
            QMessageBox.information(
                self, "Empty Pattern",
                "Please draw some candles in the Pattern Builder first."
            )
            return

        # Ask user which workflow to target
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QRadioButton, QDialogButtonBox

        dialog = QDialog(self)
        dialog.setWindowTitle("Select Target Workflow")
        layout = QVBoxLayout(dialog)

        layout.addWidget(QLabel("Where should the generated CEL code be inserted?"))

        # Radio buttons for workflow selection
        entry_radio = QRadioButton("Entry Workflow")
        entry_radio.setChecked(True)
        exit_radio = QRadioButton("Exit Workflow")
        before_exit_radio = QRadioButton("Before Exit Workflow")
        update_stop_radio = QRadioButton("Update Stop Workflow")

        layout.addWidget(entry_radio)
        layout.addWidget(exit_radio)
        layout.addWidget(before_exit_radio)
        layout.addWidget(update_stop_radio)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        # Determine selected workflow
        if entry_radio.isChecked():
            workflow = "entry"
            cel_code = self.translator.generate_entry_workflow(pattern_data)
        elif exit_radio.isChecked():
            workflow = "exit"
            cel_code = self.translator.generate_exit_workflow(pattern_data)
        else:
            workflow = "entry" if entry_radio.isChecked() else "exit"
            cel_code = self.translator.generate_with_comments(pattern_data)

        # Switch to code view
        self._switch_view_mode("code")

        # Insert generated code into selected workflow editor
        if workflow in self.code_editor.cel_editors:
            editor = self.code_editor.cel_editors[workflow]

            # Ask if user wants to replace or append
            if editor.get_code().strip():
                reply = QMessageBox.question(
                    self, "Replace or Append?",
                    f"The {workflow.title()} workflow already has code.\n\n"
                    "Replace existing code or append to it?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )

                if reply == QMessageBox.StandardButton.Yes:
                    # Replace
                    editor.set_code(cel_code)
                else:
                    # Append
                    existing = editor.get_code().strip()
                    combined = f"{existing}\n\n// Generated from pattern:\n{cel_code}"
                    editor.set_code(combined)
            else:
                # Editor is empty, just set
                editor.set_code(cel_code)

            # Show success message
            self.statusBar().showMessage(
                f"✅ Generated CEL code for {workflow} workflow from pattern",
                5000
            )

            # Show info dialog
            QMessageBox.information(
                self, "✅ CEL Code Generated",
                f"Successfully generated CEL code from pattern!\n\n"
                f"Target: {workflow.title()} Workflow\n"
                f"Candles: {pattern_data['metadata']['candle_count']}\n"
                f"Relations: {pattern_data['metadata']['relation_count']}\n\n"
                f"The code has been inserted into the {workflow} editor."
            )

    def _on_pattern_changed(self):
        """Handle pattern changes from canvas."""
        # Update validation status
        if hasattr(self, 'pattern_canvas'):
            stats = self.pattern_canvas.get_statistics()
            candle_count = stats['total_candles']
            relation_count = stats['total_relations']

            if candle_count == 0:
                self.validation_label.setText("✓ Ready")
                self.validation_label.setStyleSheet(f"color: {STATUS_SUCCESS}; font-family: 'Consolas', monospace;")
            elif candle_count < 2:
                self.validation_label.setText("⚠️ Need at least 2 candles")
                self.validation_label.setStyleSheet("color: #ffa726; font-family: 'Consolas', monospace;")
            else:
                self.validation_label.setText(f"✓ {candle_count} candles, {relation_count} relations")
                self.validation_label.setStyleSheet(f"color: {STATUS_SUCCESS}; font-family: 'Consolas', monospace;")

        # Emit main window signal
        self.pattern_changed.emit()

    def _on_candle_selected(self, candle_data: dict):
        """Handle candle selection from canvas.

        Args:
            candle_data: Dict with candle properties (type, index, ohlc, position)
        """
        # TODO: Update properties panel in Phase 2.6
        candle_type = candle_data.get('type', 'unknown')
        index = candle_data.get('index', 0)
        self.statusBar().showMessage(
            f"Selected: {candle_type.replace('_', ' ').title()} [index {index}]",
            2000
        )

    def _on_selection_cleared(self):
        """Handle selection cleared from canvas."""
        # TODO: Clear properties panel in Phase 2.6
        self.statusBar().showMessage("Selection cleared", 1000)

    def _on_candle_selected_for_properties(self, candle_data: dict):
        """Update properties panel when candle is selected.

        Args:
            candle_data: Dict with candle properties (from canvas signal)
        """
        # Get selected candles from canvas
        selected_candles = self.pattern_canvas.get_selected_candles()

        # Update properties panel
        self.properties_panel.on_canvas_selection_changed(selected_candles)

    def _on_selection_cleared_for_properties(self):
        """Clear properties panel when selection is cleared."""
        # Clear properties panel
        self.properties_panel.on_canvas_selection_changed([])

    def _on_library_pattern_selected(self, pattern_data: dict):
        """Load pattern from library to canvas.

        Args:
            pattern_data: Pattern data dict from library
        """
        try:
            # Load pattern to canvas
            self.pattern_canvas.load_pattern_data(pattern_data)

            # Switch to pattern builder view
            self._switch_view_mode("pattern")

            # Show success message with pattern info
            metadata = pattern_data.get("metadata", {})
            candle_count = metadata.get("candle_count", len(pattern_data.get("candles", [])))
            relation_count = metadata.get("relation_count", len(pattern_data.get("relations", [])))
            description = metadata.get("description", "")

            message = f"✅ Pattern loaded successfully!\n\n"
            message += f"Candles: {candle_count}\n"
            message += f"Relations: {relation_count}\n"
            if description:
                message += f"\n{description}"

            self.statusBar().showMessage(f"Pattern loaded: {candle_count} candles", 3000)

            QMessageBox.information(
                self,
                "✅ Pattern Loaded",
                message
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load pattern from library:\n{str(e)}"
            )

    def _on_show_variables(self):
        """Open Variables Reference Dialog (Variable System Integration)."""
        try:
            from ...dialogs.variables.variable_reference_dialog import VariableReferenceDialog

            # Initialize data sources
            chart_window = None
            bot_config = None
            project_vars_path = None
            indicators = None
            regime = None

            # Strategy 1: Search parent hierarchy for ChartWindow
            parent = self.parent()
            while parent:
                if parent.__class__.__name__ == "ChartWindow":
                    chart_window = parent

                    # Extract additional data from ChartWindow
                    if hasattr(parent, '_get_bot_config'):
                        try:
                            bot_config = parent._get_bot_config()
                        except Exception as e:
                            logger.debug(f"Could not get bot_config: {e}")

                    if hasattr(parent, '_get_project_vars_path'):
                        try:
                            project_vars_path = parent._get_project_vars_path()
                        except Exception as e:
                            logger.debug(f"Could not get project_vars_path: {e}")

                    if hasattr(parent, '_get_current_indicators'):
                        try:
                            indicators = parent._get_current_indicators()
                        except Exception as e:
                            logger.debug(f"Could not get indicators: {e}")

                    if hasattr(parent, '_get_current_regime'):
                        try:
                            regime = parent._get_current_regime()
                        except Exception as e:
                            logger.debug(f"Could not get regime: {e}")

                    break

                parent = parent.parent() if hasattr(parent, 'parent') else None

            # Strategy 2: Fallback - Search for .cel_variables.json in common locations
            if not project_vars_path:
                search_paths = [
                    Path.cwd() / ".cel_variables.json",
                    Path(__file__).parent.parent.parent.parent.parent / ".cel_variables.json",
                    Path.home() / ".orderpilot" / ".cel_variables.json",
                ]

                for path in search_paths:
                    if path.exists():
                        project_vars_path = str(path)
                        logger.info(f"Found project variables at: {project_vars_path}")
                        break

            # Validation: Check if we have ANY real data sources
            # NO DEMO CONTENT ALLOWED - show error if no real values available
            if not chart_window and not project_vars_path:
                logger.warning("No real data sources available for Variable Reference Dialog")
                QMessageBox.critical(
                    self,
                    "Keine Datenquellen verfügbar",
                    "Es sind keine realen Variablenwerte verfügbar.\n\n"
                    "Bitte öffnen Sie ein Chart-Fenster mit aktivem Trading oder erstellen Sie eine .cel_variables.json Datei im Projekt-Root.\n\n"
                    "Pfad: .cel_variables.json"
                )
                return

            # Log what we found
            logger.info(f"Opening Variable Reference Dialog with real data sources:")
            logger.info(f"  chart_window: {chart_window is not None}")
            logger.info(f"  bot_config: {bot_config is not None}")
            logger.info(f"  project_vars_path: {project_vars_path}")
            logger.info(f"  indicators: {indicators is not None}")
            logger.info(f"  regime: {regime is not None}")

            # Create and show dialog with available real sources ONLY
            dialog = VariableReferenceDialog(
                chart_window=chart_window,
                bot_config=bot_config,
                project_vars_path=project_vars_path,
                indicators=indicators,
                regime=regime,
                enable_live_updates=False,  # Disable live updates in CEL Editor context
                parent=self
            )
            dialog.exec()

        except Exception as e:
            logger.error(f"Failed to open Variables Reference Dialog: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Variables Error",
                f"Failed to open Variables Reference Dialog:\n{str(e)}"
            )

    def _on_show_help(self):
        """Open CEL Editor help in browser."""
        import webbrowser
        from pathlib import Path

        # Get help file path
        help_file = Path(__file__).parent.parent.parent.parent / "help" / "cel_editor_help.html"

        if help_file.exists():
            # Open in default browser
            webbrowser.open(help_file.as_uri())
        else:
            # Fallback: Show message box with basic info
            QMessageBox.information(
                self,
                "Help",
                "Help file not found at:\n" + str(help_file) + "\n\n"
                "✅ COMPLETED FEATURES (8/20 = 40%)\n\n"
                "See docs/CEL_EDITOR_HELP.md for full documentation."
            )

    def _on_show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About CEL Editor",
            "CEL Editor - Visual Pattern Builder\n\n"
            "Version: 1.0.0 (Production Ready)\n"
            "Build Date: 2026-01-21\n"
            "Part of OrderPilot-AI Trading Platform\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "📊 Features: 8/20 Complete (40%)\n"
            "📝 Lines of Code: 4,125 LOC\n"
            "🎨 Pattern Templates: 11\n"
            "💻 CEL Functions: 200+\n"
            "🤖 AI Models: 3 (OpenAI, Anthropic, Gemini)\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            "A professional visual pattern builder for creating\n"
            "CEL (Common Expression Language) trading strategies.\n\n"
            "Built with PyQt6, QScintilla, and AI assistance.\n\n"
            "© 2026 OrderPilot-AI\n"
            "Session: 2026-01-21 | Status: ✅ Production Ready"
        )

    def closeEvent(self, event):
        """Handle window close event."""
        # Save window state
        self._save_state()

        # TODO: Check for unsaved changes in later phases

        # Issue #27: Emit closed signal for button state sync
        self.closed.emit()

        event.accept()
