#!/usr/bin/env python3
"""
Code Analysis Script für OrderPilot-AI - Phase 2
Analysiert Dead Code, Duplikate und Komplexität
"""

import ast
import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict
import re


class CodeAnalyzer:
    """Analysiert Code auf Dead Code, Duplikate und Komplexität"""

    def __init__(self, inventory_file: str = "code_inventory.json"):
        """Lädt Inventur-Daten"""
        with open(inventory_file, 'r', encoding='utf-8') as f:
            self.inventory = json.load(f)

        self.root_dir = Path(self.inventory["root_dir"])

        self.analysis = {
            "projekt": self.inventory["projekt"],
            "timestamp": datetime.now().isoformat(),
            "dead_code": {
                "unused_functions": {
                    "sicher": [],  # Sicher zu entfernen
                    "unsicher": []  # Manuell prüfen
                },
                "unused_imports": [],
                "unreachable_code": []
            },
            "duplikate": {
                "exact": [],  # 100% identisch
                "structural": []  # Strukturell ähnlich
            },
            "komplexitaet": {
                "kritische_funktionen": [],  # Komplexität > 20
                "hohe_funktionen": [],  # Komplexität 11-20
                "verschachtelte_funktionen": []  # Nesting > 6
            },
            "statistiken": {
                "total_funktionen": self.inventory["funktionen"]["total"],
                "total_imports": self.inventory["imports"]["total"],
                "dead_code_kandidaten": 0,
                "duplikat_bloecke": 0,
                "komplexe_funktionen": 0
            }
        }

        # False-Positive Patterns
        self.false_positive_patterns = {
            "framework_hooks": [
                r'^__\w+__$',  # Magic methods
                r'^on_\w+',  # Event handlers
                r'^slot_\w+',  # Qt Slots
                r'^handle_\w+',  # Handlers
                r'^_on_\w+',  # Private event handlers
            ],
            "serialization": [
                r'^to_\w+',  # Serialization
                r'^from_\w+',  # Deserialization
                r'^serialize',
                r'^deserialize'
            ],
            "factory": [
                r'^create_\w+',  # Factory methods
                r'^make_\w+',  # Factory methods
                r'^build_\w+',  # Builder methods
            ],
            "test": [
                r'^test_',  # Test functions
                r'^setup',
                r'^teardown'
            ]
        }

    def is_false_positive(self, func_name: str) -> bool:
        """Prüft ob Funktionsname ein False-Positive sein könnte"""
        for category, patterns in self.false_positive_patterns.items():
            for pattern in patterns:
                if re.match(pattern, func_name):
                    return True
        return False

    def analyze_unused_functions(self):
        """Findet ungenutzte Funktionen"""
        print("🔍 Analysiere ungenutzte Funktionen...")

        # Erstelle Referenz-Map: Funktionsname -> Vorkommen
        function_refs = defaultdict(int)
        function_defs = {}  # name -> details

        # Sammle alle Funktionsdefinitionen
        for func in self.inventory["funktionen"]["liste"]:
            func_name = func["name"]
            function_defs[func_name] = func

        # Durchsuche alle Dateien nach Referenzen
        all_files = [self.root_dir / f for f in self.inventory["dateien"]["liste"]]

        for filepath in all_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Zähle Funktionsaufrufe
                for func_name in function_defs.keys():
                    # Suche nach Funktionsaufrufen (nicht Definitionen)
                    # Muster: func_name(
                    pattern = rf'\b{re.escape(func_name)}\s*\('
                    matches = re.findall(pattern, content)
                    function_refs[func_name] += len(matches)

            except Exception as e:
                print(f"⚠️  Fehler beim Lesen von {filepath}: {e}")

        # Identifiziere ungenutzte Funktionen
        for func_name, details in function_defs.items():
            refs = function_refs[func_name]

            # Funktionsdefinition selbst zählt als 1 Referenz
            # Wenn nur 1 Referenz -> ungenutzt
            if refs <= 1:
                # Prüfe auf False-Positives
                if self.is_false_positive(func_name):
                    self.analysis["dead_code"]["unused_functions"]["unsicher"].append({
                        "funktion": func_name,
                        "datei": details["datei"],
                        "zeilen": details["zeilen"],
                        "signatur": details["signatur"],
                        "referenzen": refs,
                        "warnung": "Könnte Framework-Hook/Event-Handler sein"
                    })
                elif func_name.startswith('_') and not func_name.startswith('__'):
                    # Private Funktionen
                    self.analysis["dead_code"]["unused_functions"]["unsicher"].append({
                        "funktion": func_name,
                        "datei": details["datei"],
                        "zeilen": details["zeilen"],
                        "signatur": details["signatur"],
                        "referenzen": refs,
                        "warnung": "Private Funktion - könnte via Reflection aufgerufen werden"
                    })
                else:
                    # Sicher ungenutzt (öffentliche Funktion ohne Referenzen)
                    self.analysis["dead_code"]["unused_functions"]["sicher"].append({
                        "funktion": func_name,
                        "datei": details["datei"],
                        "zeilen": details["zeilen"],
                        "signatur": details["signatur"],
                        "referenzen": refs
                    })

        sicher_count = len(self.analysis["dead_code"]["unused_functions"]["sicher"])
        unsicher_count = len(self.analysis["dead_code"]["unused_functions"]["unsicher"])
        print(f"  ✅ Gefunden: {sicher_count} sichere, {unsicher_count} unsichere Kandidaten")

    def analyze_unused_imports(self):
        """Findet ungenutzte Imports"""
        print("🔍 Analysiere ungenutzte Imports...")

        # Gruppiere Imports nach Datei
        imports_by_file = defaultdict(list)
        for imp in self.inventory["imports"]["liste"]:
            imports_by_file[imp.get("from_module", imp["module"])].append(imp)

        # Prüfe für jede Datei
        all_files = [self.root_dir / f for f in self.inventory["dateien"]["liste"]]

        unused_imports = []

        for filepath in all_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Parse AST
                try:
                    tree = ast.parse(content, filename=str(filepath))
                except SyntaxError:
                    continue

                # Sammle alle Imports in dieser Datei
                file_imports = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_imports.append({
                                "module": alias.name,
                                "alias": alias.asname or alias.name,
                                "line": node.lineno
                            })
                    elif isinstance(node, ast.ImportFrom):
                        module = node.module or ""
                        for alias in node.names:
                            file_imports.append({
                                "module": f"{module}.{alias.name}" if module else alias.name,
                                "alias": alias.asname or alias.name,
                                "from_module": module,
                                "line": node.lineno
                            })

                # Prüfe ob Import verwendet wird
                for imp in file_imports:
                    alias = imp["alias"]

                    # Zähle Vorkommen (außer Import-Zeile)
                    lines = content.split('\n')
                    usage_count = 0

                    for line_idx, line in enumerate(lines, 1):
                        if line_idx == imp["line"]:
                            continue  # Skip import line

                        # Suche nach Verwendung
                        # Muster: alias. oder alias( oder alias[
                        pattern = rf'\b{re.escape(alias)}\s*[\.\(\[]'
                        if re.search(pattern, line):
                            usage_count += 1

                    if usage_count == 0:
                        unused_imports.append({
                            "import": imp["module"],
                            "alias": alias,
                            "datei": str(filepath.relative_to(self.root_dir)),
                            "zeile": imp["line"]
                        })

            except Exception as e:
                print(f"⚠️  Fehler bei {filepath}: {e}")

        self.analysis["dead_code"]["unused_imports"] = unused_imports
        print(f"  ✅ Gefunden: {len(unused_imports)} ungenutzte Imports")

    def calculate_cyclomatic_complexity(self, node: ast.AST) -> int:
        """Berechnet McCabe Cyclomatic Complexity"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points erhöhen Komplexität
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.And, ast.Or)):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1

        return complexity

    def calculate_nesting_depth(self, node: ast.AST, current_depth: int = 0) -> int:
        """Berechnet maximale Verschachtelungstiefe"""
        max_depth = current_depth

        for child in ast.iter_child_nodes(node):
            # Erhöhe Tiefe bei Kontrollstrukturen
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.With, ast.Try)):
                child_depth = self.calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self.calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)

        return max_depth

    def analyze_complexity(self):
        """Analysiert Code-Komplexität"""
        print("🔍 Analysiere Code-Komplexität...")

        all_files = [self.root_dir / f for f in self.inventory["dateien"]["liste"]]

        for filepath in all_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                try:
                    tree = ast.parse(content, filename=str(filepath))
                except SyntaxError:
                    continue

                # Analysiere jede Funktion
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_name = node.name
                        complexity = self.calculate_cyclomatic_complexity(node)
                        nesting = self.calculate_nesting_depth(node)
                        loc = (node.end_lineno or node.lineno) - node.lineno + 1

                        func_info = {
                            "funktion": func_name,
                            "datei": str(filepath.relative_to(self.root_dir)),
                            "zeilen": [node.lineno, node.end_lineno or node.lineno],
                            "komplexitaet": complexity,
                            "verschachtelung": nesting,
                            "loc": loc
                        }

                        # Kategorisiere
                        if complexity > 20:
                            self.analysis["komplexitaet"]["kritische_funktionen"].append(func_info)
                        elif complexity > 10:
                            self.analysis["komplexitaet"]["hohe_funktionen"].append(func_info)

                        if nesting > 6:
                            self.analysis["komplexitaet"]["verschachtelte_funktionen"].append(func_info)

            except Exception as e:
                print(f"⚠️  Fehler bei {filepath}: {e}")

        kritisch = len(self.analysis["komplexitaet"]["kritische_funktionen"])
        hoch = len(self.analysis["komplexitaet"]["hohe_funktionen"])
        verschachtelt = len(self.analysis["komplexitaet"]["verschachtelte_funktionen"])

        print(f"  ✅ Gefunden: {kritisch} kritische, {hoch} hohe, {verschachtelt} verschachtelte Funktionen")

    def find_duplicates(self):
        """Findet Duplikate (exakt und strukturell)"""
        print("🔍 Suche nach Duplikaten...")

        # Code-Blöcke hashen
        code_blocks = defaultdict(list)  # hash -> [locations]

        all_files = [self.root_dir / f for f in self.inventory["dateien"]["liste"]]

        for filepath in all_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Sliding window für Code-Blöcke (min 5 Zeilen)
                min_lines = 5

                for i in range(len(lines) - min_lines + 1):
                    block = ''.join(lines[i:i+min_lines])

                    # Normalisiere (entferne Whitespace, Kommentare)
                    normalized = self._normalize_code(block)

                    if len(normalized.strip()) < 20:  # Zu klein
                        continue

                    # Hash
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()

                    code_blocks[block_hash].append({
                        "datei": str(filepath.relative_to(self.root_dir)),
                        "zeilen": [i+1, i+min_lines],
                        "code": block[:200]  # Erste 200 Zeichen als Vorschau
                    })

            except Exception as e:
                print(f"⚠️  Fehler bei {filepath}: {e}")

        # Identifiziere Duplikate
        for block_hash, locations in code_blocks.items():
            if len(locations) > 1:
                # Mehrfach vorkommender Code-Block
                self.analysis["duplikate"]["exact"].append({
                    "hash": block_hash,
                    "vorkommen": len(locations),
                    "locations": locations,
                    "zeilen_gespart": (locations[0]["zeilen"][1] - locations[0]["zeilen"][0]) * (len(locations) - 1)
                })

        print(f"  ✅ Gefunden: {len(self.analysis['duplikate']['exact'])} Duplikat-Gruppen")

    def _normalize_code(self, code: str) -> str:
        """Normalisiert Code (entfernt Whitespace, Kommentare)"""
        # Entferne Kommentare
        code = re.sub(r'#.*$', '', code, flags=re.MULTILINE)

        # Entferne Leerzeilen
        code = re.sub(r'\n\s*\n', '\n', code)

        # Entferne führende/trailing Whitespace
        lines = [line.strip() for line in code.split('\n')]
        code = '\n'.join(lines)

        return code

    def run_analysis(self):
        """Führt vollständige Analyse durch"""
        print("🚀 Starte Phase 2: Code-Analyse")
        print("="*60)

        # 1. Dead Code
        self.analyze_unused_functions()
        self.analyze_unused_imports()

        # 2. Komplexität
        self.analyze_complexity()

        # 3. Duplikate
        self.find_duplicates()

        # Statistiken aktualisieren
        self.analysis["statistiken"]["dead_code_kandidaten"] = (
            len(self.analysis["dead_code"]["unused_functions"]["sicher"]) +
            len(self.analysis["dead_code"]["unused_functions"]["unsicher"]) +
            len(self.analysis["dead_code"]["unused_imports"])
        )
        self.analysis["statistiken"]["duplikat_bloecke"] = len(self.analysis["duplikate"]["exact"])
        self.analysis["statistiken"]["komplexe_funktionen"] = (
            len(self.analysis["komplexitaet"]["kritische_funktionen"]) +
            len(self.analysis["komplexitaet"]["hohe_funktionen"])
        )

        print("\n" + "="*60)
        print("✅ PHASE 2 ABGESCHLOSSEN")
        print("="*60)

    def save_json(self, output_file: str = "code_analysis.json"):
        """Speichert Analyse als JSON"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis, f, indent=2, ensure_ascii=False)
        print(f"💾 JSON gespeichert: {output_file}")

    def generate_markdown_report(self, output_file: str = "CODE_ANALYSIS_REPORT.md"):
        """Generiert Markdown-Analyse-Report"""

        report = f"""# 🔍 CODE-ANALYSE REPORT (PHASE 2)

## Projekt-Übersicht
- **Projekt:** {self.analysis["projekt"]}
- **Timestamp:** {self.analysis["timestamp"]}
- **Total Funktionen:** {self.analysis["statistiken"]["total_funktionen"]:,}

---

## 1. DEAD CODE (Kandidaten zur Entfernung)

### ✅ Sicher zu entfernen ({len(self.analysis["dead_code"]["unused_functions"]["sicher"])} Funktionen)

**Funktionen ohne externe Referenzen:**

| # | Funktion | Datei | Zeilen | Signatur |
|---|----------|-------|--------|----------|
"""

        # Top 20 sichere Dead-Code-Kandidaten
        for idx, func in enumerate(self.analysis["dead_code"]["unused_functions"]["sicher"][:20], 1):
            zeilen = f"{func['zeilen'][0]}-{func['zeilen'][1]}"
            report += f"| {idx} | `{func['funktion']}()` | `{func['datei']}` | {zeilen} | `{func['signatur'][:60]}` |\n"

        if len(self.analysis["dead_code"]["unused_functions"]["sicher"]) > 20:
            report += f"\n*... und {len(self.analysis['dead_code']['unused_functions']['sicher']) - 20} weitere*\n"

        report += f"""
---

### ⚠️ Manuell prüfen ({len(self.analysis["dead_code"]["unused_functions"]["unsicher"])} Funktionen)

**Diese Funktionen könnten false-positives sein (Event-Handler, Framework-Hooks, etc.):**

| # | Funktion | Datei | Zeilen | Warnung |
|---|----------|-------|--------|---------|
"""

        for idx, func in enumerate(self.analysis["dead_code"]["unused_functions"]["unsicher"][:20], 1):
            zeilen = f"{func['zeilen'][0]}-{func['zeilen'][1]}"
            report += f"| {idx} | `{func['funktion']}()` | `{func['datei']}` | {zeilen} | {func['warnung']} |\n"

        if len(self.analysis["dead_code"]["unused_functions"]["unsicher"]) > 20:
            report += f"\n*... und {len(self.analysis['dead_code']['unused_functions']['unsicher']) - 20} weitere*\n"

        report += f"""
---

### 📦 Ungenutzte Imports ({len(self.analysis["dead_code"]["unused_imports"])} total)

| # | Import | Datei | Zeile |
|---|--------|-------|-------|
"""

        for idx, imp in enumerate(self.analysis["dead_code"]["unused_imports"][:20], 1):
            report += f"| {idx} | `{imp['import']}` | `{imp['datei']}` | {imp['zeile']} |\n"

        if len(self.analysis["dead_code"]["unused_imports"]) > 20:
            report += f"\n*... und {len(self.analysis['dead_code']['unused_imports']) - 20} weitere*\n"

        report += """
---

## 2. DUPLIKATE

### Exakte Duplikate

"""

        if not self.analysis["duplikate"]["exact"]:
            report += "*Keine exakten Duplikate gefunden (Min. 5 Zeilen)*\n"
        else:
            report += f"**Gefunden: {len(self.analysis['duplikate']['exact'])} Duplikat-Gruppen**\n\n"

            for idx, dup in enumerate(self.analysis["duplikate"]["exact"][:10], 1):
                report += f"""
### Duplikat {idx}
- **Vorkommen:** {dup['vorkommen']}x
- **Zeilen gespart:** {dup['zeilen_gespart']} (bei Konsolidierung)

**Locations:**
"""
                for loc in dup["locations"]:
                    zeilen = f"{loc['zeilen'][0]}-{loc['zeilen'][1]}"
                    report += f"- `{loc['datei']}` (Zeilen {zeilen})\n"

                report += f"\n**Code-Vorschau:**\n```python\n{dup['locations'][0]['code']}\n```\n\n"

        report += """
---

## 3. KOMPLEXITÄT

"""

        # Kritische Funktionen
        kritische = self.analysis["komplexitaet"]["kritische_funktionen"]
        if kritische:
            report += f"""
### ⚠️ KRITISCHE Funktionen (Komplexität > 20)

**Anzahl:** {len(kritische)}

| # | Funktion | Datei | Komplexität | Verschachtelung | LOC | Empfehlung |
|---|----------|-------|-------------|-----------------|-----|------------|
"""

            # Sortiere nach Komplexität
            sorted_kritisch = sorted(kritische, key=lambda x: x["komplexitaet"], reverse=True)

            for idx, func in enumerate(sorted_kritisch[:20], 1):
                zeilen = f"{func['zeilen'][0]}-{func['zeilen'][1]}"
                report += f"| {idx} | `{func['funktion']}()` | `{func['datei']}` | **{func['komplexitaet']}** | {func['verschachtelung']} | {func['loc']} | In 3-5 Funktionen splitten |\n"

            if len(kritische) > 20:
                report += f"\n*... und {len(kritische) - 20} weitere*\n"

        else:
            report += "✅ Keine kritischen Funktionen (Komplexität > 20) gefunden!\n"

        # Hohe Komplexität
        hohe = self.analysis["komplexitaet"]["hohe_funktionen"]
        if hohe:
            report += f"""
---

### ⚠️ HOHE Komplexität (11-20)

**Anzahl:** {len(hohe)}

| # | Funktion | Datei | Komplexität | Verschachtelung | LOC |
|---|----------|-------|-------------|-----------------|-----|
"""

            sorted_hoch = sorted(hohe, key=lambda x: x["komplexitaet"], reverse=True)

            for idx, func in enumerate(sorted_hoch[:20], 1):
                report += f"| {idx} | `{func['funktion']}()` | `{func['datei']}` | **{func['komplexitaet']}** | {func['verschachtelung']} | {func['loc']} |\n"

            if len(hohe) > 20:
                report += f"\n*... und {len(hohe) - 20} weitere*\n"

        # Verschachtelt
        verschachtelt = self.analysis["komplexitaet"]["verschachtelte_funktionen"]
        if verschachtelt:
            report += f"""
---

### 🔁 Stark verschachtelte Funktionen (Nesting > 6)

**Anzahl:** {len(verschachtelt)}

| # | Funktion | Datei | Verschachtelung | Komplexität | LOC |
|---|----------|-------|-----------------|-------------|-----|
"""

            sorted_verschachtelt = sorted(verschachtelt, key=lambda x: x["verschachtelung"], reverse=True)

            for idx, func in enumerate(sorted_verschachtelt[:20], 1):
                report += f"| {idx} | `{func['funktion']}()` | `{func['datei']}` | **{func['verschachtelung']}** | {func['komplexitaet']} | {func['loc']} |\n"

            if len(verschachtelt) > 20:
                report += f"\n*... und {len(verschachtelt) - 20} weitere*\n"

        report += f"""
---

## 4. ZUSAMMENFASSUNG & EMPFEHLUNGEN

### Statistiken

| Kategorie | Anzahl | Status |
|-----------|--------|--------|
| **Dead Code (sicher)** | {len(self.analysis["dead_code"]["unused_functions"]["sicher"])} | ⚠️ Zu entfernen |
| **Dead Code (unsicher)** | {len(self.analysis["dead_code"]["unused_functions"]["unsicher"])} | 🔍 Zu prüfen |
| **Ungenutzte Imports** | {len(self.analysis["dead_code"]["unused_imports"])} | 🧹 Zu entfernen |
| **Duplikat-Gruppen** | {len(self.analysis["duplikate"]["exact"])} | ♻️ Zu konsolidieren |
| **Kritische Komplexität** | {len(kritische)} | ⚠️ Zu refactoren |
| **Hohe Komplexität** | {len(hohe)} | 🔍 Zu überwachen |
| **Stark verschachtelt** | {len(verschachtelt)} | 🔁 Zu vereinfachen |

---

### Empfohlene Aktionen (Priorität)

1. **HOCH: Dead Code entfernen**
   - {len(self.analysis["dead_code"]["unused_functions"]["sicher"])} ungenutzte Funktionen löschen
   - {len(self.analysis["dead_code"]["unused_imports"])} ungenutzte Imports entfernen

2. **HOCH: Komplexität reduzieren**
   - {len(kritische)} kritische Funktionen in kleinere Funktionen splitten

3. **MITTEL: Duplikate konsolidieren**
   - {len(self.analysis["duplikate"]["exact"])} Duplikat-Gruppen zu gemeinsamen Funktionen extrahieren

4. **NIEDRIG: Verschachtelung reduzieren**
   - {len(verschachtelt)} Funktionen mit zu tiefer Verschachtelung vereinfachen

---

## ⏸️ WARTE AUF BESTÄTIGUNG

**Vor Phase 3 (Refactoring):**
- Prüfe die Analyse-Ergebnisse
- Bestätige welche Änderungen durchgeführt werden sollen
- Erstelle Backup (git commit)

**WICHTIG:** Keine Änderungen ohne explizite Bestätigung!

---

*Report generiert am {self.analysis["timestamp"]}*
"""

        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

        print(f"📄 Markdown-Report gespeichert: {output_file}")


