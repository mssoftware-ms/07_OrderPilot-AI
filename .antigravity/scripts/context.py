#!/usr/bin/env python3
"""
Antigravity AI Context Generator.

Generates unified AI context packets combining:
- Rules (Das Grundgesetz)
- ai_docs/ content (architecture, naming, pitfalls)
- Code structure (AST-based signatures)
- Optional: UI tree dump

Output formats:
- Markdown (.md) for direct copy-paste
- JSON (.json) for programmatic use

Usage:
    python .antigravity/scripts/context.py                    # Full context
    python .antigravity/scripts/context.py --quick            # Rules + ai_docs only
    python .antigravity/scripts/context.py --structure-only   # Code structure only
    python .antigravity/scripts/context.py --ui               # Include UI tree dump
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Add parent directory to path for imports
SCRIPT_DIR = Path(__file__).parent
ANTIGRAVITY_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = ANTIGRAVITY_DIR.parent
sys.path.insert(0, str(ANTIGRAVITY_DIR))


def get_rules() -> str:
    """Read the Grundgesetz rules."""
    rules_file = ANTIGRAVITY_DIR / "rules"
    if rules_file.exists():
        return rules_file.read_text(encoding="utf-8").strip()
    return "(Rules file not found)"


def get_ai_docs() -> dict[str, str]:
    """Read all ai_docs markdown files."""
    ai_docs_dir = PROJECT_ROOT / "ai_docs"
    docs: dict[str, str] = {}

    if ai_docs_dir.exists():
        for md_file in sorted(ai_docs_dir.glob("*.md")):
            docs[md_file.stem] = md_file.read_text(encoding="utf-8")

    return docs


def get_structure(src_dir: Optional[Path] = None) -> str:
    """Generate code structure using AST mapper."""
    try:
        from analyzers.structure_mapper import generate_structure_md

        src = src_dir or PROJECT_ROOT / "src"
        if src.exists():
            return generate_structure_md(src)
        return "(Source directory not found)"
    except ImportError as e:
        return f"(Structure mapper not available: {e})"
    except Exception as e:
        return f"(Error generating structure: {e})"


def get_ui_tree() -> Optional[dict[str, Any]]:
    """Get UI tree dump if available."""
    try:
        from core.environment import Environment

        env = Environment(PROJECT_ROOT)
        if env.has_ui_support:
            driver = env.ui_driver
            if driver.is_available:
                return driver.get_ui_tree().to_dict()
    except ImportError:
        pass
    except Exception:
        pass

    return None


def detect_stack() -> str:
    """Detect project stack."""
    try:
        from core.environment import Environment

        env = Environment(PROJECT_ROOT)
        return env.stack.name
    except ImportError:
        return "UNKNOWN"


def generate_context(
    include_structure: bool = True,
    include_ui: bool = False,
    quick_mode: bool = False,
) -> dict[str, Any]:
    """
    Generate complete AI context packet.

    Args:
        include_structure: Include code structure analysis.
        include_ui: Include UI tree dump.
        quick_mode: Only rules + ai_docs (fastest).

    Returns:
        Context dictionary.
    """
    context: dict[str, Any] = {
        "meta": {
            "generated": datetime.now(timezone.utc).isoformat(),
            "project": PROJECT_ROOT.name,
            "stack": detect_stack(),
        },
        "rules": get_rules(),
        "ai_docs": get_ai_docs(),
    }

    if not quick_mode and include_structure:
        context["structure"] = get_structure()

    if include_ui:
        ui_tree = get_ui_tree()
        if ui_tree:
            context["ui_tree"] = ui_tree

    return context


def context_to_markdown(context: dict[str, Any]) -> str:
    """Convert context dictionary to markdown format."""
    lines = [
        "# AI Context Packet",
        "",
        f"**Project:** {context['meta']['project']}",
        f"**Stack:** {context['meta']['stack']}",
        f"**Generated:** {context['meta']['generated']}",
        "",
        "---",
        "",
        "## Das Grundgesetz (Rules)",
        "",
        "```",
        context["rules"],
        "```",
        "",
    ]

    # ai_docs
    if context.get("ai_docs"):
        lines.append("---")
        lines.append("")
        for name, content in context["ai_docs"].items():
            lines.append(f"## ai_docs/{name}.md")
            lines.append("")
            lines.append(content)
            lines.append("")

    # Structure
    if context.get("structure"):
        lines.append("---")
        lines.append("")
        lines.append(context["structure"])
        lines.append("")

    # UI Tree (condensed)
    if context.get("ui_tree"):
        lines.append("---")
        lines.append("")
        lines.append("## UI Tree")
        lines.append("")
        lines.append("```json")
        # Limit depth for readability
        lines.append(json.dumps(context["ui_tree"], indent=2)[:5000])
        if len(json.dumps(context["ui_tree"])) > 5000:
            lines.append("... (truncated)")
        lines.append("```")

    return "\n".join(lines)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate AI context packet for the project.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python context.py                    # Full context (rules + ai_docs + structure)
  python context.py --quick            # Quick context (rules + ai_docs only)
  python context.py --structure-only   # Code structure only
  python context.py --ui               # Include UI tree dump
  python context.py --json             # Output as JSON instead of Markdown
        """,
    )

    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Quick mode: rules + ai_docs only (no structure analysis)",
    )
    parser.add_argument(
        "--structure-only", "-s",
        action="store_true",
        help="Output only code structure (no rules/ai_docs)",
    )
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Include UI tree dump (if available)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON instead of Markdown",
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Output file (default: .antigravity/context/ai-context.md)",
    )
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print to stdout instead of file",
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = args.output
    else:
        ext = ".json" if args.json else ".md"
        output_path = ANTIGRAVITY_DIR / "context" / f"ai-context{ext}"

    # Generate context
    print(f"[INFO] Generating AI context for: {PROJECT_ROOT.name}")

    if args.structure_only:
        content = get_structure()
        if args.stdout:
            print(content)
        else:
            output_path = output_path.with_name("structure.md")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(content, encoding="utf-8")
            print(f"[OK] Structure written to: {output_path}")
        return

    context = generate_context(
        include_structure=not args.quick,
        include_ui=args.ui,
        quick_mode=args.quick,
    )

    # Format output
    if args.json:
        content = json.dumps(context, indent=2, ensure_ascii=False)
    else:
        content = context_to_markdown(context)

    # Write or print
    if args.stdout:
        print(content)
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content, encoding="utf-8")
        print(f"[OK] Context written to: {output_path}")

        # Stats
        ai_docs_count = len(context.get("ai_docs", {}))
        has_structure = "structure" in context
        has_ui = "ui_tree" in context

        print(f"[INFO] Content: rules + {ai_docs_count} ai_docs", end="")
        if has_structure:
            print(" + structure", end="")
        if has_ui:
            print(" + ui_tree", end="")
        print()


if __name__ == "__main__":
    main()
