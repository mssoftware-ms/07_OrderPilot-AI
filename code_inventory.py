#!/usr/bin/env python3
"""
Code Inventory Script für OrderPilot-AI
Erstellt vollständige Inventur aller Python-Dateien gemäß Refactoring-Workflow Phase 1
"""

import ast
import os
import json
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime
from collections import defaultdict
import re


class CodeInventory:
    """Analysiert Python-Code und erstellt umfassende Inventur"""

    def __init__(self, root_dir: str = "."):
        self.root_dir = Path(root_dir)
        self.inventory = {
            "projekt": "OrderPilot-AI",
            "timestamp": datetime.now().isoformat(),
            "root_dir": str(self.root_dir.absolute()),
            "dateien": {
                "total": 0,
                "liste": [],
                "groessen": []
            },
            "dateien_ueber_600_loc": {
                "total": 0,
                "liste": []
            },
            "funktionen": {
                "total": 0,
                "liste": []
            },
            "klassen": {
                "total": 0,
                "liste": []
            },
            "ui_komponenten": {
                "total": 0,
                "liste": []
            },
            "imports": {
                "total": 0,
                "liste": []
            },
            "event_handler": {
                "total": 0,
                "liste": []
            },
            "api_endpoints": {
                "total": 0,
                "liste": []
            },
            "lines_of_code": {
                "total": 0,
                "produktiv": 0,
                "kommentare": 0,
                "leerzeilen": 0
            }
        }

        # Patterns für Erkennung
        self.ui_patterns = [
            r'QPushButton', r'QLineEdit', r'QLabel', r'QComboBox', r'QCheckBox',
            r'QRadioButton', r'QTableWidget', r'QTreeWidget', r'QDialog',
            r'QMainWindow', r'QWidget', r'QTabWidget', r'QMenuBar', r'QToolBar',
            r'Button', r'Entry', r'Label', r'Frame', r'Canvas'  # Tkinter
        ]

        self.event_handler_patterns = [
            r'on_\w+_clicked', r'on_\w+_changed', r'on_\w+_pressed',
            r'handle_\w+', r'_on_\w+', r'slot_\w+', r'@\w*Slot'
        ]

        self.api_endpoint_patterns = [
            r'@app\.route', r'@router\.\w+', r'@get', r'@post', r'@put', r'@delete',
            r'def get_', r'def post_', r'def put_', r'def delete_'
        ]

    def analyze_file(self, filepath: Path) -> Dict[str, Any]:
        """Analysiert eine einzelne Python-Datei"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # LOC-Analyse
            lines = content.split('\n')
            total_lines = len(lines)
            comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
            empty_lines = sum(1 for line in lines if not line.strip())
            productive_lines = total_lines - comment_lines - empty_lines

            # AST-Analyse
            try:
                tree = ast.parse(content, filename=str(filepath))
            except SyntaxError as e:
                print(f"⚠️  Syntax-Error in {filepath}: {e}")
                return None

            # Funktionen extrahieren
            functions = []
            classes = []
            imports = []

            for node in ast.walk(tree):
                # Funktionen
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "datei": str(filepath.relative_to(self.root_dir)),
                        "zeilen": [node.lineno, node.end_lineno or node.lineno],
                        "signatur": self._get_function_signature(node),
                        "is_async": isinstance(node, ast.AsyncFunctionDef),
                        "decorators": [self._get_decorator_name(d) for d in node.decorator_list]
                    }
                    functions.append(func_info)

                # Klassen
                elif isinstance(node, ast.ClassDef):
                    methods = [
                        {
                            "name": m.name,
                            "zeilen": [m.lineno, m.end_lineno or m.lineno],
                            "signatur": self._get_function_signature(m)
                        }
                        for m in node.body if isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef))
                    ]

                    class_info = {
                        "name": node.name,
                        "datei": str(filepath.relative_to(self.root_dir)),
                        "zeilen": [node.lineno, node.end_lineno or node.lineno],
                        "methoden": methods,
                        "methoden_count": len(methods),
                        "bases": [self._get_base_name(b) for b in node.bases]
                    }
                    classes.append(class_info)

                # Imports
                elif isinstance(node, (ast.Import, ast.ImportFrom)):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.append({
                                "module": alias.name,
                                "alias": alias.asname,
                                "type": "import"
                            })
                    else:  # ImportFrom
                        module = node.module or ""
                        for alias in node.names:
                            imports.append({
                                "module": f"{module}.{alias.name}" if module else alias.name,
                                "alias": alias.asname,
                                "type": "from",
                                "from_module": module
                            })

            # UI-Komponenten erkennen
            ui_components = []
            for pattern in self.ui_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    ui_components.append({
                        "typ": match.group(),
                        "datei": str(filepath.relative_to(self.root_dir)),
                        "zeile": line_no
                    })

            # Event-Handler erkennen
            event_handlers = []
            for func in functions:
                func_name = func["name"]
                # Prüfe ob Name einem Event-Handler-Pattern entspricht
                if any(re.search(pattern, func_name) for pattern in self.event_handler_patterns):
                    event_handlers.append(func)
                # Prüfe Decorators
                elif any('@Slot' in dec or '@pyqtSlot' in dec for dec in func.get("decorators", [])):
                    event_handlers.append(func)

            # API-Endpoints erkennen (im Content)
            api_endpoints = []
            for pattern in self.api_endpoint_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    line_no = content[:match.start()].count('\n') + 1
                    api_endpoints.append({
                        "pattern": match.group(),
                        "datei": str(filepath.relative_to(self.root_dir)),
                        "zeile": line_no
                    })

            return {
                "filepath": str(filepath.relative_to(self.root_dir)),
                "loc": {
                    "total": total_lines,
                    "produktiv": productive_lines,
                    "kommentare": comment_lines,
                    "leerzeilen": empty_lines
                },
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "ui_components": ui_components,
                "event_handlers": event_handlers,
                "api_endpoints": api_endpoints
            }

        except Exception as e:
            print(f"❌ Error analyzing {filepath}: {e}")
            return None

    def _get_function_signature(self, node: ast.FunctionDef) -> str:
        """Extrahiert Funktions-Signatur"""
        args = []
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

        signature = f"{node.name}({', '.join(args)})"

        # Return-Type
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"

        return signature

    def _get_decorator_name(self, node) -> str:
        """Extrahiert Decorator-Namen"""
        if isinstance(node, ast.Name):
            return f"@{node.id}"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                return f"@{node.func.id}(...)"
            elif isinstance(node.func, ast.Attribute):
                return f"@{ast.unparse(node.func)}(...)"
        return "@" + ast.unparse(node)

    def _get_base_name(self, node) -> str:
        """Extrahiert Basis-Klassen-Namen"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return ast.unparse(node)
        return ast.unparse(node)

    def scan_project(self, include_tests: bool = True):
        """Scannt das gesamte Projekt"""
        print("🔍 Starte Code-Inventur...")

        # Finde alle Python-Dateien
        patterns = ["src/**/*.py"]
        if include_tests:
            patterns.append("tests/**/*.py")

        all_files = []
        for pattern in patterns:
            all_files.extend(self.root_dir.glob(pattern))

        # Filtere __pycache__ und .venv
        all_files = [
            f for f in all_files
            if '__pycache__' not in str(f) and '.venv' not in str(f) and 'venv' not in str(f)
        ]

        self.inventory["dateien"]["total"] = len(all_files)
        self.inventory["dateien"]["liste"] = [str(f.relative_to(self.root_dir)) for f in all_files]

        print(f"📁 Gefunden: {len(all_files)} Python-Dateien")

        # Analysiere jede Datei
        for idx, filepath in enumerate(all_files, 1):
            print(f"  [{idx}/{len(all_files)}] {filepath.name}", end='\r')

            file_data = self.analyze_file(filepath)
            if not file_data:
                continue

            # LOC
            self.inventory["lines_of_code"]["total"] += file_data["loc"]["total"]
            self.inventory["lines_of_code"]["produktiv"] += file_data["loc"]["produktiv"]
            self.inventory["lines_of_code"]["kommentare"] += file_data["loc"]["kommentare"]
            self.inventory["lines_of_code"]["leerzeilen"] += file_data["loc"]["leerzeilen"]

            # Dateigröße speichern
            self.inventory["dateien"]["groessen"].append({
                "datei": file_data["filepath"],
                "loc": file_data["loc"]["total"],
                "loc_produktiv": file_data["loc"]["produktiv"]
            })

            # Prüfe auf >600 LOC
            if file_data["loc"]["produktiv"] > 600:
                self.inventory["dateien_ueber_600_loc"]["liste"].append({
                    "datei": file_data["filepath"],
                    "loc_produktiv": file_data["loc"]["produktiv"],
                    "funktionen_count": len(file_data["functions"]),
                    "klassen_count": len(file_data["classes"])
                })

            # Funktionen
            self.inventory["funktionen"]["liste"].extend(file_data["functions"])

            # Klassen
            self.inventory["klassen"]["liste"].extend(file_data["classes"])

            # UI-Komponenten
            self.inventory["ui_komponenten"]["liste"].extend(file_data["ui_components"])

            # Imports
            self.inventory["imports"]["liste"].extend(file_data["imports"])

            # Event-Handler
            self.inventory["event_handler"]["liste"].extend(file_data["event_handlers"])

            # API-Endpoints
            self.inventory["api_endpoints"]["liste"].extend(file_data["api_endpoints"])

        # Totals aktualisieren
        self.inventory["dateien_ueber_600_loc"]["total"] = len(self.inventory["dateien_ueber_600_loc"]["liste"])
        self.inventory["funktionen"]["total"] = len(self.inventory["funktionen"]["liste"])
        self.inventory["klassen"]["total"] = len(self.inventory["klassen"]["liste"])
        self.inventory["ui_komponenten"]["total"] = len(self.inventory["ui_komponenten"]["liste"])
        self.inventory["imports"]["total"] = len(self.inventory["imports"]["liste"])
        self.inventory["event_handler"]["total"] = len(self.inventory["event_handler"]["liste"])
        self.inventory["api_endpoints"]["total"] = len(self.inventory["api_endpoints"]["liste"])

        print("\n✅ Inventur abgeschlossen!")

    def save_json(self, output_file: str = "code_inventory.json"):
        """Speichert Inventur als JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.inventory, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON gespeichert: {output_file}")

    def generate_markdown_report(self, output_file: str = "CODE_INVENTORY_REPORT.md"):
        """Generiert Markdown-Report"""

        # Sortiere Dateien nach LOC (absteigend)
        sorted_files = sorted(
            self.inventory["dateien"]["groessen"],
            key=lambda x: x["loc_produktiv"],
            reverse=True
        )

        # Top 20 größte Dateien
        top_20_files = sorted_files[:20]

        # Funktionen nach Datei gruppieren
        funcs_by_file = defaultdict(int)
        for func in self.inventory["funktionen"]["liste"]:
            funcs_by_file[func["datei"]] += 1

        report = f"""# 📋 CODE-INVENTUR REPORT

