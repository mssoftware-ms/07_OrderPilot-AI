#!/usr/bin/env python3
"""
Test runner for Issue 15: Beenden-Button im Flashscreen.

This script runs comprehensive tests on the splash screen's close button
and generates a detailed test report.
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Run the test suite and generate report."""
    project_root = Path(__file__).parent

    print("=" * 80)
    print("TESTING ISSUE 15: Beenden-Button im Flashscreen")
    print("=" * 80)
    print()

    # Run pytest with detailed output
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/ui/test_splash_screen_beenden_button.py",
        "-v",
        "--tb=short",
        "--color=yes",
        "--html=test_report.html",
        "--self-contained-html",
    ]

    print(f"Running: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, cwd=project_root)

    print()
    print("=" * 80)
    if result.returncode == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"TESTS FAILED (exit code: {result.returncode})")
    print("=" * 80)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
