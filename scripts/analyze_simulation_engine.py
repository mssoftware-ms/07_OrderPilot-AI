"""
Analyze simulation_engine.py structure and categorize methods.
"""

from pathlib import Path
import re

SOURCE_FILE = Path("src/core/simulator/simulation_engine.py")

def analyze_methods():
    """Analyze all methods and their LOC."""
    with open(SOURCE_FILE, 'r') as f:
        lines = f.readlines()

    print("=" * 80)
    print("📊 SIMULATION_ENGINE.PY ANALYSIS")
    print("=" * 80)
    print(f"\nTotal lines: {len(lines)}")

    productive = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    print(f"Productive LOC: {productive}")

    # Find all methods
    methods = []
    for i, line in enumerate(lines, 1):
        if line.strip().startswith('def ') and line[0] == ' ':  # Class method
            method_name = line.strip().split('(')[0].replace('def ', '')
            methods.append((i, method_name))

    print(f"Total methods: {len(methods)}\n")

    # Calculate LOC per method
    method_locs = []
    for idx in range(len(methods)):
        start_line = methods[idx][0]
        end_line = methods[idx + 1][0] if idx + 1 < len(methods) else len(lines)
        method_lines = lines[start_line - 1:end_line - 1]
        method_loc = len([l for l in method_lines if l.strip() and not l.strip().startswith('#')])
        method_locs.append((methods[idx][1], method_loc, start_line, end_line - 1))

    # Categorize methods
    categories = {
        'Core Simulation': [
            '__init__', '_prepare_data', '_generate_signals',
            '_simulate_trades', '_run_entry_only_simulation', 'get_entry_exit_points'
        ],
        'Signal Wrappers': [
            '_breakout_signals', '_momentum_signals', '_mean_reversion_signals',
            '_trend_following_signals', '_scalping_signals', '_bollinger_squeeze_signals',
            '_trend_pullback_signals', '_opening_range_signals', '_regime_hybrid_signals'
        ],
        'Trade Management': [
            '_check_entry_signal', '_open_position', '_close_position',
            '_close_position_end', '_check_exit_conditions', '_update_trailing_stop'
        ],
        'Indicators': [
            '_calculate_bollinger_bands', '_calculate_adx', '_calculate_atr',
            '_calculate_rsi', '_calculate_obv', '_true_range'
        ],
        'Results & Metrics': [
            '_calculate_result', '_empty_result', '_calculate_trade_metrics',
            '_max_drawdown_pct', '_max_consecutive_runs', '_avg_trade_duration', '_risk_ratios'
        ]
    }

    # Print by category
    print("📂 METHODS BY CATEGORY:\n")
    for category, method_names in categories.items():
        print(f"  {category}:")
        category_loc = 0
        for name, loc, start, end in method_locs:
            if name in method_names:
                category_loc += loc
                print(f"    - {name:40s} {loc:4d} LOC (lines {start:4d}-{end:4d})")
        print(f"    TOTAL: {len([n for n in method_names if n in [m[0] for m in method_locs]])} methods, {category_loc} LOC\n")

    # Print largest methods
    print("\n📊 LARGEST METHODS (Top 10):\n")
    sorted_methods = sorted(method_locs, key=lambda x: x[1], reverse=True)[:10]
    for name, loc, start, end in sorted_methods:
        print(f"  {name:40s} {loc:4d} LOC")

    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)

    # Mixin proposal
    print("\n📋 MIXIN PROPOSAL:\n")
    print("1. simulation_indicators_mixin.py (~150 LOC)")
    print("   - Indicator calculations (6 methods)")
    print("\n2. simulation_trade_mixin.py (~300 LOC)")
    print("   - Trade management and trailing stop (6 methods)")
    print("\n3. simulation_results_mixin.py (~250 LOC)")
    print("   - Result calculation and metrics (7 methods)")
    print("\n4. simulation_signals_mixin.py (~36 LOC) - OPTIONAL")
    print("   - Signal wrapper methods (9 methods)")
    print("   - Could be removed and call _signal_generator directly")
    print("\n5. simulation_engine.py (main) (~200 LOC)")
    print("   - Core simulation logic (6 methods)")

if __name__ == "__main__":
    analyze_methods()
