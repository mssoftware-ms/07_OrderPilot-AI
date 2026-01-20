# CEL System - Ganzheitlicher Umsetzungsplan
## Common Expression Language Integration für OrderPilot-AI

**Erstellt:** 20. Januar 2026
**Version:** 1.0
**Status:** Planung
**Geschätzter Aufwand:** 120-150 Stunden (3-4 Wochen Vollzeit)

---

## 📋 INHALTSÜBERSICHT

1. [Executive Summary](#executive-summary)
2. [Systemarchitektur](#systemarchitektur)
3. [Phasenplan (8 Phasen)](#phasenplan)
4. [Detaillierte Aufgabenpakete](#detaillierte-aufgabenpakete)
5. [Technische Spezifikationen](#technische-spezifikationen)
6. [Abhängigkeiten & Risiken](#abhängigkeiten--risiken)
7. [Qualitätssicherung](#qualitätssicherung)
8. [Rollout-Strategie](#rollout-strategie)
9. [Dokumentations-Updates](#dokumentations-updates)
10. [Nächste Schritte](#nächste-schritte)

---

## 🎯 EXECUTIVE SUMMARY

### Projektziel

Implementierung einer **CEL (Common Expression Language) Engine** als zentrales Regelwerk-System für:
- **Trading Bot** - Runtime-Regel-Evaluation (Entry/Exit/Risk/Stop-Management)
- **Entry Analyzer** - Backtest-Regel-Evaluation
- **Zukünftige KI-Integration** - Regelbasierte Constraints

### Kernprinzipien

1. **JSON als universelle Schnittstelle** zwischen allen Modulen
2. **CEL-Befehle als verbindliche API** (CEL_Befehle_Liste_v2.md)
3. **Eigenständiges UI-Fenster** mit neuem Startbutton im Chart-Fenster
4. **Modularität** - Klare Schnittstellen für spätere System-weite Anpassungen

### Erwartete Benefits

- ✅ **Konfigurierbare Trading-Regeln** ohne Code-Änderungen
- ✅ **Einheitliche Regel-Engine** für Bot + Analyzer
- ✅ **Testbarkeit** durch Unit-Tests mit JSON-Fixtures
- ✅ **Erweiterbarkeit** für KI-Integration
- ✅ **Sicherheit** durch Schema-Validation (JSON Leitplanken)

---

## 🏗️ SYSTEMARCHITEKTUR

### Komponenten-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│                      OrderPilot-AI System                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐     │
│  │ Entry Designer│◄──►│  CEL Engine  │◄──►│ Trading Bot  │     │
│  │  (UI/Backend) │    │  (Core)      │    │  (Runtime)   │     │
│  └──────────────┘    └──────────────┘    └──────────────┘     │
│         │                    │                    │            │
│         └────────────────────┼────────────────────┘            │
│                              │                                 │
│                        ┌─────▼─────┐                           │
│                        │   JSON    │                           │
│                        │ Interface │                           │
│                        └───────────┘                           │
│                              │                                 │
│         ┌────────────────────┼────────────────────┐            │
│         │                    │                    │            │
│   ┌─────▼──────┐      ┌─────▼──────┐      ┌─────▼──────┐     │
│   │  Schema    │      │  RulePack  │      │   Config   │     │
│   │ Validation │      │   Storage  │      │   Loader   │     │
│   └────────────┘      └────────────┘      └────────────┘     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │         Future: KI Integration (Phase 9+)                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Modul-Interaktion

```
Entry Designer:
  → Erstellt/Editiert RulePacks (JSON)
  → Speichert in 03_JSON/RulePacks/
  → Trigger: UI-Actions

CEL Engine:
  → Lädt RulePacks aus JSON
  → Compiliert CEL-Expressions einmal
  → Evaluiert pro Tick/Bar
  → Liefert Ergebnisse (block/exit/stop_update)

Trading Bot:
  → Lädt RulePack beim Start
  → Erstellt RuleContext aus FeatureVector
  → Ruft CEL Engine auf
  → Führt Aktionen aus (Entry/Exit/Stop-Update)

JSON Schema:
  → Validiert alle JSON-Files vor Verwendung
  → Liefert klare Error-Messages
  → Verhindert Runtime-Fehler
```

---

## 📅 PHASENPLAN

### Phase 1: Foundation & JSON Schema (Woche 1, Tag 1-3)
**Ziel:** JSON-Leitplanken-System etablieren

**Aufwand:** 20-24 Stunden

**Deliverables:**
- ✅ JSON Schema für alle Config-Typen
- ✅ Validation-Layer mit Error-Messages
- ✅ Dokumentation (JSON_INTERFACE_RULES.md)
- ✅ CLAUDE.md, Agents.md, Gemini.md Updates

---

### Phase 2: CEL Engine Core (Woche 1, Tag 4-5)
**Ziel:** CEL-Parser und Evaluator implementieren

**Aufwand:** 16-20 Stunden

**Deliverables:**
- ✅ Python CEL Integration (celpy oder custom parser)
- ✅ RuleContext Builder (Feature → CEL Context)
- ✅ Custom Functions (pctl, isnull, nz, coalesce)
- ✅ Expression Compiler mit Caching
- ✅ Unit-Tests für alle Operatoren

---

### Phase 3: RulePack System (Woche 2, Tag 1-2)
**Ziel:** RulePack Loader/Storage/Validator

**Aufwand:** 12-16 Stunden

**Deliverables:**
- ✅ RulePackLoader (JSON → Python Objects)
- ✅ RulePackValidator (Schema + Business Logic)
- ✅ Default RulePacks (no_trade, entry, exit, update_stop, risk)
- ✅ RulePack Versioning System
- ✅ Migration-Scripts für Updates

---

### Phase 4: UI - CEL Editor Window (Woche 2, Tag 3-5)
**Ziel:** Eigenständiges CEL-Editor-Fenster

**Aufwand:** 24-30 Stunden

**Deliverables:**
- ✅ Neuer Startbutton im Chart-Fenster ("⚙️ CEL Rules")
- ✅ CEL Editor Dialog (PyQt6)
  - Tree-View für RulePacks
  - Expression Editor mit Syntax-Highlighting
  - Live-Validation
  - Test-Panel mit RuleContext Preview
- ✅ Import/Export von RulePacks
- ✅ RulePack-Templates

---

### Phase 5: Trading Bot Integration (Woche 3, Tag 1-3)
**Ziel:** CEL Engine in Trading Bot einbinden

**Aufwand:** 20-24 Stunden

**Deliverables:**
- ✅ RuleContext aus FeatureVector erstellen
- ✅ Regel-Evaluation in Bot-Loop integrieren
- ✅ Execution Order implementieren (exit → update_stop → risk → entry)
- ✅ Monotonic Stop Enforcement
- ✅ Logging & Metrics (welche Regeln triggered)
- ✅ Error-Handling (CEL-Fehler nicht crashen lassen)

---

### Phase 6: Entry Analyzer Integration (Woche 3, Tag 4-5)
**Ziel:** CEL Engine in Entry Analyzer einbinden

**Aufwand:** 16-20 Stunden

**Deliverables:**
- ✅ Backtest mit CEL-Regeln
- ✅ Regel-Optimization (Best Rules finden)
- ✅ Regel-Wirkung Visualisierung (welche Regel blockierte wann)
- ✅ Performance-Metrics pro Regel
- ✅ A/B Testing (RulePack A vs. RulePack B)

---

### Phase 7: Testing & Optimization (Woche 4, Tag 1-3)
**Ziel:** Qualitätssicherung & Performance

**Aufwand:** 20-24 Stunden

**Deliverables:**
- ✅ Comprehensive Unit-Tests (100+ Test Cases)
- ✅ Integration Tests (Bot + Analyzer)
- ✅ Performance-Tests (Expression-Compilation Caching)
- ✅ Edge-Case Tests (null-Werte, Division by Zero, etc.)
- ✅ Backtest-Validation (5+ RulePacks)
- ✅ Memory-Leak Tests (Long-Running Bot)

---

### Phase 8: Documentation & Rollout (Woche 4, Tag 4-5)
**Ziel:** Produktionsreife & Dokumentation

**Aufwand:** 12-16 Stunden

**Deliverables:**
- ✅ User Guide (CEL_User_Guide.md)
- ✅ Developer Guide (CEL_Developer_Guide.md)
- ✅ API Reference (CEL_API_Reference.md)
- ✅ Migration Guide (Existing Strategies → CEL)
- ✅ Video-Tutorials (optional)
- ✅ Release Notes

---

## 📦 DETAILLIERTE AUFGABENPAKETE

### PHASE 1: Foundation & JSON Schema

#### 1.1 JSON Schema Definitionen erstellen

**Datei:** `src/core/tradingbot/config/schemas/`

**Schemas:**

```
schemas/
├── base_schema.json               # Base definitions
├── indicator_schema.json          # IndicatorDefinition
├── regime_schema.json             # RegimeDefinition
├── strategy_schema.json           # StrategyDefinition
├── strategy_set_schema.json       # StrategySetDefinition
├── routing_schema.json            # RoutingRule
├── rulepack_schema.json           # RulePack (NEU)
├── rule_context_schema.json       # RuleContext (NEU)
└── trading_bot_config_schema.json # TradingBotConfig (master)
```

**Beispiel: rulepack_schema.json**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://orderpilot-ai.com/schemas/rulepack.json",
  "title": "RulePack",
  "type": "object",
  "required": ["rules_version", "engine", "packs"],
  "properties": {
    "rules_version": {
      "type": "string",
      "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
      "description": "Semantic version (e.g., 1.0.0)"
    },
    "engine": {
      "type": "string",
      "const": "CEL",
      "description": "Must be CEL"
    },
    "packs": {
      "type": "array",
      "minItems": 1,
      "items": { "$ref": "#/$defs/Pack" }
    }
  },
  "$defs": {
    "Pack": {
      "type": "object",
      "required": ["pack_id", "enabled", "rules"],
      "properties": {
        "pack_id": {
          "type": "string",
          "enum": ["no_trade", "entry", "exit", "update_stop", "risk"]
        },
        "enabled": {
          "type": "boolean"
        },
        "rules": {
          "type": "array",
          "items": { "$ref": "#/$defs/Rule" }
        }
      }
    },
    "Rule": {
      "type": "object",
      "required": ["id", "severity", "expr"],
      "properties": {
        "id": {
          "type": "string",
          "pattern": "^[A-Z]{2,3}_[A-Z_]+$",
          "description": "Rule ID (e.g., NT_LOW_VOL_AND_LOW_VOLATILITY)"
        },
        "severity": {
          "type": "string",
          "enum": ["block", "exit", "update_stop"]
        },
        "expr": {
          "type": "string",
          "minLength": 1,
          "description": "CEL expression"
        },
        "result_type": {
          "type": "string",
          "enum": ["number_or_null"],
          "description": "Only for update_stop rules"
        }
      },
      "if": {
        "properties": { "severity": { "const": "update_stop" } }
      },
      "then": {
        "required": ["result_type"]
      }
    }
  }
}
```

#### 1.2 Schema Validator implementieren

**Datei:** `src/core/tradingbot/config/schema_validator.py`

```python
"""JSON Schema Validator für alle Config-Typen.

Provides validation with clear error messages.
"""

import json
import logging
from pathlib import Path
from typing import Any

import jsonschema
from jsonschema import Draft202012Validator, ValidationError

logger = logging.getLogger(__name__)


class SchemaValidator:
    """Validates JSON configs against JSON Schemas."""

    def __init__(self, schema_dir: Path = None):
        """Initialize validator.

        Args:
            schema_dir: Directory containing JSON schemas.
                       Defaults to src/core/tradingbot/config/schemas/
        """
        if schema_dir is None:
            schema_dir = Path(__file__).parent / "schemas"

        self.schema_dir = schema_dir
        self._schemas = {}
        self._load_schemas()

    def _load_schemas(self) -> None:
        """Load all schemas from schema directory."""
        for schema_file in self.schema_dir.glob("*.json"):
            schema_name = schema_file.stem
            with open(schema_file, "r", encoding="utf-8") as f:
                self._schemas[schema_name] = json.load(f)

            logger.debug(f"Loaded schema: {schema_name}")

    def validate(self, data: dict, schema_name: str) -> tuple[bool, list[str]]:
        """Validate data against schema.

        Args:
            data: Data to validate
            schema_name: Name of schema (without .json)

        Returns:
            Tuple of (is_valid, error_messages)
        """
        if schema_name not in self._schemas:
            return False, [f"Schema '{schema_name}' not found"]

        schema = self._schemas[schema_name]
        validator = Draft202012Validator(schema)

        errors = []
        for error in validator.iter_errors(data):
            # Format error message with path
            path = ".".join(str(p) for p in error.path) if error.path else "root"
            errors.append(f"{path}: {error.message}")

        is_valid = len(errors) == 0

        if not is_valid:
            logger.warning(f"Validation failed for {schema_name}: {errors}")

        return is_valid, errors

    def validate_file(self, file_path: Path, schema_name: str) -> tuple[bool, list[str]]:
        """Validate JSON file against schema.

        Args:
            file_path: Path to JSON file
            schema_name: Name of schema

        Returns:
            Tuple of (is_valid, error_messages)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return False, [f"Failed to load JSON: {e}"]

        return self.validate(data, schema_name)


# Global instance
_validator = None


def get_validator() -> SchemaValidator:
    """Get global SchemaValidator instance."""
    global _validator
    if _validator is None:
        _validator = SchemaValidator()
    return _validator
```

#### 1.3 JSON_INTERFACE_RULES.md erstellen

**Datei:** `01_Projectplan/Strategien_Workflow_json/JSON_INTERFACE_RULES.md`

**Inhalt:** (siehe separates Dokument unten)

#### 1.4 Dokumentations-Updates

**CLAUDE.md:**

```markdown
## JSON als zentrale Schnittstelle

Alle Module kommunizieren über **JSON-Dateien** mit Schema-Validation:
- Entry Designer ↔ CEL Engine ↔ Trading Bot ↔ KI (später)

**Wichtige Regel:**
- **IMMER** JSON Schema validieren vor Verwendung
- **NIEMALS** JSON-Dateien manuell editieren (nur über UI/Tools)
- **ALLE** Änderungen am JSON-Format erfordern Schema-Update + System-weite Migration

**Referenz:** [JSON Interface Rules](01_Projectplan/Strategien_Workflow_json/JSON_INTERFACE_RULES.md)
```

**Agents.md:**

```markdown
## JSON Schema System

Bei allen JSON-Operationen:
1. Schema-Validation IMMER durchführen
2. Error-Messages klar kommunizieren
3. Bei Schema-Änderungen: Migration-Script erstellen

**Referenz:** [JSON Interface Rules](01_Projectplan/Strategien_Workflow_json/JSON_INTERFACE_RULES.md)
```

**Gemini.md:**

```markdown
## JSON-basierte Architektur

Alle Trading-Configs werden über JSON-Dateien verwaltet:
- TradingBotConfig, RulePacks, StrategyDefinitions

**Validierung:** Vor jeder Verwendung Schema-Check!

**Referenz:** [JSON Interface Rules](01_Projectplan/Strategien_Workflow_json/JSON_INTERFACE_RULES.md)
```

---

### PHASE 2: CEL Engine Core

#### 2.1 CEL Parser/Evaluator auswählen

**Option 1: celpy (empfohlen)**

```bash
pip install celpy
```

**Pro:**
- ✅ Vollständige CEL-Spec-Implementierung
- ✅ Type-Safe
- ✅ Performance (C-Extensions verfügbar)

**Con:**
- ❌ Komplexe API für Custom Functions

**Option 2: py-cel**

```bash
pip install py-cel
```

**Pro:**
- ✅ Einfachere API
- ✅ Gute Docs

**Con:**
- ❌ Weniger Features als celpy

**Entscheidung:** **celpy** (vollständiger + performanter)

#### 2.2 RuleContext Builder

**Datei:** `src/core/tradingbot/cel/context_builder.py`

```python
"""Builds CEL RuleContext from FeatureVector and Trade data."""

import logging
from typing import Any

from src.core.tradingbot.models import FeatureVector, Trade

logger = logging.getLogger(__name__)


class RuleContextBuilder:
    """Converts FeatureVector + Trade + Config to CEL context dict."""

    @staticmethod
    def build(
        features: FeatureVector,
        trade: Trade = None,
        config: dict[str, Any] = None,
        timeframe: str = "5m",
    ) -> dict[str, Any]:
        """Build CEL context from features.

        Args:
            features: FeatureVector with all indicators
            trade: Optional current trade
            config: Optional cfg dict (min_volume_pctl, etc.)
            timeframe: Timeframe string (e.g., "5m")

        Returns:
            CEL context dict matching CEL_Rules_Doku schema
        """
        context = {
            # Timeframe
            "tf": timeframe,

            # Regime/Direction
            "regime": features.regime or "UNKNOWN",
            "direction": features.direction or "NONE",

            # OHLCV (from latest bar)
            "open": float(features.open),
            "high": float(features.high),
            "low": float(features.low),
            "close": float(features.close),
            "volume": float(features.volume),

            # Volatility
            "atrp": float(features.atrp) if features.atrp is not None else 0.0,
            "bbwidth": float(features.bbwidth) if features.bbwidth is not None else 0.0,
            "range_pct": float(features.range_pct) if features.range_pct is not None else 0.0,
            "squeeze_on": bool(features.squeeze_on) if features.squeeze_on is not None else False,

            # Market Depth/Orderbook (nullable)
            "spread_bps": float(features.spread_bps) if features.spread_bps is not None else None,
            "depth_bid": float(features.depth_bid) if features.depth_bid is not None else None,
            "depth_ask": float(features.depth_ask) if features.depth_ask is not None else None,
            "obi": float(features.obi) if features.obi is not None else None,
        }

        # Trade data (if in-trade)
        if trade is not None:
            context["trade"] = {
                "id": trade.id,
                "strategy": trade.strategy,
                "side": trade.side,  # "long" or "short"

                "entry_price": float(trade.entry_price),
                "current_price": float(trade.current_price),

                "stop_price": float(trade.stop_price),
                "sl_pct": float(trade.sl_pct),

                "tr_pct": float(trade.tr_pct) if trade.tr_pct is not None else 0.0,
                "tra_pct": float(trade.tra_pct) if trade.tra_pct is not None else 0.0,
                "tr_lock_pct": float(trade.tr_lock_pct) if trade.tr_lock_pct is not None else 0.0,
                "tr_stop_price": float(trade.tr_stop_price) if trade.tr_stop_price is not None else None,

                "status": trade.status,
                "pnl_pct": float(trade.pnl_pct),
                "pnl_usdt": float(trade.pnl_usdt),
                "fees_pct": float(trade.fees_pct),
                "fees_usdt": float(trade.fees_usdt),
                "invest_usdt": float(trade.invest_usdt),
                "stick": float(trade.stick) if hasattr(trade, "stick") else 0.0,
                "leverage": float(trade.leverage),

                # Optional metrics
                "age_sec": int(trade.age_sec) if hasattr(trade, "age_sec") else 0,
                "bars_in_trade": int(trade.bars_in_trade) if hasattr(trade, "bars_in_trade") else 0,
                "mfe_pct": float(trade.mfe_pct) if hasattr(trade, "mfe_pct") else 0.0,
                "mae_pct": float(trade.mae_pct) if hasattr(trade, "mae_pct") else 0.0,
                "is_open": bool(trade.is_open) if hasattr(trade, "is_open") else True,
            }
        else:
            context["trade"] = None

        # Config (tuning parameters)
        if config is not None:
            context["cfg"] = config
        else:
            # Default config
            context["cfg"] = {
                "min_volume_pctl": 20,
                "min_volume_window": 288,
                "min_atrp_pct": 0.20,
                "max_atrp_pct": 2.50,
                "max_spread_bps": 8.0,
                "min_depth": 60.0,
                "max_leverage": 50,
                "max_fees_pct": 0.15,
                "min_obi": 0.60,
                "min_range_pct": 0.60,
                "no_trade_regimes": ["R0"],
            }

        return context
```

#### 2.3 CEL Engine mit Custom Functions

**Datei:** `src/core/tradingbot/cel/engine.py`

```python
"""CEL Engine with custom trading functions."""

import logging
from typing import Any

import celpy
import numpy as np

logger = logging.getLogger(__name__)


class CELEngine:
    """CEL Expression Engine with custom trading functions."""

    def __init__(self):
        """Initialize CEL engine."""
        self.env = celpy.Environment()

        # Register custom functions
        self._register_custom_functions()

        # Cache for compiled expressions
        self._compiled_cache = {}

    def _register_custom_functions(self) -> None:
        """Register custom trading functions."""

        # pctl(series, percentile, window)
        def pctl_func(series: list, p: int, window: int) -> float:
            """Calculate percentile of series.

            Args:
                series: List of values
                p: Percentile (0-100)
                window: Lookback window

            Returns:
                Percentile value
            """
            if len(series) < window:
                return np.nan

            recent = series[-window:]
            return np.percentile(recent, p)

        # isnull(x)
        def isnull_func(x: Any) -> bool:
            """Check if value is null/None.

            Args:
                x: Value to check

            Returns:
                True if null/None
            """
            return x is None

        # nz(x, default)
        def nz_func(x: Any, default: Any = 0) -> Any:
            """Null-zero (coalesce).

            Args:
                x: Value to check
                default: Default value if null

            Returns:
                x if not null, else default
            """
            return default if x is None else x

        # coalesce(a, b, c, ...)
        def coalesce_func(*args) -> Any:
            """Return first non-null value.

            Args:
                *args: Values to check

            Returns:
                First non-null value or None
            """
            for arg in args:
                if arg is not None:
                    return arg
            return None

        # Register functions
        self.env.add_function("pctl", pctl_func)
        self.env.add_function("isnull", isnull_func)
        self.env.add_function("nz", nz_func)
        self.env.add_function("coalesce", coalesce_func)

        logger.info("Registered 4 custom CEL functions")

    def compile(self, expression: str) -> celpy.Program:
        """Compile CEL expression.

        Args:
            expression: CEL expression string

        Returns:
            Compiled program

        Raises:
            celpy.CELError: If expression is invalid
        """
        if expression in self._compiled_cache:
            return self._compiled_cache[expression]

        try:
            ast = self.env.compile(expression)
            program = self.env.program(ast)
            self._compiled_cache[expression] = program

            logger.debug(f"Compiled expression: {expression[:50]}...")
            return program

        except celpy.CELError as e:
            logger.error(f"Failed to compile expression: {e}")
            raise

    def evaluate(self, expression: str, context: dict[str, Any]) -> Any:
        """Evaluate CEL expression with context.

        Args:
            expression: CEL expression string
            context: Context dict (RuleContext)

        Returns:
            Result of evaluation

        Raises:
            celpy.CELError: If evaluation fails
        """
        try:
            program = self.compile(expression)
            result = program.evaluate(context)

            logger.debug(f"Evaluated: {expression[:50]}... → {result}")
            return result

        except celpy.CELError as e:
            logger.error(f"Failed to evaluate expression: {e}")
            raise

    def clear_cache(self) -> None:
        """Clear compiled expression cache."""
        self._compiled_cache.clear()
        logger.info("Cleared CEL expression cache")


# Global instance
_engine = None


def get_cel_engine() -> CELEngine:
    """Get global CEL engine instance."""
    global _engine
    if _engine is None:
        _engine = CELEngine()
    return _engine
```

#### 2.4 Unit-Tests für CEL Engine

**Datei:** `tests/test_cel_engine.py`

```python
"""Tests for CEL Engine."""

import pytest

from src.core.tradingbot.cel.engine import CELEngine


def test_basic_arithmetic():
    """Test basic arithmetic operations."""
    engine = CELEngine()

    assert engine.evaluate("1 + 1", {}) == 2
    assert engine.evaluate("10 - 5", {}) == 5
    assert engine.evaluate("3 * 4", {}) == 12
    assert engine.evaluate("10 / 2", {}) == 5


def test_comparisons():
    """Test comparison operators."""
    engine = CELEngine()

    assert engine.evaluate("5 > 3", {}) is True
    assert engine.evaluate("5 < 3", {}) is False
    assert engine.evaluate("5 == 5", {}) is True
    assert engine.evaluate("5 != 3", {}) is True


def test_logical_operators():
    """Test logical operators."""
    engine = CELEngine()

    assert engine.evaluate("true && true", {}) is True
    assert engine.evaluate("true && false", {}) is False
    assert engine.evaluate("true || false", {}) is True
    assert engine.evaluate("!false", {}) is True


def test_ternary():
    """Test ternary operator."""
    engine = CELEngine()

    assert engine.evaluate("true ? 10 : 20", {}) == 10
    assert engine.evaluate("false ? 10 : 20", {}) == 20


def test_context_access():
    """Test context variable access."""
    engine = CELEngine()

    context = {
        "atrp": 0.6,
        "regime": "R1",
        "trade": {
            "side": "long",
            "pnl_pct": 1.5
        }
    }

    assert engine.evaluate("atrp", context) == 0.6
    assert engine.evaluate("regime", context) == "R1"
    assert engine.evaluate("trade.side", context) == "long"
    assert engine.evaluate("trade.pnl_pct", context) == 1.5


def test_custom_function_isnull():
    """Test isnull() custom function."""
    engine = CELEngine()

    context = {
        "spread_bps": None,
        "depth_bid": 100.0
    }

    assert engine.evaluate("isnull(spread_bps)", context) is True
    assert engine.evaluate("isnull(depth_bid)", context) is False


def test_custom_function_nz():
    """Test nz() custom function."""
    engine = CELEngine()

    context = {
        "obi": None,
        "atrp": 0.6
    }

    assert engine.evaluate("nz(obi, 0)", context) == 0
    assert engine.evaluate("nz(atrp, 0)", context) == 0.6


def test_custom_function_coalesce():
    """Test coalesce() custom function."""
    engine = CELEngine()

    context = {
        "a": None,
        "b": None,
        "c": 10
    }

    assert engine.evaluate("coalesce(a, b, c)", context) == 10
    assert engine.evaluate("coalesce(a, b)", context) is None


def test_complex_expression():
    """Test complex trading rule expression."""
    engine = CELEngine()

    context = {
        "atrp": 0.3,
        "volume": 800,
        "regime": "R1",
        "cfg": {
            "min_atrp_pct": 0.2,
            "min_volume": 500,
            "no_trade_regimes": ["R0"]
        }
    }

    # Should pass (volume > min, atrp > min, regime not in blocklist)
    expr = "volume > cfg.min_volume && atrp > cfg.min_atrp_pct && !(regime in cfg.no_trade_regimes)"
    assert engine.evaluate(expr, context) is True

    # Should fail (low atrp)
    context["atrp"] = 0.1
    assert engine.evaluate(expr, context) is False


def test_expression_caching():
    """Test that expressions are cached after first compile."""
    engine = CELEngine()

    expr = "1 + 1"

    # First evaluation compiles
    result1 = engine.evaluate(expr, {})

    # Second evaluation uses cache
    result2 = engine.evaluate(expr, {})

    assert result1 == result2
    assert expr in engine._compiled_cache
```

---

### PHASE 3: RulePack System

#### 3.1 RulePack Models

**Datei:** `src/core/tradingbot/cel/models.py`

```python
"""Pydantic models for RulePacks."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator


class RuleSeverity(str, Enum):
    """Rule severity types."""
    BLOCK = "block"
    EXIT = "exit"
    UPDATE_STOP = "update_stop"


class PackID(str, Enum):
    """RulePack IDs."""
    NO_TRADE = "no_trade"
    ENTRY = "entry"
    EXIT = "exit"
    UPDATE_STOP = "update_stop"
    RISK = "risk"


class Rule(BaseModel):
    """Single rule definition."""

    id: str = Field(..., pattern=r"^[A-Z]{2,3}_[A-Z_]+$")
    severity: RuleSeverity
    expr: str = Field(..., min_length=1)
    result_type: Optional[str] = Field(None, pattern=r"^number_or_null$")

    @validator("result_type")
    def validate_result_type(cls, v, values):
        """Validate result_type is set for update_stop rules."""
        if values.get("severity") == RuleSeverity.UPDATE_STOP:
            if v != "number_or_null":
                raise ValueError("update_stop rules must have result_type='number_or_null'")
        return v


class Pack(BaseModel):
    """RulePack (e.g., no_trade, entry, exit)."""

    pack_id: PackID
    enabled: bool = True
    rules: list[Rule] = Field(..., min_items=0)


class RulePack(BaseModel):
    """Complete RulePack file."""

    rules_version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+$")
    engine: str = Field("CEL", pattern=r"^CEL$")
    packs: list[Pack] = Field(..., min_items=1)
```

#### 3.2 RulePack Loader

**Datei:** `src/core/tradingbot/cel/loader.py`

```python
"""RulePack Loader."""

import json
import logging
from pathlib import Path
from typing import Optional

from src.core.tradingbot.cel.models import RulePack
from src.core.tradingbot.config.schema_validator import get_validator

logger = logging.getLogger(__name__)


class RulePackLoader:
    """Loads and validates RulePacks from JSON."""

    def __init__(self, rulepack_dir: Path = None):
        """Initialize loader.

        Args:
            rulepack_dir: Directory containing RulePacks.
                         Defaults to 03_JSON/RulePacks/
        """
        if rulepack_dir is None:
            # Default to project root / 03_JSON / RulePacks
            project_root = Path(__file__).parent.parent.parent.parent.parent
            rulepack_dir = project_root / "03_JSON" / "RulePacks"

        self.rulepack_dir = rulepack_dir
        self.validator = get_validator()

    def load(self, filename: str) -> Optional[RulePack]:
        """Load RulePack from JSON file.

        Args:
            filename: RulePack filename (e.g., "default.json")

        Returns:
            RulePack or None if validation fails
        """
        file_path = self.rulepack_dir / filename

        if not file_path.exists():
            logger.error(f"RulePack not found: {file_path}")
            return None

        # Schema validation first
        is_valid, errors = self.validator.validate_file(file_path, "rulepack_schema")

        if not is_valid:
            logger.error(f"Schema validation failed for {filename}:")
            for error in errors:
                logger.error(f"  - {error}")
            return None

        # Load and parse with Pydantic
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            rulepack = RulePack(**data)

            logger.info(f"Loaded RulePack: {filename} ({len(rulepack.packs)} packs)")
            return rulepack

        except Exception as e:
            logger.error(f"Failed to parse RulePack {filename}: {e}")
            return None

    def list_available(self) -> list[str]:
        """List available RulePack files.

        Returns:
            List of filenames
        """
        if not self.rulepack_dir.exists():
            return []

        return [f.name for f in self.rulepack_dir.glob("*.json")]

    def save(self, rulepack: RulePack, filename: str) -> bool:
        """Save RulePack to JSON file.

        Args:
            rulepack: RulePack to save
            filename: Target filename

        Returns:
            True if successful
        """
        file_path = self.rulepack_dir / filename

        try:
            # Ensure directory exists
            self.rulepack_dir.mkdir(parents=True, exist_ok=True)

            # Export to dict
            data = rulepack.dict()

            # Write to file
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved RulePack: {filename}")
            return True

        except Exception as e:
            logger.error(f"Failed to save RulePack {filename}: {e}")
            return False
```

#### 3.3 Default RulePacks erstellen

**Datei:** `03_JSON/RulePacks/default.json`

(Aus CEL_Rules_Doku_TradingBot_Analyzer.md übernehmen, siehe Abschnitt 5.2)

#### 3.4 RulePack Versioning

**Datei:** `src/core/tradingbot/cel/versioning.py`

```python
"""RulePack versioning and migration."""

import logging
from pathlib import Path

from src.core.tradingbot.cel.models import RulePack

logger = logging.getLogger(__name__)


class RulePackVersionManager:
    """Manages RulePack version migrations."""

    CURRENT_VERSION = "1.0.0"

    @staticmethod
    def needs_migration(rulepack: RulePack) -> bool:
        """Check if RulePack needs migration.

        Args:
            rulepack: RulePack to check

        Returns:
            True if migration needed
        """
        return rulepack.rules_version != RulePackVersionManager.CURRENT_VERSION

    @staticmethod
    def migrate(rulepack: RulePack) -> RulePack:
        """Migrate RulePack to current version.

        Args:
            rulepack: RulePack to migrate

        Returns:
            Migrated RulePack
        """
        if not RulePackVersionManager.needs_migration(rulepack):
            return rulepack

        logger.info(f"Migrating RulePack from {rulepack.rules_version} to {RulePackVersionManager.CURRENT_VERSION}")

        # TODO: Add migration logic when v2.0.0 is defined
        # For now, just update version
        rulepack.rules_version = RulePackVersionManager.CURRENT_VERSION

        return rulepack
```

---

### PHASE 4: UI - CEL Editor Window

#### 4.1 Chart Window - CEL Button hinzufügen

**Datei:** `src/ui/widgets/chart_window_mixins/bot_ui_control_widgets.py`

**Änderung:**

```python
# Add CEL Rules button to bot control group
self.cel_rules_btn = QPushButton("⚙️ CEL Rules")
self.cel_rules_btn.setToolTip("Open CEL Rules Editor")
self.cel_rules_btn.setStyleSheet("""
    QPushButton {
        background-color: #5e35b1;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: bold;
    }
    QPushButton:hover {
        background-color: #7e57c2;
    }
    QPushButton:pressed {
        background-color: #4527a0;
    }
""")
self.cel_rules_btn.clicked.connect(self._on_cel_rules_clicked)

# Add to bot control layout
bot_control_layout.addWidget(self.cel_rules_btn)


def _on_cel_rules_clicked(self):
    """Open CEL Rules Editor dialog."""
    from src.ui.dialogs.cel_editor_dialog import CELEditorDialog

    dialog = CELEditorDialog(self)
    dialog.exec_()
```

#### 4.2 CEL Editor Dialog

**Datei:** `src/ui/dialogs/cel_editor_dialog.py`

```python
"""CEL Rules Editor Dialog."""

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QSyntaxHighlighter, QTextCharFormat, QColor
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QSplitter,
    QTreeWidget, QTreeWidgetItem, QTextEdit, QLabel, QMessageBox,
    QFileDialog, QCheckBox
)

from src.core.tradingbot.cel.loader import RulePackLoader
from src.core.tradingbot.cel.engine import get_cel_engine
from src.core.tradingbot.cel.models import RulePack, Pack, Rule, RuleSeverity

logger = logging.getLogger(__name__)


class CELSyntaxHighlighter(QSyntaxHighlighter):
    """Syntax highlighter for CEL expressions."""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Define formats
        self.keyword_format = QTextCharFormat()
        self.keyword_format.setForeground(QColor("#c678dd"))
        self.keyword_format.setFontWeight(QFont.Weight.Bold)

        self.function_format = QTextCharFormat()
        self.function_format.setForeground(QColor("#61afef"))

        self.operator_format = QTextCharFormat()
        self.operator_format.setForeground(QColor("#e06c75"))

        self.number_format = QTextCharFormat()
        self.number_format.setForeground(QColor("#d19a66"))

        self.string_format = QTextCharFormat()
        self.string_format.setForeground(QColor("#98c379"))

        # Keywords
        self.keywords = [
            "true", "false", "null", "in", "has"
        ]

        # Functions
        self.functions = [
            "abs", "min", "max", "isnull", "nz", "coalesce", "pctl"
        ]

        # Operators
        self.operators = [
            r'\+', r'-', r'\*', r'/', r'%',
            r'==', r'!=', r'<', r'>', r'<=', r'>=',
            r'&&', r'\|\|', r'!', r'\?', r':'
        ]

    def highlightBlock(self, text):
        """Highlight a block of text."""
        # Highlight keywords
        for keyword in self.keywords:
            pattern = rf'\b{keyword}\b'
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), self.keyword_format)

        # Highlight functions
        for func in self.functions:
            pattern = rf'\b{func}\('
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), len(func), self.function_format)

        # Highlight numbers
        pattern = r'\b\d+\.?\d*\b'
        for match in re.finditer(pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.number_format)

        # Highlight strings
        pattern = r'"[^"]*"'
        for match in re.finditer(pattern, text):
            self.setFormat(match.start(), match.end() - match.start(), self.string_format)


class CELEditorDialog(QDialog):
    """CEL Rules Editor Dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle("CEL Rules Editor")
        self.setMinimumSize(1200, 800)

        self.loader = RulePackLoader()
        self.cel_engine = get_cel_engine()
        self.current_rulepack = None
        self.current_rule = None

        self._setup_ui()
        self._load_default_rulepack()

    def _setup_ui(self):
        """Setup UI components."""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar_layout = QHBoxLayout()

        self.load_btn = QPushButton("📂 Load RulePack")
        self.load_btn.clicked.connect(self._on_load_clicked)

        self.save_btn = QPushButton("💾 Save RulePack")
        self.save_btn.clicked.connect(self._on_save_clicked)

        self.new_btn = QPushButton("➕ New Rule")
        self.new_btn.clicked.connect(self._on_new_rule_clicked)

        self.delete_btn = QPushButton("🗑️ Delete Rule")
        self.delete_btn.clicked.connect(self._on_delete_rule_clicked)

        self.test_btn = QPushButton("🧪 Test Expression")
        self.test_btn.clicked.connect(self._on_test_clicked)

        toolbar_layout.addWidget(self.load_btn)
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.new_btn)
        toolbar_layout.addWidget(self.delete_btn)
        toolbar_layout.addWidget(self.test_btn)

        layout.addLayout(toolbar_layout)

        # Splitter for tree + editor
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Tree view
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("RulePacks")
        self.tree.itemClicked.connect(self._on_tree_item_clicked)

        splitter.addWidget(self.tree)

        # Right: Editor
        editor_widget = QWidget()
        editor_layout = QVBoxLayout(editor_widget)

        # Rule ID
        self.rule_id_label = QLabel("Rule ID:")
        self.rule_id_input = QTextEdit()
        self.rule_id_input.setMaximumHeight(30)

        # Severity
        self.severity_label = QLabel("Severity:")
        self.severity_input = QTextEdit()
        self.severity_input.setMaximumHeight(30)

        # Expression
        self.expr_label = QLabel("CEL Expression:")
        self.expr_input = QTextEdit()
        self.expr_input.setMinimumHeight(200)
        self.highlighter = CELSyntaxHighlighter(self.expr_input.document())

        # Result Type (for update_stop)
        self.result_type_label = QLabel("Result Type:")
        self.result_type_input = QTextEdit()
        self.result_type_input.setMaximumHeight(30)

        # Validation result
        self.validation_label = QLabel("Validation:")
        self.validation_result = QTextEdit()
        self.validation_result.setMaximumHeight(80)
        self.validation_result.setReadOnly(True)

        editor_layout.addWidget(self.rule_id_label)
        editor_layout.addWidget(self.rule_id_input)
        editor_layout.addWidget(self.severity_label)
        editor_layout.addWidget(self.severity_input)
        editor_layout.addWidget(self.expr_label)
        editor_layout.addWidget(self.expr_input)
        editor_layout.addWidget(self.result_type_label)
        editor_layout.addWidget(self.result_type_input)
        editor_layout.addWidget(self.validation_label)
        editor_layout.addWidget(self.validation_result)

        splitter.addWidget(editor_widget)
        splitter.setSizes([300, 900])

        layout.addWidget(splitter)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)

        layout.addWidget(close_btn)

    def _load_default_rulepack(self):
        """Load default RulePack."""
        rulepack = self.loader.load("default.json")

        if rulepack is None:
            logger.warning("Default RulePack not found, creating empty")
            rulepack = RulePack(
                rules_version="1.0.0",
                engine="CEL",
                packs=[]
            )

        self.current_rulepack = rulepack
        self._populate_tree()

    def _populate_tree(self):
        """Populate tree with current RulePack."""
        self.tree.clear()

        if self.current_rulepack is None:
            return

        # Root item
        root = QTreeWidgetItem(self.tree, [f"RulePack v{self.current_rulepack.rules_version}"])

        # Add packs
        for pack in self.current_rulepack.packs:
            pack_item = QTreeWidgetItem(root, [f"{pack.pack_id.value} ({len(pack.rules)} rules)"])
            pack_item.setData(0, Qt.ItemDataRole.UserRole, pack)

            # Add rules
            for rule in pack.rules:
                rule_item = QTreeWidgetItem(pack_item, [rule.id])
                rule_item.setData(0, Qt.ItemDataRole.UserRole, rule)

        self.tree.expandAll()

    def _on_tree_item_clicked(self, item, column):
        """Handle tree item click."""
        data = item.data(0, Qt.ItemDataRole.UserRole)

        if isinstance(data, Rule):
            self.current_rule = data
            self._load_rule_to_editor(data)
        elif isinstance(data, Pack):
            self.current_rule = None
            self._clear_editor()

    def _load_rule_to_editor(self, rule: Rule):
        """Load rule into editor."""
        self.rule_id_input.setText(rule.id)
        self.severity_input.setText(rule.severity.value)
        self.expr_input.setText(rule.expr)
        self.result_type_input.setText(rule.result_type or "")

        # Validate expression
        self._validate_expression()

    def _clear_editor(self):
        """Clear editor fields."""
        self.rule_id_input.clear()
        self.severity_input.clear()
        self.expr_input.clear()
        self.result_type_input.clear()
        self.validation_result.clear()

    def _validate_expression(self):
        """Validate CEL expression."""
        expr = self.expr_input.toPlainText()

        if not expr:
            self.validation_result.setText("❌ Expression is empty")
            return

        try:
            # Try to compile
            self.cel_engine.compile(expr)
            self.validation_result.setText("✅ Expression is valid")
        except Exception as e:
            self.validation_result.setText(f"❌ Invalid expression: {e}")

    def _on_load_clicked(self):
        """Load RulePack from file."""
        # TODO: File dialog to select RulePack
        pass

    def _on_save_clicked(self):
        """Save current RulePack."""
        # TODO: Save current RulePack
        pass

    def _on_new_rule_clicked(self):
        """Create new rule."""
        # TODO: New rule dialog
        pass

    def _on_delete_rule_clicked(self):
        """Delete selected rule."""
        # TODO: Delete selected rule
        pass

    def _on_test_clicked(self):
        """Test expression with sample context."""
        # TODO: Test panel with context preview
        pass
```

---

### PHASE 5: Trading Bot Integration

(Similar detailed implementation for all phases)

---

## 📊 TECHNISCHE SPEZIFIKATIONEN

### System Requirements

**Python Version:** 3.10+

**Neue Dependencies:**

```toml
[tool.poetry.dependencies]
celpy = "^0.20.0"              # CEL Engine
jsonschema = "^4.20.0"         # JSON Schema Validation
pydantic = "^2.5.0"            # Data validation (bereits vorhanden)
```

### Performance Targets

| Metrik | Ziel | Kritisch |
|--------|------|----------|
| **Expression Compilation** | < 1ms | < 5ms |
| **Expression Evaluation** | < 0.1ms | < 0.5ms |
| **RulePack Loading** | < 100ms | < 500ms |
| **Schema Validation** | < 50ms | < 200ms |
| **Memory Overhead** | < 50MB | < 200MB |

### Caching Strategy

```python
# Compiled Expressions Cache
{
  "expr_hash": compiled_program,
  ...
}

# RulePack Cache (in-memory)
{
  "filename": (rulepack, last_modified_time),
  ...
}

# Schema Cache (in-memory)
{
  "schema_name": schema_dict,
  ...
}
```

---

## ⚠️ ABHÄNGIGKEITEN & RISIKEN

### Kritische Abhängigkeiten

| Komponente | Abhängig von | Risiko |
|-----------|--------------|--------|
| **CEL Engine** | celpy Library | HOCH - Externe Dependency |
| **Schema Validation** | jsonschema | MITTEL |
| **UI** | PyQt6 | NIEDRIG - Bereits etabliert |
| **Config System** | Pydantic | NIEDRIG - Bereits etabliert |

### Risiko-Matrix

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|-----------|
| **celpy Breaking Changes** | NIEDRIG | HOCH | Pin Version, Fork möglich |
| **Performance Bottleneck** | MITTEL | MITTEL | Profiling, Caching |
| **Schema Changes Breaking** | HOCH | HOCH | Versioning + Migration Scripts |
| **User Errors (falsche Expressions)** | HOCH | NIEDRIG | Validation + UI-Hilfe |
| **Scope Creep** | MITTEL | HOCH | Strikter Phasenplan |

---

## ✅ QUALITÄTSSICHERUNG

### Test-Strategie

**Unit-Tests:**
- CEL Engine: 50+ Test Cases
- RulePack Loader: 20+ Test Cases
- Schema Validator: 30+ Test Cases
- Context Builder: 15+ Test Cases

**Integration Tests:**
- Bot mit CEL: 10+ Szenarien
- Analyzer mit CEL: 10+ Szenarien
- UI mit Backend: 5+ Workflows

**Performance Tests:**
- 1000 Expressions compilen: < 1s
- 10000 Evaluations: < 1s
- Memory-Leak Test: 24h Runtime

**User Acceptance Tests:**
- Entry Designer → CEL → Bot Workflow
- Backtest mit verschiedenen RulePacks
- UI-Usability Tests

### Code Quality Checks

```bash
# Linting
ruff check src/core/tradingbot/cel/

# Type Checking
mypy src/core/tradingbot/cel/

# Test Coverage
pytest --cov=src/core/tradingbot/cel/ --cov-report=html

# Coverage Target: >80%
```

---

## 🚀 ROLLOUT-STRATEGIE

### Stage 1: Alpha (Interne Tests)
**Dauer:** 1 Woche
**Features:** CEL Engine + Basic UI
**Zielgruppe:** Entwickler

### Stage 2: Beta (Closed Testing)
**Dauer:** 2 Wochen
**Features:** Full UI + Bot Integration
**Zielgruppe:** Power User

### Stage 3: Production Release
**Dauer:** -
**Features:** Alle Features + Docs
**Zielgruppe:** Alle User

---

## 📚 DOKUMENTATIONS-UPDATES

### Neue Dokumentations-Files

1. **JSON_INTERFACE_RULES.md** (siehe unten)
2. **CEL_User_Guide.md**
3. **CEL_Developer_Guide.md**
4. **CEL_API_Reference.md**
5. **CEL_Migration_Guide.md**

### Updates in existierenden Files

- ✅ CLAUDE.md: JSON-Interface-Link
- ✅ Agents.md: JSON-Schema-System
- ✅ Gemini.md: JSON-Architektur
- ✅ ARCHITECTURE.md: CEL-Komponenten hinzufügen
- ✅ README.md: CEL-Features erwähnen

---

## 🎯 NÄCHSTE SCHRITTE

### Sofort (Woche 1)

1. ✅ **Phase 1 starten:** JSON Schema System
2. ✅ Dependencies installieren (celpy, jsonschema)
3. ✅ JSON_INTERFACE_RULES.md erstellen
4. ✅ Schema-Files erstellen
5. ✅ Dokumentations-Updates (CLAUDE.md, etc.)

### Kurz (Woche 2)

6. ✅ CEL Engine Core implementieren
7. ✅ RulePack System implementieren
8. ✅ UI prototyp erstellen

### Mittel (Woche 3-4)

9. ✅ Trading Bot Integration
10. ✅ Entry Analyzer Integration
11. ✅ Testing & Optimization

### Lang (Post-Release)

12. ✅ KI-Integration vorbereiten (JSON-Interface bereits bereit)
13. ✅ Community Feedback einarbeiten
14. ✅ Advanced Features (Custom Indicators in CEL, etc.)

---

## 📝 ANHANG: JSON_INTERFACE_RULES.md

**Datei:** `01_Projectplan/Strategien_Workflow_json/JSON_INTERFACE_RULES.md`

```markdown
# JSON Interface Rules - OrderPilot-AI

## Übersicht

JSON ist die **universelle Schnittstelle** zwischen allen Modulen:
- Entry Designer ↔ CEL Engine ↔ Trading Bot ↔ KI (später)

## Verbindliche Regeln

### 1. NIEMALS JSON manuell editieren
- ✅ Verwende UI-Tools (Entry Designer, CEL Editor)
- ❌ Keine Text-Editor-Änderungen

### 2. IMMER Schema-Validation durchführen
- Vor dem Laden: Schema-Check
- Vor dem Speichern: Schema-Check
- Bei Fehlern: Klare Error-Messages

### 3. Versioning ist PFLICHT
- Jedes JSON hat `schema_version` oder `rules_version`
- Bei Breaking Changes: Major-Version erhöhen
- Migration-Scripts für alte Versionen

### 4. Rückwärtskompatibilität
- Minor-Updates: Abwärtskompatibel
- Major-Updates: Migration-Script erforderlich

## JSON-Dateien Übersicht

| Datei-Typ | Schema | Beispiel-Pfad |
|-----------|--------|---------------|
| **TradingBotConfig** | `trading_bot_config_schema.json` | `03_JSON/Trading_Bot/conservative.json` |
| **RulePack** | `rulepack_schema.json` | `03_JSON/RulePacks/default.json` |
| **IndicatorDefinition** | `indicator_schema.json` | Teil von TradingBotConfig |
| **RegimeDefinition** | `regime_schema.json` | Teil von TradingBotConfig |
| **StrategyDefinition** | `strategy_schema.json` | Teil von TradingBotConfig |

## Schema-Validation Workflow

```
1. User Action (UI)
   ↓
2. Generate JSON (in-memory)
   ↓
3. Validate against Schema
   ↓
4. If Valid → Save to File
   If Invalid → Show Errors in UI
```

## Error Handling

**Bei Schema-Validierungs-Fehler:**

```
❌ Validation failed for rulepack_schema:
  - packs.0.rules.2.expr: String too short (min: 1)
  - packs.1.rules.0.result_type: Missing required field
```

**Klare Fehlermeldungen mit:**
- ✅ JSON-Pfad zum Fehler
- ✅ Erwarteter Wert
- ✅ Tatsächlicher Wert

## Breaking Changes

**Bei Änderungen am JSON-Format:**

1. Schema-Version erhöhen
2. Migration-Script erstellen
3. Alle Module aktualisieren:
   - Entry Designer
   - CEL Engine
   - Trading Bot
   - (Später: KI)

**Beispiel Migration:**

```python
def migrate_rulepack_v1_to_v2(old_rulepack: dict) -> dict:
    \"\"\"Migrate RulePack from v1.0.0 to v2.0.0.\"\"\"

    new_rulepack = old_rulepack.copy()

    # Example: Add new field
    new_rulepack["metadata"] = {
        "created_at": datetime.now().isoformat(),
        "author": "system"
    }

    # Update version
    new_rulepack["rules_version"] = "2.0.0"

    return new_rulepack
```

## Referenzen

- **JSON Schema Specs:** [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/schema)
- **CEL Rules Doku:** `CEL_Rules_Doku_TradingBot_Analyzer.md`
- **CEL Befehle Liste:** `CEL_Befehle_Liste_v2.md`
```

---

## 📋 CHANGE LOG

| Datum | Version | Änderungen |
|-------|---------|-----------|
| 2026-01-20 | 1.0 | Initial Plan erstellt |

---

**Status:** Ready for Implementation
**Geschätzter Aufwand:** 120-150 Stunden (3-4 Wochen Vollzeit)
**Erwarteter ROI:** Sehr hoch (konfigurierbare Regeln ohne Code-Änderungen)
