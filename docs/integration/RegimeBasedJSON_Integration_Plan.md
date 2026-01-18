# Regime-Based JSON Strategy System - Integrationsplan

**Projekt:** OrderPilot-AI - Regime-Based JSON Configuration
**Version:** 2.0
**Datum:** 2026-01-18
**Basis:** `01_Projectplan/Strategien_Workflow_json/json Format Strategien Indikatoren.md`

---

## 📋 Executive Summary

### Ziel
Migration von hardcodierten Strategien zu einem **Regime-basierten JSON-Konfigurationssystem** mit:

1. **Multi-Timeframe Indikatoren** - Indikatoren auf verschiedenen Zeitrahmen
2. **Regime Detection** - Automatische Marktphasen-Erkennung (Trend, Range, Low-Volume)
3. **Strategy Sets** - Strategiebündel mit Parameter-Overrides
4. **Dynamic Routing** - Regime → Strategy-Set Zuordnung
5. **Condition System** - Flexible Bedingungslogik (gt, lt, eq, between mit all/any)

### Kernkonzept
Statt einzelner Strategien arbeitet das System mit **Regimes** (Marktphasen), die **Strategy-Sets** aktivieren. Mehrere Regimes können gleichzeitig aktiv sein (Entry-Regime, Exit-Regime), und Routing-Regeln bestimmen die aktive Strategie-Konfiguration.

---

## 🏗️ Architekturüberblick

### Aktuelles System (Hardcoded)
```
BotController
    ↓
StrategyCatalog (9 hardcoded strategies)
    ↓
StrategyDefinition (Pydantic)
    ↓
EntryExitEngine
```

**Probleme:**
- ❌ Keine Multi-Timeframe Support
- ❌ Statische Regime-Erkennung
- ❌ Keine Parameter-Anpassung basierend auf Marktphase
- ❌ Keine dynamische Strategie-Selektion

### Neues System (JSON-basiert)
```
BotController
    ↓
ConfigLoader (JSON)
    ↓
    ├─→ Indicators (Multi-Timeframe)
    ├─→ RegimeDetector (Condition Evaluator)
    ├─→ StrategyRouter (Regime → Strategy-Set)
    └─→ StrategySetExecutor (mit Overrides)
        ↓
    EntryExitEngine
```

**Vorteile:**
- ✅ Multi-Timeframe Indikatoren
- ✅ Dynamische Regime-Erkennung
- ✅ Parameter-Overrides pro Regime
- ✅ Flexible Routing-Regeln
- ✅ Keine Code-Änderungen für neue Strategien

---

## 📐 JSON Schema - Komponenten

### 1. Indicators (Multi-Timeframe)
**Zweck:** Definiert technische Indikatoren mit Parametern und optionalem Timeframe

```json
{
  "indicators": [
    {
      "id": "rsi14_1h",
      "type": "RSI",
      "params": { "period": 14 },
      "timeframe": "1h"
    },
    {
      "id": "adx14_4h",
      "type": "ADX",
      "params": { "period": 14 },
      "timeframe": "4h"
    }
  ]
}
```

**Implementierung:**
- `IndicatorDefinition` (Pydantic Model)
- `IndicatorEngine` berechnet Indikatoren auf verschiedenen Timeframes
- ID-basierte Referenzierung in Conditions

### 2. Regimes (Marktphasen)
**Zweck:** Definiert Marktregimes mit Aktivierungsbedingungen

```json
{
  "regimes": [
    {
      "id": "trend",
      "name": "Trending Market",
      "scope": "entry",
      "priority": 10,
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "adx14_1h", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          },
          {
            "left": { "indicator_id": "adx14_4h", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          }
        ]
      }
    },
    {
      "id": "exit_low_vol",
      "name": "Exit Regime - Low Volume",
      "scope": "exit",
      "conditions": {
        "all": [
          {
            "left": { "indicator_id": "vol_ratio_1h", "field": "value" },
            "op": "lt",
            "right": { "value": 0.5 }
          }
        ]
      }
    }
  ]
}
```

**Wichtig:**
- **Mehrere Regimes gleichzeitig aktiv** (Entry + Exit + InTrade)
- **Scope:** `entry`, `exit`, `in_trade` (optional, default = global)
- **Priority:** Auflösung von Konflikten

### 3. Strategies (Entry/Exit/Risk)
**Zweck:** Einzelne Handelsstrategien mit Bedingungen

