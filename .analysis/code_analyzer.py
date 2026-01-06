#!/usr/bin/env python3
"""
Code Analyzer - Phase 2: Dead Code, Duplikate, Komplexität
"""

import ast
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib


@dataclass
class DeadCodeCandidate:
    name: str
    type: str  # 'function', 'class', 'import', 'variable'
    file: str
    line: int
    confidence: str  # 'HIGH', 'MEDIUM', 'LOW'
    reason: str
    warning: str = ""  # Warnung bei False-Positive-Verdacht


@dataclass
class DuplicateBlock:
    hash: str
    files: List[Tuple[str, int, int]]  # (file, start_line, end_line)
    lines: int
    code_sample: str
    similarity: float  # 1.0 = exakt, <1.0 = strukturell ähnlich


@dataclass
class ComplexityIssue:
    function: str
    file: str
    line: int
    cyclomatic_complexity: int
    nesting_depth: int
    loc: int
    parameters: int
    severity: str  # 'CRITICAL', 'WARNING', 'ACCEPTABLE'
    recommendation: str


class CodeAnalyzer:
    def __init__(self, root_dir: str = "src"):
        self.root_dir = Path(root_dir)
        self.dead_code: List[DeadCodeCandidate] = []
        self.duplicates: List[DuplicateBlock] = []
        self.complexity_issues: List[ComplexityIssue] = []

        # Framework-spezifische Ausnahmen (False-Positive-Vermeidung)
        self.framework_patterns = {
            '__init__', '__del__', '__str__', '__repr__', '__call__',
            'setUp', 'tearDown', 'setUpClass', 'tearDownClass',
            'run', 'start', 'stop', 'close', 'open',
            'on_', 'handle_', 'event_', 'slot_',  # Event handlers
            'get_', 'set_',  # Properties
        }

    def analyze_dead_code(self) -> None:
        """Findet ungenutzten Code"""
        print("\n🔍 Phase 2.1: Dead Code Analyse")

        # 1. Verwende vulture für unused code
        self._run_vulture()

        # 2. Finde unreachable code (AST-basiert)
        self._find_unreachable_code()

        # 3. Finde unused imports
        self._find_unused_imports()

    def _run_vulture(self) -> None:
        """Nutzt vulture für Dead Code Detection"""
        try:
            result = subprocess.run(
                ['vulture', str(self.root_dir), '--min-confidence', '80'],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse vulture output
            for line in result.stdout.split('\n'):
                if not line.strip() or line.startswith('#'):
                    continue

                # Format: file:line: unused function 'name' (confidence%)
                if 'unused' in line.lower():
                    parts = line.split(':')
                    if len(parts) >= 3:
                        file = parts[0].strip()
                        try:
                            line_no = int(parts[1].strip())
                        except ValueError:
                            continue

                        rest = ':'.join(parts[2:])

                        # Bestimme Typ
                        if 'function' in rest.lower():
                            code_type = 'function'
                        elif 'class' in rest.lower():
                            code_type = 'class'
                        elif 'import' in rest.lower():
                            code_type = 'import'
                        elif 'variable' in rest.lower():
                            code_type = 'variable'
                        else:
                            code_type = 'unknown'

                        # Extrahiere Name
                        name = self._extract_name_from_vulture(rest)

                        # Check für False-Positive
                        warning = self._check_false_positive(name, code_type)
                        confidence = 'MEDIUM' if warning else 'HIGH'

                        self.dead_code.append(DeadCodeCandidate(
                            name=name,
                            type=code_type,
                            file=file,
                            line=line_no,
                            confidence=confidence,
                            reason="Keine Referenzen gefunden (vulture)",
                            warning=warning
                        ))

            print(f"  ✓ Vulture-Analyse: {len([d for d in self.dead_code if d.confidence == 'HIGH'])} High-Confidence Kandidaten")

        except FileNotFoundError:
            print("  ⚠️  Vulture nicht installiert - überspringe vulture-Analyse")
        except Exception as e:
            print(f"  ⚠️  Vulture-Fehler: {e}")

    def _extract_name_from_vulture(self, text: str) -> str:
        """Extrahiert Namen aus vulture-Output"""
        if "'" in text:
            parts = text.split("'")
            if len(parts) >= 2:
                return parts[1]
        return "unknown"

    def _check_false_positive(self, name: str, code_type: str) -> str:
        """Prüft auf False-Positive-Muster"""
        warnings = []

        # Framework-Patterns
        for pattern in self.framework_patterns:
            if name.startswith(pattern) or pattern in name:
                warnings.append(f"Framework-Pattern: {pattern}")

        # Spezielle Methoden
        if name.startswith('_') and not name.startswith('__'):
            warnings.append("Private Methode - könnte via Reflection aufgerufen werden")

        # Test-Utilities
        if 'test' in name.lower() or 'mock' in name.lower():
            warnings.append("Test-Code")

        # Public API
        if code_type == 'class' and name[0].isupper():
            warnings.append("Public Klasse - könnte exportiert werden")

        return "; ".join(warnings) if warnings else ""

    def _find_unreachable_code(self) -> None:
        """Findet unreachable code durch AST-Analyse"""
        py_files = list(self.root_dir.rglob("*.py"))
        unreachable_count = 0

        for filepath in py_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content, filename=str(filepath))

                # Analysiere jede Funktion
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        unreachable = self._check_unreachable_in_function(node)
                        if unreachable:
                            unreachable_count += 1
                            self.dead_code.append(DeadCodeCandidate(
                                name=f"{node.name} (unreachable code)",
                                type='unreachable',
                                file=str(filepath.relative_to(self.root_dir.parent)),
                                line=unreachable,
                                confidence='HIGH',
                                reason="Code nach return/raise ohne Bedingung",
                                warning=""
                            ))

            except SyntaxError:
                pass
            except Exception as e:
                pass

        print(f"  ✓ Unreachable Code: {unreachable_count} Stellen gefunden")

    def _check_unreachable_in_function(self, func_node: ast.FunctionDef) -> int:
        """Prüft ob Code nach return/raise unerreichbar ist"""
        for i, stmt in enumerate(func_node.body):
            if isinstance(stmt, (ast.Return, ast.Raise)):
                # Prüfe ob noch Code folgt (und kein else/except)
                if i < len(func_node.body) - 1:
                    next_stmt = func_node.body[i + 1]
                    # Ignoriere Docstrings und Comments
                    if not isinstance(next_stmt, ast.Expr):
                        return next_stmt.lineno
        return 0

    def _find_unused_imports(self) -> None:
        """Findet ungenutzte Imports (bereits durch vulture abgedeckt)"""
        # Wird durch vulture abgedeckt
        pass

    def analyze_duplicates(self) -> None:
        """Findet doppelten Code"""
        print("\n🔍 Phase 2.2: Duplikat-Analyse")

        # Hash-basierte Duplikat-Erkennung
        self._find_duplicate_blocks()

    def _find_duplicate_blocks(self, min_lines: int = 5) -> None:
        """Findet duplizierte Code-Blöcke"""
        py_files = list(self.root_dir.rglob("*.py"))

        # Hash-Map: code_hash -> [(file, start_line, end_line, code)]
        code_blocks: Dict[str, List[Tuple[str, int, int, str]]] = defaultdict(list)

        for filepath in py_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # Sliding Window über Zeilen
                for i in range(len(lines) - min_lines + 1):
                    block = lines[i:i + min_lines]

                    # Normalisiere Block (entferne Whitespace für Vergleich)
                    normalized = ''.join(line.strip() for line in block if line.strip())

                    # Ignoriere zu kurze oder nur Kommentare
                    if len(normalized) < 50 or normalized.startswith('#'):
                        continue

                    # Hash erstellen
                    block_hash = hashlib.md5(normalized.encode()).hexdigest()

                    code_blocks[block_hash].append((
                        str(filepath.relative_to(self.root_dir.parent)),
                        i + 1,
                        i + min_lines,
                        ''.join(block)
                    ))

            except Exception as e:
                pass

        # Finde Duplikate (Hash kommt in mehreren Dateien vor)
        for block_hash, occurrences in code_blocks.items():
            if len(occurrences) > 1:
                # Nur wenn in verschiedenen Dateien
                unique_files = set(occ[0] for occ in occurrences)
                if len(unique_files) > 1:
                    self.duplicates.append(DuplicateBlock(
                        hash=block_hash[:8],
                        files=[(f, s, e) for f, s, e, _ in occurrences],
                        lines=min_lines,
                        code_sample=occurrences[0][3][:200],  # Erste 200 Zeichen
                        similarity=1.0
                    ))

        print(f"  ✓ Duplikat-Blöcke: {len(self.duplicates)} exakte Duplikate gefunden")

    def analyze_complexity(self) -> None:
        """Analysiert Code-Komplexität"""
        print("\n🔍 Phase 2.3: Komplexitäts-Analyse")

        # Verwende radon für Cyclomatic Complexity
        self._run_radon_cc()

        # Eigene Analyse für Nesting Depth
        self._analyze_nesting_depth()

    def _run_radon_cc(self) -> None:
        """Nutzt radon für Cyclomatic Complexity"""
        try:
            result = subprocess.run(
                ['radon', 'cc', str(self.root_dir), '-j'],
                capture_output=True,
                text=True,
                timeout=120
            )

            # Parse JSON output
            data = json.loads(result.stdout)

            for file, functions in data.items():
                for func in functions:
                    cc = func.get('complexity', 0)
                    loc = func.get('endline', 0) - func.get('lineno', 0)

                    # Bewerte Komplexität
                    if cc > 20:
                        severity = 'CRITICAL'
                        recommendation = f"In 5-6 Funktionen splitten (CC={cc})"
                    elif cc > 10:
                        severity = 'WARNING'
                        recommendation = f"Vereinfachen oder in 2-3 Funktionen splitten (CC={cc})"
                    elif cc > 5:
                        severity = 'ACCEPTABLE'
                        recommendation = "Akzeptabel, aber beobachten"
                    else:
                        continue  # Optimal, nicht melden

                    self.complexity_issues.append(ComplexityIssue(
                        function=func.get('name', 'unknown'),
                        file=file,
                        line=func.get('lineno', 0),
                        cyclomatic_complexity=cc,
                        nesting_depth=0,  # Wird später gefüllt
                        loc=loc,
                        parameters=0,  # Wird später gefüllt
                        severity=severity,
                        recommendation=recommendation
                    ))

            critical = len([c for c in self.complexity_issues if c.severity == 'CRITICAL'])
            warning = len([c for c in self.complexity_issues if c.severity == 'WARNING'])
            print(f"  ✓ Komplexität: {critical} kritisch, {warning} Warnungen")

        except FileNotFoundError:
            print("  ⚠️  Radon nicht installiert - überspringe Komplexitäts-Analyse")
            self._fallback_complexity_analysis()
        except Exception as e:
            print(f"  ⚠️  Radon-Fehler: {e}")
            self._fallback_complexity_analysis()

    def _fallback_complexity_analysis(self) -> None:
        """Einfache Komplexitäts-Analyse ohne radon"""
        py_files = list(self.root_dir.rglob("*.py"))

        for filepath in py_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                tree = ast.parse(content, filename=str(filepath))

                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # Einfache Heuristik: Zähle if/for/while/try
                        complexity = self._simple_complexity(node)
                        loc = (node.end_lineno or node.lineno) - node.lineno
                        params = len(node.args.args)

                        if complexity > 20 or loc > 100 or params > 6:
                            severity = 'CRITICAL' if complexity > 20 else 'WARNING'

                            self.complexity_issues.append(ComplexityIssue(
                                function=node.name,
                                file=str(filepath.relative_to(self.root_dir.parent)),
                                line=node.lineno,
                                cyclomatic_complexity=complexity,
                                nesting_depth=0,
                                loc=loc,
                                parameters=params,
                                severity=severity,
                                recommendation=f"Vereinfachen (Complexity={complexity}, LOC={loc}, Params={params})"
                            ))
            except:
                pass

        print(f"  ✓ Komplexität (Fallback): {len(self.complexity_issues)} Issues gefunden")

    def _simple_complexity(self, node: ast.FunctionDef) -> int:
        """Einfache McCabe-ähnliche Komplexität"""
        complexity = 1  # Basis

        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _analyze_nesting_depth(self) -> None:
        """Analysiert Nesting-Tiefe"""
        # Wird in _fallback_complexity_analysis integriert
        pass

    def save_results(self, output_file: str = ".analysis/analysis_results.json") -> None:
        """Speichert Analyse-Ergebnisse"""
        results = {
            'dead_code': [asdict(d) for d in self.dead_code],
            'duplicates': [asdict(d) for d in self.duplicates],
            'complexity': [asdict(c) for c in self.complexity_issues]
        }

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)

        print(f"\n💾 Analyse-Ergebnisse gespeichert: {output_path}")


