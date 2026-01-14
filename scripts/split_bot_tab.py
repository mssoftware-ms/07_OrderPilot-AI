"""
Automatic splitter for bot_tab.py into multiple modules.

Splits based on functional areas: controls, strategy, monitoring, logs, settings.
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple

# Define splitting strategy based on method analysis
SPLITS = {
    'bot_tab.py': {
        'description': 'Main BotTab widget - coordination only',
        'line_ranges': [(1, 122), (123, 180)],  # Imports + __init__ + _setup_ui
        'note': 'Main widget with delegation to sub-modules'
    },
    'bot_tab_ui.py': {
        'description': 'UI creation methods (header, signal, position, stats sections)',
        'line_ranges': [(182, 560)],  # _create_* methods for UI
        'note': 'All _create_* methods for UI sections'
    },
    'bot_tab_controls.py': {
        'description': 'Bot control methods (start, stop, pause, resume)',
        'line_ranges': [(562, 900)],  # Control-related methods
        'note': 'Bot lifecycle control logic'
    },
    'bot_tab_monitoring.py': {
        'description': 'Position monitoring and P/L display',
        'line_ranges': [(902, 1500)],  # Monitoring and update methods
        'note': 'Position, P/L, signal monitoring'
    },
    'bot_tab_logs.py': {
        'description': 'Log display and trade history',
        'line_ranges': [(1502, 2165)],  # Log and history methods
        'note': 'Trade logs, history display'
    },
    'bot_tab_settings.py': {
        'description': 'BotSettingsDialog class',
        'line_ranges': [(2168, 2441)],  # BotSettingsDialog complete
        'note': 'Settings dialog (separate class)'
    }
}

def extract_lines(filepath: Path, start: int, end: int) -> List[str]:
    """Extract lines from file (1-indexed)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    # Handle edge case for line_ranges
    return lines[start-1:end] if end < len(lines) else lines[start-1:]

def analyze_structure(source_file: Path):
    """Analyze file structure to determine exact split points."""
    with open(source_file, 'r') as f:
        content = f.read()
        lines = content.split('\n')

    tree = ast.parse(content, str(source_file))

    # Find all classes and top-level methods
    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        'name': item.name,
                        'lineno': item.lineno,
                        'end_lineno': item.end_lineno or item.lineno
                    })
            classes.append({
                'name': node.name,
                'lineno': node.lineno,
                'end_lineno': node.end_lineno or node.lineno,
                'methods': methods
            })

    print("\n📋 FILE STRUCTURE ANALYSIS:")
    print("=" * 80)
    for cls in classes:
        print(f"\n{cls['name']} (lines {cls['lineno']}-{cls['end_lineno']}, {len(cls['methods'])} methods)")

        # Categorize methods
        categories = {
            'UI Creation': [],
            'Controls': [],
            'Monitoring': [],
            'Logs': [],
            'Settings': [],
            'Other': []
        }

        for m in cls['methods']:
            name = m['name']
            if any(x in name for x in ['_create_', '_setup_ui']):
                categories['UI Creation'].append(m)
            elif any(x in name.lower() for x in ['start', 'stop', 'pause', 'resume', 'toggle', 'apply']):
                categories['Controls'].append(m)
            elif any(x in name.lower() for x in ['monitor', 'update', 'position', 'pnl', 'display']):
                categories['Monitoring'].append(m)
            elif any(x in name.lower() for x in ['log', 'history', 'trade', 'signal_received']):
                categories['Logs'].append(m)
            elif 'settings' in name.lower() or 'config' in name.lower():
                categories['Settings'].append(m)
            else:
                categories['Other'].append(m)

        for cat_name, methods in categories.items():
            if methods:
                print(f"  {cat_name}: {len(methods)} methods")
                if len(methods) <= 5:
                    for m in methods:
                        print(f"    - {m['name']} (lines {m['lineno']}-{m['end_lineno']})")

    return classes

