Configuration Loader
====================

.. automodule:: src.core.tradingbot.config.loader
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``ConfigLoader`` provides **two-stage validation** for JSON configurations:

1. **JSON Schema Validation**: Structural validation against JSON Schema Draft 2020-12
2. **Pydantic Model Validation**: Type safety and business logic validation

This ensures configurations are both syntactically correct and semantically valid before use.

Key Features
------------

**Two-Stage Validation:**
   JSON Schema first for structure, then Pydantic for types and business rules.

**Helpful Error Messages:**
   Detailed error messages with line numbers and specific validation failures.

**File Discovery:**
   List all valid configurations in a directory with metadata.

**Schema Caching:**
   JSON Schema loaded once and cached for performance.

**Path Resolution:**
   Handles relative and absolute paths consistently.

Usage Example
-------------

.. code-block:: python

    from src.core.tradingbot.config.loader import ConfigLoader

    # Initialize loader
    loader = ConfigLoader()

    # Load and validate config
    try:
        config = loader.load_config("03_JSON/Trading_Bot/my_strategy.json")
        print(f"Loaded: {config.metadata.get('name', 'Unnamed')}")
    except FileNotFoundError:
        print("Config file not found")
    except ValueError as e:
        print(f"Validation failed: {e}")

    # List all configs in directory
    configs = loader.list_configs("03_JSON/Trading_Bot/")
    for config_info in configs:
        print(f"{config_info['name']} - {config_info['path']}")

Classes
-------

.. autoclass:: src.core.tradingbot.config.loader.ConfigLoader
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

load_config(config_path)
~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.loader.ConfigLoader.load_config

Load and validate JSON configuration file.

**Parameters:**

* ``config_path`` (str | Path): Path to JSON configuration file

**Returns:**

* ``TradingBotConfig``: Validated Pydantic model instance

**Raises:**

* ``FileNotFoundError``: If config file doesn't exist
* ``ValueError``: If JSON is malformed or validation fails

**Validation Flow:**

1. **Load JSON file:**

   .. code-block:: python

       with open(config_path) as f:
           data = json.load(f)

2. **JSON Schema Validation:**

   .. code-block:: python

       jsonschema.validate(data, self.json_schema)
       # Validates: structure, required fields, data types

3. **Pydantic Model Validation:**

   .. code-block:: python

       config = TradingBotConfig(**data)
       # Validates: type safety, business rules, cross-field logic

4. **Return validated config**

**Example:**

.. code-block:: python

    # Valid config
    config = loader.load_config("trend_following.json")
    print(config.indicators[0].id)  # Fully typed access

    # Invalid config (missing required field)
    try:
        config = loader.load_config("invalid.json")
    except ValueError as e:
        print(f"Error: {e}")
        # Output: "Error: Field 'indicators' is required"

validate_config_data(config_data)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.loader.ConfigLoader.validate_config_data

Validate configuration data dict (without loading from file).

**Parameters:**

* ``config_data`` (dict): Configuration dictionary

**Returns:**

* ``TradingBotConfig``: Validated Pydantic model instance

**Raises:**

* ``ValueError``: If validation fails

**Use Cases:**

1. **Validate programmatically generated configs:**

   .. code-block:: python

       config_dict = {
           "schema_version": "1.0.0",
           "indicators": [...],
           "regimes": [...],
           "strategies": [...],
           "strategy_sets": [...],
           "routing": [...]
       }

       config = loader.validate_config_data(config_dict)

2. **Validate before saving:**

   .. code-block:: python

       # Generate config with AI
       generated_config = ai_generate_strategy(...)

       # Validate before saving
       try:
           validated = loader.validate_config_data(generated_config)
           # Save only if valid
           with open("new_strategy.json", "w") as f:
               json.dump(generated_config, f, indent=2)
       except ValueError as e:
           print(f"Generated config is invalid: {e}")

