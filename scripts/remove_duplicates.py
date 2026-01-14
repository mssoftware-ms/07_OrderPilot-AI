"""
Remove duplicate methods from backtest_tab.py and delegate to BacktestConfigVariants.

Removes:
- get_available_indicator_sets() (89 LOC)
- generate_ai_test_variants() (113 LOC)
Total: 202 LOC removed
"""

from pathlib import Path

SOURCE_FILE = Path("src/ui/widgets/bitunix_trading/backtest_tab.py")

def remove_duplicates():
    """Remove duplicate methods and add delegation."""
    print("=" * 80)
    print("🔧 REMOVING DUPLICATE METHODS")
    print("=" * 80)

    # Read original file
    with open(SOURCE_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    print(f"\n📊 Original file: {len(lines)} lines")

    # Find method boundaries
    get_indicator_start = None
    get_indicator_end = None
    generate_variants_start = None
    generate_variants_end = None

    for i, line in enumerate(lines, 1):
        if 'def get_available_indicator_sets(self)' in line and get_indicator_start is None:
            get_indicator_start = i
        elif get_indicator_start and 'def generate_ai_test_variants(self' in line and generate_variants_start is None:
            get_indicator_end = i - 1
            generate_variants_start = i
        elif generate_variants_start and i > generate_variants_start + 10:
            # Find next method definition
            if line.strip().startswith('def ') and 'generate_ai_test_variants' not in line:
                generate_variants_end = i - 1
                break

    if not all([get_indicator_start, get_indicator_end, generate_variants_start, generate_variants_end]):
        print("❌ Could not find all method boundaries")
        return

    print(f"\n📍 get_available_indicator_sets: lines {get_indicator_start}-{get_indicator_end} ({get_indicator_end - get_indicator_start + 1} lines)")
    print(f"📍 generate_ai_test_variants: lines {generate_variants_start}-{generate_variants_end} ({generate_variants_end - generate_variants_start + 1} lines)")

    # Build new content
    new_content = []

    # Part 1: Before first method
    new_content.extend(lines[:get_indicator_start - 1])

    # Part 2: Delegation methods (much shorter!)
    delegation_code = '''    def get_available_indicator_sets(self) -> list[Dict[str, Any]]:
        """Delegate to BacktestConfigVariants."""
        from .backtest_config_variants import BacktestConfigVariants
        variants = BacktestConfigVariants(self)
        return variants.get_available_indicator_sets()

    def generate_ai_test_variants(self, base_spec: list[Dict], num_variants: int = 10) -> list[Dict[str, Any]]:
        """Delegate to BacktestConfigVariants."""
        from .backtest_config_variants import BacktestConfigVariants
        variants = BacktestConfigVariants(self)
        return variants.generate_ai_test_variants(base_spec, num_variants)

'''
    new_content.append(delegation_code)

    # Part 3: After last method
    new_content.extend(lines[generate_variants_end:])

    # Write new file
    with open(SOURCE_FILE, 'w', encoding='utf-8') as f:
        f.writelines(new_content)

    original_size = len(lines)
    new_size = len(new_content)
    removed = original_size - new_size

    print(f"\n✅ New file: {new_size} lines")
    print(f"📉 Reduction: {removed} lines removed")
    print(f"📊 Delegation methods: ~15 LOC (vs {(get_indicator_end - get_indicator_start + 1) + (generate_variants_end - generate_variants_start + 1)} LOC)")
    print("\n" + "=" * 80)
    print("✅ DUPLICATE REMOVAL COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    remove_duplicates()