```json
{
  "strategies": [
    {
      "id": "trend_follow",
      "name": "Trend Following",
      "entry": {
        "all": [
          {
            "left": { "indicator_id": "adx14_1h", "field": "value" },
            "op": "gt",
            "right": { "value": 25 }
          },
          {
            "left": { "indicator_id": "rsi14_1h", "field": "value" },
            "op": "gt",
            "right": { "value": 60 }
          }
        ]
      },
      "exit": {
        "any": [
          {
            "left": { "indicator_id": "adx14_1h", "field": "value" },
            "op": "lt",
            "right": { "value": 20 }
          },
          {
            "left": { "indicator_id": "rsi14_1h", "field": "value" },
            "op": "lt",
            "right": { "value": 40 }
          }
        ]
      },
      "risk": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 5.0,
        "trailing_mode": "atr",
        "trailing_multiplier": 1.5
      }
    }
  ]
}
```

### 4. Strategy Sets (mit Overrides)
**Zweck:** Bündel von Strategien mit anpassbaren Parametern

```json
{
  "strategy_sets": [
    {
      "id": "set_trend_exit",
      "name": "Trend - Exit Signals Active",
      "strategies": [
        {
          "strategy_id": "trend_follow",
          "strategy_overrides": {
            "risk": {
              "stop_loss_pct": 1.0,
              "take_profit_pct": 2.0
            }
          }
        }
      ],
      "indicator_overrides": [
        {
          "indicator_id": "rsi14_1h",
          "params": { "period": 21 }
        }
      ]
    }
  ]
}
```

**Wichtig:**
- Keine Duplikate - Basis-Strategie wird referenziert
- `strategy_overrides` - Override Entry/Exit/Risk
- `indicator_overrides` - Override Indikator-Parameter

### 5. Routing (Regime → Strategy-Set)
**Zweck:** Zuordnung von Regime-Kombinationen zu Strategy-Sets

```json
{
  "routing": [
    {
      "strategy_set_id": "set_trend_normal",
      "match": {
        "all_of": ["entry_trend"],
        "none_of": ["exit_low_vol", "exit_trend_reversal"]
      }
    },
    {
      "strategy_set_id": "set_trend_exit",
      "match": {
        "all_of": ["entry_trend"],
        "any_of": ["exit_low_vol", "exit_trend_reversal"]
      }
    }
  ]
}
```

**Matching-Logic:**
- `all_of`: Alle genannten Regimes müssen aktiv sein
- `any_of`: Mindestens eines muss aktiv sein
- `none_of`: Keines darf aktiv sein

---

## 🔧 Implementierungsplan

### Phase 1: Core Infrastructure (Woche 1-2)

#### 1.1 JSON Schema & Validation
**Datei:** `src/core/tradingbot/config/schema.json`
- Kopiere Schema aus Projektplan
- Erstelle JSON Schema Validator

**Datei:** `src/core/tradingbot/config/models.py`
```python
from pydantic import BaseModel, Field
from enum import Enum

class IndicatorType(str, Enum):
    RSI = "RSI"
    MACD = "MACD"
    ADX = "ADX"
    SMA = "SMA"
    EMA = "EMA"
    ATR = "ATR"
    BB = "BollingerBands"
    STOCH = "Stochastic"
    VOLUME_RATIO = "VolumeRatio"

class ConditionOperator(str, Enum):
    GT = "gt"     # Greater than
    LT = "lt"     # Less than
    EQ = "eq"     # Equal
    BETWEEN = "between"

class IndicatorRef(BaseModel):
    indicator_id: str
    field: str

class ConstantValue(BaseModel):
    value: float

class BetweenRange(BaseModel):
    min: float
    max: float

class Condition(BaseModel):
    left: IndicatorRef | ConstantValue
    op: ConditionOperator
    right: IndicatorRef | ConstantValue | BetweenRange

class ConditionGroup(BaseModel):
    all: list[Condition] | None = None
    any: list[Condition] | None = None

class IndicatorDefinition(BaseModel):
    id: str
    type: IndicatorType
    params: dict[str, Any]
    timeframe: str | None = None  # e.g., "1h", "4h", "1d"

class RegimeScope(str, Enum):
    ENTRY = "entry"
    EXIT = "exit"
    IN_TRADE = "in_trade"

class RegimeDefinition(BaseModel):
    id: str
    name: str
    conditions: ConditionGroup
    priority: int = 0
    scope: RegimeScope | None = None

class RiskSettings(BaseModel):
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    trailing_mode: str | None = None
    trailing_multiplier: float | None = None
    risk_per_trade_pct: float | None = None

class StrategyDefinitionJson(BaseModel):
    id: str
    name: str
    entry: ConditionGroup | None = None
    exit: ConditionGroup | None = None
    risk: RiskSettings | None = None

class StrategyOverride(BaseModel):
    entry: ConditionGroup | None = None
    exit: ConditionGroup | None = None
    risk: RiskSettings | None = None

class StrategyInSet(BaseModel):
    strategy_id: str
    strategy_overrides: StrategyOverride | None = None

class IndicatorOverride(BaseModel):
    indicator_id: str
    params: dict[str, Any]

class StrategySet(BaseModel):
    id: str
    name: str | None = None
    strategies: list[StrategyInSet]
    indicator_overrides: list[IndicatorOverride] | None = None

class RoutingMatch(BaseModel):
    all_of: list[str] | None = None
    any_of: list[str] | None = None
    none_of: list[str] | None = None

class RoutingRule(BaseModel):
    strategy_set_id: str
    match: RoutingMatch

class TradingBotConfig(BaseModel):
    schema_version: str
    metadata: dict[str, Any] | None = None
    indicators: list[IndicatorDefinition]
    regimes: list[RegimeDefinition]
    strategies: list[StrategyDefinitionJson]
    strategy_sets: list[StrategySet]
    routing: list[RoutingRule]
```

