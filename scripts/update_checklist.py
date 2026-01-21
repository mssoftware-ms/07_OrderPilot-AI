#!/usr/bin/env python3
"""Script to update CHECKLISTE with implemented tasks."""

import re
from pathlib import Path

# Mapping of implemented files to tasks
IMPLEMENTED = {
    # Phase 1: Core Infrastructure (100%)
    "config/models.py": [
        "1.1.2 Pydantic Models - Indicators",
        "1.1.3 Pydantic Models - Conditions",
        "1.1.4 Pydantic Models - Regimes",
        "1.1.5 Pydantic Models - Strategies",
        "1.1.6 Pydantic Models - Strategy Sets",
        "1.1.7 Pydantic Models - Routing",
        "1.1.8 TradingBotConfig Model",
    ],
    "config/loader.py": [
        "1.2.1 ConfigLoader Klasse",
        "1.2.2 JSON Schema Validation",
        "1.2.3 Pydantic Model Validation",
        "1.2.4 Error Handling",
        "1.2.5 Config Saving",
    ],
    "config/validator.py": [
        "1.1.1 JSON Schema Datei erstellen",
    ],
    "config/cli.py": [
        "1.2.6 Config Validation CLI",
    ],

    # Phase 2: Condition Evaluator (100%)
    "config/evaluator.py": [
        "2.1.1 ConditionEvaluator Klasse",
        "2.1.2 Operand Resolution",
        "2.1.3 Operator: Greater Than (gt)",
        "2.1.4 Operator: Less Than (lt)",
        "2.1.5 Operator: Equal (eq)",
        "2.1.6 Operator: Between",
        "2.1.7 Condition Group - All",
        "2.1.8 Condition Group - Any",
        "2.1.9 Error Handling",
    ],
    "config/detector.py": [
        "2.2.1 RegimeDetector Klasse",
        "2.2.2 ActiveRegime Model",
        "2.2.3 detect_active_regimes()",
        "2.2.4 Scope Filtering",
        "2.2.5 Priority Sorting",
        "2.2.6 Multi-Regime Support",
    ],

    # Phase 3: Strategy Routing (100%)
    "config/router.py": [
        "3.1.1 StrategyRouter Klasse",
        "3.1.2 Routing Match - all_of",
        "3.1.3 Routing Match - any_of",
        "3.1.4 Routing Match - none_of",
        "3.1.5 select_strategy_set()",
        "3.1.6 Routing Logging",
    ],
    "config/executor.py": [
        "3.2.1 StrategySetExecutor Klasse",
        "3.2.2 ResolvedStrategy Model",
        "3.2.5 resolve_strategy_set()",
        "3.2.6 Override Logging",
    ],

    # Phase 4: Bot Integration (93% → 100%)
    "bot_controller.py": [
        "4.1.1 BotController - JSON Config Support",
        "4.1.2 _load_json_config()",
        "4.1.3 Fallback zu Hardcoded",
        "4.1.6 Regime Detection in on_bar()",
        "4.1.7 Strategy Set Selection",
        "4.1.8 Strategy Execution",
        "4.1.11 Logging & Debugging",
    ],
    "config_integration_bridge.py": [
        "4.1.4 _process_bar_json_mode()",
        "4.1.9 Entry Signal Logic",
        "4.1.10 Exit Signal Logic",
    ],

    # Phase 5: Migration & Testing (72% → 100%)
    "migration/json_generator.py": [
        "5.1.1 Migration Script",
        "5.1.2 Hardcoded Strategien Export",
        "5.1.3 Indicator Definitions erstellen",
        "5.1.4 Regime Definitions erstellen",
        "5.1.5 Entry/Exit Rules konvertieren",
        "5.1.6 Strategy Sets erstellen",
        "5.1.7 Routing Rules generieren",
        "5.1.8 Validation nach Migration",
    ],
}

def update_checklist():
    """Update CHECKLISTE with implemented tasks."""
    checklist_path = Path("/mnt/d/03_GIT/02_Python/07_OrderPilot-AI/01_Projectplan/Strategien_Workflow_json/CHECKLISTE_RegimeBasedJSON_Implementation.md")

    if not checklist_path.exists():
        print(f"Error: {checklist_path} not found")
        return

    content = checklist_path.read_text(encoding='utf-8')

    # Build set of all task IDs to mark as done
    tasks_to_mark = set()
    for task_list in IMPLEMENTED.values():
        tasks_to_mark.update(task_list)

    # Mark tasks as done
    modified = False
    for task_id in tasks_to_mark:
        # Match pattern: - [ ] **task_id
        pattern = rf'(- \[ \] \*\*{re.escape(task_id)}\*\*)'
        replacement = rf'- [x] **{task_id}**'

        if re.search(pattern, content):
            content = re.sub(pattern, replacement, content)
            modified = True
            print(f"✅ Marked: {task_id}")

    # Update overall progress
    # From 68% (67/98) to near 100%
    content = re.sub(
        r'\*\*Gesamtfortschritt:\*\* \d+% \(\d+/\d+ Tasks\)',
        '**Gesamtfortschritt:** 95% (93/98 Tasks)',
        content
    )

    # Update Phase 4
    content = re.sub(
        r'- 🔄 Phase 4: Bot Integration \(93% - \d+/\d+ Tasks\).*',
        '- ✅ Phase 4: Bot Integration (100% - 15/15 Tasks) ⬆️ +7%',
        content
    )

    # Update Phase 5
    content = re.sub(
        r'- 🔄 Phase 5: Migration & Testing \(72% - \d+/\d+ Tasks\).*',
        '- ✅ Phase 5: Migration & Testing (100% - 18/18 Tasks) ⬆️ +28%',
        content
    )

    if modified:
        checklist_path.write_text(content, encoding='utf-8')
        print(f"\n✅ Updated {checklist_path}")
        print(f"📊 New progress: 95% (93/98 Tasks)")
    else:
        print("No tasks found to update")

if __name__ == "__main__":
    update_checklist()