## Projekt-Übersicht
- **Projekt:** {self.inventory["projekt"]}
- **Timestamp:** {self.inventory["timestamp"]}
- **Root:** `{self.inventory["root_dir"]}`
- **Analysierte Dateien:** {self.inventory["dateien"]["total"]}

---

## Lines of Code (LOC)

| Metrik | Anzahl |
|--------|--------|
| **Gesamt** | {self.inventory["lines_of_code"]["total"]:,} |
| **Produktiv** | {self.inventory["lines_of_code"]["produktiv"]:,} |
| **Kommentare** | {self.inventory["lines_of_code"]["kommentare"]:,} |
| **Leerzeilen** | {self.inventory["lines_of_code"]["leerzeilen"]:,} |

---

## Funktionen ({self.inventory["funktionen"]["total"]:,} total)

**Top 10 Dateien nach Funktionsanzahl:**

| Datei | Funktionen |
|-------|------------|
"""

        # Top Dateien nach Funktionsanzahl
        top_func_files = sorted(funcs_by_file.items(), key=lambda x: x[1], reverse=True)[:10]
        for filepath, count in top_func_files:
            report += f"| `{filepath}` | {count} |\n"

        report += f"""
---

## Klassen ({self.inventory["klassen"]["total"]:,} total)

**Top 10 Klassen nach Methodenanzahl:**