#### 1.2 Config Loader
**Datei:** `src/core/tradingbot/config/loader.py`
```python
import json
import jsonschema
from pathlib import Path
from typing import Optional

from .models import TradingBotConfig

class ConfigLoadError(Exception):
    """Configuration loading error."""
    pass

class ConfigLoader:
    """Load and validate trading bot JSON configuration."""

    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self.schema = self._load_schema()

    def _load_schema(self) -> dict:
        """Load JSON schema."""
        with open(self.schema_path) as f:
            return json.load(f)

    def load_config(self, config_path: Path) -> TradingBotConfig:
        """Load and validate configuration.

        Args:
            config_path: Path to JSON config file

        Returns:
            Validated TradingBotConfig

        Raises:
            ConfigLoadError: On validation failure
        """
        try:
            with open(config_path) as f:
                data = json.load(f)

            # JSON Schema validation
            jsonschema.validate(data, self.schema)

            # Pydantic validation
            return TradingBotConfig.model_validate(data)

        except json.JSONDecodeError as e:
            raise ConfigLoadError(f"Invalid JSON: {e}")
        except jsonschema.ValidationError as e:
            raise ConfigLoadError(f"Schema validation failed: {e.message}")
        except Exception as e:
            raise ConfigLoadError(f"Config load failed: {e}")

    def save_config(
        self,
        config: TradingBotConfig,
        file_path: Path,
        validate: bool = True
    ) -> None:
        """Save configuration to JSON file.

        Args:
            config: Configuration to save
            file_path: Target file path
            validate: Run validation before saving
        """
        data = config.model_dump(exclude_none=True, mode='json')

        if validate:
            jsonschema.validate(data, self.schema)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
```

---

### Phase 2: Condition Evaluator (Woche 2-3)

#### 2.1 Condition Evaluator
**Datei:** `src/core/tradingbot/regime/condition_evaluator.py`
```python
from typing import Dict, Any
from ..config.models import Condition, ConditionGroup, ConditionOperator

class ConditionEvaluator:
    """Evaluate condition expressions against indicator values."""

    def __init__(self, indicator_values: Dict[str, Dict[str, float]]):
        """
        Args:
            indicator_values: Dict mapping indicator_id -> field -> value
                Example: {"rsi14_1h": {"value": 65.3}, "adx14_1h": {"value": 28.5}}
        """
        self.indicator_values = indicator_values

    def evaluate_condition(self, condition: Condition) -> bool:
        """Evaluate single condition.

        Returns:
            True if condition is met, False otherwise
        """
        left_value = self._resolve_operand(condition.left)
        right_value = self._resolve_operand(condition.right)

        if condition.op == ConditionOperator.GT:
            return left_value > right_value
        elif condition.op == ConditionOperator.LT:
            return left_value < right_value
        elif condition.op == ConditionOperator.EQ:
            return abs(left_value - right_value) < 1e-6
        elif condition.op == ConditionOperator.BETWEEN:
            # right_value is BetweenRange
            return condition.right.min <= left_value <= condition.right.max
        else:
            raise ValueError(f"Unknown operator: {condition.op}")

    def evaluate_group(self, group: ConditionGroup) -> bool:
        """Evaluate condition group (all/any logic).

        Returns:
            True if group conditions are met
        """
        if group.all:
            return all(self.evaluate_condition(c) for c in group.all)
        elif group.any:
            return any(self.evaluate_condition(c) for c in group.any)
        else:
            return True  # Empty group = always true

    def _resolve_operand(self, operand: Any) -> float:
        """Resolve operand to numeric value.

        Args:
            operand: IndicatorRef, ConstantValue, or BetweenRange

        Returns:
            Numeric value
        """
        if hasattr(operand, 'indicator_id'):
            # IndicatorRef
            indicator_data = self.indicator_values.get(operand.indicator_id, {})
            value = indicator_data.get(operand.field)
            if value is None:
                raise ValueError(
                    f"Indicator {operand.indicator_id}.{operand.field} not found"
                )
            return float(value)
        elif hasattr(operand, 'value'):
            # ConstantValue
            return float(operand.value)
        else:
            raise ValueError(f"Unknown operand type: {type(operand)}")
```

