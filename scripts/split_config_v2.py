"""
Automatic splitter for config_v2.py into multiple modules.

Splits based on class categories and line ranges.
"""

import ast
import os
from pathlib import Path
from typing import List, Tuple

# Define splitting strategy
SPLITS = {
    'enums.py': {
        'description': 'All enum types',
        'line_ranges': [(37, 118)],  # All enums
        'imports': ['from enum import Enum']
    },
    'optimizable.py': {
        'description': 'Optimizable parameter types + WeightPreset',
        'line_ranges': [(127, 263)],  # OptimizableFloat, OptimizableInt, WeightPreset
        'imports': [
            'from dataclasses import dataclass, field',
            'from typing import Any, Dict, List, Optional, Union'
        ]
    },
    'indicators.py': {
        'description': 'Indicator parameters and meta sections',
        'line_ranges': [(280, 323), (373, 413)],  # MetaSection, IndicatorParams
        'imports': [
            'from dataclasses import dataclass, field',
            'from typing import Any, Dict, List, Optional',
            'from .enums import StrategyType, AssetClass',
            'from .optimizable import OptimizableFloat, OptimizableInt'
        ]
    },
    'entry.py': {
        'description': 'Entry score configs and triggers',
        'line_ranges': [(327, 369), (417, 591)],  # StrategyProfileSection + EntryScore + Triggers
        'imports': [
            'from dataclasses import dataclass, field',
            'from typing import Any, Dict, List, Optional',
            'from .enums import WeightPresetName, DirectionBias',
            'from .optimizable import OptimizableFloat, OptimizableInt, WeightPreset',
            'from .indicators import IndicatorParams'
        ]
    },
    'exit.py': {
        'description': 'Exit management configs (SL/TP/Trailing)',
        'line_ranges': [(595, 759)],  # StopLoss, TakeProfit, Trailing, PartialTP, TimeStop, ExitManagement
        'imports': [
            'from dataclasses import dataclass, field',
            'from typing import Any, Dict, Optional',
            'from .enums import StopLossType, TakeProfitType, TrailingType',
            'from .optimizable import OptimizableFloat'
        ]
    },
    'risk.py': {
        'description': 'Risk/Leverage and execution/simulation configs',
        'line_ranges': [(763, 847)],  # RiskLeverage + ExecutionSimulation
        'imports': [
            'from dataclasses import dataclass, field',
            'from typing import Optional',
            'from .enums import SlippageMethod',
            'from .optimizable import OptimizableFloat, OptimizableInt'
        ]
    },
    'optimization.py': {
        'description': 'Optimization, WalkForward, Constraints',
        'line_ranges': [(851, 1014)],  # Optimization + WalkForward + ParameterGroup + Conditional + Constraints
        'imports': [
            'from dataclasses import dataclass, field',
            'from datetime import datetime',
            'from typing import Any, Dict, List, Optional',
            'from .enums import OptimizationMethod, TargetMetric'
        ]
    },
    'main.py': {
        'description': 'Main BacktestConfigV2 class',
        'line_ranges': [(1023, 1197)],  # BacktestConfigV2
        'imports': [
            'import json',
            'import logging',
            'from dataclasses import dataclass, field',
            'from datetime import datetime',
            'from pathlib import Path',
            'from typing import Any, Dict, List, Optional',
            'from .indicators import MetaSection',
            'from .entry import StrategyProfileSection, EntryScoreSection, EntryTriggersSection',
            'from .exit import ExitManagementSection, TimeStopConfig',
            'from .risk import RiskLeverageSection, ExecutionSimulationSection',
            'from .optimization import OptimizationSection, WalkForwardSection, ConstraintsSection'
        ]
    }
}

def extract_lines(filepath: Path, start: int, end: int) -> List[str]:
    """Extract lines from file (1-indexed)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    return lines[start-1:end]

def create_module(output_dir: Path, module_name: str, config: dict, source_file: Path):
    """Create a module file from line ranges."""
    output_file = output_dir / module_name

    # Build content
    content_lines = []

    # Module docstring
    content_lines.append('"""\n')
    content_lines.append(f'Backtesting Configuration - {config["description"]}\n')
    content_lines.append('"""\n\n')
    content_lines.append('from __future__ import annotations\n\n')

    # Imports
    for imp in config['imports']:
        content_lines.append(f'{imp}\n')
    content_lines.append('\n')

    if module_name == 'main.py':
        content_lines.append('logger = logging.getLogger(__name__)\n\n')

    # Extract class definitions from source
    for start, end in config['line_ranges']:
        lines = extract_lines(source_file, start, end)
        content_lines.extend(lines)
        content_lines.append('\n')

    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(content_lines)

    print(f"✅ Created: {output_file}")

