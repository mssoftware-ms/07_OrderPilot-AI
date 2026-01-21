Parameter Optimizer
===================

.. automodule:: src.ai.parameter_optimizer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Overview
--------

The ``ParameterOptimizer`` automatically tunes strategy parameters using optimization algorithms:

* **Regime Threshold Optimization**: Tunes ADX, ATR, and other regime detection thresholds
* **Indicator Parameter Optimization**: Optimizes periods, multipliers, and other indicator settings
* **Risk Parameter Optimization**: Tunes stop loss, take profit, position size, and trailing stops
* **Multi-Algorithm Support**: GENETIC, BAYESIAN, GRID, RANDOM optimization methods
* **Multi-Objective**: Supports SHARPE, WIN_RATE, PROFIT_FACTOR, TOTAL_RETURN, RISK_ADJ_RETURN

Key Features
------------

**Intelligent Optimization:**
   Uses genetic algorithms, Bayesian optimization, grid search, or random search to find optimal parameters.

**Flexible Objectives:**
   Optimize for Sharpe ratio, win rate, profit factor, total return, or risk-adjusted return.

**Parameter Range Control:**
   Define min/max bounds and step sizes for each parameter.

**Comprehensive Results:**
   Returns best parameters, objective value, convergence history, and parameter evolution.

**Safe Application:**
   Validates parameters before applying to ensure config integrity.

Usage Example
-------------

.. code-block:: python

    from src.ai.parameter_optimizer import ParameterOptimizer, OptimizationMethod, OptimizationObjective
    from src.core.tradingbot.config.loader import ConfigLoader
    import pandas as pd

    # 1. Load config and data
    loader = ConfigLoader()
    config = loader.load_config('strategy.json')
    df = load_market_data('BTCUSD', '1h', lookback_days=180)

    # 2. Initialize optimizer
    optimizer = ParameterOptimizer()

    # 3. Optimize regime thresholds
    param_ranges = {
        'adx_threshold': (15, 35, 5),  # (min, max, step)
        'atr_low': (0.01, 0.025, 0.005),
        'atr_high': (0.03, 0.06, 0.01)
    }

    def objective_fn(config, data):
        # Run backtest
        result = run_backtest(config, data)
        # Return Sharpe ratio
        return result.sharpe

    result = optimizer.optimize_regime_thresholds(
        config=config,
        data=df,
        param_ranges=param_ranges,
        objective_fn=objective_fn,
        method=OptimizationMethod.GENETIC,
        max_iterations=50
    )

    # 4. Check result
    if result.success:
        print(f"✓ Optimization complete")
        print(f"Best Sharpe: {result.best_value:.2f}")
        print(f"Best Parameters:")
        for param, value in result.best_params.items():
            print(f"  {param}: {value}")

        # 5. Apply best parameters
        optimized_config = optimizer.apply_best_params(
            config=config,
            params=result.best_params,
            target_type='regime_thresholds'
        )

        # 6. Save optimized config
        save_config(optimized_config, 'strategy_optimized.json')
    else:
        print(f"✗ Optimization failed: {result.error}")

Classes
-------

.. autoclass:: src.ai.parameter_optimizer.ParameterOptimizer
   :members:
   :undoc-members:
   :show-inheritance:
   :special-members: __init__

Key Methods
-----------