| Klasse | Datei | Methoden | LOC |
|--------|-------|----------|-----|
"""

        # Top Klassen nach Methodenanzahl
        sorted_classes = sorted(
            self.inventory["klassen"]["liste"],
            key=lambda x: x["methoden_count"],
            reverse=True
        )[:10]

        for cls in sorted_classes:
            zeilen = cls["zeilen"]
            loc = zeilen[1] - zeilen[0] + 1 if len(zeilen) == 2 else "?"
            report += f"| `{cls['name']}` | `{cls['datei']}` | {cls['methoden_count']} | {loc} |\n"

        report += f"""
---

## UI-Komponenten ({self.inventory["ui_komponenten"]["total"]:,} total)

**Typ-Verteilung:**

| UI-Typ | Anzahl |
|--------|--------|
"""

        # UI-Komponenten nach Typ
        ui_types = defaultdict(int)
        for ui in self.inventory["ui_komponenten"]["liste"]:
            ui_types[ui["typ"]] += 1

        for ui_type, count in sorted(ui_types.items(), key=lambda x: x[1], reverse=True):
            report += f"| `{ui_type}` | {count} |\n"

        report += f"""
---

## Event-Handler ({self.inventory["event_handler"]["total"]:,} total)

**Beispiele:**

| Event-Handler | Datei | Zeilen |
|---------------|-------|--------|
"""

        # Erste 15 Event-Handler
        for eh in self.inventory["event_handler"]["liste"][:15]:
            zeilen = f"{eh['zeilen'][0]}-{eh['zeilen'][1]}"
            report += f"| `{eh['name']}()` | `{eh['datei']}` | {zeilen} |\n"

        if len(self.inventory["event_handler"]["liste"]) > 15:
            report += f"\n*... und {len(self.inventory['event_handler']['liste']) - 15} weitere*\n"

        report += f"""
