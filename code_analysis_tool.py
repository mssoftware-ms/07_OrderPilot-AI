#!/usr/bin/env python3
"""Code Analysis Tool for OrderPilot-AI.

Analyzes Python code for:
- Complexity metrics (Cyclomatic, Cognitive)
- Dead code detection
- Code duplicates
- Anti-patterns and code smells
"""

import ast
import os
import sys
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Set, Any
import hashlib
import difflib

class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor to calculate complexity metrics."""

    def __init__(self):
        self.cyclomatic = 1  # Start at 1
        self.cognitive = 0
        self.nesting_level = 0
        self.function_count = 0
        self.class_count = 0
        self.lines = 0

    def visit_FunctionDef(self, node):
        """Visit function definitions."""
        self.function_count += 1
        self.lines += (node.end_lineno or 0) - node.lineno
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Visit class definitions."""
        self.class_count += 1
        self.generic_visit(node)

    def visit_If(self, node):
        """Visit If statements."""
        self.cyclomatic += 1
        self.cognitive += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_For(self, node):
        """Visit For loops."""
        self.cyclomatic += 1
        self.cognitive += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_While(self, node):
        """Visit While loops."""
        self.cyclomatic += 1
        self.cognitive += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

    def visit_Try(self, node):
        """Visit Try statements."""
        for handler in node.handlers:
            self.cyclomatic += 1
            self.cognitive += 1 + self.nesting_level
        self.nesting_level += 1
        self.generic_visit(node)
        self.nesting_level -= 1

class FunctionAnalyzer(ast.NodeVisitor):
    """Analyzer for individual functions."""

    def __init__(self):
        self.functions = []
        self.classes = []
        self.imports = set()

    def visit_FunctionDef(self, node):
        """Analyze function definition."""
        complexity_visitor = ComplexityVisitor()
        complexity_visitor.visit(node)

        function_info = {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno or 0,
            'lines_of_code': (node.end_lineno or 0) - node.lineno,
            'parameters': len(node.args.args),
            'cyclomatic_complexity': complexity_visitor.cyclomatic,
            'cognitive_complexity': complexity_visitor.cognitive,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'docstring': ast.get_docstring(node),
        }
        self.functions.append(function_info)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        """Analyze class definition."""
        class_info = {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno or 0,
            'lines_of_code': (node.end_lineno or 0) - node.lineno,
            'methods': len([n for n in node.body if isinstance(n, ast.FunctionDef)]),
            'docstring': ast.get_docstring(node),
        }
        self.classes.append(class_info)
        self.generic_visit(node)

    def visit_Import(self, node):
        """Track imports."""
        for alias in node.names:
            self.imports.add(alias.name)

    def visit_ImportFrom(self, node):
        """Track from imports."""
        if node.module:
            for alias in node.names:
                self.imports.add(f"{node.module}.{alias.name}")

def analyze_file(file_path: Path) -> Dict[str, Any]:
    """Analyze a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        tree = ast.parse(content)
        analyzer = FunctionAnalyzer()
        analyzer.visit(tree)

        return {
            'file_path': str(file_path),
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'functions': analyzer.functions,
            'classes': analyzer.classes,
            'imports': list(analyzer.imports),
            'content_hash': hashlib.md5(content.encode()).hexdigest(),
        }

    except (SyntaxError, UnicodeDecodeError, Exception) as e:
        return {
            'file_path': str(file_path),
            'error': str(e),
            'functions': [],
            'classes': [],
            'imports': [],
        }

def find_duplicates(analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find duplicate code blocks."""
    duplicates = []
    content_hashes = defaultdict(list)

    # Group by content hash
    for result in analysis_results:
        if 'content_hash' in result:
            content_hashes[result['content_hash']].append(result)

    # Find hash duplicates
    for hash_value, files in content_hashes.items():
        if len(files) > 1:
            duplicates.append({
                'type': 'exact_duplicate',
                'hash': hash_value,
                'files': [f['file_path'] for f in files],
                'size': files[0].get('file_size', 0),
            })

    # Find function name duplicates
    function_names = defaultdict(list)
    for result in analysis_results:
        for func in result.get('functions', []):
            function_names[func['name']].append({
                'file': result['file_path'],
                'function': func
            })

    for name, instances in function_names.items():
        if len(instances) > 1 and name not in ['__init__', '__str__', '__repr__']:
            duplicates.append({
                'type': 'function_name_duplicate',
                'name': name,
                'instances': instances,
            })

    return duplicates