def main():
    """Hauptfunktion"""
    analyzer = CodeAnalyzer(inventory_file="code_inventory.json")

    # Führe Analyse durch
    analyzer.run_analysis()

    # Speichere Ergebnisse
    analyzer.save_json("code_analysis.json")
    analyzer.generate_markdown_report("CODE_ANALYSIS_REPORT.md")

    print("\n" + "="*60)
    print("📊 PHASE 2 ABGESCHLOSSEN: Analyse-Report erstellt")
    print("="*60)
    print(f"\n📈 Ergebnisse:")
    print(f"   - Dead Code (sicher): {len(analyzer.analysis['dead_code']['unused_functions']['sicher'])}")
    print(f"   - Dead Code (unsicher): {len(analyzer.analysis['dead_code']['unused_functions']['unsicher'])}")
    print(f"   - Ungenutzte Imports: {len(analyzer.analysis['dead_code']['unused_imports'])}")
    print(f"   - Duplikate: {len(analyzer.analysis['duplikate']['exact'])} Gruppen")
    print(f"   - Kritische Komplexität: {len(analyzer.analysis['komplexitaet']['kritische_funktionen'])}")
    print(f"   - Hohe Komplexität: {len(analyzer.analysis['komplexitaet']['hohe_funktionen'])}")
    print(f"\n📁 Ausgabedateien:")
    print(f"   - code_analysis.json")
    print(f"   - CODE_ANALYSIS_REPORT.md")
    print("\n⏸️  Warte auf Bestätigung vor Phase 3 (Refactoring)")


if __name__ == "__main__":
    main()
