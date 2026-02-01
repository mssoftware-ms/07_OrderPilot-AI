"""
Lightweight Structure Mapper using Python AST.

Extracts class and method signatures WITHOUT code bodies.
Designed to be token-efficient for AI context (~3k tokens vs ~50k for full repomix).

Usage:
    from analyzers.structure_mapper import generate_structure_md

    # Generate markdown structure for src/
    md = generate_structure_md(Path("src"))
    Path(".antigravity/context/structure.md").write_text(md)

CLI Usage:
    python .antigravity/analyzers/structure_mapper.py [src_dir] [output_file]
"""
from __future__ import annotations

import ast
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class MethodInfo:
    """Method/function signature information."""
    name: str
    args: list[str]
    returns: Optional[str] = None
    docstring: Optional[str] = None  # First line only
    lineno: int = 0
    is_async: bool = False
    is_property: bool = False
    is_classmethod: bool = False
    is_staticmethod: bool = False

    def to_markdown(self) -> str:
        """Convert to markdown signature line."""
        prefix = ""
        if self.is_async:
            prefix = "async "
        if self.is_property:
            prefix = "@property "
        if self.is_classmethod:
            prefix = "@classmethod "
        if self.is_staticmethod:
            prefix = "@staticmethod "

        args_str = ", ".join(self.args)
        sig = f"{prefix}`{self.name}({args_str})`"

        if self.returns:
            sig += f" → `{self.returns}`"

        if self.docstring:
            # Truncate long docstrings
            doc = self.docstring[:80]
            if len(self.docstring) > 80:
                doc += "..."
            sig += f"  *{doc}*"

        return sig


@dataclass
class ClassInfo:
    """Class information with methods."""
    name: str
    bases: list[str]
    methods: list[MethodInfo] = field(default_factory=list)
    docstring: Optional[str] = None
    lineno: int = 0

    def to_markdown(self) -> str:
        """Convert to markdown section."""
        bases_str = ", ".join(self.bases) if self.bases else "object"
        lines = [f"### `{self.name}({bases_str})`"]

        if self.docstring:
            doc = self.docstring.split("\n")[0][:100]
            lines.append(f"*{doc}*")

        lines.append("")

        # Group methods by type
        public_methods = [m for m in self.methods if not m.name.startswith("_")]
        private_methods = [m for m in self.methods
                         if m.name.startswith("_") and not m.name.startswith("__")]
        dunder_methods = [m for m in self.methods if m.name.startswith("__")]

        # Show public methods first
        for method in public_methods:
            lines.append(f"- {method.to_markdown()}")

        # Then private (collapsed hint)
        if private_methods:
            lines.append(f"- *...{len(private_methods)} private methods*")

        # Dunder methods only if few
        if len(dunder_methods) <= 3:
            for method in dunder_methods:
                lines.append(f"- {method.to_markdown()}")
        elif dunder_methods:
            lines.append(f"- *...{len(dunder_methods)} dunder methods*")

        return "\n".join(lines)


@dataclass
class ModuleInfo:
    """Module (file) information."""
    path: Path
    classes: list[ClassInfo] = field(default_factory=list)
    functions: list[MethodInfo] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)

    def to_markdown(self, relative_to: Optional[Path] = None) -> str:
        """Convert to markdown section."""
        rel_path = self.path.relative_to(relative_to) if relative_to else self.path
        lines = [f"## `{rel_path}`"]

        if self.classes:
            for cls in self.classes:
                lines.append("")
                lines.append(cls.to_markdown())

        if self.functions:
            lines.append("")
            lines.append("### Module Functions")
            for func in self.functions:
                lines.append(f"- {func.to_markdown()}")

        return "\n".join(lines)


