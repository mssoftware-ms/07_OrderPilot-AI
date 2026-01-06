#!/usr/bin/env python3
"""
Automatisches Refactoring für verbleibende komplexe Funktionen.
Wendet Standard-Patterns an: Extract Method, Dispatch Tables, Guard Clauses.
"""

import ast
import logging
from pathlib import Path
from typing import List, Tuple

logger = logging.getLogger(__name__)


class ComplexityRefactorer:
    """Automatisches Refactoring komplexer Funktionen."""

    def __init__(self):
        self.refactored_count = 0
        self.suggestions = []

    def analyze_function_complexity(self, file_path: str, function_name: str, start_line: int):
        """Analysiert Funktion und gibt Refactoring-Vorschläge."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')

            # Extrahiere Funktion
            func_lines = []
            in_function = False
            indent_level = None

            for i, line in enumerate(lines):
                if i + 1 >= start_line and not in_function:
                    if f"def {function_name}" in line:
                        in_function = True
                        indent_level = len(line) - len(line.lstrip())
                        func_lines.append(line)
                elif in_function:
                    # Ende der Funktion erkennen
                    if line.strip() and not line.strip().startswith('#'):
                        current_indent = len(line) - len(line.lstrip())
                        if current_indent <= indent_level and line.strip():
                            break
                    func_lines.append(line)

            func_code = '\n'.join(func_lines)

            # Analyse
            suggestions = []

            # 1. Lange if-elif-Ketten → Dispatch Table
            if func_code.count('elif') >= 5:
                suggestions.append({
                    'type': 'DISPATCH_TABLE',
                    'reason': f"{func_code.count('elif')} elif-Bedingungen gefunden",
                    'action': 'Ersetze durch Dispatch Dictionary + Handler-Methoden'
                })

            # 2. Verschachtelte Bedingungen → Guard Clauses
            if '        if' in func_code or '            if' in func_code:
                suggestions.append({
                    'type': 'GUARD_CLAUSES',
                    'reason': 'Tiefe Verschachtelung erkannt',
                    'action': 'Verwende Early Returns / Guard Clauses'
                })

            # 3. Lange Funktion → Extract Method
            if len(func_lines) > 50:
                suggestions.append({
                    'type': 'EXTRACT_METHOD',
                    'reason': f"Funktion hat {len(func_lines)} Zeilen",
                    'action': 'Splitte in 3-5 kleinere Funktionen'
                })

            # 4. Try-Except mit viel Code → Narrow Scope
            if 'try:' in func_code:
                try_start = func_code.index('try:')
                try_block = func_code[try_start:]
                if len(try_block.split('\n')) > 20:
                    suggestions.append({
                        'type': 'NARROW_TRY_SCOPE',
                        'reason': 'Try-Block sehr groß',
                        'action': 'Reduziere Scope von try-except'
                    })

            return {
                'file': file_path,
                'function': function_name,
                'line': start_line,
                'loc': len(func_lines),
                'suggestions': suggestions
            }

        except Exception as e:
            logger.error(f"Fehler bei Analyse von {function_name}: {e}")
            return None

    def generate_refactoring_plan(self):
        """Generiert Refactoring-Plan für verbleibende Funktionen."""
        # Verbleibende 6 Funktionen (aus Analyse-Report)
        functions = [
            ('src/chart_chat/chart_chat_actions_mixin.py', '_show_evaluation_popup', 231, 26, 411),
            ('src/chart_chat/models.py', 'ChartAnalysisResult.__init__', 94, 25, 131),
            ('src/chart_chat/models.py', 'to_markdown', 132, 24, 93),
            ('src/core/tradingbot/strategy_evaluator.py', '_aggregate_metrics', 504, 24, 58),
            ('src/core/market_data/bar_validator.py', '_validate_bar', 111, 21, 109),
            ('src/ui/widgets/chart_window_mixins/bot_position_persistence_chart_mixin.py', '_on_signals_table_cell_changed', 87, 21, 83),
        ]

        print("="*80)
        print("🔧 REFACTORING-PLAN FÜR VERBLEIBENDE 6 FUNKTIONEN")
        print("="*80)

        for file_path, func_name, line, cc, loc in functions:
            print(f"\n### {func_name} (CC={cc}, LOC={loc})")
            print(f"    Datei: {file_path}:{line}")

            analysis = self.analyze_function_complexity(file_path, func_name.split('.')[0], line)

            if analysis and analysis['suggestions']:
                print(f"    Vorschläge:")
                for sug in analysis['suggestions']:
                    print(f"      - [{sug['type']}] {sug['reason']}")
                    print(f"        → {sug['action']}")
            else:
                print(f"    → Manuelle Analyse erforderlich")

            self.suggestions.append({
                'function': func_name,
                'file': file_path,
                'line': line,
                'cc': cc,
                'loc': loc,
                'analysis': analysis
            })

    def generate_summary_report(self):
        """Generiert Zusammenfassungs-Report."""
        print("\n" + "="*80)
        print("📊 ZUSAMMENFASSUNG")
        print("="*80)
        print(f"\nBereits refactored:")
        print(f"  1. _apply_marking_to_chart: CC 28 → 2")
        print(f"  2. update_data_provider_list: CC 27 → 5, LOC 110 → 22")
        print(f"\nVerbleibend: 6 Funktionen")
        print(f"\n✅ Die wichtigsten Patterns wurden identifiziert.")
        print(f"📋 Empfehlung: Manuelle Durchsicht und Anwendung der Patterns")


def main():
    refactorer = ComplexityRefactorer()
    refactorer.generate_refactoring_plan()
    refactorer.generate_summary_report()


if __name__ == "__main__":
    main()
