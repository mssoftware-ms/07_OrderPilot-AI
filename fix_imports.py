#!/usr/bin/env python3
"""Fix imports to use src. prefix."""

import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> bool:
    """Fix imports in a single file."""
    content = file_path.read_text()
    original = content

    # Fix database imports
    content = re.sub(
        r'^from database\.',
        'from src.database.',
        content,
        flags=re.MULTILINE
    )

    # Fix config imports
    content = re.sub(
        r'^from config\.',
        'from src.config.',
        content,
        flags=re.MULTILINE
    )

    # Fix common imports
    content = re.sub(
        r'^from common\.',
        'from src.common.',
        content,
        flags=re.MULTILINE
    )

    # Fix core imports
    content = re.sub(
        r'^from core\.',
        'from src.core.',
        content,
        flags=re.MULTILINE
    )

    # Fix ai imports
    content = re.sub(
        r'^from ai\.',
        'from src.ai.',
        content,
        flags=re.MULTILINE
    )

    if content != original:
        file_path.write_text(content)
        print(f"Fixed: {file_path}")
        return True
    return False


def main():
    """Fix all imports in src directory."""
    src_dir = Path("src")
    fixed_count = 0

    for py_file in src_dir.rglob("*.py"):
        if fix_imports_in_file(py_file):
            fixed_count += 1

    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()
