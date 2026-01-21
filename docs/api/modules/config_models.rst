Configuration Models
====================

.. automodule:: src.core.tradingbot.config.models
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``config.models`` module provides **type-safe Pydantic models** for JSON configuration:

* **Indicator Definitions**: RSI, MACD, ADX, SMA, EMA, ATR, BB, Volume (15+ types)
* **Regime Definitions**: Market condition detection with scopes and priorities
* **Strategy Definitions**: Entry/exit conditions + risk management
* **Strategy Sets**: Groups of strategies with parameter overrides
* **Routing Rules**: Maps regime combinations to strategy sets

All models use Pydantic v2 for validation, type safety, and automatic JSON Schema generation.

Key Features
------------

**Type Safety:**
   Pydantic models catch configuration errors at load time, not runtime.

**JSON Schema Integration:**
   Models auto-generate JSON Schema for IDE validation and documentation.

**Nested Validation:**
   Complex nested structures (conditions, overrides) validated recursively.

**Immutability:**
   Config models are frozen (immutable) after creation to prevent accidental modifications.

**Comprehensive Coverage:**
   Every JSON configuration element has a corresponding Pydantic model.

Model Hierarchy
---------------

.. code-block:: text

    TradingBotConfig (Root)
    ├── Indicator[]
    ├── Regime[]
    │   └── Condition | ConditionGroup
    ├── Strategy[]
    │   ├── Condition | ConditionGroup (entry)
    │   ├── Condition | ConditionGroup (exit)
    │   └── RiskConfig
    ├── StrategySet[]
    │   ├── StrategySetStrategy[]
    │   ├── IndicatorOverride{}
    │   └── StrategyOverride{}
    └── RoutingRule[]
        └── RegimeMatch

Core Models
-----------

TradingBotConfig
~~~~~~~~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.TradingBotConfig
   :members:
   :undoc-members:

**Root configuration model** containing all trading bot settings.

**Fields:**

.. code-block:: python

    class TradingBotConfig(BaseModel):
        schema_version: str = "1.0.0"
        metadata: dict[str, Any] = {}
        indicators: list[Indicator]
        regimes: list[Regime]
        strategies: list[Strategy]
        strategy_sets: list[StrategySet]
        routing: list[RoutingRule]

**Validation Rules:**

1. All indicator IDs must be unique
2. All regime IDs must be unique
3. All strategy IDs must be unique
4. All strategy set IDs must be unique
5. Routing rules must reference existing strategy sets
6. Strategy sets must reference existing strategies
7. Overrides must reference existing indicators/strategies

**Example:**

.. code-block:: python

    from src.core.tradingbot.config.models import TradingBotConfig

    config = TradingBotConfig(
        indicators=[...],
        regimes=[...],
        strategies=[...],
        strategy_sets=[...],
        routing=[...]
    )

    # Access nested data
    print(config.indicators[0].id)
    print(config.strategies[0].entry_conditions)

Indicator
~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.Indicator
   :members:
   :undoc-members:

**Indicator definition** with type and parameters.

**Fields:**

.. code-block:: python

    class Indicator(BaseModel):
        id: str  # Unique identifier (e.g., "rsi_14")
        type: IndicatorType  # RSI, MACD, ADX, etc.
        params: dict[str, Any] = {}  # Type-specific parameters

**Supported Types:**

.. code-block:: python

    class IndicatorType(str, Enum):
        RSI = "RSI"
        MACD = "MACD"
        ADX = "ADX"
        SMA = "SMA"
        EMA = "EMA"
        ATR = "ATR"
        BB = "BB"  # Bollinger Bands
        VOLUME = "Volume"
        PRICE = "Price"
        PLUS_DI = "PlusDI"
        MINUS_DI = "MinusDI"
        # ... 15+ total

**Example:**

.. code-block:: python

    indicators = [
        Indicator(id="rsi_14", type=IndicatorType.RSI, params={"period": 14}),
        Indicator(id="macd_default", type=IndicatorType.MACD, params={
            "fast": 12, "slow": 26, "signal": 9
        }),
        Indicator(id="sma_50", type=IndicatorType.SMA, params={"period": 50})
    ]

Regime
~~~~~~

.. autoclass:: src.core.tradingbot.config.models.Regime
   :members:
   :undoc-members:

**Regime definition** with market condition detection.

**Fields:**

.. code-block:: python

    class Regime(BaseModel):
        id: str
        name: str
        description: str = ""
        conditions: Condition | ConditionGroup
        scope: RegimeScope = RegimeScope.ENTRY
        priority: int = 0

**Scope Types:**

.. code-block:: python

    class RegimeScope(str, Enum):
        ENTRY = "entry"        # Evaluated before entry
        EXIT = "exit"          # Evaluated on every bar
        IN_TRADE = "in_trade"  # Only while in position
        GLOBAL = "global"      # Always evaluated

**Example:**