class StructureMapper:
    """
    AST-based code structure extractor.

    Extracts classes, methods, and function signatures from Python files.
    Optimized for minimal token usage while maintaining useful context.
    """

    def __init__(self, root: Path):
        """
        Initialize structure mapper.

        Args:
            root: Root directory to analyze.
        """
        self.root = root
        self._modules: list[ModuleInfo] = []

    def analyze(self) -> list[ModuleInfo]:
        """
        Analyze all Python files in root directory.

        Returns:
            List of ModuleInfo for each analyzed file.
        """
        self._modules = []

        for py_file in sorted(self.root.rglob("*.py")):
            # Skip common exclusions
            path_str = str(py_file)
            if any(excl in path_str for excl in [
                "__pycache__",
                ".venv",
                ".wsl_venv",
                "node_modules",
                ".git",
                "build",
                "dist",
                ".egg-info",
            ]):
                continue

            module = self._analyze_file(py_file)
            if module and (module.classes or module.functions):
                self._modules.append(module)

        return self._modules

    def to_markdown(self) -> str:
        """
        Generate markdown representation of analyzed structure.

        Returns:
            Markdown string with all modules, classes, and methods.
        """
        lines = [
            "# Code Structure",
            "",
            f"*Generated from `{self.root}` - Signatures only (no code bodies)*",
            "",
            f"**Modules:** {len(self._modules)}",
            f"**Classes:** {sum(len(m.classes) for m in self._modules)}",
            f"**Methods:** {sum(sum(len(c.methods) for c in m.classes) for m in self._modules)}",
            "",
            "---",
        ]

        for module in self._modules:
            lines.append("")
            lines.append(module.to_markdown(relative_to=self.root.parent))

        return "\n".join(lines)

    def _analyze_file(self, path: Path) -> Optional[ModuleInfo]:
        """Analyze single Python file."""
        try:
            source = path.read_text(encoding="utf-8")
            tree = ast.parse(source, filename=str(path))
        except (SyntaxError, UnicodeDecodeError) as e:
            # Skip files that can't be parsed
            return None

        module = ModuleInfo(path=path)

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                cls = self._extract_class(node)
                if cls:
                    module.classes.append(cls)

            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func = self._extract_method(node)
                if func:
                    module.functions.append(func)

            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                module.imports.extend(self._extract_imports(node))

        return module

    def _extract_class(self, node: ast.ClassDef) -> ClassInfo:
        """Extract class information from AST node."""
        # Get base classes
        bases = []
        for base in node.bases:
            try:
                bases.append(ast.unparse(base))
            except Exception:
                bases.append("?")

        # Get docstring (first line only)
        docstring = ast.get_docstring(node)
        if docstring:
            docstring = docstring.split("\n")[0].strip()

        cls = ClassInfo(
            name=node.name,
            bases=bases,
            docstring=docstring,
            lineno=node.lineno,
        )

        # Extract methods
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                method = self._extract_method(item)
                if method:
                    cls.methods.append(method)

        return cls

    def _extract_method(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> MethodInfo:
        """Extract method/function information from AST node."""
        # Get arguments (skip 'self' and 'cls')
        args = []
        for arg in node.args.args:
            if arg.arg not in ("self", "cls"):
                args.append(arg.arg)

        # Get return type
        returns = None
        if node.returns:
            try:
                returns = ast.unparse(node.returns)
            except Exception:
                returns = "?"

        # Get docstring (first line only)
        docstring = ast.get_docstring(node)
        if docstring:
            docstring = docstring.split("\n")[0].strip()

        # Check decorators
        is_property = False
        is_classmethod = False
        is_staticmethod = False

        for decorator in node.decorator_list:
            dec_name = ""
            if isinstance(decorator, ast.Name):
                dec_name = decorator.id
            elif isinstance(decorator, ast.Attribute):
                dec_name = decorator.attr

            if dec_name == "property":
                is_property = True
            elif dec_name == "classmethod":
                is_classmethod = True
            elif dec_name == "staticmethod":
                is_staticmethod = True

        return MethodInfo(
            name=node.name,
            args=args,
            returns=returns,
            docstring=docstring,
            lineno=node.lineno,
            is_async=isinstance(node, ast.AsyncFunctionDef),
            is_property=is_property,
            is_classmethod=is_classmethod,
            is_staticmethod=is_staticmethod,
        )

    def _extract_imports(self, node: ast.Import | ast.ImportFrom) -> list[str]:
        """Extract import names."""
        imports = []

        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append(f"{module}.{alias.name}")

        return imports


def generate_structure_md(src_dir: Path, output: Optional[Path] = None) -> str:
    """
    Generate structure markdown for a directory.

    Args:
        src_dir: Source directory to analyze.
        output: Optional output file path.

    Returns:
        Generated markdown string.
    """
    mapper = StructureMapper(src_dir)
    mapper.analyze()
    md = mapper.to_markdown()

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(md, encoding="utf-8")

    return md


def main():
    """CLI entry point."""
    src_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("src")
    output = Path(sys.argv[2]) if len(sys.argv) > 2 else None

    if not src_dir.exists():
        print(f"[ERROR] Directory not found: {src_dir}")
        sys.exit(1)

    print(f"[INFO] Analyzing: {src_dir}")
    md = generate_structure_md(src_dir, output)

    if output:
        print(f"[OK] Written to: {output}")
    else:
        print(md)


if __name__ == "__main__":
    main()