#### 2.2 Regime Detector
**Datei:** `src/core/tradingbot/regime/regime_detector.py`
```python
from typing import List, Dict
from ..config.models import RegimeDefinition, RegimeScope
from .condition_evaluator import ConditionEvaluator

class ActiveRegime:
    """Represents an active regime instance."""
    def __init__(self, definition: RegimeDefinition, confidence: float = 1.0):
        self.definition = definition
        self.confidence = confidence

    @property
    def id(self) -> str:
        return self.definition.id

    @property
    def scope(self) -> RegimeScope | None:
        return self.definition.scope

class RegimeDetector:
    """Detect active market regimes based on indicator values."""

    def __init__(self, regime_definitions: List[RegimeDefinition]):
        self.regime_definitions = regime_definitions

    def detect_active_regimes(
        self,
        indicator_values: Dict[str, Dict[str, float]]
    ) -> List[ActiveRegime]:
        """Detect all currently active regimes.

        Args:
            indicator_values: Current indicator values

        Returns:
            List of active regimes
        """
        evaluator = ConditionEvaluator(indicator_values)
        active = []

        for regime_def in self.regime_definitions:
            if evaluator.evaluate_group(regime_def.conditions):
                active.append(ActiveRegime(regime_def))

        # Sort by priority (higher first)
        active.sort(key=lambda r: r.definition.priority, reverse=True)

        return active

    def get_regimes_by_scope(
        self,
        active_regimes: List[ActiveRegime],
        scope: RegimeScope
    ) -> List[ActiveRegime]:
        """Filter active regimes by scope.

        Args:
            active_regimes: All active regimes
            scope: Scope to filter (entry, exit, in_trade)

        Returns:
            Regimes matching the scope
        """
        return [
            r for r in active_regimes
            if r.scope == scope or r.scope is None  # None = global scope
        ]

    def get_regime_ids(self, active_regimes: List[ActiveRegime]) -> List[str]:
        """Extract regime IDs from active regimes."""
        return [r.id for r in active_regimes]
```

---

### Phase 3: Strategy Routing (Woche 3-4)

#### 3.1 Strategy Router
**Datei:** `src/core/tradingbot/routing/strategy_router.py`
```python
from typing import List, Optional
from ..config.models import RoutingRule, StrategySet

class StrategyRouter:
    """Route active regimes to strategy sets."""

    def __init__(self, routing_rules: List[RoutingRule]):
        self.routing_rules = routing_rules

    def select_strategy_set(
        self,
        active_regime_ids: List[str],
        strategy_sets: List[StrategySet]
    ) -> Optional[StrategySet]:
        """Select strategy set based on active regimes.

        Args:
            active_regime_ids: List of active regime IDs
            strategy_sets: Available strategy sets

        Returns:
            Matched strategy set or None
        """
        for rule in self.routing_rules:
            if self._matches_rule(active_regime_ids, rule):
                # Find strategy set by ID
                for strategy_set in strategy_sets:
                    if strategy_set.id == rule.strategy_set_id:
                        return strategy_set
        return None

    def _matches_rule(
        self,
        active_regime_ids: List[str],
        rule: RoutingRule
    ) -> bool:
        """Check if active regimes match routing rule.

        Args:
            active_regime_ids: Current active regime IDs
            rule: Routing rule to check

        Returns:
            True if rule matches
        """
        match = rule.match

        # Check all_of (all must be active)
        if match.all_of:
            if not all(rid in active_regime_ids for rid in match.all_of):
                return False

        # Check any_of (at least one must be active)
        if match.any_of:
            if not any(rid in active_regime_ids for rid in match.any_of):
                return False

        # Check none_of (none must be active)
        if match.none_of:
            if any(rid in active_regime_ids for rid in match.none_of):
                return False

        return True
```