.. code-block:: python

    regime = Regime(
        id="strong_uptrend",
        name="Strong Uptrend",
        conditions=ConditionGroup(
            all=[
                Condition(
                    left=OperandValue(indicator="adx"),
                    op=ConditionOperator.GT,
                    right=OperandValue(value=25)
                ),
                Condition(
                    left=OperandValue(indicator="plus_di"),
                    op=ConditionOperator.GT,
                    right=OperandValue(indicator="minus_di")
                )
            ]
        ),
        scope=RegimeScope.ENTRY,
        priority=10
    )

Strategy
~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.Strategy
   :members:
   :undoc-members:

**Strategy definition** with entry/exit conditions and risk management.

**Fields:**

.. code-block:: python

    class Strategy(BaseModel):
        id: str
        name: str
        description: str = ""
        entry_conditions: Condition | ConditionGroup
        exit_conditions: Condition | ConditionGroup
        risk: RiskConfig

**Example:**

.. code-block:: python

    strategy = Strategy(
        id="trend_following",
        name="Trend Following Strategy",
        entry_conditions=ConditionGroup(all=[...]),
        exit_conditions=ConditionGroup(any=[...]),
        risk=RiskConfig(
            stop_loss_pct=2.0,
            take_profit_pct=4.0,
            position_size_pct=5.0
        )
    )

RiskConfig
~~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.RiskConfig
   :members:
   :undoc-members:

**Risk management configuration** for a strategy.

**Fields:**

.. code-block:: python

    class RiskConfig(BaseModel):
        stop_loss_pct: float  # Stop loss percentage below entry
        take_profit_pct: float  # Take profit percentage above entry
        position_size_pct: float  # Position size as % of capital
        trailing_stop_pct: float | None = None  # Optional trailing stop
        max_holding_bars: int | None = None  # Optional time limit

**Validation:**

.. code-block:: python

    @field_validator('stop_loss_pct', 'take_profit_pct', 'position_size_pct')
    def validate_positive(cls, v):
        if v <= 0:
            raise ValueError("Must be positive")
        return v

**Example:**

.. code-block:: python

    risk = RiskConfig(
        stop_loss_pct=2.5,
        take_profit_pct=5.0,
        position_size_pct=6.0,
        trailing_stop_pct=3.0,
        max_holding_bars=20
    )

StrategySet
~~~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.StrategySet
   :members:
   :undoc-members:

**Strategy set** with parameter overrides for specific market conditions.

**Fields:**

.. code-block:: python

    class StrategySet(BaseModel):
        id: str
        name: str
        description: str = ""
        strategies: list[StrategySetStrategy]
        indicator_overrides: dict[str, dict[str, Any]] = {}
        strategy_overrides: dict[str, dict[str, Any]] = {}

**Example:**

.. code-block:: python

    strategy_set = StrategySet(
        id="trending_aggressive",
        name="Aggressive Trend Following",
        strategies=[
            StrategySetStrategy(strategy_id="trend_following")
        ],
        indicator_overrides={
            "rsi_14": {"period": 14}  # Faster RSI for trending markets
        },
        strategy_overrides={
            "trend_following": {
                "risk": {
                    "stop_loss_pct": 3.0,      # Wider stop
                    "position_size_pct": 8.0    # Larger position
                }
            }
        }
    )

RoutingRule
~~~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.RoutingRule
   :members:
   :undoc-members:

**Routing rule** mapping regime combinations to strategy sets.

**Fields:**

.. code-block:: python

    class RoutingRule(BaseModel):
        regimes: RegimeMatch
        strategy_set_id: str
        priority: int = 0

**RegimeMatch:**

.. code-block:: python

    class RegimeMatch(BaseModel):
        all_of: list[str] = []   # All regimes must be active
        any_of: list[str] = []   # At least one regime active
        none_of: list[str] = []  # None of these regimes active

**Example:**

.. code-block:: python

    routing = [
        RoutingRule(
            regimes=RegimeMatch(
                all_of=["strong_uptrend", "normal_volatility"]
            ),
            strategy_set_id="trending_aggressive",
            priority=10
        ),
        RoutingRule(
            regimes=RegimeMatch(
                any_of=["range_bound", "low_volatility"]
            ),
            strategy_set_id="ranging_conservative",
            priority=5
        )
    ]

Condition Models
----------------

Condition
~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.Condition
   :members:
   :undoc-members:

**Single condition** comparing two operands.

**Fields:**

.. code-block:: python

    class Condition(BaseModel):
        left: OperandValue
        op: ConditionOperator
        right: OperandValue

**Operators:**

.. code-block:: python

    class ConditionOperator(str, Enum):
        GT = "gt"          # Greater than
        LT = "lt"          # Less than
        EQ = "eq"          # Equal
        GTE = "gte"        # Greater than or equal
        LTE = "lte"        # Less than or equal
        BETWEEN = "between"  # Between two values

**Example:**

