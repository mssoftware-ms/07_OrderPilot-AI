"""
Rebuild backtest_tab.py with mixin inheritance - V2 (Fixed method extraction).

Creates new main file that:
- Inherits from all 7 mixins
- Keeps only methods not in mixins
- Properly extracts __init__ and all remaining methods
"""

from pathlib import Path
import re

SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/backtest_tab_pre_mixin_refactor.py")
TARGET_FILE = Path("src/ui/widgets/bitunix_trading/backtest_tab.py")

# Methods that ARE in mixins (will be removed from main file)
MIXIN_METHODS = {
    # UI Setup Mixin
    '_setup_ui', '_create_compact_button_row', '_create_setup_tab',
    '_create_execution_tab', '_create_kpi_card',

    # UI Results Mixin
    '_create_results_tab', '_update_metrics_table', '_update_trades_table',
    '_update_breakdown_table',

    # UI Batch Mixin
    '_create_batch_tab', '_update_batch_results_table', '_update_wf_results_table',

    # Callbacks Mixin
    '_on_batch_btn_clicked', '_on_wf_btn_clicked', '_on_save_template_clicked',
    '_on_load_template_clicked', '_on_derive_variant_clicked',
    '_on_auto_generate_clicked', '_on_load_configs_clicked', '_on_indicator_set_changed',

    # Config Mixin
    'collect_engine_configs', '_get_default_engine_configs', '_build_backtest_config',
    '_build_entry_config', 'get_parameter_specification', 'get_parameter_space_from_configs',
    '_convert_v2_to_parameters', '_get_nested_value',

    # Update Mixin
    '_on_progress_updated', '_on_log_message', '_log',

    # Export Mixin
    '_export_csv', '_export_equity_csv', '_export_json', '_export_batch_results',
    '_export_variants_json',
}

def find_method_end(lines, start_idx, method_indent):
    """Find the end of a method definition."""
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if not line.strip():  # Empty line
            continue

        current_indent = len(line) - len(line.lstrip())

        # If we hit a line at the same or lower indent level that starts a new def, we found the end
        if current_indent <= method_indent and line.strip().startswith('def '):
            return i

    return len(lines)  # End of file

def extract_method(lines, start_idx, end_idx):
    """Extract method lines from start to end."""
    return lines[start_idx:end_idx]

def rebuild_main_file():
    """Rebuild main backtest_tab.py with mixin inheritance."""
    print("=" * 80)
    print("🔧 REBUILDING BACKTEST_TAB.PY WITH MIXINS (V2)")
    print("=" * 80)

    # Read source file
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📁 Source: {SOURCE_FILE} ({len(lines)} lines)")

    # Find class definition line
    class_line_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith('class BacktestTab(QWidget):'):
            class_line_idx = i
            break

    if class_line_idx is None:
        print("❌ Could not find class definition")
        return

    # Find all methods in the class
    methods = []  # List of (method_name, start_idx, end_idx)
    for i in range(class_line_idx + 1, len(lines)):
        line = lines[i]
        if line.strip().startswith('def '):
            method_name = line.strip().split('(')[0].replace('def ', '')
            method_indent = len(line) - len(line.lstrip())
            end_idx = find_method_end(lines, i, method_indent)
            methods.append((method_name, i, end_idx))

    print(f"📊 Found {len(methods)} methods in class")

    # Separate methods to keep
    methods_to_keep = [(name, start, end) for name, start, end in methods if name not in MIXIN_METHODS]
    print(f"🔧 Keeping {len(methods_to_keep)} methods ({len(methods) - len(methods_to_keep)} moved to mixins)")

    # Build new content
    new_content = []

    # Part 1: Module docstring and imports (lines 1 to class definition)
    new_content.extend(lines[:class_line_idx])

    # Part 2: Mixin imports
    new_content.append('\n# Import mixins\n')
    new_content.append('from .backtest_tab_ui_setup_mixin import BacktestTabUISetupMixin\n')
    new_content.append('from .backtest_tab_ui_results_mixin import BacktestTabUIResultsMixin\n')
    new_content.append('from .backtest_tab_ui_batch_mixin import BacktestTabUIBatchMixin\n')
    new_content.append('from .backtest_tab_callbacks_mixin import BacktestTabCallbacksMixin\n')
    new_content.append('from .backtest_tab_config_mixin import BacktestTabConfigMixin\n')
    new_content.append('from .backtest_tab_update_mixin import BacktestTabUpdateMixin\n')
    new_content.append('from .backtest_tab_export_mixin import BacktestTabExportMixin\n')
    new_content.append('\n')

    # Part 3: New class definition with mixin inheritance
    new_content.append('class BacktestTab(\n')
    new_content.append('    BacktestTabUISetupMixin,\n')
    new_content.append('    BacktestTabUIResultsMixin,\n')
    new_content.append('    BacktestTabUIBatchMixin,\n')
    new_content.append('    BacktestTabCallbacksMixin,\n')
    new_content.append('    BacktestTabConfigMixin,\n')
    new_content.append('    BacktestTabUpdateMixin,\n')
    new_content.append('    BacktestTabExportMixin,\n')
    new_content.append('    QWidget\n')
    new_content.append('):\n')

    # Part 4: Class docstring and signals (from class_line_idx+1 to first method)
    first_method_idx = methods[0][1] if methods else len(lines)
    new_content.extend(lines[class_line_idx + 1:first_method_idx])

    # Part 5: Add methods to keep
    for method_name, start_idx, end_idx in methods_to_keep:
        method_lines = extract_method(lines, start_idx, end_idx)
        new_content.extend(method_lines)
        new_content.append('\n')

    # Write new file
    with open(TARGET_FILE, 'w', encoding='utf-8') as f:
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
    print("1. Validate syntax of new backtest_tab.py")
    print("2. Test imports")
    print("3. Commit changes")

if __name__ == "__main__":
    rebuild_main_file()
