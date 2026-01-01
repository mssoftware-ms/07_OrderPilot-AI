from __future__ import annotations

import ast
import re
from typing import List, Optional, Dict, Any

from refactoring_inventory_models import (
    FunctionInfo,
    ClassInfo,
    ImportInfo,
    EventHandlerInfo,
    UIComponentInfo,
)

class InventoryAnalyzer(ast.NodeVisitor):
    """AST-Visitor für Code-Analyse."""

    def __init__(self, file_path: str, source_code: str):
        self.file_path = file_path
        self.source_code = source_code
        self.source_lines = source_code.split('\n')
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.imports: List[ImportInfo] = []
        self.event_handlers: List[EventHandlerInfo] = []
        self.ui_components: List[UIComponentInfo] = []
        self.constants: List[Dict[str, Any]] = []
        self.global_variables: List[Dict[str, Any]] = []
        self.current_class: Optional[str] = None

        # PyQt6 UI-Basisklassen
        self.ui_base_classes = {
            'QWidget', 'QMainWindow', 'QDialog', 'QFrame', 'QGroupBox',
            'QScrollArea', 'QStackedWidget', 'QTabWidget', 'QDockWidget',
            'QMdiArea', 'QMdiSubWindow', 'QAbstractItemView', 'QListView',
            'QTableView', 'QTreeView', 'QColumnView', 'QHeaderView',
            'QAbstractScrollArea', 'QGraphicsView', 'QWebEngineView',
            'QOpenGLWidget', 'QQuickWidget', 'QPushButton', 'QToolButton',
            'QRadioButton', 'QCheckBox', 'QComboBox', 'QFontComboBox',
            'QLineEdit', 'QTextEdit', 'QPlainTextEdit', 'QSpinBox',
            'QDoubleSpinBox', 'QDateEdit', 'QTimeEdit', 'QDateTimeEdit',
            'QSlider', 'QDial', 'QProgressBar', 'QLabel', 'QLCDNumber',
            'QCalendarWidget', 'QMenuBar', 'QMenu', 'QToolBar', 'QStatusBar',
            'QSplitter', 'QSplitterHandle', 'QRubberBand', 'QSizeGrip',
            'QDesktopWidget', 'QDialogButtonBox', 'QFocusFrame', 'QKeySequenceEdit',
            'QWizard', 'QWizardPage', 'QColorDialog', 'QErrorMessage',
            'QFileDialog', 'QFontDialog', 'QInputDialog', 'QMessageBox',
            'QProgressDialog'
        }

        # Signal-Pattern für Event-Handler-Erkennung
        self.signal_pattern = re.compile(r'\.connect\s*\(')
        self.slot_decorator_pattern = re.compile(r'@(Slot|pyqtSlot)')

    def get_decorator_names(self, node: ast.AST) -> List[str]:
        """Extrahiert Decorator-Namen."""
        decorators = []
        for decorator in getattr(node, 'decorator_list', []):
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
            elif isinstance(decorator, ast.Attribute):
                decorators.append(f"{self._get_full_name(decorator)}")
            elif isinstance(decorator, ast.Call):
                if isinstance(decorator.func, ast.Name):
                    decorators.append(decorator.func.id)
                elif isinstance(decorator.func, ast.Attribute):
                    decorators.append(self._get_full_name(decorator.func))
        return decorators

    def _get_full_name(self, node: ast.AST) -> str:
        """Holt vollständigen Namen eines Attributs."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_full_name(node.value)}.{node.attr}"
        return ""

    def _get_signature(self, node: ast.FunctionDef) -> str:
        """Erstellt Funktionssignatur."""
        args = []

        # Positional args
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # *args
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")

        # **kwargs
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")

        # Return annotation
        returns = ""
        if node.returns:
            returns = f" -> {ast.unparse(node.returns)}"

        return f"({', '.join(args)}){returns}"

    def _get_docstring(self, node: ast.AST) -> Optional[str]:
        """Extrahiert Docstring."""
        if node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Constant):
                if isinstance(node.body[0].value.value, str):
                    return node.body[0].value.value[:200]  # Erste 200 Zeichen
        return None

    def _get_end_line(self, node: ast.AST) -> int:
        """Holt Endzeile eines Nodes."""
        return getattr(node, 'end_lineno', node.lineno)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Besucht Funktionsdefinition."""
        decorators = self.get_decorator_names(node)

        func_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=self._get_end_line(node),
            signature=self._get_signature(node),
            decorators=decorators,
            is_async=False,
            docstring=self._get_docstring(node),
            class_name=self.current_class
        )
        self.functions.append(func_info)

        # Prüfe auf Slot/Event-Handler
        if any(d in ['Slot', 'pyqtSlot', 'slot'] for d in decorators):
            self.event_handlers.append(EventHandlerInfo(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                signal_name=None,
                handler_type='slot'
            ))
        elif node.name.startswith('on_') or node.name.endswith('_handler'):
            self.event_handlers.append(EventHandlerInfo(
                name=node.name,
                file_path=self.file_path,
                line_number=node.lineno,
                signal_name=None,
                handler_type='callback'
            ))

        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """Besucht async Funktionsdefinition."""
        decorators = self.get_decorator_names(node)

        func_info = FunctionInfo(
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=self._get_end_line(node),
            signature=self._get_signature(node),
            decorators=decorators,
            is_async=True,
            docstring=self._get_docstring(node),
            class_name=self.current_class
        )
        self.functions.append(func_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Besucht Klassendefinition."""
        bases = [ast.unparse(base) for base in node.bases]
        decorators = self.get_decorator_names(node)

        # Prüfe auf UI-Komponente
        is_ui = any(base in self.ui_base_classes for base in bases) or \
                any(b.split('.')[-1] in self.ui_base_classes for b in bases)

        # Sammle Methoden
        methods = []
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append(item.name)

        class_info = ClassInfo(
            name=node.name,
            file_path=self.file_path,
            line_start=node.lineno,
            line_end=self._get_end_line(node),
            bases=bases,
            methods=methods,
            decorators=decorators,
            docstring=self._get_docstring(node),
            is_ui_component=is_ui
        )
        self.classes.append(class_info)

        if is_ui:
            # Analysiere UI-Komponente detaillierter
            signals = []
            slots = []
            for item in node.body:
                if isinstance(item, ast.Assign):
                    # Suche nach Signal-Definitionen
                    for target in item.targets:
                        if isinstance(target, ast.Name):
                            if isinstance(item.value, ast.Call):
                                if hasattr(item.value.func, 'attr'):
                                    if item.value.func.attr in ['Signal', 'pyqtSignal']:
                                        signals.append(target.id)
                elif isinstance(item, ast.FunctionDef):
                    if any(d in ['Slot', 'pyqtSlot'] for d in self.get_decorator_names(item)):
                        slots.append(item.name)

            self.ui_components.append(UIComponentInfo(
                class_name=node.name,
                file_path=self.file_path,
                line_start=node.lineno,
                line_end=self._get_end_line(node),
                widget_type=bases[0] if bases else 'Unknown',
                parent_class=bases[0] if bases else '',
                signals=signals,
                slots=slots
            ))

        # Setze aktuellen Klassenkontext
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class

    def visit_Import(self, node: ast.Import):
        """Besucht Import-Statement."""
        for alias in node.names:
            self.imports.append(ImportInfo(
                module=alias.name,
                names=[alias.asname or alias.name],
                file_path=self.file_path,
                line_number=node.lineno,
                is_from_import=False
            ))
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Besucht from-Import-Statement."""
        module = node.module or ''
        names = [alias.name for alias in node.names]

        self.imports.append(ImportInfo(
            module=module,
            names=names,
            file_path=self.file_path,
            line_number=node.lineno,
            is_from_import=True
        ))
        self.generic_visit(node)

    def visit_Assign(self, node: ast.Assign):
        """Besucht Zuweisung (für Konstanten und globale Variablen)."""
        if self.current_class is None:  # Nur auf Modulebene
            for target in node.targets:
                if isinstance(target, ast.Name):
                    name = target.id
                    # Konstante = UPPERCASE
                    if name.isupper():
                        self.constants.append({
                            'name': name,
                            'line': node.lineno,
                            'value_type': type(node.value).__name__
                        })
                    else:
                        self.global_variables.append({
                            'name': name,
                            'line': node.lineno,
                            'value_type': type(node.value).__name__
                        })
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        """Besucht Funktionsaufruf (für Signal-Connections)."""
        # Suche nach .connect() Aufrufen
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'connect':
                # Signal-Connection gefunden
                if node.args:
                    handler_name = None
                    if isinstance(node.args[0], ast.Name):
                        handler_name = node.args[0].id
                    elif isinstance(node.args[0], ast.Attribute):
                        handler_name = self._get_full_name(node.args[0])

                    if handler_name:
                        signal_name = self._get_full_name(node.func.value)
                        self.event_handlers.append(EventHandlerInfo(
                            name=handler_name,
                            file_path=self.file_path,
                            line_number=node.lineno,
                            signal_name=signal_name,
                            handler_type='pyqt_signal'
                        ))
        self.generic_visit(node)