.. code-block:: python

    # RSI > 50
    condition = Condition(
        left=OperandValue(indicator="rsi_14"),
        op=ConditionOperator.GT,
        right=OperandValue(value=50)
    )

    # Price between SMA 20 and SMA 50
    condition = Condition(
        left=OperandValue(indicator="price"),
        op=ConditionOperator.BETWEEN,
        right=OperandValue(value=[
            {"indicator": "sma_20"},
            {"indicator": "sma_50"}
        ])
    )

ConditionGroup
~~~~~~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.ConditionGroup
   :members:
   :undoc-members:

**Group of conditions** with AND/OR logic.

**Fields:**

.. code-block:: python

    class ConditionGroup(BaseModel):
        all: list[Condition | ConditionGroup] = []  # AND logic
        any: list[Condition | ConditionGroup] = []  # OR logic

**Example:**

.. code-block:: python

    # (RSI > 50 AND Price > SMA 50) OR (MACD > 0)
    group = ConditionGroup(
        any=[
            ConditionGroup(
                all=[
                    Condition(left={"indicator": "rsi_14"}, op="gt", right={"value": 50}),
                    Condition(left={"indicator": "price"}, op="gt", right={"indicator": "sma_50"})
                ]
            ),
            Condition(left={"indicator": "macd_histogram"}, op="gt", right={"value": 0})
        ]
    )

OperandValue
~~~~~~~~~~~~

.. autoclass:: src.core.tradingbot.config.models.OperandValue
   :members:
   :undoc-members:

**Operand value** (indicator reference, constant, or expression).

**Fields:**

.. code-block:: python

    class OperandValue(BaseModel):
        indicator: str | None = None      # Indicator ID reference
        value: Any | None = None          # Constant value
        expression: str | None = None     # CEL expression (future)
        offset: float | None = None       # Multiplier offset
        multiplier: float | None = None   # Value multiplier

**Examples:**

.. code-block:: python

    # Indicator reference
    OperandValue(indicator="rsi_14")

    # Constant value
    OperandValue(value=50)

    # Indicator with offset (+2%)
    OperandValue(indicator="sma_50", offset=1.02)

    # Indicator with multiplier (1.5x)
    OperandValue(indicator="volume_sma", multiplier=1.5)

Validation Features
-------------------

**Automatic Validation:**

.. code-block:: python

    # This will raise ValidationError
    try:
        config = TradingBotConfig(
            indicators=[
                Indicator(id="rsi", type="INVALID_TYPE", params={})
            ],
            # ... other fields
        )
    except ValidationError as e:
        print(e.json())

**Field Validation:**

.. code-block:: python

    class RiskConfig(BaseModel):
        @field_validator('stop_loss_pct')
        def validate_stop_loss(cls, v):
            if v <= 0:
                raise ValueError("Stop loss must be positive")
            if v > 100:
                raise ValueError("Stop loss cannot exceed 100%")
            return v

**Cross-Field Validation:**

.. code-block:: python

    class Strategy(BaseModel):
        @model_validator(mode='after')
        def validate_risk_reward(self):
            if self.risk.take_profit_pct < self.risk.stop_loss_pct:
                raise ValueError("Take profit should be > stop loss")
            return self

JSON Schema Generation
----------------------

**Auto-generate JSON Schema:**

.. code-block:: python

    from src.core.tradingbot.config.models import TradingBotConfig

    schema = TradingBotConfig.model_json_schema()

    with open("strategy_config_schema.json", "w") as f:
        json.dump(schema, f, indent=2)

**Use for IDE Validation:**

In VSCode ``settings.json``:

.. code-block:: json

    {
        "json.schemas": [
            {
                "fileMatch": ["03_JSON/Trading_Bot/*.json"],
                "url": "./03_JSON/schema/strategy_config_schema.json"
            }
        ]
    }

Best Practices
--------------

**1. Use Type Hints:**

.. code-block:: python

    def load_config(config_dict: dict) -> TradingBotConfig:
        return TradingBotConfig(**config_dict)

**2. Validate Early:**

.. code-block:: python

    try:
        config = TradingBotConfig(**json_data)
    except ValidationError as e:
        logger.error(f"Invalid config: {e}")
        raise

**3. Immutable Configs:**

.. code-block:: python

    # ❌ Don't modify after creation
    config.indicators[0].params["period"] = 21  # Frozen!

    # ✅ Create new instance
    new_config = config.model_copy(update={
        "indicators": [...]
    })

**4. Use Field Defaults:**

.. code-block:: python

    class Strategy(BaseModel):
        description: str = ""  # Optional field with default
        scope: RegimeScope = RegimeScope.ENTRY  # Enum with default

See Also
--------

* :doc:`config_loader` - Loads and validates JSON configs using these models
* :doc:`config_evaluator` - Evaluates conditions defined in these models
* :doc:`config_detector` - Detects regimes using these models
* :doc:`config_router` - Routes using routing rules defined here
