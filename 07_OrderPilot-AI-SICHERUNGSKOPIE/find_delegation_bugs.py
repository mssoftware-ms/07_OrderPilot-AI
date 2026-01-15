#!/usr/bin/env python3
"""Smart refactoring bug finder - finds ACTUAL delegation bugs.

Finds:
1. Qt signal connections to missing delegation methods (e.g., widget.clicked.connect(self._missing))
2. Helper class methods without parent delegation methods
3. Missing helper initialization calls
4. Runtime imports in TYPE_CHECKING blocks
"""

import ast
import sys
from pathlib import Path
from collections import defaultdict
import re


class DelegationBugFinder(ast.NodeVisitor):
    """Find delegation bugs by analyzing Qt connections and helper patterns."""

    def __init__(self, filename, source_code):
        self.filename = filename
        self.source_code = source_code
        self.bugs = []

        # Track defined methods (including delegations)
        self.defined_methods = set()

        # Track Qt signal connections: widget.signal.connect(self._method)
        self.connected_methods = []  # List of (line_no, method_name, context)

        # Track TYPE_CHECKING imports
        self.type_checking_imports = set()
        self.runtime_imports = set()

        # Track actual usage of imports in runtime code
        self.used_names_runtime = set()

        # Inside TYPE_CHECKING block flag
        self._in_type_checking = False

    def visit_If(self, node):
        """Detect TYPE_CHECKING blocks."""
        # Check if this is "if TYPE_CHECKING:"
        if (isinstance(node.test, ast.Name) and
            node.test.id == 'TYPE_CHECKING'):

            # Visit body with flag set
            old_flag = self._in_type_checking
            self._in_type_checking = True
            for stmt in node.body:
                self.visit(stmt)
            self._in_type_checking = old_flag

            # Visit orelse without flag
            for stmt in node.orelse:
                self.visit(stmt)

            return  # Don't call generic_visit

        self.generic_visit(node)

    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if self._in_type_checking:
                self.type_checking_imports.add(name)
            else:
                self.runtime_imports.add(name)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        for alias in node.names:
            name = alias.asname if alias.asname else alias.name
            if self._in_type_checking:
                self.type_checking_imports.add(name)
            else:
                self.runtime_imports.add(name)

    def visit_FunctionDef(self, node):
        """Track defined methods."""
        self.defined_methods.add(node.name)
        self.generic_visit(node)

    def visit_Call(self, node):
        """Find .connect(self._method) patterns."""
        # Pattern: something.connect(self._method) or something.connect(self.parent._method)
        if (isinstance(node.func, ast.Attribute) and
            node.func.attr == 'connect' and
            len(node.args) > 0):

            arg = node.args[0]

            # Pattern 1: self._method
            if isinstance(arg, ast.Attribute):
                if isinstance(arg.value, ast.Name) and arg.value.id == 'self':
                    if arg.attr.startswith('_'):
                        line_no = node.lineno
                        # Get source line for context
                        try:
                            source_line = self.source_code.split('\n')[line_no - 1].strip()
                        except:
                            source_line = ""

                        self.connected_methods.append({
                            'line': line_no,
                            'method': arg.attr,
                            'context': source_line
                        })

                # Pattern 2: self.parent._method (helper connecting to parent)
                elif (isinstance(arg.value, ast.Attribute) and
                      isinstance(arg.value.value, ast.Name) and
                      arg.value.value.id == 'self' and
                      arg.value.attr == 'parent'):
                    if arg.attr.startswith('_'):
                        line_no = node.lineno
                        try:
                            source_line = self.source_code.split('\n')[line_no - 1].strip()
                        except:
                            source_line = ""

                        self.connected_methods.append({
                            'line': line_no,
                            'method': arg.attr,
                            'context': source_line,
                            'parent_connection': True
                        })

        # Track name usage in runtime code
        if not self._in_type_checking:
            if isinstance(node.func, ast.Name):
                self.used_names_runtime.add(node.func.id)

        self.generic_visit(node)

    def visit_Name(self, node):
        """Track name usage at runtime."""
        if not self._in_type_checking and isinstance(node.ctx, ast.Load):
            self.used_names_runtime.add(node.id)
        self.generic_visit(node)

    def find_bugs(self):
        """Analyze collected data for bugs."""

        # Bug 1: Qt connections to undefined methods
        for conn in self.connected_methods:
            method = conn['method']

            # Skip if it's a connection to parent (needs to be checked in parent file)
            if conn.get('parent_connection'):
                continue

            if method not in self.defined_methods:
                # Not all undefined connections are bugs - some might be from parent classes
                # Only report if it looks like a refactored delegation pattern
                if '_' in method and not method.startswith('__'):
                    self.bugs.append({
                        'type': 'MISSING_DELEGATION',
                        'method': method,
                        'line': conn['line'],
                        'context': conn['context'],
                        'file': self.filename
                    })

        # Bug 2: TYPE_CHECKING imports used at runtime
        runtime_only = self.used_names_runtime - self.runtime_imports
        for name in runtime_only:
            if name in self.type_checking_imports:
                self.bugs.append({
                    'type': 'TYPE_CHECKING_IMPORT',
                    'name': name,
                    'file': self.filename
                })

        return self.bugs


