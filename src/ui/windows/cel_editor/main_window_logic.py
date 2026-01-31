"""CEL Editor Window - Business Logic Mixin.

This module contains business logic methods for the CEL Editor main window.
Extracted from monolithic main_window.py (1798 LOC) as part of Phase 3 refactoring.

Responsibilities:
- File I/O operations (_save_to_file, _load_rulepack, _save_rulepack_to_file)
- Window state persistence (_restore_state, _save_state)
- RulePack mode management (_set_rulepack_mode)
- Rule count updates (_update_rule_counts_from_rulepack)
- Editor clearing (_clear_all_editors)

Author: CODER-009 (Claude Sonnet 4.5)
Date: 2026-01-31
Task: 3.1.1 - Split cel_editor/main_window.py
"""

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QMessageBox, QFileDialog
import json
import logging
from pathlib import Path
from datetime import datetime

from src.core.tradingbot.cel.models import RulePack, Rule, RulePackMetadata

logger = logging.getLogger(__name__)


class CelEditorWindowLogicMixin:
    """Mixin for CEL Editor window business logic.

    This mixin provides methods for:
    - Saving/loading strategy files (JSON format)
    - RulePack file operations
    - Window state persistence (QSettings)
    - RulePack mode state management
    - Rule counting and status updates

    Usage:
        class CelEditorWindow(CelEditorWindowLogicMixin, QMainWindow):
            def __init__(self):
                super().__init__()
                self._restore_state()
    """

    def _restore_state(self):
        """Restore window state from QSettings."""
        settings = QSettings("OrderPilot-AI", "CELEditor")

        # Restore geometry
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        # Restore dock state
        state = settings.value("windowState")
        if state:
            self.restoreState(state)


    def _save_state(self):
        """Save window state to QSettings."""
        settings = QSettings("OrderPilot-AI", "CELEditor")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    # Placeholder methods (will be implemented in later phases)


    def _set_rulepack_mode(self, enabled: bool) -> None:
        """Switch UI between Strategy and RulePack editing."""
        self.rulepack_mode = enabled
        if enabled:
            self.left_dock.setWindowTitle("RulePack Editor")
            self.left_tabs.setTabEnabled(1, True)
            self.left_tabs.setCurrentWidget(self.rulepack_panel)
            self.action_save_rulepack.setEnabled(True)
            self.action_save_rulepack_as.setEnabled(True)
        else:
            self.left_dock.setWindowTitle("Pattern Library & Templates")
            self.left_tabs.setCurrentWidget(self.pattern_library)
            self.left_tabs.setTabEnabled(1, False)
            self.action_save_rulepack.setEnabled(False)
            self.action_save_rulepack_as.setEnabled(False)
            self.selected_rule = None
            self.selected_pack_type = None


    def _update_rule_counts_from_rulepack(self) -> None:
        """Update status bar rule counts based on RulePack."""
        if not self.current_rulepack:
            return
        counts = {"entry": 0, "exit": 0, "risk": 0, "stop": 0}
        for pack in self.current_rulepack.packs:
            enabled_count = len([r for r in pack.rules if r.enabled])
            if pack.pack_type == "entry":
                counts["entry"] += enabled_count
            elif pack.pack_type == "exit":
                counts["exit"] += enabled_count
            elif pack.pack_type == "update_stop":
                counts["stop"] += enabled_count
            elif pack.pack_type in ("risk", "no_trade"):
                counts["risk"] += enabled_count

        self.rule_counts_label.setText(
            f"  {counts['entry']} Entry  |  {counts['exit']} Exit  |  {counts['risk']} Risk  |  {counts['stop']} Stop  "
        )


    def _clear_all_editors(self):
        """Clear all workflow editors."""
        for editor in self.code_editor.cel_editors.values():
            editor.set_code("")


    def _save_to_file(self, file_path: Path):
        """Internal method to save strategy to specific file.

        Args:
            file_path: Path to save file
        """
        try:
            # Collect pattern data
            pattern_data = self.pattern_canvas.get_pattern_data()

            # Collect workflow expressions
            workflows = {}
            for workflow_name, editor in self.code_editor.cel_editors.items():
                workflows[workflow_name] = editor.get_code()

            # Build complete strategy JSON
            strategy_data = {
                "version": "1.0",
                "name": self.strategy_name,
                "pattern": pattern_data,
                "workflows": workflows,
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "modified": datetime.now().isoformat()
                }
            }

            # Save to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(strategy_data, f, indent=2, ensure_ascii=False)

            # Update state
            self.current_file = file_path
            self.modified = False
            self.strategy_name = file_path.stem
            self.setWindowTitle(f"CEL Editor - {self.strategy_name}")

            self.statusBar().showMessage(
                f"Saved strategy: {file_path.name}", 3000
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save strategy:\n{str(e)}"
            )


    def _load_rulepack(self, data: dict, file_path: Path):
        """Internal method to load RulePack data.

        Args:
            data: RulePack JSON data
            file_path: Path to RulePack file
        """
        try:
            # Parse with Pydantic
            rulepack = RulePack(**data)

            # Clear current state
            self._clear_all_editors()

            # Load RulePack into RulePack panel
            self.rulepack_panel.load_rulepack(rulepack)

            # Update state
            self.current_rulepack = rulepack
            self.current_rulepack_file = file_path
            self._set_rulepack_mode(True)
            self.modified = False
            self.strategy_name = rulepack.metadata.name if rulepack.metadata and rulepack.metadata.name else file_path.stem
            self.setWindowTitle(f"CEL Editor - RulePack: {self.strategy_name}")

            # Switch to code view
            self._switch_view_mode("code")

            self._update_rule_counts_from_rulepack()

            self.statusBar().showMessage(
                f"Loaded RulePack: {file_path.name}", 5000
            )

            QMessageBox.information(
                self, "RulePack Loaded",
                f"Loaded {len(rulepack.packs)} pack(s) from {file_path.name}.\n\n"
                f"Select rules in the RulePack panel to edit."
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Parse Error",
                f"Failed to parse RulePack:\n{str(e)}\n\n"
                f"Ensure the file matches the RulePack schema."
            )


    def _save_rulepack_to_file(self, file_path: Path):
        """Internal method to save RulePack to specific file.

        Args:
            file_path: Path to save file
        """
        if not self.current_rulepack:
            QMessageBox.warning(
                self, "No RulePack",
                "No RulePack loaded. Please open a RulePack first."
            )
            return

        try:
            # Update metadata
            if self.current_rulepack.metadata:
                self.current_rulepack.metadata.updated_at = datetime.now()
            else:
                self.current_rulepack.metadata = RulePackMetadata(
                    name=self.strategy_name,
                    updated_at=datetime.now()
                )

            # Convert to dict and save
            rulepack_dict = self.current_rulepack.model_dump(mode='json')

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(rulepack_dict, f, indent=2, ensure_ascii=False)

            # Update state
            self.current_rulepack_file = file_path
            self.modified = False
            self.strategy_name = file_path.stem
            self.setWindowTitle(f"CEL Editor - RulePack: {self.strategy_name}")

            self.statusBar().showMessage(
                f"Saved RulePack: {file_path.name}", 3000
            )

            QMessageBox.information(
                self, "Save Successful",
                f"RulePack saved to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self, "Save Error",
                f"Failed to save RulePack:\n{str(e)}"
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Regime JSON Methods (Entry Analyzer format)
    # ─────────────────────────────────────────────────────────────────────────

