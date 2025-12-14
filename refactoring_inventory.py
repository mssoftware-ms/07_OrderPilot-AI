#!/usr/bin/env python3
"""
Refactoring Inventory Tool V2.0
Vollständige Code-Inventur für sichere Refactorierung.

Analysiert alle Python-Dateien und erstellt eine detaillierte Inventur von:
- Funktionen/Methoden (mit Signaturen)
- Klassen (mit allen Methoden)
- UI-Komponenten (PyQt6)
- Event-Handler und Callbacks
- Imports/Exports
- Decorators
- Konstanten und Variablen
"""

import ast
import json
import hashlib
import os
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Set, Optional, Any
from datetime import datetime
import re


@dataclass
class FunctionInfo:
    """Information über eine Funktion/Methode."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    signature: str
    decorators: List[str]
    is_async: bool
    docstring: Optional[str]
    class_name: Optional[str] = None  # Falls Methode einer Klasse


@dataclass
class ClassInfo:
    """Information über eine Klasse."""
    name: str
    file_path: str
    line_start: int
    line_end: int
    bases: List[str]
    methods: List[str]
    decorators: List[str]
    docstring: Optional[str]
    is_ui_component: bool = False


@dataclass
class ImportInfo:
    """Information über einen Import."""
    module: str
    names: List[str]
    file_path: str
    line_number: int
    is_from_import: bool


@dataclass
class EventHandlerInfo:
    """Information über Event-Handler."""
    name: str
    file_path: str
    line_number: int
    signal_name: Optional[str]
    handler_type: str  # 'pyqt_signal', 'callback', 'slot', 'event_bus'


@dataclass
class UIComponentInfo:
    """Information über UI-Komponenten."""
    class_name: str
    file_path: str
    line_start: int
    line_end: int
    widget_type: str
    parent_class: str
    signals: List[str]
    slots: List[str]


@dataclass
class FileInventory:
    """Inventur einer einzelnen Datei."""
    file_path: str
    line_count: int
    code_lines: int  # Ohne Leerzeilen und Kommentare
    checksum: str
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)
    imports: List[ImportInfo] = field(default_factory=list)
    event_handlers: List[EventHandlerInfo] = field(default_factory=list)
    ui_components: List[UIComponentInfo] = field(default_factory=list)
    constants: List[Dict[str, Any]] = field(default_factory=list)
    global_variables: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ProjectInventory:
    """Gesamtinventur des Projekts."""
    timestamp: str
    project_root: str
    total_files: int
    total_lines: int
    total_code_lines: int
    total_functions: int
    total_classes: int
    total_ui_components: int
    total_event_handlers: int
    total_imports: int
    files: Dict[str, FileInventory] = field(default_factory=dict)


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


def calculate_file_checksum(file_path: str) -> str:
    """Berechnet MD5-Checksum einer Datei."""
    with open(file_path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def count_code_lines(source_code: str) -> int:
    """Zählt echte Code-Zeilen (ohne Leerzeilen und reine Kommentare)."""
    count = 0
    in_multiline_string = False

    for line in source_code.split('\n'):
        stripped = line.strip()

        # Skip Leerzeilen
        if not stripped:
            continue

        # Skip reine Kommentare
        if stripped.startswith('#'):
            continue

        # Multiline-Strings (einfache Behandlung)
        if '"""' in stripped or "'''" in stripped:
            count += 1
            continue

        count += 1

    return count


