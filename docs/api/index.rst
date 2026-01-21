OrderPilot-AI API Documentation
================================

.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python Version

.. image:: https://img.shields.io/badge/status-production-green.svg
   :alt: Status

**OrderPilot-AI** is a regime-based trading bot with AI integration for adaptive market strategies.

Features
--------

✅ **Regime-Based Trading**: Automatically switches strategies based on market conditions

✅ **JSON Configuration**: Type-safe, version-controlled strategy definitions

✅ **AI Integration**: Chart pattern recognition and strategy generation

✅ **Walk-Forward Validation**: Robust backtesting with out-of-sample testing

✅ **Real-Time Monitoring**: Performance tracking and regime stability analysis

Quick Links
-----------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Getting Started
---------------

For user guides and tutorials, see:

* `Getting Started with Regime-Based Strategies <../guides/01_Getting_Started_Regime_Based_Strategies.html>`_
* `JSON Configuration Format Guide <../guides/02_JSON_Configuration_Format_Guide.html>`_
* `Creating Custom Regimes <../guides/03_Creating_Custom_Regimes.html>`_
* `Strategy Creation Guide <../guides/04_Strategy_Creation_Guide.html>`_
* `Advanced Features Guide <../guides/05_Advanced_Features_Guide.html>`_

API Reference
-------------

Core Trading Bot
~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: Core Modules

   modules/bot_controller
   modules/regime_engine
   modules/entry_scorer
   modules/regime_stability

Configuration System
~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: JSON Configuration

   modules/config_models
   modules/config_loader
   modules/config_evaluator
   modules/config_detector
   modules/config_router
   modules/config_executor

Backtesting & Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: Backtesting

   modules/backtest_engine
   modules/backtest_harness
   modules/strategy_evaluator

AI Integration
~~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: AI Modules

   modules/pattern_recognizer
   modules/strategy_generator
   modules/parameter_optimizer

UI Components
~~~~~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: User Interface

   modules/performance_monitor_widget
   modules/entry_analyzer_popup

Utilities
~~~~~~~~~

.. toctree::
   :maxdepth: 2
   :caption: Utilities

   modules/config_integration_bridge
   modules/config_reloader

Module Overview
---------------

Core Trading Bot
~~~~~~~~~~~~~~~~

:mod:`bot_controller`
    Main bot controller with regime-based strategy switching

:mod:`regime_engine`
    Market regime classification (trend, range, volatility)

:mod:`entry_scorer`
    Entry signal scoring with multi-component analysis

:mod:`regime_stability`
    Regime stability tracking for production monitoring

Configuration System
~~~~~~~~~~~~~~~~~~~~

:mod:`config.models`
    Pydantic models for type-safe JSON configuration

:mod:`config.loader`
    Two-stage validation (JSON Schema + Pydantic)

:mod:`config.evaluator`
    Condition evaluation engine (operator-based + CEL)

:mod:`config.detector`
    Multi-regime detection with scope filtering

:mod:`config.router`
    Strategy routing based on active regimes

:mod:`config.executor`
    Parameter override execution and state management

Backtesting & Validation
~~~~~~~~~~~~~~~~~~~~~~~~~

:mod:`backtest_engine`
    Core backtesting engine with multi-timeframe support

:mod:`backtest_harness`
    Full bot backtest with feature engine integration

:mod:`strategy_evaluator`
    Walk-forward validation and robustness testing

AI Integration
~~~~~~~~~~~~~~

:mod:`pattern_recognizer`
    Chart pattern detection (15+ patterns)

:mod:`strategy_generator`
    LLM-based strategy generation from patterns

:mod:`parameter_optimizer`
    4 optimization algorithms (Genetic, Bayesian, Grid, Random)

UI Components
~~~~~~~~~~~~~

:mod:`performance_monitor_widget`
    Real-time performance monitoring with charts

:mod:`entry_analyzer_popup`
    Strategy analysis and backtesting interface

Architecture
------------

.. code-block:: text

    OrderPilot-AI/
    ├── src/core/tradingbot/
    │   ├── bot_controller.py          # Main bot orchestration
    │   ├── regime_engine.py           # Regime classification
    │   ├── entry_scorer.py            # Entry scoring
    │   ├── regime_stability.py        # Stability tracking
    │   ├── config/
    │   │   ├── models.py              # Pydantic models
    │   │   ├── loader.py              # Config loading
    │   │   ├── evaluator.py           # Condition evaluation
    │   │   ├── detector.py            # Regime detection
    │   │   ├── router.py              # Strategy routing
    │   │   └── executor.py            # Parameter overrides
    │   └── ...
    ├── src/backtesting/
    │   ├── engine.py                  # Backtest engine
    │   └── ...
    ├── src/ai/
    │   ├── pattern_recognizer.py     # Chart patterns
    │   ├── strategy_generator.py     # LLM generation
    │   └── parameter_optimizer.py    # Optimization
    └── src/ui/
        ├── widgets/
        │   └── performance_monitor_widget.py
        └── dialogs/
            └── entry_analyzer_popup.py

Data Flow
---------

.. code-block:: text

    Market Data
        ↓
    RegimeEngine.classify()
        ↓
    RegimeDetector.detect_active_regimes()
        ↓
    StrategyRouter.route()
        ↓
    StrategySetExecutor.prepare_execution()
        ↓
    BotController._switch_strategy()
        ↓
    EntryScorer.calculate_score()
        ↓
    Trade Execution

Changelog
---------

Version 1.0.0 (2026-01-20)
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Major Features:**

* ✅ Regime-based JSON configuration system (Phases 1-3)
* ✅ Dynamic strategy switching with parameter overrides (Phase 2.2)
* ✅ Complete UI integration (Phase 4)
* ✅ Walk-forward validation system (Phase 5)
* ✅ AI integration with pattern recognition (Phase 6)
* ✅ Production monitoring tools (Phase 7)

**Modules Added:**

* ``regime_stability.py`` - Regime stability tracking
* ``performance_monitor_widget.py`` - Real-time UI monitoring
* ``pattern_recognizer.py`` - Chart pattern detection
* ``strategy_generator.py`` - LLM-based strategy generation
* ``parameter_optimizer.py`` - Multi-algorithm optimization
* ``evaluator_validation.py`` - Walk-forward validation
* ``evaluator_visualization.py`` - Validation result charts

**Test Coverage:**

* 25+ test files
* 220+ test methods
* 80%+ code coverage

**Documentation:**

* 5 comprehensive user guides (15,700+ lines)
* Complete API reference (this document)
* Production deployment guides

Contributing
------------

For contribution guidelines, see ``CONTRIBUTING.md`` in the project root.

License
-------

See ``LICENSE`` file in the project root.

Support
-------

* **Documentation:** `/docs/`
* **User Guides:** `/docs/guides/`
* **GitHub Issues:** `https://github.com/your-repo/issues`

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
