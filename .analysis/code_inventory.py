#!/usr/bin/env python3
"""
Code Inventory Tool - Vollständige Projektanalyse
Erstellt eine detaillierte Inventur aller Python-Dateien.
"""

import ast
import os
import json
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class FunctionInfo:
    name: str
    file: str
    lines: Tuple[int, int]
    parameters: List[str]
    is_async: bool = False
    is_method: bool = False
    class_name: str = ""


@dataclass
class ClassInfo:
    name: str
    file: str
    lines: Tuple[int, int]
    methods: List[str]
    base_classes: List[str]
    is_ui_component: bool = False


@dataclass
class FileInfo:
    path: str
    loc_total: int
    loc_productive: int
    loc_comments: int
    loc_blank: int
    functions: int
    classes: int


@dataclass
class Inventory:
    project: str
    timestamp: str
    files_total: int
    files_over_600: int
    files_list: List[FileInfo]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    loc_total: int
    loc_productive: int
    loc_comments: int
    loc_blank: int
    ui_components: List[str]
    imports_total: int


class CodeInventoryAnalyzer:
    def __init__(self, root_dir: str = "src"):
        self.root_dir = Path(root_dir)
        self.functions: List[FunctionInfo] = []
        self.classes: List[ClassInfo] = []
        self.files: List[FileInfo] = []
        self.ui_components: List[str] = []
        self.imports_count = 0

        # UI Framework markers
        self.ui_markers = {
            'PyQt6', 'PyQt5', 'PySide6', 'PySide2', 'Tkinter', 'tkinter',
            'QWidget', 'QMainWindow', 'QDialog', 'QFrame', 'QPushButton',
            'QLabel', 'QLineEdit', 'QTextEdit', 'QComboBox', 'QSpinBox'
        }

    def count_lines(self, filepath: Path) -> Tuple[int, int, int, int]:
        """Zählt LOC: (total, produktiv, kommentare, leerzeilen)"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            total = len(lines)
            blank = sum(1 for line in lines if line.strip() == '')
            comments = 0
            in_docstring = False
            docstring_delimiters = ('"""', "'''")

            for line in lines:
                stripped = line.strip()
                # Check for docstring start/end
                for delim in docstring_delimiters:
                    if stripped.startswith(delim):
                        in_docstring = not in_docstring
                        comments += 1
                        break
                else:
                    if in_docstring:
                        comments += 1
                    elif stripped.startswith('#'):
                        comments += 1

            productive = total - blank - comments
            return (total, productive, comments, blank)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
            return (0, 0, 0, 0)

    def analyze_file(self, filepath: Path) -> None:
        """Analysiert eine einzelne Python-Datei"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            tree = ast.parse(content, filename=str(filepath))

            # Count imports
            for node in ast.walk(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    self.imports_count += 1

            # Analyze functions and classes
            self._analyze_ast(tree, filepath)

            # Count lines
            loc_total, loc_prod, loc_comm, loc_blank = self.count_lines(filepath)

            # Count functions and classes in this file
            file_funcs = sum(1 for f in self.functions if f.file == str(filepath))
            file_classes = sum(1 for c in self.classes if c.file == str(filepath))

            file_info = FileInfo(
                path=str(filepath.relative_to(self.root_dir.parent)),
                loc_total=loc_total,
                loc_productive=loc_prod,
                loc_comments=loc_comm,
                loc_blank=loc_blank,
                functions=file_funcs,
                classes=file_classes
            )
            self.files.append(file_info)

        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
        except Exception as e:
            print(f"Error analyzing {filepath}: {e}")

    def _analyze_ast(self, tree: ast.AST, filepath: Path) -> None:
        """Analysiert AST für Funktionen und Klassen"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                params = [arg.arg for arg in node.args.args]
                func_info = FunctionInfo(
                    name=node.name,
                    file=str(filepath.relative_to(self.root_dir.parent)),
                    lines=(node.lineno, node.end_lineno or node.lineno),
                    parameters=params,
                    is_async=isinstance(node, ast.AsyncFunctionDef)
                )
                self.functions.append(func_info)

            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                bases = [self._get_base_name(base) for base in node.bases]

                # Check if UI component
                is_ui = any(base in self.ui_markers for base in bases)
                if is_ui:
                    self.ui_components.append(f"{node.name} ({filepath.relative_to(self.root_dir.parent)})")

                class_info = ClassInfo(
                    name=node.name,
                    file=str(filepath.relative_to(self.root_dir.parent)),
                    lines=(node.lineno, node.end_lineno or node.lineno),
                    methods=methods,
                    base_classes=bases,
                    is_ui_component=is_ui
                )
                self.classes.append(class_info)

    def _get_base_name(self, base: ast.expr) -> str:
        """Extrahiert Basisklassen-Namen"""
        if isinstance(base, ast.Name):
            return base.id
        elif isinstance(base, ast.Attribute):
            return base.attr
        return "Unknown"

    def run(self) -> Inventory:
        """Führt die Inventur durch"""
        print(f"🔍 Analysiere Projekt in: {self.root_dir}")

        # Finde alle Python-Dateien
        py_files = list(self.root_dir.rglob("*.py"))
        print(f"📁 Gefunden: {len(py_files)} Python-Dateien")

        # Analysiere jede Datei
        for i, filepath in enumerate(py_files, 1):
            if i % 50 == 0:
                print(f"  ... {i}/{len(py_files)} Dateien analysiert")
            self.analyze_file(filepath)

        # Erstelle Inventur
        files_over_600 = sum(1 for f in self.files if f.loc_productive > 600)

        inventory = Inventory(
            project="OrderPilot-AI",
            timestamp=datetime.now().isoformat(),
            files_total=len(self.files),
            files_over_600=files_over_600,
            files_list=self.files,
            functions=self.functions,
            classes=self.classes,
            loc_total=sum(f.loc_total for f in self.files),
            loc_productive=sum(f.loc_productive for f in self.files),
            loc_comments=sum(f.loc_comments for f in self.files),
            loc_blank=sum(f.loc_blank for f in self.files),
            ui_components=self.ui_components,
            imports_total=self.imports_count
        )

        print(f"\n✅ Inventur abgeschlossen!")
        print(f"  📊 Dateien: {inventory.files_total}")
        print(f"  ⚠️  Dateien >600 LOC: {inventory.files_over_600}")
        print(f"  📈 LOC gesamt: {inventory.loc_total:,}")
        print(f"  💻 LOC produktiv: {inventory.loc_productive:,}")
        print(f"  🔧 Funktionen: {len(self.functions)}")
        print(f"  🏗️  Klassen: {len(self.classes)}")
        print(f"  🖼️  UI-Komponenten: {len(self.ui_components)}")

        return inventory

    def save_report(self, inventory: Inventory, output_file: str = ".analysis/inventory_before.json") -> None:
        """Speichert Inventur als JSON"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert to dict (with custom serialization for dataclasses)
        def serialize(obj):
            if hasattr(obj, '__dict__'):
                return asdict(obj)
            return str(obj)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(asdict(inventory), f, indent=2, default=serialize)

        print(f"\n💾 Inventur gespeichert: {output_path}")


def main():
    analyzer = CodeInventoryAnalyzer("src")
    inventory = analyzer.run()
    analyzer.save_report(inventory)

    # Ausgabe der größten Dateien
    print("\n" + "="*80)
    print("📋 DATEIEN ÜBER 600 LOC (SPLITTING ERFORDERLICH):")
    print("="*80)

    large_files = sorted(
        [f for f in inventory.files_list if f.loc_productive > 600],
        key=lambda x: x.loc_productive,
        reverse=True
    )

    if large_files:
        print(f"\n{'Datei':<60} {'LOC':>8} {'Fkt':>5} {'Kls':>5}")
        print("-" * 80)
        for f in large_files:
            print(f"{f.path:<60} {f.loc_productive:>8} {f.functions:>5} {f.classes:>5}")
    else:
        print("\n✅ Keine Dateien über 600 LOC gefunden!")


if __name__ == "__main__":
    main()
