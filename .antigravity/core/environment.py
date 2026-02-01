"""
Environment Detection for Antigravity.

Automatically detects project stack (PyQt, React, Django, etc.) and provides
lazy-loaded access to stack-specific drivers and tools.

Usage:
    from core.environment import Environment

    env = Environment()
    print(env.stack)        # Stack.PYQT
    driver = env.ui_driver  # Lazy-loaded PyQtDriver
"""
from __future__ import annotations

import json
from enum import Enum, auto
from functools import cached_property
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from ..drivers.base import BaseUIDriver


class Stack(Enum):
    """Detected project stack/framework."""
    PYQT6 = auto()
    PYQT5 = auto()
    PYSIDE6 = auto()
    PYSIDE2 = auto()
    REACT = auto()
    NEXT = auto()
    VUE = auto()
    ANGULAR = auto()
    DJANGO = auto()
    FLASK = auto()
    FASTAPI = auto()
    TAURI = auto()
    ELECTRON = auto()
    UNKNOWN = auto()


class Environment:
    """
    Detects project environment and provides lazy-loaded access to tools.

    Attributes:
        root: Project root directory
        stack: Detected framework/stack
        ui_driver: Lazy-loaded UI introspection driver
    """

    def __init__(self, root: Optional[Path] = None):
        """
        Initialize environment detection.

        Args:
            root: Project root directory. Defaults to current working directory.
        """
        self.root = Path(root) if root else Path.cwd()
        self._ui_driver: Optional[BaseUIDriver] = None

    @cached_property
    def stack(self) -> Stack:
        """Detect project stack from file markers and dependencies."""
        # Check Python dependencies first
        python_stack = self._detect_python_stack()
        if python_stack != Stack.UNKNOWN:
            return python_stack

        # Check JavaScript/TypeScript
        js_stack = self._detect_js_stack()
        if js_stack != Stack.UNKNOWN:
            return js_stack

        # Check Rust/Tauri
        rust_stack = self._detect_rust_stack()
        if rust_stack != Stack.UNKNOWN:
            return rust_stack

        return Stack.UNKNOWN

    @cached_property
    def ui_driver(self) -> "BaseUIDriver":
        """
        Lazy-load appropriate UI driver based on detected stack.

        Returns:
            UI driver instance for the detected stack.
        """
        if self.stack in (Stack.PYQT6, Stack.PYQT5, Stack.PYSIDE6, Stack.PYSIDE2):
            try:
                from ..drivers.pyqt_driver import PyQtDriver
                return PyQtDriver(self.stack)
            except ImportError:
                pass

        elif self.stack in (Stack.REACT, Stack.NEXT, Stack.VUE, Stack.ANGULAR):
            try:
                from ..drivers.playwright_driver import PlaywrightDriver
                return PlaywrightDriver()
            except ImportError:
                pass

        elif self.stack == Stack.ELECTRON:
            try:
                from ..drivers.electron_driver import ElectronDriver
                return ElectronDriver()
            except ImportError:
                pass

        # Fallback to null driver
        from ..drivers.base import NullDriver
        return NullDriver()

    @cached_property
    def has_ui_support(self) -> bool:
        """Check if UI introspection is available for this stack."""
        return self.stack in (
            Stack.PYQT6, Stack.PYQT5, Stack.PYSIDE6, Stack.PYSIDE2,
            Stack.REACT, Stack.NEXT, Stack.VUE, Stack.ANGULAR,
            Stack.ELECTRON
        )

    @cached_property
    def is_python_project(self) -> bool:
        """Check if this is a Python project."""
        return self.stack in (
            Stack.PYQT6, Stack.PYQT5, Stack.PYSIDE6, Stack.PYSIDE2,
            Stack.DJANGO, Stack.FLASK, Stack.FASTAPI
        )

    @cached_property
    def is_web_project(self) -> bool:
        """Check if this is a web frontend project."""
        return self.stack in (
            Stack.REACT, Stack.NEXT, Stack.VUE, Stack.ANGULAR
        )

    def _detect_python_stack(self) -> Stack:
        """Detect Python-based frameworks."""
        deps = self._get_python_dependencies()

        # Qt frameworks (order matters - check 6 before 5)
        if "pyqt6" in deps:
            return Stack.PYQT6
        if "pyside6" in deps:
            return Stack.PYSIDE6
        if "pyqt5" in deps:
            return Stack.PYQT5
        if "pyside2" in deps:
            return Stack.PYSIDE2

        # Web frameworks
        if "django" in deps:
            return Stack.DJANGO
        if "flask" in deps:
            return Stack.FLASK
        if "fastapi" in deps:
            return Stack.FASTAPI

        return Stack.UNKNOWN

    def _detect_js_stack(self) -> Stack:
        """Detect JavaScript/TypeScript frameworks."""
        package_json = self.root / "package.json"
        if not package_json.exists():
            return Stack.UNKNOWN

        try:
            pkg = json.loads(package_json.read_text())
            deps = {
                **pkg.get("dependencies", {}),
                **pkg.get("devDependencies", {})
            }
            dep_names = {k.lower() for k in deps.keys()}

            # Check for frameworks (order: specific before generic)
            if "next" in dep_names:
                return Stack.NEXT
            if "@angular/core" in dep_names:
                return Stack.ANGULAR
            if "vue" in dep_names:
                return Stack.VUE
            if "react" in dep_names:
                return Stack.REACT
            if "electron" in dep_names:
                return Stack.ELECTRON

        except (json.JSONDecodeError, KeyError):
            pass

        return Stack.UNKNOWN

    def _detect_rust_stack(self) -> Stack:
        """Detect Rust/Tauri projects."""
        tauri_indicators = [
            self.root / "tauri.conf.json",
            self.root / "src-tauri" / "tauri.conf.json",
            self.root / "src-tauri" / "Cargo.toml",
        ]

        if any(f.exists() for f in tauri_indicators):
            return Stack.TAURI

        return Stack.UNKNOWN

    def _get_python_dependencies(self) -> set[str]:
        """Extract Python dependencies from project files."""
        deps: set[str] = set()

        # requirements.txt
        req_file = self.root / "requirements.txt"
        if req_file.exists():
            for line in req_file.read_text().splitlines():
                line = line.strip().lower()
                if line and not line.startswith("#"):
                    # Extract package name (before ==, >=, etc.)
                    pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("[")[0]
                    deps.add(pkg.strip())

        # pyproject.toml
        pyproject = self.root / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text().lower()
            # Simple check for common packages
            for pkg in ["pyqt6", "pyqt5", "pyside6", "pyside2", "django", "flask", "fastapi"]:
                if pkg in content:
                    deps.add(pkg)

        return deps

    def __repr__(self) -> str:
        return f"Environment(root={self.root}, stack={self.stack.name})"
