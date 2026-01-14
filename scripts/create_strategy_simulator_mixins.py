"""
Create sub-mixins for strategy_simulator_run_mixin.py.

Splits into 5 focused mixins to reduce LOC from 849 to under 200.
"""

from pathlib import Path
from typing import List, Any

SOURCE_FILE = Path("src/ui/widgets/chart_window_mixins/strategy_simulator_run_mixin_pre_split.py")
TARGET_DIR = Path("src/ui/widgets/chart_window_mixins")

# Mixin definitions
MIXINS = {
    'strategy_simulator_execution_mixin.py': {
        'class_name': 'StrategySimulatorExecutionMixin',
        'description': 'Simulation execution flow and worker management',
        'methods': [
            '_on_run_simulation',
            '_start_simulation_with_visible_range',
            '_start_simulation_with_data',
            '_on_stop_simulation',
            '_cleanup_simulation_worker',
            '_create_simulation_worker',
            '_wire_simulation_worker',
            '_resolve_simulation_mode',
        ],
    },
    'strategy_simulator_data_mixin.py': {
        'class_name': 'StrategySimulatorDataMixin',
        'description': 'Data filtering and chart access',
        'methods': [
            '_filter_data_to_time_range',
            '_filter_data_to_visible_range',
            '_get_chart_dataframe',
            '_get_full_chart_dataframe',
            '_get_simulation_symbol',
            '_get_data_range_info',
            '_fill_date_range',
        ],
    },
    'strategy_simulator_settings_mixin.py': {
        'class_name': 'StrategySimulatorSettingsMixin',
        'description': 'Settings collection from UI widgets',
        'methods': [
            '_get_trigger_exit_settings',
            '_get_all_bot_settings',
            '_collect_simulation_params',
            '_prepare_simulation_run',
            '_collect_all_test_parameters',
        ],
    },
    'strategy_simulator_results_mixin.py': {
        'class_name': 'StrategySimulatorResultsMixin',
        'description': 'Result handling and optimization',
        'methods': [
            '_on_simulation_finished',
            '_handle_simulation_result',
            '_handle_simulation_run_result',
            '_resolve_result_objective_label',
            '_build_simulation_status',
            '_handle_optimization_result',
            '_log_optimization_errors',
            '_handle_no_trials',
            '_add_best_result',
            '_add_top_trials',
            '_build_optimization_status',
            '_finalize_all_run',
        ],
    },
    'strategy_simulator_ui_callbacks_mixin.py': {
        'class_name': 'StrategySimulatorUICallbacksMixin',
        'description': 'UI updates, progress tracking, and callbacks',
        'methods': [
            '_set_simulation_ui_state',
            '_log_simulation_start',
            '_on_simulation_progress',
            '_on_simulation_error',
            '_on_simulation_partial_result',
            '_on_simulation_strategy_started',
            '_log_simulator_to_ki',
            '_on_show_test_parameters',
        ],
    },
}

def extract_method(lines: List[str], method_name: str, start_line: int) -> tuple[int, int] | None:
    """Find method start and end lines."""
    method_start = None
    for i in range(start_line - 1, len(lines)):
        if f'def {method_name}(' in lines[i]:
            method_start = i + 1
            break

    if not method_start:
        return None

    indent_level = len(lines[method_start - 1]) - len(lines[method_start - 1].lstrip())
    method_end = None

    for i in range(method_start, len(lines)):
        line = lines[i]
        if line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent == indent_level and line.strip().startswith('def '):
                method_end = i
                break

    if not method_end:
        method_end = len(lines)

    return (method_start, method_end)

def get_common_imports() -> str:
    """Get common imports for all mixins."""
    return '''from __future__ import annotations

import logging
import pandas as pd
from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)

'''

def create_mixin(filename: str, config: dict[str, Any], source_lines: List[str]) -> bool:
    """Create a single mixin file."""
    print(f"\n📝 Creating {filename}...")

    all_method_lines = []
    for method_name in config['methods']:
        result = extract_method(source_lines, method_name, 1)
        if result:
            start, end = result
            all_method_lines.extend(source_lines[start-1:end-1])
            all_method_lines.append('\n')
        else:
            print(f"   ⚠️  Method {method_name} not found, skipping...")

    if not all_method_lines:
        print(f"   ❌ No methods found for {filename}")
        return False

    content = get_common_imports()
    content += f'class {config["class_name"]}:\n'
    content += f'    """{config["description"]}"""\n\n'

    for line in all_method_lines:
        content += line

    target_path = TARGET_DIR / filename
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(content)

    productive_loc = len([l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')])
    total_loc = len(content.split('\n'))

    print(f"   ✅ {total_loc} total LOC, {productive_loc} productive LOC")
    print(f"   🔧 {len(config['methods'])} methods included")

    return True

def main():
    """Create all mixins."""
    print("=" * 80)
    print("🔧 CREATING STRATEGY_SIMULATOR_RUN SUB-MIXINS")
    print("=" * 80)

    if not SOURCE_FILE.exists():
        print(f"❌ Source file not found: {SOURCE_FILE}")
        return

    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

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
        print("2. Create new strategy_simulator_run_mixin.py that inherits from all")
        print("3. Test that simulator still works")
        print("4. Commit changes")

if __name__ == "__main__":
    main()