def create_init_file(output_dir: Path):
    """Create __init__.py with all re-exports for backwards compatibility."""
    init_content = '''"""
Backtesting Configuration Package

For backwards compatibility, all classes are re-exported here.
"""

# Enums
from .enums import (
    StrategyType,
    WeightPresetName,
    DirectionBias,
    ScenarioType,
    AssetClass,
    StopLossType,
    TakeProfitType,
    TrailingType,
    SlippageMethod,
    OptimizationMethod,
    TargetMetric,
)

# Optimizable Types
from .optimizable import OptimizableFloat, OptimizableInt, WeightPreset

# Indicators
from .indicators import MetaSection, IndicatorParams

# Entry
from .entry import (
    StrategyProfileSection,
    EntryScoreGates,
    EntryScoreSection,
    BreakoutTrigger,
    PullbackTrigger,
    SfpTrigger,
    EntryTriggersSection,
)

# Exit
from .exit import (
    StopLossConfig,
    TakeProfitConfig,
    TrailingStopConfig,
    PartialTPConfig,
    TimeStopConfig,
    ExitManagementSection,
)

# Risk
from .risk import RiskLeverageSection, ExecutionSimulationSection

# Optimization
from .optimization import (
    OptimizationSection,
    WalkForwardSection,
    ParameterGroup,
    Conditional,
    ConstraintsSection,
)

# Main
from .main import BacktestConfigV2

__all__ = [
    # Enums
    "StrategyType",
    "WeightPresetName",
    "DirectionBias",
    "ScenarioType",
    "AssetClass",
    "StopLossType",
    "TakeProfitType",
    "TrailingType",
    "SlippageMethod",
    "OptimizationMethod",
    "TargetMetric",
    # Optimizable
    "OptimizableFloat",
    "OptimizableInt",
    "WeightPreset",
    # Indicators
    "MetaSection",
    "IndicatorParams",
    # Entry
    "StrategyProfileSection",
    "EntryScoreGates",
    "EntryScoreSection",
    "BreakoutTrigger",
    "PullbackTrigger",
    "SfpTrigger",
    "EntryTriggersSection",
    # Exit
    "StopLossConfig",
    "TakeProfitConfig",
    "TrailingStopConfig",
    "PartialTPConfig",
    "TimeStopConfig",
    "ExitManagementSection",
    # Risk
    "RiskLeverageSection",
    "ExecutionSimulationSection",
    # Optimization
    "OptimizationSection",
    "WalkForwardSection",
    "ParameterGroup",
    "Conditional",
    "ConstraintsSection",
    # Main
    "BacktestConfigV2",
]
'''

    init_file = output_dir / '__init__.py'
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(init_content)

    print(f"✅ Created: {init_file}")

def main():
    """Run the splitter."""
    source_file = Path('src/core/backtesting/config_v2.py')
    output_dir = Path('src/core/backtesting/configs')

    if not source_file.exists():
        print(f"❌ Source file not found: {source_file}")
        return

    output_dir.mkdir(exist_ok=True)

    print("=" * 80)
    print("🔄 SPLITTING config_v2.py INTO MODULES")
    print("=" * 80)

    # Create modules
    for module_name, config in SPLITS.items():
        create_module(output_dir, module_name, config, source_file)

    # Create __init__.py
    create_init_file(output_dir)

    print("\n" + "=" * 80)
    print("✅ SPLITTING COMPLETE")
    print("=" * 80)
    print(f"\nModules created in: {output_dir}")
    print(f"Total modules: {len(SPLITS) + 1} (including __init__.py)")
    print("\nNext steps:")
    print("1. Update imports in config_v2.py to use: from .configs import BacktestConfigV2")
    print("2. Or rename config_v2.py to config_v2_old.py and configs/__init__.py becomes the new entry point")
    print("3. Test all imports still work")

if __name__ == "__main__":
    main()
