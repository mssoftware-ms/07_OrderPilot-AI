"""
Rebuild backtest_tab.py with mixin inheritance.

Creates new main file that:
- Inherits from all 7 mixins
- Keeps only methods not in mixins
- Follows same pattern as bot_tab.py
"""

from pathlib import Path

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

def extract_methods_to_keep(source_lines):
    """Extract methods that should stay in main file."""
    methods_content = []
    current_method = []
    in_method = False
    method_name = None
    method_indent = None

    for i, line in enumerate(source_lines):
        # Check if starting new method
        if line.strip().startswith('def '):
            # Save previous method if it should be kept
            if current_method and method_name and method_name not in MIXIN_METHODS:
                methods_content.extend(current_method)
                methods_content.append('\n')

            # Start new method
            current_method = [line]
            in_method = True
            method_name = line.strip().split('(')[0].replace('def ', '')
            method_indent = len(line) - len(line.lstrip())

        elif in_method:
            current_line_indent = len(line) - len(line.lstrip())

            # Check if we're still in the method
            if line.strip() and current_line_indent <= method_indent:
                # End of method
                if method_name not in MIXIN_METHODS:
                    methods_content.extend(current_method)
                    methods_content.append('\n')
                current_method = []
                in_method = False
                method_name = None

                # This line might be start of new method
                if line.strip().startswith('def '):
                    current_method = [line]
                    in_method = True
                    method_name = line.strip().split('(')[0].replace('def ', '')
                    method_indent = len(line) - len(line.lstrip())
            else:
                # Continue current method
                current_method.append(line)

    # Don't forget last method
    if current_method and method_name and method_name not in MIXIN_METHODS:
        methods_content.extend(current_method)

    return methods_content

def rebuild_main_file():
    """Rebuild main backtest_tab.py with mixin inheritance."""
    print("=" * 80)
    print("🔧 REBUILDING BACKTEST_TAB.PY WITH MIXINS")
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

    if not class_line_idx:
        print("❌ Could not find class definition")
        return

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

    # Part 4: Class docstring and signals (find them in original)
    for i in range(class_line_idx + 1, min(class_line_idx + 20, len(lines))):
        line = lines[i]
        if 'def __init__' in line:
            break
        new_content.append(line)

    # Part 5: Extract methods from __init__ onwards that are NOT in mixins
    remaining_lines = lines[class_line_idx + 1:]
    methods_to_keep = extract_methods_to_keep(remaining_lines)
    new_content.extend(methods_to_keep)

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
    print(f"🔧 Methods moved to mixins: {len(MIXIN_METHODS)}")

    print("\n" + "=" * 80)
    print("✅ REBUILD COMPLETE")
    print("=" * 80)
    print("\n📋 NEXT STEPS:")
    print("1. Validate syntax of new backtest_tab.py")
    print("2. Test imports")
    print("3. Commit changes")

if __name__ == "__main__":
    rebuild_main_file()