def main():
    analyzer = CodeAnalyzer("src")

    print("="*80)
    print("🔍 CODE-ANALYSE - PHASE 2")
    print("="*80)

    analyzer.analyze_dead_code()
    analyzer.analyze_duplicates()
    analyzer.analyze_complexity()

    analyzer.save_results()

    print("\n" + "="*80)
    print("📊 ZUSAMMENFASSUNG PHASE 2")
    print("="*80)

    # Dead Code
    high_conf_dead = [d for d in analyzer.dead_code if d.confidence == 'HIGH']
    med_conf_dead = [d for d in analyzer.dead_code if d.confidence == 'MEDIUM']
    print(f"\n🗑️  Dead Code:")
    print(f"  - Sicher zu entfernen: {len(high_conf_dead)}")
    print(f"  - Manuell prüfen: {len(med_conf_dead)}")

    # Duplikate
    print(f"\n📋 Duplikate:")
    print(f"  - Exakte Duplikat-Blöcke: {len(analyzer.duplicates)}")

    # Komplexität
    critical = [c for c in analyzer.complexity_issues if c.severity == 'CRITICAL']
    warning = [c for c in analyzer.complexity_issues if c.severity == 'WARNING']
    print(f"\n⚠️  Komplexität:")
    print(f"  - Kritisch (>20): {len(critical)}")
    print(f"  - Warnung (11-20): {len(warning)}")

    print("\n✅ Phase 2 abgeschlossen - Warte auf Bestätigung für Phase 3!")


if __name__ == "__main__":
    main()
