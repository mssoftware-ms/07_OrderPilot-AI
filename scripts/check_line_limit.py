#!/usr/bin/env python3
"""Line limit check script for OrderPilot-AI.

Enforces the 600-line maximum per Python file rule.
Exit code 1 if any file exceeds the limit.
"""

from __future__ import annotations

import sys
from pathlib import Path

MAX_LINES = 600
SRC_DIR = Path(__file__).parent.parent / "src"


def check_line_limits() -> list[tuple[Path, int]]:
    """Check all Python files in src/ for line count violations.

    Returns:
        List of (path, line_count) tuples for files exceeding MAX_LINES.
    """
    violations: list[tuple[Path, int]] = []

    for py_file in SRC_DIR.rglob("*.py"):
        try:
            line_count = len(py_file.read_text(encoding="utf-8").splitlines())
            if line_count > MAX_LINES:
                violations.append((py_file, line_count))
        except (OSError, UnicodeDecodeError) as e:
            print(f"Warning: Could not read {py_file}: {e}", file=sys.stderr)

    return sorted(violations, key=lambda x: -x[1])


def main() -> int:
    """Main entry point.

    Returns:
        0 if all files pass, 1 if any violations found.
    """
    violations = check_line_limits()

    if not violations:
        print(f"✅ All Python files in src/ are under {MAX_LINES} lines.")
        return 0

    print(f"❌ {len(violations)} file(s) exceed {MAX_LINES} lines:\n")
    for path, count in violations:
        rel_path = path.relative_to(SRC_DIR.parent)
        print(f"  {count:4d} lines: {rel_path}")

    print(f"\n⚠️  These files must be split before merge.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