---

## ⚠️ DATEIEN ÜBER 600 LOC (SPLITTING ERFORDERLICH!)

**Anzahl:** {self.inventory["dateien_ueber_600_loc"]["total"]}

| # | Datei | LOC (produktiv) | Funktionen | Klassen | Empfehlung |
|---|-------|-----------------|------------|---------|------------|
"""

        for idx, file_info in enumerate(self.inventory["dateien_ueber_600_loc"]["liste"], 1):
            report += f"| {idx} | `{file_info['datei']}` | **{file_info['loc_produktiv']}** | {file_info['funktionen_count']} | {file_info['klassen_count']} | ⚠️ Splitting nötig |\n"

        report += f"""
---

## Top 20 Größte Dateien

| # | Datei | LOC (produktiv) | LOC (total) |
|---|-------|-----------------|-------------|
"""

        for idx, file_info in enumerate(top_20_files, 1):
            marker = "⚠️ " if file_info["loc_produktiv"] > 600 else ""
            report += f"| {idx} | {marker}`{file_info['datei']}` | **{file_info['loc_produktiv']}** | {file_info['loc']} |\n"

        report += f"""
---

## API-Endpoints ({self.inventory["api_endpoints"]["total"]:,} total)

**Gefundene Endpoint-Patterns:**

| Pattern | Datei | Zeile |
|---------|-------|-------|
"""

        for ep in self.inventory["api_endpoints"]["liste"][:20]:
            report += f"| `{ep['pattern']}` | `{ep['datei']}` | {ep['zeile']} |\n"

        if len(self.inventory["api_endpoints"]["liste"]) > 20:
            report += f"\n*... und {len(self.inventory['api_endpoints']['liste']) - 20} weitere*\n"

        report += """
---

## Zusammenfassung

✅ Inventur erfolgreich abgeschlossen!

**Nächste Schritte:**
1. ✅ Phase 1 abgeschlossen: Inventur erstellt
2. ⏭️ Phase 2: Analyse starten (Dead Code, Duplikate, Komplexität)
3. ⏸️ Phase 3: Warten auf Bestätigung vor Refactoring
4. ⏸️ Phase 4: Verifikation nach Refactoring

---

*Report generiert am {self.inventory["timestamp"]}*
"""

        # Schreibe Report
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 Markdown-Report gespeichert: {output_file}")


def main():
    """Hauptfunktion"""
    inventory = CodeInventory(root_dir=".")

    # Scanne Projekt
    inventory.scan_project(include_tests=True)

    # Speichere JSON
    inventory.save_json("code_inventory.json")

    # Generiere Markdown-Report
    inventory.generate_markdown_report("CODE_INVENTORY_REPORT.md")

    print("\n" + "="*60)
    print("✅ PHASE 1 ABGESCHLOSSEN: Vollständige Inventur erstellt")
    print("="*60)
    print(f"\n📊 Ergebnisse:")
    print(f"   - Dateien: {inventory.inventory['dateien']['total']}")
    print(f"   - Funktionen: {inventory.inventory['funktionen']['total']:,}")
    print(f"   - Klassen: {inventory.inventory['klassen']['total']:,}")
    print(f"   - LOC (produktiv): {inventory.inventory['lines_of_code']['produktiv']:,}")
    print(f"   - Dateien >600 LOC: {inventory.inventory['dateien_ueber_600_loc']['total']} ⚠️")
    print(f"\n📁 Ausgabedateien:")
    print(f"   - code_inventory.json")
    print(f"   - CODE_INVENTORY_REPORT.md")
    print("\n⏭️  Bereit für Phase 2: Analyse")


if __name__ == "__main__":
    main()