def analyze_file(file_path: str) -> Optional[FileInventory]:
    """Analysiert eine einzelne Python-Datei."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = ast.parse(source_code, filename=file_path)

        analyzer = InventoryAnalyzer(file_path, source_code)
        analyzer.visit(tree)

        return FileInventory(
            file_path=file_path,
            line_count=len(source_code.split('\n')),
            code_lines=count_code_lines(source_code),
            checksum=calculate_file_checksum(file_path),
            functions=analyzer.functions,
            classes=analyzer.classes,
            imports=analyzer.imports,
            event_handlers=analyzer.event_handlers,
            ui_components=analyzer.ui_components,
            constants=analyzer.constants,
            global_variables=analyzer.global_variables
        )
    except SyntaxError as e:
        print(f"Syntax-Fehler in {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Fehler bei Analyse von {file_path}: {e}")
        return None


def find_python_files(root_dir: str, exclude_patterns: List[str] = None) -> List[str]:
    """Findet alle Python-Dateien im Verzeichnis."""
    exclude_patterns = exclude_patterns or ['__pycache__', '.venv', 'venv', '.git', 'node_modules']
    python_files = []

    for root, dirs, files in os.walk(root_dir):
        # Exclude-Patterns anwenden
        dirs[:] = [d for d in dirs if not any(p in d for p in exclude_patterns)]

        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))

    return sorted(python_files)


def create_inventory(project_root: str, output_file: str = None) -> ProjectInventory:
    """Erstellt vollständige Projektinventur."""
    print(f"Starte Inventur für: {project_root}")
    print("-" * 60)

    python_files = find_python_files(project_root)
    print(f"Gefundene Python-Dateien: {len(python_files)}")

    files_inventory: Dict[str, FileInventory] = {}
    total_functions = 0
    total_classes = 0
    total_ui_components = 0
    total_event_handlers = 0
    total_imports = 0
    total_lines = 0
    total_code_lines = 0

    for file_path in python_files:
        rel_path = os.path.relpath(file_path, project_root)
        print(f"Analysiere: {rel_path}")

        inventory = analyze_file(file_path)
        if inventory:
            files_inventory[rel_path] = inventory
            total_functions += len(inventory.functions)
            total_classes += len(inventory.classes)
            total_ui_components += len(inventory.ui_components)
            total_event_handlers += len(inventory.event_handlers)
            total_imports += len(inventory.imports)
            total_lines += inventory.line_count
            total_code_lines += inventory.code_lines

    project_inv = ProjectInventory(
        timestamp=datetime.now().isoformat(),
        project_root=project_root,
        total_files=len(files_inventory),
        total_lines=total_lines,
        total_code_lines=total_code_lines,
        total_functions=total_functions,
        total_classes=total_classes,
        total_ui_components=total_ui_components,
        total_event_handlers=total_event_handlers,
        total_imports=total_imports,
        files=files_inventory
    )

    # Speichere Inventur
    if output_file:
        save_inventory(project_inv, output_file)

    return project_inv


def save_inventory(inventory: ProjectInventory, output_file: str):
    """Speichert Inventur als JSON."""
    def convert_to_dict(obj):
        if hasattr(obj, '__dict__'):
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = convert_to_dict(value)
            return result
        elif isinstance(obj, dict):
            return {k: convert_to_dict(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_dict(item) for item in obj]
        else:
            return obj

    data = convert_to_dict(inventory)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nInventur gespeichert: {output_file}")


def print_summary(inventory: ProjectInventory):
    """Druckt Zusammenfassung der Inventur."""
    print("\n" + "=" * 60)
    print("INVENTUR-ZUSAMMENFASSUNG")
    print("=" * 60)
    print(f"Zeitstempel:           {inventory.timestamp}")
    print(f"Projekt-Root:          {inventory.project_root}")
    print("-" * 60)
    print(f"Gesamte Dateien:       {inventory.total_files}")
    print(f"Gesamte Zeilen:        {inventory.total_lines:,}")
    print(f"Code-Zeilen:           {inventory.total_code_lines:,}")
    print(f"Gesamte Funktionen:    {inventory.total_functions}")
    print(f"Gesamte Klassen:       {inventory.total_classes}")
    print(f"UI-Komponenten:        {inventory.total_ui_components}")
    print(f"Event-Handler:         {inventory.total_event_handlers}")
    print(f"Import-Statements:     {inventory.total_imports}")
    print("=" * 60)

    # Top 10 größte Dateien
    print("\nTop 10 größte Dateien (nach Code-Zeilen):")
    print("-" * 60)
    sorted_files = sorted(
        inventory.files.items(),
        key=lambda x: x[1].code_lines,
        reverse=True
    )[:10]
    for path, file_inv in sorted_files:
        print(f"  {file_inv.code_lines:5d} Zeilen | {len(file_inv.functions):3d} Fkt | {len(file_inv.classes):2d} Kls | {path}")

    # UI-Komponenten
    print(f"\nUI-Komponenten ({inventory.total_ui_components} gesamt):")
    print("-" * 60)
    for path, file_inv in inventory.files.items():
        for ui_comp in file_inv.ui_components:
            print(f"  {ui_comp.class_name:40s} | {ui_comp.widget_type:20s} | {path}")

    # Dateien mit vielen Funktionen (potenzielle Split-Kandidaten)
    print("\nDateien mit >15 Funktionen (Split-Kandidaten):")
    print("-" * 60)
    for path, file_inv in sorted_files:
        if len(file_inv.functions) > 15:
            print(f"  {len(file_inv.functions):3d} Funktionen | {file_inv.code_lines:5d} Zeilen | {path}")


def create_detailed_report(inventory: ProjectInventory, output_file: str):
    """Erstellt detaillierten Bericht im Markdown-Format."""
    lines = []
    lines.append("# Code-Inventur Bericht\n")
    lines.append(f"**Erstellt:** {inventory.timestamp}\n")
    lines.append(f"**Projekt:** {inventory.project_root}\n\n")

    lines.append("## Übersicht\n")
    lines.append("| Metrik | Wert |")
    lines.append("|--------|------|")
    lines.append(f"| Dateien | {inventory.total_files} |")
    lines.append(f"| Gesamte Zeilen | {inventory.total_lines:,} |")
    lines.append(f"| Code-Zeilen | {inventory.total_code_lines:,} |")
    lines.append(f"| Funktionen | {inventory.total_functions} |")
    lines.append(f"| Klassen | {inventory.total_classes} |")
    lines.append(f"| UI-Komponenten | {inventory.total_ui_components} |")
    lines.append(f"| Event-Handler | {inventory.total_event_handlers} |")
    lines.append(f"| Imports | {inventory.total_imports} |\n")

    # Dateiliste mit Details
    lines.append("## Datei-Details\n")

    sorted_files = sorted(inventory.files.items())

    for path, file_inv in sorted_files:
        lines.append(f"### {path}\n")
        lines.append(f"- **Zeilen:** {file_inv.line_count} (Code: {file_inv.code_lines})")
        lines.append(f"- **Checksum:** `{file_inv.checksum}`")
        lines.append(f"- **Funktionen:** {len(file_inv.functions)}")
        lines.append(f"- **Klassen:** {len(file_inv.classes)}\n")

        if file_inv.classes:
            lines.append("**Klassen:**")
            for cls in file_inv.classes:
                ui_marker = " 🖥️" if cls.is_ui_component else ""
                lines.append(f"- `{cls.name}` (Zeile {cls.line_start}-{cls.line_end}){ui_marker}")
                if cls.methods:
                    lines.append(f"  - Methoden: {', '.join(cls.methods[:10])}" +
                               (f"... (+{len(cls.methods)-10})" if len(cls.methods) > 10 else ""))
            lines.append("")

        if file_inv.functions:
            # Nur Top-Level Funktionen (nicht Methoden)
            top_level_funcs = [f for f in file_inv.functions if f.class_name is None]
            if top_level_funcs:
                lines.append("**Top-Level Funktionen:**")
                for func in top_level_funcs[:20]:
                    async_marker = "async " if func.is_async else ""
                    lines.append(f"- `{async_marker}{func.name}{func.signature}` (Zeile {func.line_start})")
                if len(top_level_funcs) > 20:
                    lines.append(f"  ... und {len(top_level_funcs) - 20} weitere")
                lines.append("")

        lines.append("---\n")

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    print(f"Detaillierter Bericht erstellt: {output_file}")


if __name__ == "__main__":
    import sys

    # Projektverzeichnis
    project_root = os.path.dirname(os.path.abspath(__file__))

    # Erstelle Inventur
    inventory = create_inventory(
        project_root,
        output_file=os.path.join(project_root, "refactoring_inventory.json")
    )

    # Drucke Zusammenfassung
    print_summary(inventory)

    # Erstelle detaillierten Bericht
    create_detailed_report(
        inventory,
        os.path.join(project_root, "REFACTORING_INVENTORY_REPORT.md")
    )

    print("\n✓ Inventur abgeschlossen!")
