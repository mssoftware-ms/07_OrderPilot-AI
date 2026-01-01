#!/usr/bin/env python3
"""
Refactoring Inventory Tool V2.0
Vollständige Code-Inventur für sichere Refactorierung.
"""

from __future__ import annotations

import ast
import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict

from refactoring_inventory_analyzer import InventoryAnalyzer
from refactoring_inventory_models import FileInventory, ProjectInventory

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
