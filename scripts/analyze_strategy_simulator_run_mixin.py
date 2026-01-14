"""
Analyze strategy_simulator_run_mixin.py structure.
"""

from pathlib import Path

SOURCE_FILE = Path("src/ui/widgets/chart_window_mixins/strategy_simulator_run_mixin.py")

def analyze():
    """Analyze the file structure."""
    with open(SOURCE_FILE, 'r') as f:
        lines = f.readlines()

    print("=" * 80)
    print("📊 STRATEGY_SIMULATOR_RUN_MIXIN.PY ANALYSIS")
    print("=" * 80)
    print(f"\nTotal lines: {len(lines)}")

    productive = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    print(f"Productive LOC: {productive}")

    # Count methods
    methods = []
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('def ') and line[0] == ' ':
            method_name = line.strip().split('(')[0].replace('def ', '')
            methods.append((i, method_name))

    print(f"Total methods: {len(methods)}\n")

    # Categorize methods
    categories = {
        'Simulation Execution': [
            '_on_run_simulation', '_start_simulation_with_data',
            '_start_simulation_with_visible_range', '_on_stop_simulation',
            '_cleanup_simulation_worker',
        ],
        'Data Handling': [
            '_filter_data_to_time_range', '_filter_data_to_visible_range',
            '_get_chart_dataframe', '_get_full_chart_dataframe',
            '_get_data_range_info', '_fill_date_range',
        ],
        'Settings Collection': [
            '_get_trigger_exit_settings', '_get_all_bot_settings',
            '_collect_simulation_params', '_prepare_simulation_run',
            '_collect_all_test_parameters',
        ],
        'Worker Management': [
            '_create_simulation_worker', '_wire_simulation_worker',
            '_resolve_simulation_mode',
        ],
        'Result Handling': [
            '_on_simulation_finished', '_handle_simulation_result',
            '_handle_simulation_run_result', '_handle_optimization_result',
            '_add_best_result', '_add_top_trials', '_build_optimization_status',
            '_resolve_result_objective_label', '_build_simulation_status',
            '_log_optimization_errors', '_handle_no_trials', '_finalize_all_run',
        ],
        'UI & Callbacks': [
            '_set_simulation_ui_state', '_log_simulation_start',
            '_on_simulation_progress', '_on_simulation_error',
            '_on_simulation_partial_result', '_on_simulation_strategy_started',
            '_log_simulator_to_ki', '_on_show_test_parameters',
        ],
        'Utility': [
            '_get_simulation_symbol',
        ],
    }

    print("📂 PROPOSED MIXIN SPLIT:\n")
    print("1. strategy_simulator_execution_mixin.py (~150 LOC)")
    print("   - Simulation execution flow (5 methods)")
    print("\n2. strategy_simulator_data_mixin.py (~150 LOC)")
    print("   - Data filtering and chart access (6 methods)")
    print("\n3. strategy_simulator_settings_mixin.py (~250 LOC)")
    print("   - Settings collection from UI widgets (5 methods)")
    print("\n4. strategy_simulator_results_mixin.py (~200 LOC)")
    print("   - Result handling and optimization (12 methods)")
    print("\n5. strategy_simulator_ui_mixin.py (~100 LOC)")
    print("   - UI updates and callbacks (8 methods)")
    print("\n6. strategy_simulator_run_mixin.py (main) (~50 LOC)")
    print("   - Coordination and utility (3 methods)")

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    analyze()