def find_dead_code_candidates(analysis_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find potential dead code candidates."""
    dead_code = []
    all_functions = set()
    all_imports = set()

    # Collect all function names and imports
    for result in analysis_results:
        for func in result.get('functions', []):
            all_functions.add(func['name'])
        for imp in result.get('imports', []):
            all_imports.add(imp)

    # Find potentially unused functions (basic heuristic)
    for result in analysis_results:
        for func in result.get('functions', []):
            name = func['name']
            if (name.startswith('_') and
                not name.startswith('__') and
                func.get('lines_of_code', 0) > 5):
                dead_code.append({
                    'type': 'potentially_unused_private',
                    'file': result['file_path'],
                    'function': name,
                    'lines': func.get('lines_of_code', 0),
                    'line_start': func.get('line_start', 0),
                })

    return dead_code

def generate_complexity_report(analysis_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate complexity analysis report."""
    complexity_issues = []
    total_functions = 0
    total_complexity = 0

    for result in analysis_results:
        for func in result.get('functions', []):
            total_functions += 1
            cyclomatic = func.get('cyclomatic_complexity', 0)
            cognitive = func.get('cognitive_complexity', 0)
            lines = func.get('lines_of_code', 0)
            params = func.get('parameters', 0)

            total_complexity += cyclomatic

            # Flag high complexity
            if cyclomatic > 10 or cognitive > 15 or lines > 50 or params > 5:
                complexity_issues.append({
                    'file': result['file_path'],
                    'function': func['name'],
                    'cyclomatic_complexity': cyclomatic,
                    'cognitive_complexity': cognitive,
                    'lines_of_code': lines,
                    'parameters': params,
                    'line_start': func.get('line_start', 0),
                })

    avg_complexity = total_complexity / max(total_functions, 1)

    return {
        'total_functions': total_functions,
        'average_complexity': round(avg_complexity, 2),
        'complexity_issues': sorted(complexity_issues,
                                  key=lambda x: x['cyclomatic_complexity'],
                                  reverse=True),
    }

def analyze_codebase(src_path: Path) -> Dict[str, Any]:
    """Analyze entire codebase."""
    print(f"Analyzing codebase in: {src_path}")

    # Find all Python files
    python_files = list(src_path.rglob("*.py"))
    print(f"Found {len(python_files)} Python files")

    # Analyze each file
    results = []
    for i, file_path in enumerate(python_files, 1):
        if i % 10 == 0:
            print(f"Progress: {i}/{len(python_files)} files analyzed")

        result = analyze_file(file_path)
        results.append(result)

    print("Analysis complete. Generating reports...")

    # Generate reports
    complexity_report = generate_complexity_report(results)
    duplicates = find_duplicates(results)
    dead_code_candidates = find_dead_code_candidates(results)

    return {
        'summary': {
            'total_files': len(python_files),
            'total_lines': sum(r.get('line_count', 0) for r in results),
            'total_functions': complexity_report['total_functions'],
            'average_complexity': complexity_report['average_complexity'],
        },
        'complexity_report': complexity_report,
        'duplicates': duplicates,
        'dead_code_candidates': dead_code_candidates,
        'file_details': results,
    }

if __name__ == "__main__":
    # Analyze the src directory
    src_path = Path(__file__).parent / "src"
    if not src_path.exists():
        print(f"Source directory not found: {src_path}")
        sys.exit(1)

    analysis = analyze_codebase(src_path)

    # Print summary
    print("\n" + "="*80)
    print("CODE ANALYSIS SUMMARY")
    print("="*80)

    summary = analysis['summary']
    print(f"Total Files: {summary['total_files']}")
    print(f"Total Lines: {summary['total_lines']:,}")
    print(f"Total Functions: {summary['total_functions']}")
    print(f"Average Complexity: {summary['average_complexity']}")

    # Complexity issues
    complexity_issues = analysis['complexity_report']['complexity_issues']
    if complexity_issues:
        print(f"\n🔴 HIGH COMPLEXITY FUNCTIONS ({len(complexity_issues)}):")
        for issue in complexity_issues[:10]:  # Top 10
            print(f"  {issue['function']} in {issue['file']}")
            print(f"    Cyclomatic: {issue['cyclomatic_complexity']}, "
                  f"Cognitive: {issue['cognitive_complexity']}, "
                  f"Lines: {issue['lines_of_code']}, "
                  f"Params: {issue['parameters']}")

    # Duplicates
    duplicates = analysis['duplicates']
    if duplicates:
        print(f"\n🟡 CODE DUPLICATES ({len(duplicates)}):")
        for dup in duplicates[:5]:  # Top 5
            if dup['type'] == 'exact_duplicate':
                print(f"  Exact duplicate in {len(dup['files'])} files:")
                for file in dup['files']:
                    print(f"    - {file}")
            elif dup['type'] == 'function_name_duplicate':
                print(f"  Function '{dup['name']}' duplicated in {len(dup['instances'])} files")

    # Dead code candidates
    dead_code = analysis['dead_code_candidates']
    if dead_code:
        print(f"\n🟢 POTENTIAL DEAD CODE ({len(dead_code)}):")
        for dead in dead_code[:10]:  # Top 10
            print(f"  {dead['function']} in {dead['file']} ({dead['lines']} lines)")

    print("\n" + "="*80)
    print(f"Analysis complete! Full results available in analysis object.")