"""
Rebuild simulation_engine.py with mixin inheritance.

Creates new main file that:
- Inherits from all 3 mixins
- Keeps only core simulation methods
"""

from pathlib import Path

SOURCE_FILE = Path("src/core/simulator/simulation_engine_pre_mixin_refactor.py")
TARGET_FILE = Path("src/core/simulator/simulation_engine.py")

# Methods that ARE in mixins (will be removed from main file)
MIXIN_METHODS = {
    # Indicators Mixin
    '_calculate_bollinger_bands', '_calculate_adx', '_calculate_atr',
    '_true_range', '_calculate_rsi', '_calculate_obv',

    # Trade Mixin
    '_check_entry_signal', '_open_position', '_close_position',
    '_close_position_end', '_check_exit_conditions', '_update_trailing_stop',

    # Results Mixin
    '_calculate_result', '_empty_result', '_calculate_trade_metrics',
    '_max_drawdown_pct', '_max_consecutive_runs', '_avg_trade_duration', '_risk_ratios',
}

def find_method_end(lines, start_idx, method_indent):
    """Find the end of a method definition."""
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if not line.strip():  # Empty line
            continue

        current_indent = len(line) - len(line.lstrip())

        # If we hit a line at the same or lower indent level that starts a new def or class, we found the end
        if current_indent <= method_indent and (line.strip().startswith('def ') or line.strip().startswith('class ')):
            return i

    return len(lines)  # End of file

def rebuild_main_file():
    """Rebuild main simulation_engine.py with mixin inheritance."""
    print("=" * 80)
    print("🔧 REBUILDING SIMULATION_ENGINE.PY WITH MIXINS")
    print("=" * 80)

    # Read source file
    with open(SOURCE_FILE, 'r') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

    # Find SimulationConfig class definition
    config_class_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('class SimulationConfig:'):
            config_class_idx = i
            break

    # Find StrategySimulator class definition
    class_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('class StrategySimulator:'):
            class_line_idx = i
            break

    if class_line_idx is None:
        print("❌ Could not find StrategySimulator class definition")
        return

    # Find all methods in StrategySimulator class
    methods = []  # List of (method_name, start_idx, end_idx)
    for i in range(class_line_idx + 1, len(lines)):
        line = lines[i]
        if line.strip().startswith('def '):
            method_name = line.strip().split('(')[0].replace('def ', '')
            method_indent = len(line) - len(line.lstrip())
            end_idx = find_method_end(lines, i, method_indent)
            methods.append((method_name, i, end_idx))

    print(f"📊 Found {len(methods)} methods in StrategySimulator class")

    # Separate methods to keep
    methods_to_keep = [(name, start, end) for name, start, end in methods if name not in MIXIN_METHODS]
    print(f"🔧 Keeping {len(methods_to_keep)} methods ({len(methods) - len(methods_to_keep)} moved to mixins)")

    # Build new content
    new_content = []

    # Part 1: Everything before StrategySimulator class (includes imports, SimulationConfig, etc.)
    new_content.extend(lines[:class_line_idx])

    # Part 2: Mixin imports (insert before StrategySimulator class)
    new_content.append('\n# Import mixins\n')
    new_content.append('from .simulation_indicators_mixin import SimulationIndicatorsMixin\n')
    new_content.append('from .simulation_trade_mixin import SimulationTradeMixin\n')
    new_content.append('from .simulation_results_mixin import SimulationResultsMixin\n')
    new_content.append('\n')

    # Part 3: New class definition with mixin inheritance
    new_content.append('class StrategySimulator(\n')
    new_content.append('    SimulationIndicatorsMixin,\n')
    new_content.append('    SimulationTradeMixin,\n')
    new_content.append('    SimulationResultsMixin,\n')
    new_content.append('):\n')

    # Part 4: Class docstring (from class_line_idx+1 to first method)
    first_method_idx = methods[0][1] if methods else len(lines)
    new_content.extend(lines[class_line_idx + 1:first_method_idx])

    # Part 5: Add methods to keep
    for method_name, start_idx, end_idx in methods_to_keep:
        method_lines = lines[start_idx:end_idx]
        new_content.extend(method_lines)
        new_content.append('\n')

    # Write new file
    with open(TARGET_FILE, 'w') as f:
        f.writelines(new_content)

    # Stats
    original_loc = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    new_loc = len([l for l in new_content if l.strip() and not l.strip().startswith('#')])

    print(f"\n✅ New file created: {TARGET_FILE}")
    print(f"📊 Original: {len(lines)} lines ({original_loc} productive)")
    print(f"📊 New: {len(new_content)} lines ({new_loc} productive)")
    print(f"📉 Reduction: {len(lines) - len(new_content)} lines ({original_loc - new_loc} productive)")

    print("\n" + "=" * 80)
    print("✅ REBUILD COMPLETE")
    print("=" * 80)
    print("\n📋 NEXT STEPS:")
    print("1. Validate syntax of new simulation_engine.py")
    print("2. Test that simulator still works")
    print("3. Commit changes")

if __name__ == "__main__":
    rebuild_main_file()
