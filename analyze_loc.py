#!/usr/bin/env python3
"""Analyze productive lines of code (excluding comments, docstrings, blank lines)."""

import ast
import os
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Tuple

@dataclass
class FileAnalysis:
    path: str
    total_lines: int
    productive_loc: int
    blank_lines: int
    comment_lines: int
    docstring_lines: int
    functions: List[str]
    classes: List[str]
    function_sizes: Dict[str, int]
    class_sizes: Dict[str, int]

def count_productive_loc(filepath: str) -> FileAnalysis:
    """Count productive lines of code in a Python file."""
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.split('\n')
    
    total_lines = len(lines)
    blank_lines = sum(1 for line in lines if not line.strip())
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    
    # Parse AST to find docstrings and function/class info
    docstring_lines = 0
    functions = []
    classes = []
    function_sizes = {}
    class_sizes = {}
    
    try:
        tree = ast.parse(content)
        
        # Find all docstrings
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
                if (node.body and isinstance(node.body[0], ast.Expr) and 
                    isinstance(node.body[0].value, ast.Constant) and 
                    isinstance(node.body[0].value.value, str)):
                    # Count docstring lines
                    docstring = node.body[0].value.value
                    docstring_lines += len(docstring.split('\n'))
        
        # Find functions and classes with sizes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                name = node.name
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    size = node.end_lineno - node.lineno + 1
                else:
                    size = 0
                functions.append(name)
                function_sizes[name] = size
            elif isinstance(node, ast.ClassDef):
                name = node.name
                if hasattr(node, 'end_lineno') and hasattr(node, 'lineno'):
                    size = node.end_lineno - node.lineno + 1
                else:
                    size = 0
                classes.append(name)
                class_sizes[name] = size
                
    except SyntaxError:
        pass
    
    productive_loc = total_lines - blank_lines - comment_lines - docstring_lines
    
    return FileAnalysis(
        path=filepath,
        total_lines=total_lines,
        productive_loc=productive_loc,
        blank_lines=blank_lines,
        comment_lines=comment_lines,
        docstring_lines=docstring_lines,
        functions=functions,
        classes=classes,
        function_sizes=function_sizes,
        class_sizes=class_sizes
    )

def main():
    files = [
        "src/ui/widgets/embedded_tradingview_chart.py",
        "src/core/market_data/history_provider.py",
        "src/ui/widgets/chart_window.py",
        "src/ui/app.py",
        "src/core/strategy/engine.py",
        "src/core/backtesting/backtrader_integration.py",
        "src/ui/widgets/performance_dashboard.py",
        "src/ai/openai_service.py",
        "src/config/loader.py",
        "src/ui/dialogs/parameter_optimization_dialog.py",
        "src/core/broker/base.py",
        "src/ui/dialogs/settings_dialog.py",
        "src/ui/widgets/watchlist.py",
        "src/core/backtesting/optimization.py",
        "src/ui/dialogs/ai_backtest_dialog.py",
    ]
    
    base_path = Path("/mnt/d/03_GIT/02_Python/07_OrderPilot-AI")
    
    print("## DATEIGRÖSSEN-ANALYSE (Produktiver Code)")
    print()
    print("| Datei | Total | Produktiv | Blank | Comments | Docstrings | Funktionen | Klassen |")
    print("|-------|-------|-----------|-------|----------|------------|------------|---------|")
    
    results = []
    for f in files:
        filepath = base_path / f
        if filepath.exists():
            analysis = count_productive_loc(str(filepath))
            results.append(analysis)
            shortname = f.split('/')[-1]
            status = "⚠️" if analysis.productive_loc > 600 else "✅"
            print(f"| {status} {shortname} | {analysis.total_lines} | **{analysis.productive_loc}** | {analysis.blank_lines} | {analysis.comment_lines} | {analysis.docstring_lines} | {len(analysis.functions)} | {len(analysis.classes)} |")
    
    print()
    print("### Dateien über 600 produktive LOC (SPLITTING ERFORDERLICH):")
    print()
    
    for analysis in results:
        if analysis.productive_loc > 600:
            shortname = analysis.path.split('/')[-1]
            print(f"#### {shortname} ({analysis.productive_loc} LOC)")
            print()
            
            # Show large classes
            large_classes = [(name, size) for name, size in analysis.class_sizes.items() if size > 100]
            if large_classes:
                print("**Große Klassen (>100 LOC):**")
                for name, size in sorted(large_classes, key=lambda x: -x[1]):
                    print(f"- {name}: {size} LOC")
                print()
            
            # Show large functions
            large_funcs = [(name, size) for name, size in analysis.function_sizes.items() if size > 50]
            if large_funcs:
                print("**Große Funktionen (>50 LOC):**")
                for name, size in sorted(large_funcs, key=lambda x: -x[1])[:10]:
                    print(f"- {name}: {size} LOC")
                print()

if __name__ == "__main__":
    main()