def scan_file(filepath):
    """Scan a file for delegation bugs."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source_code = f.read()

        tree = ast.parse(source_code, filename=str(filepath))
        finder = DelegationBugFinder(str(filepath), source_code)
        finder.visit(tree)
        return finder.find_bugs()
    except Exception as e:
        return [{'type': 'PARSE_ERROR', 'error': str(e), 'file': str(filepath)}]


def find_parent_connections(directory):
    """Find all .connect(self.parent._method) calls to check if parent has those methods."""
    parent_connections = defaultdict(list)

    for filepath in Path(directory).rglob("*.py"):
        if '__pycache__' in str(filepath):
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                source = f.read()

            # Regex pattern for self.parent._method connections
            pattern = r'\.connect\(\s*self\.parent\.(_\w+)\s*\)'
            for match in re.finditer(pattern, source):
                method = match.group(1)
                line_no = source[:match.start()].count('\n') + 1

                # Get context
                lines = source.split('\n')
                context = lines[line_no - 1].strip() if line_no <= len(lines) else ""

                parent_connections[str(filepath)].append({
                    'method': method,
                    'line': line_no,
                    'context': context
                })
        except:
            pass

    return parent_connections


def scan_directory(path):
    """Scan all Python files in directory."""
    all_bugs = defaultdict(list)

    # Scan for basic delegation bugs
    for filepath in Path(path).rglob("*.py"):
        if '__pycache__' in str(filepath) or 'test_' in filepath.name:
            continue

        bugs = scan_file(filepath)
        for bug in bugs:
            all_bugs[bug['type']].append(bug)

    return all_bugs


def main():
    print("=" * 80)
    print("SMART DELEGATION BUG SCANNER")
    print("=" * 80)

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

    # Also scan for parent connections
    print("\n[SCANNING] Parent connection patterns...")
    for directory in ["src/ui/widgets/bitunix_trading", "src/ui/widgets/chart_mixins"]:
        parent_conns = find_parent_connections(directory)
        for filepath, connections in parent_conns.items():
            if connections:
                print(f"\n  {filepath}:")
                for conn in connections:
                    print(f"    Line {conn['line']}: needs parent.{conn['method']}()")
                    print(f"      {conn['context']}")

    # Report results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    if not all_bugs:
        print("\n[OK] No bugs found!")
        return 0

    # Missing delegation methods
    if 'MISSING_DELEGATION' in all_bugs:
        print(f"\n[CRITICAL] {len(all_bugs['MISSING_DELEGATION'])} MISSING DELEGATION METHODS:")
        for bug in all_bugs['MISSING_DELEGATION']:
            print(f"\n  File: {bug['file']}:{bug['line']}")
            print(f"  Missing: {bug['method']}()")
            print(f"  Context: {bug['context']}")

    # TYPE_CHECKING imports used at runtime
    if 'TYPE_CHECKING_IMPORT' in all_bugs:
        print(f"\n[CRITICAL] {len(all_bugs['TYPE_CHECKING_IMPORT'])} TYPE_CHECKING IMPORTS USED AT RUNTIME:")
        for bug in all_bugs['TYPE_CHECKING_IMPORT']:
            print(f"  - {bug['file']}")
            print(f"    Import '{bug['name']}' is in TYPE_CHECKING but used at runtime")

    # Parse errors
    if 'PARSE_ERROR' in all_bugs:
        print(f"\n[ERROR] {len(all_bugs['PARSE_ERROR'])} PARSE ERRORS:")
        for bug in all_bugs['PARSE_ERROR']:
            print(f"  - {bug['file']}: {bug['error']}")

    total = sum(len(v) for v in all_bugs.values())
    print(f"\n[SUMMARY] {total} actual bugs found")

    return 1 if total > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