#### 3.2 Strategy Set Executor
**Datei:** `src/core/tradingbot/routing/strategy_set_executor.py`
```python
from typing import Dict, Any, List
from ..config.models import (
    StrategySet,
    StrategyDefinitionJson,
    IndicatorDefinition,
    StrategyInSet,
    RiskSettings
)

class ResolvedStrategy:
    """Strategy with applied overrides."""
    def __init__(
        self,
        base_strategy: StrategyDefinitionJson,
        applied_overrides: dict
    ):
        self.id = base_strategy.id
        self.name = base_strategy.name
        self.entry = base_strategy.entry
        self.exit = base_strategy.exit
        self.risk = base_strategy.risk

        # Apply overrides
        if applied_overrides.get('entry'):
            self.entry = applied_overrides['entry']
        if applied_overrides.get('exit'):
            self.exit = applied_overrides['exit']
        if applied_overrides.get('risk'):
            self.risk = self._merge_risk(self.risk, applied_overrides['risk'])

    def _merge_risk(
        self,
        base: RiskSettings,
        override: RiskSettings
    ) -> RiskSettings:
        """Merge risk settings with overrides."""
        merged = base.model_copy(deep=True)
        for field, value in override.model_dump(exclude_none=True).items():
            setattr(merged, field, value)
        return merged

class StrategySetExecutor:
    """Execute strategy set with overrides."""

    def __init__(
        self,
        strategies: List[StrategyDefinitionJson],
        indicators: List[IndicatorDefinition]
    ):
        self.strategies = {s.id: s for s in strategies}
        self.indicators = {i.id: i for i in indicators}

    def resolve_strategy_set(
        self,
        strategy_set: StrategySet
    ) -> List[ResolvedStrategy]:
        """Resolve strategy set with all overrides applied.

        Args:
            strategy_set: Strategy set configuration

        Returns:
            List of resolved strategies
        """
        resolved = []

        # Apply indicator overrides (mutate temporarily)
        original_indicators = {}
        if strategy_set.indicator_overrides:
            for override in strategy_set.indicator_overrides:
                indicator = self.indicators[override.indicator_id]
                original_indicators[indicator.id] = indicator.params.copy()
                indicator.params.update(override.params)

        # Resolve strategies with overrides
        for strategy_in_set in strategy_set.strategies:
            base_strategy = self.strategies[strategy_in_set.strategy_id]
            overrides = {}

            if strategy_in_set.strategy_overrides:
                overrides = strategy_in_set.strategy_overrides.model_dump(
                    exclude_none=True
                )

            resolved.append(ResolvedStrategy(base_strategy, overrides))

        # Restore original indicator params
        for indicator_id, original_params in original_indicators.items():
            self.indicators[indicator_id].params = original_params

        return resolved
```

---

### Phase 4: Integration mit bestehendem Bot (Woche 4-5)

#### 4.1 BotController Anpassung
**Datei:** `src/core/tradingbot/bot_controller.py` (Erweiterung)
```python
from .config.loader import ConfigLoader
from .config.models import TradingBotConfig
from .regime.regime_detector import RegimeDetector
from .routing.strategy_router import StrategyRouter
from .routing.strategy_set_executor import StrategySetExecutor

class BotController:
    """Main bot controller with JSON config support."""

    def __init__(self, config_path: Path | None = None):
        # Legacy support: Wenn kein config_path, nutze hardcoded strategies
        self.config: TradingBotConfig | None = None
        self.regime_detector: RegimeDetector | None = None
        self.strategy_router: StrategyRouter | None = None
        self.strategy_executor: StrategySetExecutor | None = None

        if config_path:
            self._load_json_config(config_path)
        else:
            # Fallback zu hardcoded
            self._init_legacy_mode()

    def _load_json_config(self, config_path: Path):
        """Load configuration from JSON file."""
        loader = ConfigLoader(SCHEMA_PATH)
        self.config = loader.load_config(config_path)

        # Initialize regime detection
        self.regime_detector = RegimeDetector(self.config.regimes)

        # Initialize routing
        self.strategy_router = StrategyRouter(self.config.routing)

        # Initialize strategy executor
        self.strategy_executor = StrategySetExecutor(
            self.config.strategies,
            self.config.indicators
        )

    def on_bar(self, bar: Bar):
        """Process new bar."""
        if self.config:
            self._process_bar_json_mode(bar)
        else:
            self._process_bar_legacy_mode(bar)

    def _process_bar_json_mode(self, bar: Bar):
        """Process bar with JSON configuration."""
        # 1. Calculate indicators
        indicator_values = self._calculate_indicators(bar)

        # 2. Detect active regimes
        active_regimes = self.regime_detector.detect_active_regimes(
            indicator_values
        )
        active_regime_ids = [r.id for r in active_regimes]

        # 3. Select strategy set
        strategy_set = self.strategy_router.select_strategy_set(
            active_regime_ids,
            self.config.strategy_sets
        )

        if not strategy_set:
            logger.warning("No strategy set matched, using default")
            # Fallback logic
            return

        # 4. Resolve strategies with overrides
        resolved_strategies = self.strategy_executor.resolve_strategy_set(
            strategy_set
        )

        # 5. Execute strategy logic
        for strategy in resolved_strategies:
            self._execute_strategy(strategy, indicator_values)

    def _calculate_indicators(self, bar: Bar) -> Dict[str, Dict[str, float]]:
        """Calculate all indicators from config."""
        # Implementation: Multi-Timeframe indicator calculation
        # Returns: {"indicator_id": {"field": value}}
        pass

    def _execute_strategy(
        self,
        strategy: ResolvedStrategy,
        indicator_values: Dict
    ):
        """Execute single strategy logic."""
        # Evaluate entry conditions
        if strategy.entry:
            evaluator = ConditionEvaluator(indicator_values)
            if evaluator.evaluate_group(strategy.entry):
                # Entry signal
                self._handle_entry_signal(strategy)

        # Evaluate exit conditions
        if strategy.exit and self.in_position:
            evaluator = ConditionEvaluator(indicator_values)
            if evaluator.evaluate_group(strategy.exit):
                # Exit signal
                self._handle_exit_signal(strategy)
```

