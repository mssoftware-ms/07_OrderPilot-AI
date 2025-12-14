#!/usr/bin/env python3
"""Dead Code Finder for Python codebases.

This script analyzes Python files to find potentially unused functions and methods.
"""

import ast
import os
import sys
from pathlib import Path
from typing import Set, Dict, List
import re


class DeadCodeFinder(ast.NodeVisitor):
    """AST visitor to find potentially dead code."""

    def __init__(self):
        self.defined_functions: Set[str] = set()
        self.called_functions: Set[str] = set()
        self.defined_classes: Set[str] = set()
        self.used_classes: Set[str] = set()

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        self.defined_functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definitions."""
        self.defined_classes.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Visit function calls."""
        if isinstance(node.func, ast.Name):
            self.called_functions.add(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            self.called_functions.add(node.func.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        """Visit name references."""
        if isinstance(node.ctx, ast.Load):
            self.used_classes.add(node.id)


def analyze_file(filepath: Path) -> Dict[str, Set[str]]:
    """Analyze a single Python file for dead code."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        finder = DeadCodeFinder()
        finder.visit(tree)

        return {
            'defined_functions': finder.defined_functions,
            'called_functions': finder.called_functions,
            'defined_classes': finder.defined_classes,
            'used_classes': finder.used_classes
        }
    except Exception as e:
        print(f"Error analyzing {filepath}: {e}")
        return {
            'defined_functions': set(),
            'called_functions': set(),
            'defined_classes': set(),
            'used_classes': set()
        }


def find_dead_code_in_directory(directory: Path) -> Dict[str, any]:
    """Find potentially dead code in a directory."""
    all_defined_functions = set()
    all_called_functions = set()
    all_defined_classes = set()
    all_used_classes = set()

    file_analysis = {}

    # Analyze all Python files
    for py_file in directory.rglob("*.py"):
        analysis = analyze_file(py_file)
        file_analysis[str(py_file)] = analysis

        all_defined_functions.update(analysis['defined_functions'])
        all_called_functions.update(analysis['called_functions'])
        all_defined_classes.update(analysis['defined_classes'])
        all_used_classes.update(analysis['used_classes'])

    # Find potentially unused functions
    potentially_unused_functions = all_defined_functions - all_called_functions

    # Filter out special methods and known patterns
    special_patterns = {
        '__init__', '__str__', '__repr__', '__eq__', '__hash__',
        '__enter__', '__exit__', '__call__', '__getitem__', '__setitem__',
        'setUp', 'tearDown', 'test_', 'run', 'main'
    }

    filtered_unused_functions = set()
    for func in potentially_unused_functions:
        if not any(func.startswith(pattern) for pattern in special_patterns):
            filtered_unused_functions.add(func)

    # Find potentially unused classes
    potentially_unused_classes = all_defined_classes - all_used_classes

    return {
        'unused_functions': filtered_unused_functions,
        'unused_classes': potentially_unused_classes,
        'file_analysis': file_analysis
    }


if __name__ == "__main__":
    src_path = Path("src")
    if not src_path.exists():
        print("Source directory 'src' not found")
        sys.exit(1)

    print("Analyzing codebase for dead code...")
    results = find_dead_code_in_directory(src_path)

    print(f"\n📊 DEAD CODE ANALYSIS RESULTS")
    print(f"{'='*50}")

    print(f"\n🟡 POTENTIALLY UNUSED FUNCTIONS ({len(results['unused_functions'])}):")
    for func in sorted(results['unused_functions'])[:20]:  # Top 20
        print(f"  - {func}")

    print(f"\n🟡 POTENTIALLY UNUSED CLASSES ({len(results['unused_classes'])}):")
    for cls in sorted(results['unused_classes'])[:20]:  # Top 20
        print(f"  - {cls}")

    print(f"\n⚠️  WARNING: This is a basic analysis that may have false positives!")
    print(f"   - Dynamic calls (getattr, exec, eval) are not detected")
    print(f"   - Framework-specific patterns may not be recognized")
    print(f"   - Manual verification is required before deletion")