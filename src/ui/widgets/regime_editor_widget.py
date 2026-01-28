"""Generic JSON Editor Widget - Edit any JSON file in CEL Editor.

Provides flexible UI for viewing and editing ANY JSON file:
- Dynamic tree structure
- In-place value editing
- Array and object support
- Add/Remove items
- Schema validation (optional)

NOT hardcoded for a specific format!
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QSplitter, QLineEdit, QDoubleSpinBox, QSpinBox,
    QComboBox, QGroupBox, QFormLayout, QScrollArea, QFrame, QMessageBox,
    QHeaderView, QFileDialog, QCheckBox, QTextEdit, QMenu, QTabWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QAction

logger = logging.getLogger(__name__)


class JsonTreeItem(QTreeWidgetItem):
    """Tree item with JSON data tracking."""

    def __init__(self, key: str, value: Any, parent=None, json_path: list = None):
        super().__init__(parent)
        self.key = key
        self.value = value
        self.json_path = json_path or []
        self.value_type = type(value).__name__

        self._update_display()

    def _update_display(self):
        """Update display text based on value type."""
        self.setText(0, str(self.key))

        if isinstance(self.value, dict):
            self.setText(1, f"{{...}} ({len(self.value)} items)")
        elif isinstance(self.value, list):
            self.setText(1, f"[...] ({len(self.value)} items)")
        elif isinstance(self.value, bool):
            self.setText(1, "true" if self.value else "false")
        elif self.value is None:
            self.setText(1, "null")
        else:
            self.setText(1, str(self.value))


class RegimeEditorWidget(QWidget):
    """Generic JSON Editor Widget.

    Can edit ANY JSON file - not hardcoded for specific formats.
    Displays JSON as an editable tree with in-place value editing.

    Signals:
        config_modified: Emitted when JSON is modified
        config_saved: Emitted after successful save (file_path)
    """

    config_modified = pyqtSignal()
    config_saved = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_config: dict[str, Any] | None = None
        self.current_file_path: Path | None = None
        self.is_modified = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the widget layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Tabs: JSON Editor | AI Editor
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        layout.addWidget(self.tabs, 1)

        # JSON Editor tab (existing UI)
        json_tab = self._create_json_tab()
        self.tabs.addTab(json_tab, "JSON Editor")

        # AI Editor tab (Entry/Exit/Before Exit/Update Stop)
        ai_tab = self._create_ai_tab()
        self.tabs.addTab(ai_tab, "AI Editor")

    def _create_json_tab(self) -> QWidget:
        """Create JSON Editor tab content."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # Header with file info and actions
        header = self._create_header()
        layout.addWidget(header)

        # Main splitter: Left (tree) | Right (editor)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Tree view of JSON structure
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)

        self.tree = self._create_tree_view()
        tree_layout.addWidget(self.tree)

        # Tree actions
        tree_actions = QHBoxLayout()
        self.btn_add = QPushButton("+")
        self.btn_add.setToolTip("Add item to selected node")
        self.btn_add.setMaximumWidth(30)
        self.btn_remove = QPushButton("-")
        self.btn_remove.setToolTip("Remove selected item")
        self.btn_remove.setMaximumWidth(30)
        self.btn_expand = QPushButton("Expand All")
        self.btn_collapse = QPushButton("Collapse All")
        tree_actions.addWidget(self.btn_add)
        tree_actions.addWidget(self.btn_remove)
        tree_actions.addStretch()
        tree_actions.addWidget(self.btn_expand)
        tree_actions.addWidget(self.btn_collapse)
        tree_layout.addLayout(tree_actions)

        splitter.addWidget(tree_container)

        # Right: Value editor panel
        editor_scroll = QScrollArea()
        editor_scroll.setWidgetResizable(True)
        editor_scroll.setFrameStyle(QFrame.Shape.NoFrame)

        self.editor_panel = self._create_editor_panel()
        editor_scroll.setWidget(self.editor_panel)
        splitter.addWidget(editor_scroll)

        splitter.setSizes([350, 450])
        layout.addWidget(splitter, 1)

        # Status bar
        self.status_label = QLabel("No JSON file loaded - open any JSON file to edit")
        self.status_label.setStyleSheet("color: #848E9C; font-size: 11px;")
        layout.addWidget(self.status_label)

        return tab

    def _create_ai_tab(self) -> QWidget:
        """Create AI Editor tab content for strategy editing."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        from src.ui.widgets.cel_strategy_editor_widget import CelStrategyEditorWidget
        from src.ui.widgets.cel_ai_assistant_panel import CelAIAssistantPanel

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Strategy editor (Entry/Exit/Before Exit/Update Stop)
        self.ai_strategy_editor = CelStrategyEditorWidget(self)
        splitter.addWidget(self.ai_strategy_editor)

        # AI assistant panel
        self.ai_assistant_panel = CelAIAssistantPanel(self)
        self.ai_assistant_panel.code_ready.connect(self._on_ai_tab_code_ready)
        splitter.addWidget(self.ai_assistant_panel)

        splitter.setSizes([650, 350])
        layout.addWidget(splitter, 1)

        # Sync workflow selection with AI panel
        self.ai_strategy_editor.workflow_tabs.currentChanged.connect(
            self._on_ai_tab_workflow_changed
        )

        return tab

    def _create_header(self) -> QWidget:
        """Create header with file info and action buttons."""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        # File info label
        self.file_label = QLabel("No file loaded")
        self.file_label.setStyleSheet("color: #E0E0E0; font-weight: bold;")
        layout.addWidget(self.file_label)

        layout.addStretch()

        # Action buttons
        self.btn_open = QPushButton("Open JSON...")
        self.btn_open.setToolTip("Open any JSON file")
        layout.addWidget(self.btn_open)

        self.btn_save = QPushButton("Save")
        self.btn_save.setToolTip("Save changes")
        self.btn_save.setEnabled(False)
        layout.addWidget(self.btn_save)

        self.btn_save_as = QPushButton("Save As...")
        self.btn_save_as.setToolTip("Save to a new file")
        self.btn_save_as.setEnabled(False)
        layout.addWidget(self.btn_save_as)

        self.btn_reload = QPushButton("Reload")
        self.btn_reload.setToolTip("Reload from file (discard changes)")
        self.btn_reload.setEnabled(False)
        layout.addWidget(self.btn_reload)

        return header

    def _create_tree_view(self) -> QTreeWidget:
        """Create tree view for JSON structure."""
        tree = QTreeWidget()
        tree.setHeaderLabels(["Key", "Value"])
        tree.setColumnCount(2)
        tree.setAlternatingRowColors(True)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._show_tree_context_menu)
        tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1E1E1E;
                border: 1px solid #32363E;
                font-family: 'Consolas', monospace;
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px;
            }
            QTreeWidget::item:selected {
                background-color: #3A3A3A;
            }
        """)

        header = tree.header()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        tree.setColumnWidth(0, 180)

        return tree

    def _create_editor_panel(self) -> QWidget:
        """Create value editor panel."""
        panel = QWidget()
        self.editor_layout = QVBoxLayout(panel)
        self.editor_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Placeholder
        placeholder = QLabel("Select an item in the tree to edit its value")
        placeholder.setStyleSheet("color: #848E9C; font-size: 13px;")
        placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.editor_layout.addWidget(placeholder)

        return panel

    def _connect_signals(self):
        """Connect widget signals."""
        self.btn_open.clicked.connect(self._on_open_file)
        self.btn_save.clicked.connect(self._on_save_file)
        self.btn_save_as.clicked.connect(self._on_save_file_as)
        self.btn_reload.clicked.connect(self._on_reload_file)
        self.btn_add.clicked.connect(self._on_add_item)
        self.btn_remove.clicked.connect(self._on_remove_item)
        self.btn_expand.clicked.connect(self.tree.expandAll)
        self.btn_collapse.clicked.connect(self.tree.collapseAll)
        self.tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_ai_tab_code_ready(self, workflow_type: str, code: str) -> None:
        """Insert AI generated code into AI Editor workflow."""
        if not hasattr(self, "ai_strategy_editor"):
            return
        editor = self.ai_strategy_editor.cel_editors.get(workflow_type)
        if editor:
            editor.set_code(code)

    def _on_ai_tab_workflow_changed(self, index: int) -> None:
        """Sync AI panel workflow with selected tab."""
        if not hasattr(self, "ai_strategy_editor") or not hasattr(self, "ai_assistant_panel"):
            return
        tab_name = self.ai_strategy_editor.workflow_tabs.tabText(index).lower().replace(" ", "_")
        self.ai_assistant_panel.set_workflow(tab_name)

    def _on_open_file(self):
        """Open file dialog to select any JSON file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open JSON File",
            "",  # Start from current directory
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.load_config(file_path)

    def load_config(self, file_path: str | Path):
        """Load any JSON file and populate tree.

        Args:
            file_path: Path to JSON file
        """
        file_path = Path(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                self.current_config = json.load(f)

            self.current_file_path = file_path
            self.is_modified = False

            # Update UI
            self.file_label.setText(f"File: {file_path.name}")
            self.btn_save.setEnabled(True)
            self.btn_save_as.setEnabled(True)
            self.btn_reload.setEnabled(True)

            # Populate tree
            self._populate_tree()

            # Update status
            self._update_status()

            logger.info(f"Loaded JSON: {file_path}")

        except json.JSONDecodeError as e:
            QMessageBox.critical(
                self,
                "JSON Parse Error",
                f"Failed to parse JSON file:\n{str(e)}"
            )
            logger.error(f"JSON parse error: {e}")
        except Exception as e:
            QMessageBox.critical(
                self,
                "Load Error",
                f"Failed to load file:\n{str(e)}"
            )
            logger.error(f"Failed to load JSON: {e}")

    def _populate_tree(self):
        """Populate tree with JSON data."""
        self.tree.clear()

        if not self.current_config:
            return

        self._add_json_to_tree(self.current_config, None, [])
        self.tree.expandToDepth(1)

    def _add_json_to_tree(self, data: Any, parent: QTreeWidgetItem | None, path: list):
        """Recursively add JSON data to tree."""
        if isinstance(data, dict):
            for key, value in data.items():
                item = JsonTreeItem(key, value, parent, path + [key])
                if parent:
                    parent.addChild(item)
                else:
                    self.tree.addTopLevelItem(item)

                if isinstance(value, (dict, list)):
                    self._add_json_to_tree(value, item, path + [key])

        elif isinstance(data, list):
            for idx, value in enumerate(data):
                item = JsonTreeItem(f"[{idx}]", value, parent, path + [idx])
                if parent:
                    parent.addChild(item)
                else:
                    self.tree.addTopLevelItem(item)

                if isinstance(value, (dict, list)):
                    self._add_json_to_tree(value, item, path + [idx])

    def _on_tree_selection_changed(self):
        """Handle tree selection change - show value editor."""
        items = self.tree.selectedItems()
        if not items:
            return

        item = items[0]
        if isinstance(item, JsonTreeItem):
            self._show_value_editor(item)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click for quick edit."""
        if column == 1 and isinstance(item, JsonTreeItem):
            if not isinstance(item.value, (dict, list)):
                self._show_value_editor(item)

    def _show_value_editor(self, item: JsonTreeItem):
        """Show appropriate editor for selected item."""
        # Clear existing editor panel
        while self.editor_layout.count():
            child = self.editor_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Create editor based on value type
        value = item.value
        path_str = " → ".join(str(p) for p in item.json_path)

        # Path display
        path_label = QLabel(f"Path: {path_str}")
        path_label.setStyleSheet("color: #F29F05; font-family: Consolas; font-size: 11px;")
        path_label.setWordWrap(True)
        self.editor_layout.addWidget(path_label)

        # Type display
        type_label = QLabel(f"Type: {type(value).__name__}")
        type_label.setStyleSheet("color: #848E9C; font-size: 11px;")
        self.editor_layout.addWidget(type_label)

        # Value editor
        group = QGroupBox("Edit Value")
        form = QFormLayout(group)

        if isinstance(value, dict):
            info = QLabel(f"Object with {len(value)} keys:\n" + ", ".join(value.keys())[:100])
            info.setWordWrap(True)
            form.addRow(info)
        elif isinstance(value, list):
            info = QLabel(f"Array with {len(value)} items")
            form.addRow(info)
        elif isinstance(value, bool):
            checkbox = QCheckBox()
            checkbox.setChecked(value)
            checkbox.stateChanged.connect(lambda state: self._update_value(item, state == Qt.CheckState.Checked.value))
            form.addRow("Value:", checkbox)
        elif isinstance(value, int):
            spin = QSpinBox()
            spin.setRange(-2147483648, 2147483647)
            spin.setValue(value)
            spin.valueChanged.connect(lambda v: self._update_value(item, v))
            form.addRow("Value:", spin)
        elif isinstance(value, float):
            spin = QDoubleSpinBox()
            spin.setRange(-1e308, 1e308)
            spin.setDecimals(6)
            spin.setValue(value)
            spin.valueChanged.connect(lambda v: self._update_value(item, v))
            form.addRow("Value:", spin)
        elif value is None:
            combo = QComboBox()
            combo.addItems(["null", "0", "\"\"", "false", "true", "[]", "{}"])
            combo.setCurrentText("null")
            combo.currentTextChanged.connect(lambda v: self._update_value_from_type(item, v))
            form.addRow("Value:", combo)
        else:
            # String or other
            if len(str(value)) > 100:
                # Multi-line editor for long strings
                edit = QTextEdit()
                edit.setPlainText(str(value))
                edit.setMaximumHeight(200)
                edit.textChanged.connect(lambda: self._update_value(item, edit.toPlainText()))
                form.addRow("Value:", edit)
            else:
                edit = QLineEdit(str(value))
                edit.textChanged.connect(lambda v: self._update_value(item, v))
                form.addRow("Value:", edit)

        self.editor_layout.addWidget(group)

        # Add JSON preview
        preview_group = QGroupBox("JSON Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview = QTextEdit()
        preview.setReadOnly(True)
        preview.setMaximumHeight(150)
        preview.setStyleSheet("background: #252525; font-family: Consolas; font-size: 11px;")

        try:
            preview.setPlainText(json.dumps(value, indent=2, ensure_ascii=False))
        except:
            preview.setPlainText(str(value))

        preview_layout.addWidget(preview)
        self.editor_layout.addWidget(preview_group)

        self.editor_layout.addStretch()

    def _update_value(self, item: JsonTreeItem, new_value: Any):
        """Update value in JSON config."""
        self._set_value_at_path(self.current_config, item.json_path, new_value)
        item.value = new_value
        item._update_display()
        self._mark_modified()

    def _update_value_from_type(self, item: JsonTreeItem, type_str: str):
        """Convert type string to actual value."""
        type_map = {
            "null": None,
            "0": 0,
            "\"\"": "",
            "false": False,
            "true": True,
            "[]": [],
            "{}": {}
        }
        if type_str in type_map:
            self._update_value(item, type_map[type_str])

    def _set_value_at_path(self, config: Any, path: list, value: Any):
        """Set value at specified path in config."""
        if not path:
            return

        current = config
        for key in path[:-1]:
            current = current[key]
        current[path[-1]] = value

    def _mark_modified(self):
        """Mark config as modified."""
        if not self.is_modified:
            self.is_modified = True
            self.file_label.setText(
                f"File: {self.current_file_path.name} *" if self.current_file_path else "Modified *"
            )
            self.config_modified.emit()

    def _update_status(self):
        """Update status label with file info."""
        if not self.current_config:
            self.status_label.setText("No JSON file loaded")
            return

        # Count items
        def count_items(data):
            if isinstance(data, dict):
                return sum(1 + count_items(v) for v in data.values())
            elif isinstance(data, list):
                return sum(1 + count_items(v) for v in data)
            return 0

        num_items = count_items(self.current_config)
        self.status_label.setText(f"Items: {num_items} | File: {self.current_file_path}")

    def _show_tree_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        add_action = menu.addAction("Add Item")
        remove_action = menu.addAction("Remove")
        menu.addSeparator()
        copy_action = menu.addAction("Copy Value")

        action = menu.exec(self.tree.mapToGlobal(position))

        if action == add_action:
            self._on_add_item()
        elif action == remove_action:
            self._on_remove_item()
        elif action == copy_action:
            self._copy_value(item)

    def _on_add_item(self):
        """Add item to selected node."""
        items = self.tree.selectedItems()
        if not items:
            QMessageBox.information(self, "Add Item", "Please select a node first.")
            return

        item = items[0]
        if not isinstance(item, JsonTreeItem):
            return

        if isinstance(item.value, dict):
            # Add new key to dict
            key, ok = QInputDialog.getText(self, "Add Key", "Enter key name:")
            if ok and key:
                item.value[key] = ""
                self._set_value_at_path(self.current_config, item.json_path, item.value)
                self._populate_tree()
                self._mark_modified()

        elif isinstance(item.value, list):
            # Add new item to list
            item.value.append("")
            self._set_value_at_path(self.current_config, item.json_path, item.value)
            self._populate_tree()
            self._mark_modified()
        else:
            QMessageBox.information(self, "Add Item", "Can only add items to objects or arrays.")

    def _on_remove_item(self):
        """Remove selected item."""
        items = self.tree.selectedItems()
        if not items:
            return

        item = items[0]
        if not isinstance(item, JsonTreeItem):
            return

        if not item.json_path:
            QMessageBox.warning(self, "Remove", "Cannot remove root item.")
            return

        reply = QMessageBox.question(
            self, "Remove Item",
            f"Remove '{item.key}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Get parent and remove
            parent_path = item.json_path[:-1]
            key = item.json_path[-1]

            parent = self.current_config
            for p in parent_path:
                parent = parent[p]

            if isinstance(parent, dict):
                del parent[key]
            elif isinstance(parent, list):
                parent.pop(key)

            self._populate_tree()
            self._mark_modified()

    def _copy_value(self, item: QTreeWidgetItem):
        """Copy value to clipboard."""
        if isinstance(item, JsonTreeItem):
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            try:
                clipboard.setText(json.dumps(item.value, indent=2, ensure_ascii=False))
            except:
                clipboard.setText(str(item.value))

    def _on_save_file(self):
        """Save config to current file."""
        if not self.current_file_path:
            self._on_save_file_as()
            return

        self._save_to_file(self.current_file_path)

    def _on_save_file_as(self):
        """Save config to new file."""
        default_dir = str(self.current_file_path.parent) if self.current_file_path else ""

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            default_dir,
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self._save_to_file(Path(file_path))

    def _save_to_file(self, file_path: Path):
        """Save current config to file."""
        if not self.current_config:
            return

        try:
            # Ensure .json extension
            if file_path.suffix != ".json":
                file_path = file_path.with_suffix(".json")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.current_config, f, indent=2, ensure_ascii=False)

            self.current_file_path = file_path
            self.is_modified = False
            self.file_label.setText(f"File: {file_path.name}")
            self.status_label.setText(f"Saved: {file_path}")

            self.config_saved.emit(str(file_path))
            logger.info(f"Saved JSON to {file_path}")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Save Error",
                f"Failed to save JSON:\n{str(e)}"
            )
            logger.error(f"Failed to save JSON: {e}")

    def _on_reload_file(self):
        """Reload file from disk."""
        if not self.current_file_path:
            return

        if self.is_modified:
            reply = QMessageBox.question(
                self, "Reload",
                "Discard unsaved changes and reload?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.load_config(self.current_file_path)

    def has_unsaved_changes(self) -> bool:
        """Check if there are unsaved changes."""
        return self.is_modified


# Import for QInputDialog (used in _on_add_item)
from PyQt6.QtWidgets import QInputDialog