---

### Phase 5: Migration Utility (Woche 5)

#### 5.1 Migration Tool
**Datei:** `tools/migrate_to_regime_json.py`
```python
"""Migrate hardcoded strategies to regime-based JSON format."""

from pathlib import Path
from datetime import datetime
from src.core.tradingbot.strategy_catalog import StrategyCatalog
from src.core.tradingbot.config.models import TradingBotConfig

def migrate_catalog_to_json(output_dir: Path):
    """Export strategies from catalog to JSON format.

    Creates:
    - Indicators for each strategy
    - Regimes based on applicable_regimes
    - Strategies with entry/exit rules
    - Strategy sets grouped by regime
    - Routing rules
    """
    catalog = StrategyCatalog()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    indicators = []
    regimes = []
    strategies = []
    strategy_sets = []
    routing = []

    # Create common indicators
    indicators.extend([
        {
            "id": "rsi14_1h",
            "type": "RSI",
            "params": {"period": 14},
            "timeframe": "1h"
        },
        {
            "id": "adx14_1h",
            "type": "ADX",
            "params": {"period": 14},
            "timeframe": "1h"
        },
        {
            "id": "macd_1h",
            "type": "MACD",
            "params": {"fast": 12, "slow": 26, "signal": 9},
            "timeframe": "1h"
        },
        {
            "id": "sma20_1h",
            "type": "SMA",
            "params": {"period": 20},
            "timeframe": "1h"
        },
        {
            "id": "sma50_1h",
            "type": "SMA",
            "params": {"period": 50},
            "timeframe": "1h"
        },
        {
            "id": "bb_1h",
            "type": "BollingerBands",
            "params": {"period": 20, "std": 2},
            "timeframe": "1h"
        },
        {
            "id": "vol_ratio_1h",
            "type": "VolumeRatio",
            "params": {"period": 20},
            "timeframe": "1h"
        }
    ])

    # Create regimes
    regimes.extend([
        {
            "id": "trend_up",
            "name": "Uptrend",
            "scope": "entry",
            "conditions": {
                "all": [
                    {
                        "left": {"indicator_id": "adx14_1h", "field": "value"},
                        "op": "gt",
                        "right": {"value": 25}
                    },
                    {
                        "left": {"indicator_id": "plus_di_1h", "field": "value"},
                        "op": "gt",
                        "right": {"indicator_id": "minus_di_1h", "field": "value"}
                    }
                ]
            }
        },
        {
            "id": "trend_down",
            "name": "Downtrend",
            "scope": "entry",
            "conditions": {
                "all": [
                    {
                        "left": {"indicator_id": "adx14_1h", "field": "value"},
                        "op": "gt",
                        "right": {"value": 25}
                    },
                    {
                        "left": {"indicator_id": "minus_di_1h", "field": "value"},
                        "op": "gt",
                        "right": {"indicator_id": "plus_di_1h", "field": "value"}
                    }
                ]
            }
        },
        {
            "id": "range",
            "name": "Range-Bound",
            "scope": "entry",
            "conditions": {
                "all": [
                    {
                        "left": {"indicator_id": "adx14_1h", "field": "value"},
                        "op": "lt",
                        "right": {"value": 20}
                    }
                ]
            }
        },
        {
            "id": "low_vol",
            "name": "Low Volume",
            "scope": "exit",
            "conditions": {
                "all": [
                    {
                        "left": {"indicator_id": "vol_ratio_1h", "field": "value"},
                        "op": "lt",
                        "right": {"value": 0.5}
                    }
                ]
            }
        }
    ])

    # Migrate each strategy
    for strategy_name in catalog.list_strategies():
        old_strategy = catalog.get_strategy(strategy_name)

        # Convert to JSON format
        strategy_json = {
            "id": old_strategy.profile.name,
            "name": old_strategy.profile.description or old_strategy.profile.name,
            "entry": _convert_entry_rules_to_conditions(old_strategy.entry_rules),
            "exit": _convert_exit_rules_to_conditions(old_strategy.exit_rules),
            "risk": {
                "stop_loss_pct": old_strategy.stop_loss_pct,
                "take_profit_pct": old_strategy.profile.expected_profit_factor * old_strategy.stop_loss_pct,
                "trailing_mode": old_strategy.trailing_mode.value,
                "trailing_multiplier": old_strategy.trailing_params.get("multiplier", 1.5)
            }
        }
        strategies.append(strategy_json)

    # Create strategy sets per regime
    strategy_sets.extend([
        {
            "id": "set_trend_up",
            "name": "Uptrend Strategies",
            "strategies": [
                {"strategy_id": "trend_following_conservative"},
                {"strategy_id": "trend_following_aggressive"}
            ]
        },
        {
            "id": "set_range",
            "name": "Range Strategies",
            "strategies": [
                {"strategy_id": "mean_reversion_bb"},
                {"strategy_id": "mean_reversion_rsi"},
                {"strategy_id": "scalping_range"}
            ]
        }
    ])

    # Create routing rules
    routing.extend([
        {
            "strategy_set_id": "set_trend_up",
            "match": {
                "all_of": ["trend_up"],
                "none_of": ["low_vol"]
            }
        },
        {
            "strategy_set_id": "set_range",
            "match": {
                "all_of": ["range"],
                "none_of": ["low_vol"]
            }
        }
    ])

    # Save complete configuration
    config = {
        "schema_version": "1.0",
        "metadata": {
            "author": "migration_tool",
            "created_at": datetime.utcnow().isoformat(),
            "notes": "Migrated from hardcoded StrategyCatalog"
        },
        "indicators": indicators,
        "regimes": regimes,
        "strategies": strategies,
        "strategy_sets": strategy_sets,
        "routing": routing
    }

    output_file = output_dir / "migrated_config.json"
    with open(output_file, 'w') as f:
        json.dump(config, f, indent=2)

    print(f"✓ Migration complete: {output_file}")

def _convert_entry_rules_to_conditions(entry_rules) -> dict:
    """Convert old EntryRule list to ConditionGroup."""
    # Simplified conversion - nur als Beispiel
    conditions = []
    for rule in entry_rules:
        if rule.indicator and rule.condition:
            condition = {
                "left": {"indicator_id": rule.indicator, "field": "value"},
                "op": "gt" if "above" in rule.condition else "lt",
                "right": {"value": rule.threshold} if rule.threshold else {"value": 0}
            }
            conditions.append(condition)

    return {"all": conditions} if conditions else None

if __name__ == "__main__":
    migrate_catalog_to_json(Path("03_JSON/Trading_Bot"))
```