def create_refined_splits(source_file: Path, classes: list) -> dict:
    """Create refined split ranges based on actual class structure."""
    # Find BotTab class
    bot_tab_class = next((c for c in classes if c['name'] == 'BotTab'), None)
    settings_class = next((c for c in classes if c['name'] == 'BotSettingsDialog'), None)

    if not bot_tab_class:
        print("❌ BotTab class not found!")
        return {}

    # Read file for imports
    with open(source_file, 'r') as f:
        lines = f.readlines()

    # Find import section end (before first class)
    import_end = bot_tab_class['lineno'] - 1

    # Categorize methods by line ranges
    ui_methods = []
    control_methods = []
    monitoring_methods = []
    log_methods = []
    other_methods = []

    for m in bot_tab_class['methods']:
        name = m['name']
        if any(x in name for x in ['_create_', '_setup_ui', '_setup_signals', '_setup_timers']):
            ui_methods.append(m)
        elif any(x in name.lower() for x in ['start', 'stop', 'pause', 'resume', 'toggle', 'handle', 'clicked', 'apply']):
            control_methods.append(m)
        elif any(x in name.lower() for x in ['monitor', 'update', 'position', 'pnl', 'display', 'status']):
            monitoring_methods.append(m)
        elif any(x in name.lower() for x in ['log', 'history', 'trade', 'signal_received', 'error', 'order']):
            log_methods.append(m)
        else:
            other_methods.append(m)

    # Determine line ranges
    init_method = next((m for m in bot_tab_class['methods'] if m['name'] == '__init__'), None)

    refined_splits = {
        'bot_tab.py': {
            'description': 'Main BotTab widget - imports, __init__, delegation',
            'line_ranges': [(1, import_end), (bot_tab_class['lineno'], init_method['end_lineno'] if init_method else bot_tab_class['lineno'] + 50)],
            'methods': ['imports', '__init__']
        },
        'bot_tab_ui.py': {
            'description': 'UI creation methods',
            'line_ranges': [(ui_methods[0]['lineno'], ui_methods[-1]['end_lineno'])] if ui_methods else [],
            'methods': [m['name'] for m in ui_methods]
        },
        'bot_tab_controls.py': {
            'description': 'Bot control methods',
            'line_ranges': [(control_methods[0]['lineno'], control_methods[-1]['end_lineno'])] if control_methods else [],
            'methods': [m['name'] for m in control_methods]
        },
        'bot_tab_monitoring.py': {
            'description': 'Position monitoring',
            'line_ranges': [(monitoring_methods[0]['lineno'], monitoring_methods[-1]['end_lineno'])] if monitoring_methods else [],
            'methods': [m['name'] for m in monitoring_methods]
        },
        'bot_tab_logs.py': {
            'description': 'Logs and history',
            'line_ranges': [(log_methods[0]['lineno'], log_methods[-1]['end_lineno'])] if log_methods else [],
            'methods': [m['name'] for m in log_methods]
        }
    }

    # Add settings dialog
    if settings_class:
        refined_splits['bot_tab_settings.py'] = {
            'description': 'Settings dialog',
            'line_ranges': [(settings_class['lineno'], settings_class['end_lineno'])],
            'methods': ['BotSettingsDialog class']
        }

    return refined_splits

def main():
    """Run the analysis."""
    source_file = Path('src/ui/widgets/bitunix_trading/bot_tab.py')

    if not source_file.exists():
        print(f"❌ Source file not found: {source_file}")
        return

    print("=" * 80)
    print("🔍 ANALYZING bot_tab.py STRUCTURE")
    print("=" * 80)

    # Analyze structure
    classes = analyze_structure(source_file)

    # Create refined splits
    refined_splits = create_refined_splits(source_file, classes)

    print("\n" + "=" * 80)
    print("📝 RECOMMENDED SPLIT STRATEGY:")
    print("=" * 80)

    for module_name, config in refined_splits.items():
        if not config.get('line_ranges'):
            continue
        print(f"\n{module_name}:")
        print(f"  {config['description']}")
        print(f"  Line ranges: {config['line_ranges']}")
        print(f"  Methods: {len(config.get('methods', []))}")
        if len(config.get('methods', [])) <= 10:
            for method in config.get('methods', [])[:10]:
                print(f"    - {method}")

    print("\n" + "=" * 80)
    print("⚠️  NOTE: This is an ANALYSIS ONLY")
    print("    Actual splitting requires careful method extraction to avoid breaking dependencies")
    print("    Recommend manual splitting based on this analysis")
    print("=" * 80)

if __name__ == "__main__":
    main()
