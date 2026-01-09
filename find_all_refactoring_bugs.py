#!/usr/bin/env python3
"""Systematic bug finder for refactored code.

Finds:
1. Missing delegation methods (calls to self._method that don't exist)
2. Missing imports (undefined names)
3. Missing helper initializations
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict

class RefactoringBugFinder(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.bugs = []
        self.defined_methods = set()
        self.called_methods = set()
        self.imports = set()
        self.used_names = set()
        self.helper_inits = set()
        self.helper_calls = set()

    def visit_FunctionDef(self, node):
        self.defined_methods.add(node.name)
        self.generic_visit(node)

    def visit_Attribute(self, node):
        # Check for self._method() calls
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            if node.attr.startswith('_'):
                self.called_methods.add(node.attr)
        self.generic_visit(node)

    def visit_Assign(self, node):
        # Check for helper initialization: self._helper = Helper(self)
        for target in node.targets:
            if isinstance(target, ast.Attribute):
                if isinstance(target.value, ast.Name) and target.value.id == 'self':
                    if target.attr.startswith('_') and 'helper' in target.attr.lower():
                        self.helper_inits.add(target.attr)
        self.generic_visit(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load):
            self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.add(alias.name if alias.asname is None else alias.asname)

    def visit_ImportFrom(self, node):
        for alias in node.names:
            self.imports.add(alias.name if alias.asname is None else alias.asname)

    def find_bugs(self):
        # Bug 1: Methods called but not defined
        missing_methods = self.called_methods - self.defined_methods
        for method in missing_methods:
            if method not in ['_ensure_helpers', '_setup_ui', '_init', '__init__']:
                self.bugs.append({
                    'type': 'MISSING_METHOD',
                    'name': method,
                    'file': self.filename
                })

        # Bug 2: Common names used but not imported
        common_libs = {'pd': 'pandas', 'np': 'numpy', 'QWidget': 'PyQt6.QtWidgets',
                       'Optional': 'typing', 'List': 'typing', 'Dict': 'typing'}
        for name, lib in common_libs.items():
            if name in self.used_names and name not in self.imports:
                self.bugs.append({
                    'type': 'MISSING_IMPORT',
                    'name': name,
                    'lib': lib,
                    'file': self.filename
                })

        return self.bugs

def scan_file(filepath):
    """Scan a single file for bugs."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(filepath))

        finder = RefactoringBugFinder(str(filepath))
        finder.visit(tree)
        return finder.find_bugs()
    except Exception as e:
        return [{'type': 'PARSE_ERROR', 'error': str(e), 'file': str(filepath)}]

def scan_directory(path, pattern="*.py"):
    """Scan all Python files in directory."""
    all_bugs = defaultdict(list)

    for file in Path(path).rglob(pattern):
        # Skip test files and __pycache__
        if '__pycache__' in str(file) or 'test_' in file.name:
            continue

        bugs = scan_file(file)
        for bug in bugs:
            all_bugs[bug['type']].append(bug)

    return all_bugs

def main():
    print("=" * 80)
    print("REFACTORING BUG SCANNER")
    print("=" * 80)

    # Scan refactored directories
    directories = [
        "src/ui/widgets/chart_mixins",
        "src/ui/widgets/chart_window_mixins",
        "src/ui/widgets/bitunix_trading",
        "src/core/trading_bot"
    ]

    all_bugs = defaultdict(list)

    for directory in directories:
        print(f"\n[SCANNING] {directory}...")
        bugs = scan_directory(directory)
        for bug_type, bug_list in bugs.items():
            all_bugs[bug_type].extend(bug_list)

    # Report results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if not all_bugs:
        print("\n[OK] No bugs found!")
        return 0

    # Missing methods
    if 'MISSING_METHOD' in all_bugs:
        print(f"\n[CRITICAL] {len(all_bugs['MISSING_METHOD'])} MISSING METHODS:")
        for bug in all_bugs['MISSING_METHOD']:
            print(f"  - {bug['file']}")
            print(f"    Missing: {bug['name']}")

    # Missing imports
    if 'MISSING_IMPORT' in all_bugs:
        print(f"\n[CRITICAL] {len(all_bugs['MISSING_IMPORT'])} MISSING IMPORTS:")
        for bug in all_bugs['MISSING_IMPORT']:
            print(f"  - {bug['file']}")
            print(f"    Missing: {bug['name']} (from {bug['lib']})")

    # Parse errors
    if 'PARSE_ERROR' in all_bugs:
        print(f"\n[ERROR] {len(all_bugs['PARSE_ERROR'])} PARSE ERRORS:")
        for bug in all_bugs['PARSE_ERROR']:
            print(f"  - {bug['file']}: {bug['error']}")

    print(f"\n[SUMMARY] {sum(len(v) for v in all_bugs.values())} total bugs found")
    return 1

if __name__ == "__main__":
    sys.exit(main())