---

## 📂 Verzeichnisstruktur

```
03_JSON/
├── Trading_Bot/                    # Production Configs
│   ├── configs/
│   │   ├── default_config.json     # Migrated from hardcoded
│   │   ├── aggressive_trend.json   # Custom config
│   │   └── conservative_range.json
│   │
│   └── templates/                  # Config Templates
│       ├── template_trend.json
│       └── template_range.json
│
└── AI_Analyse/                     # Backtest Configs
    ├── configs/                    # Test Configurations
    │   └── backtest_config.json
    │
    ├── results/                    # Backtest Results
    │   └── trend_follow_20260118.json
    │
    └── optimization/               # Parameter Optimization
        └── rsi_optimization.json
```

---

## 🔄 Migration-Strategie

### Schritt 1: Bestehende Strategien exportieren
```bash
python tools/migrate_to_regime_json.py
```

### Schritt 2: Validierung
```bash
python tools/validate_config.py 03_JSON/Trading_Bot/configs/default_config.json
```

### Schritt 3: Bot mit JSON starten
```python
from pathlib import Path
from src.core.tradingbot.bot_controller import BotController

config_path = Path("03_JSON/Trading_Bot/configs/default_config.json")
bot = BotController(config_path=config_path)
```

### Schritt 4: Fallback Test
```python
# Wenn config_path=None, nutzt Bot hardcoded strategies
bot_legacy = BotController(config_path=None)
```