optimize_regime_thresholds(config, data, param_ranges, objective_fn, method, max_iterations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.parameter_optimizer.ParameterOptimizer.optimize_regime_thresholds

Optimize regime detection thresholds (ADX, ATR, BB Width).

**Parameters:**

* ``config`` (TradingBotConfig): Base configuration
* ``data`` (pd.DataFrame): Historical data for backtesting
* ``param_ranges`` (dict[str, tuple]): Parameter ranges as {name: (min, max, step)}
* ``objective_fn`` (callable): Function that takes (config, data) and returns float to maximize
* ``method`` (OptimizationMethod): GENETIC, BAYESIAN, GRID, or RANDOM
* ``max_iterations`` (int): Maximum optimization iterations

**Returns:**

* ``OptimizationResult``: Result with best params, value, history

**Algorithm (GENETIC method):**

1. **Initialize Population:**

   .. code-block:: python

       population_size = 20
       population = []

       for _ in range(population_size):
           # Random individual
           individual = {
               param: random.uniform(min_val, max_val)
               for param, (min_val, max_val, _) in param_ranges.items()
           }
           population.append(individual)

2. **Evaluate Fitness:**

   .. code-block:: python

       def evaluate_fitness(individual):
           # Apply parameters to config
           test_config = config.copy()
           for param, value in individual.items():
               set_regime_threshold(test_config, param, value)

           # Run backtest
           fitness = objective_fn(test_config, data)

           return fitness

       fitness_scores = [evaluate_fitness(ind) for ind in population]

3. **Selection (Tournament):**

   .. code-block:: python

       def tournament_selection(population, fitness_scores, k=3):
           # Select k random individuals
           tournament_indices = random.sample(range(len(population)), k)

           # Return best from tournament
           best_idx = max(tournament_indices, key=lambda i: fitness_scores[i])
           return population[best_idx]

4. **Crossover (Uniform):**

   .. code-block:: python

       def crossover(parent1, parent2):
           child = {}
           for param in parent1.keys():
               # 50% chance to inherit from each parent
               child[param] = parent1[param] if random.random() < 0.5 else parent2[param]
           return child

5. **Mutation:**

   .. code-block:: python

       def mutate(individual, mutation_rate=0.1):
           mutated = individual.copy()
           for param, value in mutated.items():
               if random.random() < mutation_rate:
                   # Add Gaussian noise
                   min_val, max_val, step = param_ranges[param]
                   noise = random.gauss(0, (max_val - min_val) * 0.1)
                   mutated[param] = np.clip(value + noise, min_val, max_val)
           return mutated

6. **Evolution Loop:**

   .. code-block:: python

       for generation in range(max_iterations):
           # Create new population
           new_population = []

           # Elitism: keep best 10%
           elite_size = population_size // 10
           elite_indices = np.argsort(fitness_scores)[-elite_size:]
           new_population.extend([population[i] for i in elite_indices])

           # Generate rest through selection, crossover, mutation
           while len(new_population) < population_size:
               parent1 = tournament_selection(population, fitness_scores)
               parent2 = tournament_selection(population, fitness_scores)
               child = crossover(parent1, parent2)
               child = mutate(child)
               new_population.append(child)

           # Replace population
           population = new_population
           fitness_scores = [evaluate_fitness(ind) for ind in population]

           # Track best
           best_idx = np.argmax(fitness_scores)
           history.append({
               'generation': generation,
               'best_value': fitness_scores[best_idx],
               'best_params': population[best_idx]
           })

7. **Return Best:**

   .. code-block:: python

       best_idx = np.argmax(fitness_scores)
       return OptimizationResult(
           success=True,
           best_params=population[best_idx],
           best_value=fitness_scores[best_idx],
           history=history,
           method=OptimizationMethod.GENETIC
       )

**Example:**

.. code-block:: python

    # Optimize ADX and ATR thresholds
    result = optimizer.optimize_regime_thresholds(
        config=config,
        data=df,
        param_ranges={
            'adx_threshold': (15, 35, 5),
            'atr_low_pct': (1.0, 2.5, 0.5),
            'atr_high_pct': (3.0, 6.0, 0.5)
        },
        objective_fn=lambda cfg, data: run_backtest(cfg, data).sharpe,
        method=OptimizationMethod.GENETIC,
        max_iterations=100
    )

    print(f"Optimal ADX threshold: {result.best_params['adx_threshold']:.1f}")
    print(f"Optimal ATR low%: {result.best_params['atr_low_pct']:.2f}%")
    print(f"Optimal ATR high%: {result.best_params['atr_high_pct']:.2f}%")

optimize_indicator_params(config, data, indicator_id, param_ranges, method, max_iterations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.parameter_optimizer.ParameterOptimizer.optimize_indicator_params

Optimize parameters for a specific indicator.

**Parameters:**

* ``config`` (TradingBotConfig): Base configuration
* ``data`` (pd.DataFrame): Historical data
* ``indicator_id`` (str): ID of indicator to optimize (e.g., 'rsi_14')
* ``param_ranges`` (dict[str, tuple]): Parameter ranges
* ``method`` (OptimizationMethod): Optimization algorithm
* ``max_iterations`` (int): Maximum iterations

**Returns:**

* ``OptimizationResult``: Best parameters for indicator

**Algorithm (GRID method):**

1. **Generate Parameter Grid:**

   .. code-block:: python

       # Create grid of all combinations
       param_names = list(param_ranges.keys())
       param_values = []

       for param, (min_val, max_val, step) in param_ranges.items():
           values = np.arange(min_val, max_val + step, step)
           param_values.append(values)

       # Cartesian product
       grid = list(itertools.product(*param_values))

       # Example for RSI period: [10, 12, 14, 16, 18, 20]

2. **Evaluate All Combinations:**

   .. code-block:: python

       best_params = None
       best_value = -float('inf')
       history = []

       for i, param_combination in enumerate(grid):
           # Create parameter dict
           params = {name: value for name, value in zip(param_names, param_combination)}

           # Apply to config
           test_config = config.copy()
           indicator = next(ind for ind in test_config.indicators if ind.id == indicator_id)
           indicator.params.update(params)

           # Evaluate
           value = objective_fn(test_config, data)

           # Track best
           if value > best_value:
               best_value = value
               best_params = params

           history.append({
               'iteration': i,
               'params': params,
               'value': value
           })

3. **Return Best:**

   .. code-block:: python

       return OptimizationResult(
           success=True,
           best_params=best_params,
           best_value=best_value,
           history=history,
           method=OptimizationMethod.GRID
       )

**Example:**

.. code-block:: python

    # Optimize RSI period
    result = optimizer.optimize_indicator_params(
        config=config,
        data=df,
        indicator_id='rsi_14',
        param_ranges={
            'period': (10, 20, 2)  # Test periods: 10, 12, 14, 16, 18, 20
        },
        method=OptimizationMethod.GRID,
        max_iterations=None  # Not needed for GRID
    )

    print(f"Optimal RSI period: {result.best_params['period']}")
    print(f"Sharpe with optimal period: {result.best_value:.2f}")

    # Optimize MACD parameters
    result = optimizer.optimize_indicator_params(
        config=config,
        data=df,
        indicator_id='macd',
        param_ranges={
            'fast': (8, 16, 2),
            'slow': (21, 34, 3),
            'signal': (7, 11, 2)
        },
        method=OptimizationMethod.GENETIC,  # GRID would be too many combinations
        max_iterations=100
    )

optimize_risk_params(config, data, strategy_id, method, max_iterations)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.parameter_optimizer.ParameterOptimizer.optimize_risk_params

Optimize risk parameters (stop loss, take profit, position size).

**Parameters:**

* ``config`` (TradingBotConfig): Base configuration
* ``data`` (pd.DataFrame): Historical data
* ``strategy_id`` (str): ID of strategy to optimize
* ``method`` (OptimizationMethod): Optimization algorithm
* ``max_iterations`` (int): Maximum iterations

**Returns:**

* ``OptimizationResult``: Optimized risk parameters

**Algorithm (BAYESIAN method - simplified):**

1. **Initialize with Random Samples:**

   .. code-block:: python

       # Random initial samples
       n_initial = 10
       param_samples = []
       objective_values = []

       for _ in range(n_initial):
           params = {
               'stop_loss_pct': random.uniform(1.0, 5.0),
               'take_profit_pct': random.uniform(2.0, 10.0),
               'position_size_pct': random.uniform(3.0, 15.0)
           }

           # Evaluate
           test_config = apply_risk_params(config, strategy_id, params)
           value = objective_fn(test_config, data)

           param_samples.append(params)
           objective_values.append(value)

2. **Build Surrogate Model (Simplified Gaussian Process):**

   .. code-block:: python

       def surrogate_predict(params, param_samples, objective_values):
           # Simple distance-weighted average (simplified GP)
           weights = []
           for sample in param_samples:
               # Euclidean distance in parameter space
               dist = np.sqrt(sum((params[k] - sample[k])**2 for k in params.keys()))
               weight = np.exp(-dist / 2.0)  # Gaussian kernel
               weights.append(weight)

           # Normalize weights
           weights = np.array(weights) / sum(weights)

           # Weighted average of objectives
           mean = sum(w * v for w, v in zip(weights, objective_values))

           # Uncertainty (inversely proportional to weight sum)
           uncertainty = 1.0 / (sum(weights) + 1.0)

           return mean, uncertainty

3. **Acquisition Function (Upper Confidence Bound):**

   .. code-block:: python

       def acquisition_ucb(params, param_samples, objective_values, kappa=2.0):
           mean, uncertainty = surrogate_predict(params, param_samples, objective_values)
           # UCB = mean + kappa * uncertainty
           # Balances exploitation (mean) and exploration (uncertainty)
           return mean + kappa * uncertainty

4. **Optimization Loop:**

   .. code-block:: python

       for iteration in range(n_initial, max_iterations):
           # Find best parameters according to acquisition function
           best_acq = -float('inf')
           best_params = None

           # Random search over parameter space
           for _ in range(1000):
               candidate_params = {
                   'stop_loss_pct': random.uniform(1.0, 5.0),
                   'take_profit_pct': random.uniform(2.0, 10.0),
                   'position_size_pct': random.uniform(3.0, 15.0)
               }

               acq = acquisition_ucb(candidate_params, param_samples, objective_values)

               if acq > best_acq:
                   best_acq = acq
                   best_params = candidate_params

           # Evaluate best candidate
           test_config = apply_risk_params(config, strategy_id, best_params)
           value = objective_fn(test_config, data)

           # Add to samples
           param_samples.append(best_params)
           objective_values.append(value)

           history.append({
               'iteration': iteration,
               'params': best_params,
               'value': value
           })

5. **Return Best:**

   .. code-block:: python

       best_idx = np.argmax(objective_values)
       return OptimizationResult(
           success=True,
           best_params=param_samples[best_idx],
           best_value=objective_values[best_idx],
           history=history,
           method=OptimizationMethod.BAYESIAN
       )

**Example:**

.. code-block:: python

    # Optimize risk parameters
    result = optimizer.optimize_risk_params(
        config=config,
        data=df,
        strategy_id='trend_following',
        method=OptimizationMethod.BAYESIAN,
        max_iterations=50
    )

    print(f"Optimal Stop Loss: {result.best_params['stop_loss_pct']:.2f}%")
    print(f"Optimal Take Profit: {result.best_params['take_profit_pct']:.2f}%")
    print(f"Optimal Position Size: {result.best_params['position_size_pct']:.2f}%")
    print(f"Sharpe with optimal params: {result.best_value:.2f}")

apply_best_params(config, params, target_type, target_id)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. automethod:: src.ai.parameter_optimizer.ParameterOptimizer.apply_best_params

Apply optimized parameters to configuration.

**Parameters:**

* ``config`` (TradingBotConfig): Configuration to modify
* ``params`` (dict[str, Any]): Parameters to apply
* ``target_type`` (str): 'regime_thresholds', 'indicator', 'risk'
* ``target_id`` (str | None): Indicator/strategy ID (required for indicator/risk)

**Returns:**

* ``TradingBotConfig``: Modified configuration

**Algorithm:**

.. code-block:: python

    modified_config = config.copy()

    if target_type == 'regime_thresholds':
        # Update regime detection thresholds
        for regime in modified_config.regimes:
            for condition in regime.conditions:
                # Update threshold values in conditions
                if condition.left.indicator == 'adx' and 'adx_threshold' in params:
                    condition.right.value = params['adx_threshold']
                elif condition.left.indicator == 'atr_pct' and 'atr_low_pct' in params:
                    condition.right.value = params['atr_low_pct']

    elif target_type == 'indicator':
        # Find indicator by ID
        indicator = next(ind for ind in modified_config.indicators if ind.id == target_id)

        # Update parameters
        indicator.params.update(params)

    elif target_type == 'risk':
        # Find strategy by ID
        strategy = next(strat for strat in modified_config.strategies if strat.id == target_id)

        # Update risk parameters
        if 'stop_loss_pct' in params:
            strategy.risk.stop_loss_pct = params['stop_loss_pct']
        if 'take_profit_pct' in params:
            strategy.risk.take_profit_pct = params['take_profit_pct']
        if 'position_size_pct' in params:
            strategy.risk.position_size_pct = params['position_size_pct']
        if 'trailing_stop_pct' in params:
            strategy.risk.trailing_stop_pct = params['trailing_stop_pct']

    return modified_config

**Example:**

.. code-block:: python

    # Apply optimized regime thresholds
    optimized_config = optimizer.apply_best_params(
        config=config,
        params={'adx_threshold': 25.0, 'atr_low_pct': 1.8},
        target_type='regime_thresholds'
    )

    # Apply optimized indicator params
    optimized_config = optimizer.apply_best_params(
        config=config,
        params={'period': 16},
        target_type='indicator',
        target_id='rsi_14'
    )

    # Apply optimized risk params
    optimized_config = optimizer.apply_best_params(
        config=config,
        params={'stop_loss_pct': 2.8, 'take_profit_pct': 5.6},
        target_type='risk',
        target_id='trend_following'
    )

Common Patterns
---------------

**Pattern 1: Full Strategy Optimization Pipeline**

.. code-block:: python

    def optimize_complete_strategy(config, data):
        optimizer = ParameterOptimizer()

        # 1. Optimize regime thresholds
        print("Step 1: Optimizing regime detection...")
        regime_result = optimizer.optimize_regime_thresholds(
            config=config,
            data=data,
            param_ranges={
                'adx_threshold': (15, 35, 5),
                'atr_low_pct': (1.0, 2.5, 0.5),
                'atr_high_pct': (3.0, 6.0, 0.5)
            },
            objective_fn=lambda cfg, d: run_backtest(cfg, d).sharpe,
            method=OptimizationMethod.GENETIC,
            max_iterations=50
        )

        config = optimizer.apply_best_params(
            config, regime_result.best_params, 'regime_thresholds'
        )
        print(f"  Sharpe after regime optimization: {regime_result.best_value:.2f}")

        # 2. Optimize each indicator
        print("Step 2: Optimizing indicators...")
        for indicator in config.indicators:
            if indicator.type == 'RSI':
                ind_result = optimizer.optimize_indicator_params(
                    config, data, indicator.id,
                    {'period': (10, 20, 2)},
                    OptimizationMethod.GRID
                )
                config = optimizer.apply_best_params(
                    config, ind_result.best_params, 'indicator', indicator.id
                )

        # 3. Optimize risk parameters
        print("Step 3: Optimizing risk parameters...")
        for strategy in config.strategies:
            risk_result = optimizer.optimize_risk_params(
                config, data, strategy.id,
                OptimizationMethod.BAYESIAN,
                max_iterations=50
            )
            config = optimizer.apply_best_params(
                config, risk_result.best_params, 'risk', strategy.id
            )
            print(f"  {strategy.id}: Sharpe = {risk_result.best_value:.2f}")

        # 4. Final backtest
        final_result = run_backtest(config, data)
        print(f"\nFinal Sharpe: {final_result.sharpe:.2f}")

        return config

**Pattern 2: Walk-Forward Optimization**

.. code-block:: python

    def walk_forward_optimization(config, data, train_days=180, test_days=60):
        optimizer = ParameterOptimizer()
        results = []

        # Split into periods
        for i in range(0, len(data) - train_days - test_days, test_days):
            train_data = data.iloc[i:i+train_days]
            test_data = data.iloc[i+train_days:i+train_days+test_days]

            print(f"Period {i // test_days + 1}:")

            # Optimize on training data
            result = optimizer.optimize_risk_params(
                config, train_data, 'trend_following',
                OptimizationMethod.BAYESIAN,
                max_iterations=30
            )

            # Apply to config
            optimized_config = optimizer.apply_best_params(
                config, result.best_params, 'risk', 'trend_following'
            )

            # Test on out-of-sample data
            test_result = run_backtest(optimized_config, test_data)

            results.append({
                'train_sharpe': result.best_value,
                'test_sharpe': test_result.sharpe,
                'params': result.best_params
            })

            print(f"  Train Sharpe: {result.best_value:.2f}")
            print(f"  Test Sharpe: {test_result.sharpe:.2f}")

        # Analyze results
        avg_train = np.mean([r['train_sharpe'] for r in results])
        avg_test = np.mean([r['test_sharpe'] for r in results])
        degradation = (avg_train - avg_test) / avg_train

        print(f"\nAverage Train Sharpe: {avg_train:.2f}")
        print(f"Average Test Sharpe: {avg_test:.2f}")
        print(f"Degradation: {degradation:.2%}")

        return results

**Pattern 3: Multi-Objective Optimization**

.. code-block:: python

    def multi_objective_optimization(config, data):
        optimizer = ParameterOptimizer()

        # Define objective functions
        def sharpe_objective(cfg, d):
            return run_backtest(cfg, d).sharpe

        def win_rate_objective(cfg, d):
            return run_backtest(cfg, d).win_rate

        def max_dd_objective(cfg, d):
            # Minimize max drawdown (invert for maximization)
            return -run_backtest(cfg, d).max_dd

        # Optimize for each objective
        objectives = {
            'sharpe': sharpe_objective,
            'win_rate': win_rate_objective,
            'max_dd': max_dd_objective
        }

        results = {}
        for name, obj_fn in objectives.items():
            result = optimizer.optimize_risk_params(
                config, data, 'trend_following',
                method=OptimizationMethod.GENETIC,
                max_iterations=50,
                objective_fn=obj_fn
            )
            results[name] = result

        # Compare Pareto-optimal solutions
        print("Objective Trade-offs:")
        for name, result in results.items():
            bt = run_backtest(
                optimizer.apply_best_params(config, result.best_params, 'risk', 'trend_following'),
                data
            )
            print(f"{name.upper()}: Sharpe={bt.sharpe:.2f}, WR={bt.win_rate:.2%}, MaxDD={bt.max_dd:.2%}")

**Pattern 4: Robustness Testing Across Market Conditions**

.. code-block:: python

    def optimize_for_robustness(config, data):
        optimizer = ParameterOptimizer()

        # Split data by market regime
        bull_data = data[data['close'].pct_change(20) > 0.10]
        bear_data = data[data['close'].pct_change(20) < -0.10]
        range_data = data[abs(data['close'].pct_change(20)) < 0.05]

        # Optimize on each regime
        regimes = {'bull': bull_data, 'bear': bear_data, 'range': range_data}
        regime_results = {}

        for regime_name, regime_data in regimes.items():
            print(f"Optimizing for {regime_name} market...")
            result = optimizer.optimize_risk_params(
                config, regime_data, 'trend_following',
                OptimizationMethod.BAYESIAN,
                max_iterations=40
            )
            regime_results[regime_name] = result

        # Find parameters that work well across all regimes
        # (Average of regime-specific optimals)
        avg_params = {
            'stop_loss_pct': np.mean([r.best_params['stop_loss_pct'] for r in regime_results.values()]),
            'take_profit_pct': np.mean([r.best_params['take_profit_pct'] for r in regime_results.values()]),
            'position_size_pct': np.mean([r.best_params['position_size_pct'] for r in regime_results.values()])
        }

        # Test robust parameters on full dataset
        robust_config = optimizer.apply_best_params(config, avg_params, 'risk', 'trend_following')
        full_result = run_backtest(robust_config, data)

        print(f"\nRobust Parameters: {avg_params}")
        print(f"Full Dataset Sharpe: {full_result.sharpe:.2f}")

Data Models
-----------

OptimizationMethod
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class OptimizationMethod(Enum):
        GENETIC = "genetic"
        BAYESIAN = "bayesian"
        GRID = "grid"
        RANDOM = "random"

**Methods:**

* ``GENETIC``: Genetic algorithm with tournament selection, crossover, mutation
* ``BAYESIAN``: Simplified Bayesian optimization (normally uses Gaussian processes)
* ``GRID``: Exhaustive grid search (tests all parameter combinations)
* ``RANDOM``: Random search (samples random parameter combinations)

**When to Use:**

.. code-block:: python

    # GENETIC: Good for 3-5 parameters, moderate search space
    # - Balances exploration and exploitation
    # - Converges faster than random search
    # - Example: Optimizing 3-5 risk parameters

    # BAYESIAN: Good for expensive objective functions, small search space
    # - Minimizes number of evaluations
    # - Uses surrogate model to guide search
    # - Example: Optimizing parameters when backtests are slow

    # GRID: Good for 1-2 parameters, small discrete space
    # - Guaranteed to find global optimum in discrete space
    # - Exhaustive but thorough
    # - Example: Optimizing RSI period (10-20 with step=2)

    # RANDOM: Good for high-dimensional spaces, baseline comparison
    # - Simple and parallelizable
    # - No convergence guarantee
    # - Example: Exploratory optimization or sanity check

OptimizationObjective
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    class OptimizationObjective(Enum):
        SHARPE = "sharpe"
        WIN_RATE = "win_rate"
        PROFIT_FACTOR = "profit_factor"
        TOTAL_RETURN = "total_return"
        RISK_ADJ_RETURN = "risk_adjusted_return"

**Objectives:**

* ``SHARPE``: Sharpe ratio (return / volatility) - balances risk and reward
* ``WIN_RATE``: Percentage of winning trades - simple win rate
* ``PROFIT_FACTOR``: Gross profit / gross loss - profitability measure
* ``TOTAL_RETURN``: Total return percentage - absolute performance
* ``RISK_ADJ_RETURN``: Return / max drawdown - risk-adjusted profitability

OptimizationResult
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    @dataclass
    class OptimizationResult:
        success: bool
        best_params: dict[str, Any] | None
        best_value: float | None
        history: list[dict]
        method: OptimizationMethod
        error: str | None = None

**Fields:**

* ``success``: Whether optimization completed successfully
* ``best_params``: Optimal parameters found
* ``best_value``: Objective value at best parameters
* ``history``: List of {iteration, params, value} dicts showing convergence
* ``method``: Optimization method used
* ``error``: Error message if failed

Best Practices
--------------

**1. Use Appropriate Method:**

.. code-block:: python

    # ✅ Good: Choose method based on problem
    # Few parameters, discrete space → GRID
    result = optimizer.optimize_indicator_params(
        config, data, 'rsi_14',
        {'period': (10, 20, 2)},
        OptimizationMethod.GRID
    )

    # Many parameters, continuous space → GENETIC
    result = optimizer.optimize_risk_params(
        config, data, 'trend_following',
        OptimizationMethod.GENETIC,
        max_iterations=100
    )

    # ❌ Bad: Using GRID for high-dimensional space
    result = optimizer.optimize_risk_params(
        config, data, 'trend_following',
        OptimizationMethod.GRID  # Will take too long!
    )

**2. Use Walk-Forward Validation:**

.. code-block:: python

    # ✅ Good: Optimize on training, test on holdout
    train_data = data.iloc[:180]
    test_data = data.iloc[180:]

    result = optimizer.optimize_risk_params(config, train_data, 'trend_following')
    optimized_config = optimizer.apply_best_params(config, result.best_params, 'risk', 'trend_following')

    # Test on out-of-sample data
    oos_result = run_backtest(optimized_config, test_data)

    # ❌ Bad: Optimize and test on same data
    result = optimizer.optimize_risk_params(config, data, 'trend_following')
    test_result = run_backtest(optimized_config, data)  # Overfitted!

**3. Set Reasonable Bounds:**

.. code-block:: python

    # ✅ Good: Realistic parameter ranges
    param_ranges = {
        'stop_loss_pct': (1.0, 5.0, 0.5),  # 1-5%
        'take_profit_pct': (2.0, 10.0, 1.0),  # 2-10%
        'position_size_pct': (3.0, 15.0, 1.0)  # 3-15%
    }

    # ❌ Bad: Unrealistic ranges
    param_ranges = {
        'stop_loss_pct': (0.1, 20.0, 1.0),  # Too wide, includes impractical values
        'position_size_pct': (1.0, 100.0, 5.0)  # 100% position size is dangerous
    }

**4. Monitor Convergence:**

.. code-block:: python

    # ✅ Good: Check convergence history
    result = optimizer.optimize_risk_params(config, data, 'trend_following')

    # Plot convergence
    import matplotlib.pyplot as plt
    plt.plot([h['iteration'] for h in result.history],
             [h['value'] for h in result.history])
    plt.xlabel('Iteration')
    plt.ylabel('Objective Value')
    plt.title('Optimization Convergence')
    plt.show()

    # Check if converged
    last_10_values = [h['value'] for h in result.history[-10:]]
    if max(last_10_values) - min(last_10_values) < 0.01:
        print("✓ Converged")
    else:
        print("⚠ May need more iterations")

See Also
--------

* :doc:`strategy_generator` - Generates strategies that can be optimized
* :doc:`pattern_recognizer` - Provides market context for optimization
* :doc:`backtest_engine` - Used as objective function for optimization
* :doc:`strategy_evaluator` - Walk-forward validation of optimized strategies
* :doc:`config_models` - Configuration models modified by optimizer