list_configs(directory, recursive)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.loader.ConfigLoader.list_configs

List all valid configuration files in directory.

**Parameters:**

* ``directory`` (str | Path): Directory to search
* ``recursive`` (bool): Search subdirectories (default: False)

**Returns:**

* ``list[dict]``: List of config metadata dicts with keys:

  * ``path`` (str): Absolute path to config file
  * ``name`` (str): Config name from metadata
  * ``description`` (str): Config description from metadata
  * ``schema_version`` (str): Schema version
  * ``is_valid`` (bool): Whether config passes validation

**Example:**

.. code-block:: python

    configs = loader.list_configs("03_JSON/Trading_Bot/", recursive=True)

    # Filter by name
    trend_configs = [c for c in configs if "trend" in c["name"].lower()]

    # List all valid configs
    for config in configs:
        if config["is_valid"]:
            print(f"✓ {config['name']} - {config['path']}")
        else:
            print(f"✗ {config['name']} - {config['path']} (invalid)")

    # Load first valid config
    valid_configs = [c for c in configs if c["is_valid"]]
    if valid_configs:
        config = loader.load_config(valid_configs[0]["path"])

_load_json_schema()
~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.loader.ConfigLoader._load_json_schema

**Internal method** - Load JSON Schema from file.

**Schema Location:**

.. code-block:: python

    SCHEMA_PATH = "03_JSON/schema/strategy_config_schema.json"

**Caching:**

Schema is loaded once and cached in ``self.json_schema``.

**Schema Content:**

.. code-block:: json

    {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "type": "object",
        "properties": {
            "schema_version": {"type": "string"},
            "indicators": {"type": "array", "items": {"$ref": "#/$defs/Indicator"}},
            "regimes": {"type": "array", "items": {"$ref": "#/$defs/Regime"}},
            ...
        },
        "required": ["indicators", "regimes", "strategies", "strategy_sets", "routing"],
        "$defs": {
            "Indicator": {...},
            "Regime": {...},
            ...
        }
    }

_validate_with_json_schema(data)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.core.tradingbot.config.loader.ConfigLoader._validate_with_json_schema

**Internal method** - Validate data against JSON Schema.

**Validation:**

.. code-block:: python

    jsonschema.validate(data, self.json_schema)

**Error Handling:**

.. code-block:: python

    try:
        jsonschema.validate(data, self.json_schema)
    except jsonschema.ValidationError as e:
        # Convert to user-friendly error message
        raise ValueError(f"JSON Schema validation failed: {e.message}\nPath: {e.path}")

Validation Stages Explained
----------------------------

**Stage 1: JSON Schema Validation**

**Purpose**: Catch structural errors early

**Checks:**
- Required fields present
- Correct data types (string, number, array, object)
- Enum values valid
- Array/object structure correct

**Example Errors:**

.. code-block:: text

    ❌ Missing required field 'indicators'
    ❌ Field 'schema_version' must be string (got number)
    ❌ Field 'indicators' must be array (got object)
    ❌ Indicator type 'INVALID' not in enum [RSI, MACD, ADX, ...]

**Stage 2: Pydantic Model Validation**

**Purpose**: Type safety and business logic

**Checks:**
- Type annotations (List[Indicator], etc.)
- Field validators (positive values, etc.)
- Model validators (cross-field logic)
- Enum conversions
- Nested model validation

**Example Errors:**

.. code-block:: text

    ❌ Field 'stop_loss_pct' must be positive (got -2.0)
    ❌ Field 'take_profit_pct' must be > 'stop_loss_pct'
    ❌ Indicator ID 'rsi_14' referenced but not defined
    ❌ Strategy set 'trending' references unknown strategy 'unknown_strat'

Error Handling
--------------

**FileNotFoundError:**

.. code-block:: python

    try:
        config = loader.load_config("nonexistent.json")
    except FileNotFoundError:
        print("Config file not found")