---

## ✅ Deliverables & Meilensteine

### Woche 1-2: Core Infrastructure
- [x] JSON Schema erstellen
- [x] Pydantic Models
- [x] ConfigLoader
- [ ] Unit Tests

### Woche 2-3: Condition Evaluator
- [ ] ConditionEvaluator implementieren
- [ ] RegimeDetector implementieren
- [ ] Multi-Regime Support testen
- [ ] Unit Tests

### Woche 3-4: Strategy Routing
- [ ] StrategyRouter implementieren
- [ ] StrategySetExecutor implementieren
- [ ] Override-Mechanismus testen
- [ ] Integration Tests

### Woche 4-5: Bot Integration
- [ ] BotController erweitern
- [ ] Multi-Timeframe Indicator Support
- [ ] Fallback zu hardcoded
- [ ] End-to-End Tests

### Woche 5: Migration & Testing
- [ ] Migration Tool
- [ ] 9 Strategien exportieren
- [ ] Validierung
- [ ] Performance Tests

---

## 🧪 Testing-Strategie

### Unit Tests
```python
def test_condition_evaluator_gt():
    """Test greater-than condition."""
    indicator_values = {"rsi14_1h": {"value": 65.0}}
    condition = Condition(
        left=IndicatorRef(indicator_id="rsi14_1h", field="value"),
        op=ConditionOperator.GT,
        right=ConstantValue(value=60.0)
    )
    evaluator = ConditionEvaluator(indicator_values)
    assert evaluator.evaluate_condition(condition) == True

def test_regime_detector_multiple_active():
    """Test multiple regimes active simultaneously."""
    regimes = [
        RegimeDefinition(
            id="entry_trend",
            name="Entry Trend",
            scope=RegimeScope.ENTRY,
            conditions=ConditionGroup(all=[...])
        ),
        RegimeDefinition(
            id="exit_low_vol",
            name="Exit Low Vol",
            scope=RegimeScope.EXIT,
            conditions=ConditionGroup(all=[...])
        )
    ]
    detector = RegimeDetector(regimes)
    active = detector.detect_active_regimes(indicator_values)
    assert len(active) == 2  # Both entry and exit regime
```

### Integration Tests
```python
def test_full_routing_flow():
    """Test complete regime → strategy set → execution flow."""
    # 1. Load config
    config = ConfigLoader(SCHEMA_PATH).load_config(CONFIG_PATH)

    # 2. Detect regimes
    detector = RegimeDetector(config.regimes)
    active_regimes = detector.detect_active_regimes(indicator_values)

    # 3. Route to strategy set
    router = StrategyRouter(config.routing)
    strategy_set = router.select_strategy_set(
        [r.id for r in active_regimes],
        config.strategy_sets
    )

    # 4. Resolve strategies
    executor = StrategySetExecutor(config.strategies, config.indicators)
    resolved = executor.resolve_strategy_set(strategy_set)

    assert len(resolved) > 0
    assert resolved[0].risk.stop_loss_pct > 0
```

---

## 📊 Success Metrics

- **Validierung:** 100% aller JSON Configs validieren
- **Performance:** < 50ms für Regime-Detection + Routing
- **Test Coverage:** > 85%
- **Backward Compatibility:** 100% (Fallback zu hardcoded)
- **Multi-Timeframe:** Indikatoren auf 3+ Timeframes parallel

---

## ⚠️ Risiken

| Risiko | Impact | Mitigation |
|--------|--------|-----------|
| **Komplexität für User** | Hoch | Wizard + Templates |
| **Performance Multi-TF** | Mittel | Caching + Lazy Loading |
| **Breaking Changes** | Mittel | Fallback-Modus |
| **Condition Evaluator Bugs** | Hoch | Extensive Tests + Logging |

---

## 🚀 Next Steps

1. **Review Projektplan** - Stakeholder Feedback
2. **Phase 1 starten** - JSON Schema + Models
3. **Proof of Concept** - Einfaches Beispiel mit 2 Regimes
4. **Migration Tool** - Hardcoded → JSON
5. **UI Integration** - Config Editor

---

**Status:** ✅ Plan Complete - Ready for Implementation
**Last Updated:** 2026-01-18
**Author:** Claude Code (Sonnet 4.5)
**Basis:** `01_Projectplan/Strategien_Workflow_json/json Format Strategien Indikatoren.md`
