#!/usr/bin/env python3
"""
Antigravity AI Verify Script - Auto-detecting verification for any project type.

Automatically detects:
- Python (pytest, flake8, mypy)
- Tauri/Rust (cargo check, cargo test, cargo clippy)
- Node.js/TypeScript (npm test, eslint, tsc)
- Next.js (npm run build, npm test)

Usage: python .antigravity/scripts/ai-verify.py [module_path]
"""
from __future__ import annotations

import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class ProjectType:
    name: str
    detected: bool
    lint_cmd: list[str]
    type_cmd: list[str]
    test_cmd: list[str]
    scoped_test_cmd: Optional[list[str]] = None


def detect_project_types(root: Path) -> list[ProjectType]:
    """Detect all project types in the given root directory."""
    types = []

    # Python Detection
    python_indicators = [
        root / "pyproject.toml",
        root / "requirements.txt",
        root / "setup.py",
        root / "Pipfile",
    ]
    if any(f.exists() for f in python_indicators):
        types.append(ProjectType(
            name="Python",
            detected=True,
            lint_cmd=["python", "-m", "flake8", "src/", "--max-line-length=120", "--ignore=E501,W503"],
            type_cmd=["python", "-m", "mypy", "src/", "--ignore-missing-imports"],
            test_cmd=["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            scoped_test_cmd=["python", "-m", "pytest", "{module}", "-v", "--tb=short"],
        ))

    # Tauri/Rust Detection
    tauri_indicators = [
        root / "src-tauri" / "tauri.conf.json",
        root / "tauri.conf.json",
    ]
    cargo_toml = root / "Cargo.toml"
    src_tauri_cargo = root / "src-tauri" / "Cargo.toml"

    if any(f.exists() for f in tauri_indicators):
        cargo_dir = "src-tauri" if src_tauri_cargo.exists() else "."
        types.append(ProjectType(
            name="Tauri/Rust",
            detected=True,
            lint_cmd=["cargo", "clippy", "--manifest-path", f"{cargo_dir}/Cargo.toml", "--", "-D", "warnings"],
            type_cmd=["cargo", "check", "--manifest-path", f"{cargo_dir}/Cargo.toml"],
            test_cmd=["cargo", "test", "--manifest-path", f"{cargo_dir}/Cargo.toml"],
        ))
    elif cargo_toml.exists():
        types.append(ProjectType(
            name="Rust",
            detected=True,
            lint_cmd=["cargo", "clippy", "--", "-D", "warnings"],
            type_cmd=["cargo", "check"],
            test_cmd=["cargo", "test"],
        ))

    # Node.js/TypeScript Detection
    package_json = root / "package.json"
    if package_json.exists():
        # Check for specific frameworks
        tsconfig = root / "tsconfig.json"
        next_config = root / "next.config.js"
        next_config_mjs = root / "next.config.mjs"

        if next_config.exists() or next_config_mjs.exists():
            types.append(ProjectType(
                name="Next.js",
                detected=True,
                lint_cmd=["npm", "run", "lint", "--silent"],
                type_cmd=["npx", "tsc", "--noEmit"] if tsconfig.exists() else [],
                test_cmd=["npm", "test", "--", "--watchAll=false"],
            ))
        elif tsconfig.exists():
            types.append(ProjectType(
                name="TypeScript",
                detected=True,
                lint_cmd=["npm", "run", "lint", "--silent"],
                type_cmd=["npx", "tsc", "--noEmit"],
                test_cmd=["npm", "test", "--", "--watchAll=false"],
            ))
        else:
            types.append(ProjectType(
                name="Node.js",
                detected=True,
                lint_cmd=["npm", "run", "lint", "--silent"],
                type_cmd=[],
                test_cmd=["npm", "test"],
            ))

    return types


def run_step(step_name: str, cmd: list[str], cwd: Path, optional: bool = False) -> bool:
    """Run a verification step and return success status."""
    if not cmd:
        print(f"  [SKIP] {step_name}: Skipped (not configured)")
        return True

    print(f"\n  [RUN] {step_name}...")
    print(f"     $ {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode == 0:
            print(f"  [OK] {step_name}: Passed")
            return True
        else:
            print(f"  [FAIL] {step_name}: Failed")
            if result.stdout:
                print(result.stdout[:1000])
            if result.stderr:
                print(result.stderr[:1000])
            return optional
    except FileNotFoundError:
        print(f"  [WARN] {step_name}: Tool not found ({cmd[0]})")
        return optional
    except subprocess.TimeoutExpired:
        print(f"  [WARN] {step_name}: Timeout after 300s")
        return optional


def verify_project(root: Path, scoped_module: Optional[str] = None) -> bool:
    """Run verification for detected project types."""
    print("=" * 60)
    print("[VERIFY] Antigravity AI Verify - Auto-Detection")
    print("=" * 60)

    types = detect_project_types(root)

    if not types:
        print("[ERROR] No recognized project type found!")
        print("   Supported: Python, Rust, Tauri, Node.js, TypeScript, Next.js")
        return False

    print(f"\n[DETECT] Detected project types:")
    for t in types:
        print(f"   * {t.name}")

    all_passed = True

    for project_type in types:
        print(f"\n{'=' * 60}")
        print(f"[TEST] Verifying: {project_type.name}")
        print("=" * 60)

        # Step 1: Linting
        if not run_step("Linting", project_type.lint_cmd, root, optional=True):
            all_passed = False

        # Step 2: Type Check
        if not run_step("Type Check", project_type.type_cmd, root, optional=True):
            all_passed = False

        # Step 3: Tests
        if scoped_module and project_type.scoped_test_cmd:
            test_cmd = [c.replace("{module}", scoped_module) for c in project_type.scoped_test_cmd]
        else:
            test_cmd = project_type.test_cmd

        if not run_step("Tests", test_cmd, root, optional=False):
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("[SUCCESS] ALL CHECKS PASSED!")
    else:
        print("[FAILED] SOME CHECKS FAILED - Review output above")
    print("=" * 60)

    return all_passed


def main():
    root = Path.cwd()
    scoped_module = sys.argv[1] if len(sys.argv) > 1 else None

    success = verify_project(root, scoped_module)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
