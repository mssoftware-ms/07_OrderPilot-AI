"""RulePack Panel for advanced RulePack editing (Phase 2.5.2)."""

from __future__ import annotations

from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTabWidget,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QLineEdit,
    QTextEdit,
    QFormLayout,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QLabel,
    QSplitter,
    QMessageBox,
)

from src.core.tradingbot.cel.models import RulePack, Rule, Pack


class CelRulePackPanel(QWidget):
    """UI panel for editing RulePack rules and metadata."""

    rule_selected = pyqtSignal(str, str)  # pack_type, rule_id
    rule_updated = pyqtSignal(str, str)  # pack_type, rule_id
    rule_order_changed = pyqtSignal(str)  # pack_type

    PACK_ORDER = ("entry", "exit", "update_stop", "no_trade", "risk")

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self._loading = False
        self.rulepack: Optional[RulePack] = None
        self._current_pack_type: Optional[str] = None
        self._current_rule_id: Optional[str] = None
        self._list_by_pack: dict[str, QListWidget] = {}
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("RulePack Editor")
        header.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        for pack_type in self.PACK_ORDER:
            tab = QWidget()
            tab_layout = QHBoxLayout(tab)
            tab_layout.setContentsMargins(6, 6, 6, 6)

            splitter = QSplitter(Qt.Orientation.Horizontal)

            # Left: rule list + controls
            left = QWidget()
            left_layout = QVBoxLayout(left)

            list_widget = QListWidget()
            list_widget.itemSelectionChanged.connect(self._on_rule_selected)
            self._list_by_pack[pack_type] = list_widget
            left_layout.addWidget(list_widget)

            btn_row = QHBoxLayout()
            add_btn = QPushButton("+")
            add_btn.setToolTip("Add rule")
            add_btn.clicked.connect(lambda _=False, p=pack_type: self.add_rule(p))
            del_btn = QPushButton("-")
            del_btn.setToolTip("Remove rule")
            del_btn.clicked.connect(lambda _=False, p=pack_type: self.remove_selected_rule(p))
            up_btn = QPushButton("↑")
            up_btn.setToolTip("Move up")
            up_btn.clicked.connect(lambda _=False, p=pack_type: self.move_rule(p, -1))
            down_btn = QPushButton("↓")
            down_btn.setToolTip("Move down")
            down_btn.clicked.connect(lambda _=False, p=pack_type: self.move_rule(p, 1))

            for btn in (add_btn, del_btn, up_btn, down_btn):
                btn_row.addWidget(btn)
            left_layout.addLayout(btn_row)

            splitter.addWidget(left)

            # Right: metadata editor
            right = QWidget()
            form = QFormLayout(right)
            form.setContentsMargins(6, 6, 6, 6)

            self.id_field = QLineEdit()
            self.id_field.setReadOnly(True)
            self.name_field = QLineEdit()
            self.desc_field = QTextEdit()
            self.desc_field.setMaximumHeight(80)
            self.severity_field = QComboBox()
            self.severity_field.addItems(["block", "exit", "update_stop", "warn"])
            self.priority_field = QSpinBox()
            self.priority_field.setRange(0, 100)
            self.enabled_field = QCheckBox("Enabled")
            self.tags_field = QLineEdit()
            self.message_field = QLineEdit()

            form.addRow("Rule ID", self.id_field)
            form.addRow("Name", self.name_field)
            form.addRow("Description", self.desc_field)
            form.addRow("Severity", self.severity_field)
            form.addRow("Priority", self.priority_field)
            form.addRow("Enabled", self.enabled_field)
            form.addRow("Tags (comma)", self.tags_field)
            form.addRow("Message", self.message_field)

            for w in (
                self.name_field,
                self.desc_field,
                self.severity_field,
                self.priority_field,
                self.enabled_field,
                self.tags_field,
                self.message_field,
            ):
                if isinstance(w, QTextEdit):
                    w.textChanged.connect(self._on_metadata_changed)
                elif isinstance(w, QComboBox):
                    w.currentIndexChanged.connect(self._on_metadata_changed)
                elif isinstance(w, QSpinBox):
                    w.valueChanged.connect(self._on_metadata_changed)
                elif isinstance(w, QCheckBox):
                    w.stateChanged.connect(self._on_metadata_changed)
                else:
                    w.textChanged.connect(self._on_metadata_changed)

            splitter.addWidget(right)
            splitter.setSizes([240, 360])
            tab_layout.addWidget(splitter)

            self.tabs.addTab(tab, pack_type)

    def load_rulepack(self, rulepack: RulePack) -> None:
        """Load rulepack into UI."""
        self.rulepack = rulepack
        self._loading = True
        try:
            for pack_type in self.PACK_ORDER:
                self._populate_pack_list(pack_type)
        finally:
            self._loading = False
        self.select_first_rule()

    def select_first_rule(self) -> None:
        """Select first available rule and emit selection signal."""
        if not self.rulepack:
            return
        for pack_type in self.PACK_ORDER:
            lw = self._list_by_pack[pack_type]
            if lw.count() > 0:
                lw.setCurrentRow(0)
                self._on_rule_selected()
                break

    def _populate_pack_list(self, pack_type: str) -> None:
        lw = self._list_by_pack[pack_type]
        lw.clear()
        if not self.rulepack:
            return
        pack = self._get_pack(pack_type)
        if not pack:
            return
        for rule in pack.rules:
            item = QListWidgetItem(self._format_rule_label(rule))
            item.setData(Qt.ItemDataRole.UserRole, rule.id)
            lw.addItem(item)

    def _format_rule_label(self, rule: Rule) -> str:
        status = "✅" if rule.enabled else "⏸"
        return f"{status} {rule.name} ({rule.priority})"

    def _get_pack(self, pack_type: str) -> Optional[Pack]:
        if not self.rulepack:
            return None
        return self.rulepack.get_pack(pack_type)

    def _find_rule(self, pack_type: str, rule_id: str) -> Optional[Rule]:
        pack = self._get_pack(pack_type)
        if not pack:
            return None
        for rule in pack.rules:
            if rule.id == rule_id:
                return rule
        return None

    def _on_rule_selected(self) -> None:
        if self._loading or not self.rulepack:
            return
        current_tab = self.tabs.currentIndex()
        pack_type = self.PACK_ORDER[current_tab]
        lw = self._list_by_pack[pack_type]
        item = lw.currentItem()
        if not item:
            return
        rule_id = item.data(Qt.ItemDataRole.UserRole)
        rule = self._find_rule(pack_type, rule_id)
        if not rule:
            return
        self._current_pack_type = pack_type
        self._current_rule_id = rule_id
        self._load_rule_metadata(rule)
        self.rule_selected.emit(pack_type, rule_id)

    def _load_rule_metadata(self, rule: Rule) -> None:
        self._loading = True
        try:
            self.id_field.setText(rule.id)
            self.name_field.setText(rule.name)
            self.desc_field.setText(rule.description or "")
            self.severity_field.setCurrentText(rule.severity)
            self.priority_field.setValue(rule.priority)
            self.enabled_field.setChecked(rule.enabled)
            self.tags_field.setText(", ".join(rule.tags))
            self.message_field.setText(rule.message or "")
        finally:
            self._loading = False

    def _on_metadata_changed(self) -> None:
        if self._loading or not self.rulepack:
            return
        if not self._current_pack_type or not self._current_rule_id:
            return
        rule = self._find_rule(self._current_pack_type, self._current_rule_id)
        if not rule:
            return
        rule.name = self.name_field.text().strip() or rule.name
        rule.description = self.desc_field.toPlainText().strip() or None
        rule.severity = self.severity_field.currentText()
        rule.priority = int(self.priority_field.value())
        rule.enabled = self.enabled_field.isChecked()
        tags = [t.strip() for t in self.tags_field.text().split(",") if t.strip()]
        rule.tags = tags
        rule.message = self.message_field.text().strip() or None

        # Update list label
        self._refresh_current_item_label()
        self.rule_updated.emit(self._current_pack_type, self._current_rule_id)

    def _refresh_current_item_label(self) -> None:
        if not self._current_pack_type or not self._current_rule_id:
            return
        lw = self._list_by_pack[self._current_pack_type]
        item = lw.currentItem()
        rule = self._find_rule(self._current_pack_type, self._current_rule_id)
        if item and rule:
            item.setText(self._format_rule_label(rule))

    def add_rule(self, pack_type: str) -> None:
        if not self.rulepack:
            return
        pack = self._get_pack(pack_type)
        if not pack:
            return
        new_id = self._generate_rule_id(pack)
        rule = Rule(
            id=new_id,
            name=f"New {pack_type} rule",
            description="",
            expression="true",
            severity="warn",
            message=None,
            enabled=True,
            tags=[],
            priority=50,
        )
        pack.rules.append(rule)
        self._populate_pack_list(pack_type)
        lw = self._list_by_pack[pack_type]
        lw.setCurrentRow(lw.count() - 1)
        self.rule_updated.emit(pack_type, rule.id)

    def remove_selected_rule(self, pack_type: str) -> None:
        if not self.rulepack:
            return
        lw = self._list_by_pack[pack_type]
        item = lw.currentItem()
        if not item:
            return
        rule_id = item.data(Qt.ItemDataRole.UserRole)
        pack = self._get_pack(pack_type)
        if not pack:
            return
        if len(pack.rules) <= 1:
            QMessageBox.warning(self, "Cannot Remove", "Each pack must contain at least one rule.")
            return
        pack.rules = [r for r in pack.rules if r.id != rule_id]
        self._populate_pack_list(pack_type)
        if lw.count() > 0:
            lw.setCurrentRow(0)
        self.rule_updated.emit(pack_type, "")

    def move_rule(self, pack_type: str, direction: int) -> None:
        if not self.rulepack:
            return
        pack = self._get_pack(pack_type)
        if not pack:
            return
        lw = self._list_by_pack[pack_type]
        row = lw.currentRow()
        if row < 0:
            return
        new_row = row + direction
        if new_row < 0 or new_row >= len(pack.rules):
            return
        pack.rules[row], pack.rules[new_row] = pack.rules[new_row], pack.rules[row]
        self._populate_pack_list(pack_type)
        lw.setCurrentRow(new_row)
        self.rule_order_changed.emit(pack_type)

    def _generate_rule_id(self, pack: Pack) -> str:
        base = f"{pack.pack_type}_rule"
        existing = {r.id for r in pack.rules}
        idx = 1
        while f"{base}_{idx}" in existing:
            idx += 1
        return f"{base}_{idx}"

    def set_rule_expression(self, pack_type: str, rule_id: str, expression: str) -> None:
        """Update rule expression from editor."""
        rule = self._find_rule(pack_type, rule_id)
        if rule:
            rule.expression = expression.strip()
            self.rule_updated.emit(pack_type, rule_id)