**JSON Parse Error:**

.. code-block:: python

    # Malformed JSON (trailing comma, etc.)
    try:
        config = loader.load_config("malformed.json")
    except ValueError as e:
        print(f"JSON parse error: {e}")

**JSON Schema Validation Error:**

.. code-block:: python

    # Missing required field
    try:
        config = loader.load_config("incomplete.json")
    except ValueError as e:
        print(f"Schema validation failed: {e}")
        # Output: "Field 'indicators' is required"

**Pydantic Validation Error:**

.. code-block:: python

    # Invalid value (e.g., negative stop loss)
    try:
        config = loader.load_config("invalid_values.json")
    except ValueError as e:
        print(f"Validation failed: {e}")
        # Output: "Field 'stop_loss_pct' must be positive"

Best Practices
--------------

**1. Always Validate Before Use:**

.. code-block:: python

    # ✅ Good: Load with validation
    try:
        config = loader.load_config("strategy.json")
        bot.set_config(config)
    except ValueError as e:
        logger.error(f"Config validation failed: {e}")
        return

    # ❌ Bad: Load JSON directly
    with open("strategy.json") as f:
        data = json.load(f)
    bot.set_config(data)  # No validation! Runtime errors possible

**2. Use list_configs() for Discovery:**

.. code-block:: python

    # Get all valid configs
    valid_configs = [c for c in loader.list_configs("03_JSON/Trading_Bot/") if c["is_valid"]]

    # Let user choose
    for i, config in enumerate(valid_configs):
        print(f"{i+1}. {config['name']} - {config['description']}")

    choice = int(input("Select config: "))
    config = loader.load_config(valid_configs[choice-1]["path"])

**3. Validate Programmatically Generated Configs:**

.. code-block:: python

    # AI-generated config
    generated_config = {
        "schema_version": "1.0.0",
        "indicators": ai_generate_indicators(),
        "regimes": ai_generate_regimes(),
        "strategies": ai_generate_strategies(),
        "strategy_sets": ai_generate_strategy_sets(),
        "routing": ai_generate_routing()
    }

    # Validate before using
    try:
        validated = loader.validate_config_data(generated_config)
        print("✓ AI-generated config is valid")
    except ValueError as e:
        print(f"✗ AI-generated config is invalid: {e}")

**4. Handle Errors Gracefully:**

.. code-block:: python

    def load_config_safe(path: str) -> TradingBotConfig | None:
        """Load config with comprehensive error handling."""
        try:
            return loader.load_config(path)
        except FileNotFoundError:
            logger.error(f"Config file not found: {path}")
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON in {path}: {e}")
        except ValueError as e:
            logger.error(f"Config validation failed for {path}: {e}")
        return None

Integration Example
-------------------

**Complete Bot Startup Flow:**

.. code-block:: python

    from src.core.tradingbot.config.loader import ConfigLoader
    from src.core.tradingbot.bot_controller import BotController

    # 1. Initialize loader
    loader = ConfigLoader()

    # 2. List available configs
    configs = loader.list_configs("03_JSON/Trading_Bot/")
    print(f"Found {len(configs)} configurations")

    # 3. Load selected config
    config_path = "03_JSON/Trading_Bot/regime_adaptive_balanced.json"
    try:
        config = loader.load_config(config_path)
        print(f"✓ Loaded: {config.metadata.get('name')}")
    except ValueError as e:
        print(f"✗ Failed to load config: {e}")
        sys.exit(1)

    # 4. Initialize bot with validated config
    bot = BotController()
    bot.set_json_config(config)

    # 5. Start trading
    bot.start()

See Also
--------

* :doc:`config_models` - Pydantic models used for validation
* :doc:`config_evaluator` - Evaluates conditions from loaded configs
* :doc:`bot_controller` - Uses ConfigLoader to load trading configs
* :doc:`config_reloader` - Auto-reloads configs on file changes
