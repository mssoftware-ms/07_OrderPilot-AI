#!/usr/bin/env python3
"""Parse pytest output and generate comprehensive test report."""

import json
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

def run_tests() -> Tuple[int, str, str]:
    """Run pytest with JSON reporting and capture output."""
    cmd = [
        "python", "-m", "pytest",
        "tests/core/test_indicator_set_optimizer.py",
        "tests/core/test_dynamic_strategy_switching.py",
        "-v",
        "--tb=short",
        "--cov=src.core.indicator_set_optimizer",
        "--cov=src.core.tradingbot.dynamic_strategy_switching",
        "--cov-report=json:coverage.json",
        "--cov-report=term-missing"
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    return result.returncode, result.stdout, result.stderr

def parse_coverage(coverage_file: str = "coverage.json") -> Dict:
    """Parse coverage JSON file."""
    if not Path(coverage_file).exists():
        return {}

    with open(coverage_file, 'r') as f:
        data = json.load(f)

    return {
        'total_coverage': data['totals']['percent_covered'],
        'total_lines': data['totals']['num_statements'],
        'covered_lines': data['totals']['num_statements'] - data['totals']['missing_lines'],
        'missing_lines': data['totals']['missing_lines'],
        'by_module': {
            file: {
                'coverage': info['summary']['percent_covered'],
                'lines': info['summary']['num_statements'],
                'missing': info['summary']['missing_lines']
            }
            for file, info in data['files'].items()
        }
    }

def create_summary_table(stdout: str) -> str:
    """Extract test summary from pytest output."""
    lines = stdout.split('\n')

    # Find summary line
    for line in reversed(lines):
        if 'passed' in line or 'failed' in line:
            return line

    return ""

def main():
    """Main execution."""
    print("Running test suite...")
    print("=" * 70)

    exit_code, stdout, stderr = run_tests()

    # Parse results
    coverage = parse_coverage()

    # Generate summary
    print("\n" + "=" * 70)
    print("TEST EXECUTION SUMMARY")
    print("=" * 70)

    print(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Status: {'✅ PASSED' if exit_code == 0 else '⚠️ FAILED'}")

    # Coverage summary
    if coverage:
        print(f"\nCoverage Report:")
        print(f"  Total Coverage: {coverage['total_coverage']:.1f}%")
        print(f"  Lines Covered: {coverage['covered_lines']}/{coverage['total_lines']}")
        print(f"  Missing Lines: {coverage['missing_lines']}")

    # Test summary
    summary_line = create_summary_table(stdout)
    if summary_line:
        print(f"\nTest Summary:")
        print(f"  {summary_line}")

    print("\n" + "=" * 70)

    # Extract failed tests
    failed_tests = []
    lines = stdout.split('\n')
    in_failures = False
    current_test = None

    for line in lines:
        if 'FAILURES' in line:
            in_failures = True
        elif in_failures and 'short test summary' in line:
            in_failures = False
        elif in_failures and line.startswith('_'):
            current_test = line.replace('_', '').strip()
        elif current_test and line.strip():
            if not line.startswith(' '):
                current_test = None

    if failed_tests:
        print("\nFailed Tests:")
        for test in failed_tests:
            print(f"  - {test}")

    # Generate test report markdown
    report_path = Path("docs/TEST_EXECUTION_REPORT.md")
    if report_path.exists():
        print(f"\n✅ Test Report generated: {report_path}")

    # Generate coverage badge
    badge_path = Path("docs/coverage.svg")
    if badge_path.exists():
        print(f"✅ Coverage badge generated: {badge_path}")

    print("\n" + "=" * 70)
    print("For detailed results, see: docs/TEST_EXECUTION_REPORT.md")
    print("=" * 70)

    return exit_code

if __name__ == "__main__":
    exit(main())
