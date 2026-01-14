"""
Create mixins for simulation_engine.py based on method categorization.

Splits StrategySimulator class into 3 mixins for better modularity.
"""

from pathlib import Path
from typing import List, Any

SOURCE_FILE = Path("src/core/simulator/simulation_engine_pre_mixin_refactor.py")
TARGET_DIR = Path("src/core/simulator")

# Mixin definitions based on analysis
MIXINS = {
    'simulation_indicators_mixin.py': {
        'class_name': 'SimulationIndicatorsMixin',
        'description': 'Indicator calculations (Bollinger Bands, ADX, ATR, RSI, OBV, True Range)',
        'methods': [
            '_calculate_bollinger_bands',
            '_calculate_adx',
            '_calculate_atr',
            '_true_range',
            '_calculate_rsi',
            '_calculate_obv',
        ],
    },
    'simulation_trade_mixin.py': {
        'class_name': 'SimulationTradeMixin',
        'description': 'Trade management (entry, exit, trailing stop)',
        'methods': [
            '_check_entry_signal',
            '_open_position',
            '_close_position',
            '_close_position_end',
            '_check_exit_conditions',
            '_update_trailing_stop',
        ],
    },
    'simulation_results_mixin.py': {
        'class_name': 'SimulationResultsMixin',
        'description': 'Result calculation and performance metrics',
        'methods': [
            '_calculate_result',
            '_empty_result',
            '_calculate_trade_metrics',
            '_max_drawdown_pct',
            '_max_consecutive_runs',
            '_avg_trade_duration',
            '_risk_ratios',
        ],
    },
}

def extract_method(lines: List[str], method_name: str, start_line: int) -> tuple[int, int] | None:
    """Find method start and end lines."""
    # Find method start
    method_start = None
    for i in range(start_line - 1, len(lines)):
        if f'def {method_name}(' in lines[i]:
            method_start = i + 1  # 1-indexed
            break

    if not method_start:
        return None

    # Find method end (next method or class end)
    indent_level = len(lines[method_start - 1]) - len(lines[method_start - 1].lstrip())
    method_end = None

    for i in range(method_start, len(lines)):
        line = lines[i]
        if line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            # Check if we hit next method at same indent level
            if current_indent == indent_level and line.strip().startswith('def '):
                method_end = i  # 1-indexed
                break

    if not method_end:
        method_end = len(lines)

    return (method_start, method_end)

def get_common_imports() -> str:
    """Get common imports for all mixins."""
    return '''from __future__ import annotations

from typing import Any
import pandas as pd
import numpy as np

'''

def create_mixin(filename: str, config: dict[str, Any], source_lines: List[str]) -> bool:
    """Create a single mixin file."""
    print(f"\n📝 Creating {filename}...")

    # Extract all methods
    all_method_lines = []
    for method_name in config['methods']:
        result = extract_method(source_lines, method_name, 1)
        if result:
            start, end = result
            all_method_lines.extend(source_lines[start-1:end-1])
            all_method_lines.append('\n')  # Spacing between methods
        else:
            print(f"   ⚠️  Method {method_name} not found, skipping...")

    if not all_method_lines:
        print(f"   ❌ No methods found for {filename}")
        return False

    # Build content
    content = get_common_imports()
    content += f'class {config["class_name"]}:\n'
    content += f'    """{config["description"]}"""\n\n'

    # Add methods
    for line in all_method_lines:
        content += line

    # Write file
    target_path = TARGET_DIR / filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Count LOC
    productive_loc = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
    total_loc = len(content.split('\n'))

    print(f"   ✅ {total_loc} total LOC, {productive_loc} productive LOC")
    print(f"   🔧 {len(config['methods'])} methods included")

    return True

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING SIMULATION_ENGINE MIXINS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    # Read source file
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

    # Create all mixins
    success_count = 0
    for filename, config in MIXINS.items():
        if create_mixin(filename, config, lines):
            success_count += 1

    print("\n" + "=" * 80)
    print(f"✅ MIXINS CREATED: {success_count}/{len(MIXINS)}")
    print("=" * 80)

    if success_count == len(MIXINS):
        print("\n📋 NEXT STEPS:")
        print("1. Validate syntax of all mixins")
        print("2. Create new simulation_engine.py that inherits from all mixins")
        print("3. Test that simulator still works")
        print("4. Commit changes")

if __name__ == "__main__":
    main()
