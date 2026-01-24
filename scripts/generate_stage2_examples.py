"""Generate Stage-2 example JSON files for all 3 regimes."""

import json
from pathlib import Path
from typing import Dict, Any
from datetime import datetime


def create_indicator_optimization_results_example(regime: str) -> Dict[str, Any]:
    """Create example indicator_optimization_results.json"""

    # Regime-specific adjustments
    regime_configs = {
        "BULL": {
            "color": "#26a69a",
            "entry_long_score": 78.5,
            "entry_short_score": 55.2,
            "exit_long_score": 82.1,
            "exit_short_score": 60.8
        },
        "BEAR": {
            "color": "#ef5350",
            "entry_long_score": 60.3,
            "entry_short_score": 75.8,
            "exit_long_score": 68.5,
            "exit_short_score": 79.2
        },
        "SIDEWAYS": {
            "color": "#9e9e9e",
            "entry_long_score": 68.7,
            "entry_short_score": 67.4,
            "exit_long_score": 73.2,
            "exit_short_score": 72.1
        }
    }

    config = regime_configs[regime]

    return {
        "version": "2.0",
        "meta": {
            "stage": "indicator_optimization",
            "regime": regime,
            "created_at": datetime.now().isoformat(),
            "regime_config_ref": f"optimized_regime_{regime}_BTCUSDT_5m.json",
            "regime_data": {
                "total_bars": 5000,
                "percentage_of_data": 33.3,
                "periods_count": 15
            },
            "source": {
                "symbol": "BTCUSDT",
                "timeframe": "5m"
            },
            "method": "tpe_multivariate",
            "mode": "auto",
            "tested_indicators": ["RSI", "MACD", "STOCH", "BB", "ATR", "EMA", "CCI"],
            "duration_seconds": 450.5
        },
        "optimization_config": {
            "mode": "standard",
            "method": "tpe",
            "trials_per_indicator": 40,
            "indicator_selection": {
                "mode": "all",
                "selected": ["RSI", "MACD", "STOCH", "BB", "ATR", "EMA", "CCI"]
            },
            "early_stopping": {
                "enabled": True,
                "min_trades": 5
            },
            "actual_performance": {
                "total_combinations_if_grid": 16800,
                "actual_trials_run": 280,
                "speedup_factor": 60.0
            }
        },
        "param_ranges": {
            "RSI": {
                "period": {"min": 10, "max": 20, "step": 1},
                "threshold_low": {"min": 20, "max": 35, "step": 5},
                "threshold_high": {"min": 65, "max": 80, "step": 5}
            },
            "MACD": {
                "fast": {"min": 8, "max": 16, "step": 2},
                "slow": {"min": 20, "max": 30, "step": 2},
                "signal": {"min": 7, "max": 11, "step": 1}
            },
            "STOCH": {
                "k_period": {"min": 10, "max": 18, "step": 2},
                "d_period": {"min": 3, "max": 5, "step": 1},
                "threshold_low": {"min": 15, "max": 25, "step": 5},
                "threshold_high": {"min": 75, "max": 85, "step": 5}
            },
            "BB": {
                "period": {"min": 15, "max": 25, "step": 5},
                "std_dev": {"min": 1.5, "max": 2.5, "step": 0.5}
            },
            "ATR": {
                "period": {"min": 10, "max": 20, "step": 2},
                "multiplier": {"min": 1.0, "max": 3.0, "step": 0.5}
            },
            "EMA": {
                "period": {"min": 5, "max": 30, "step": 5}
            },
            "CCI": {
                "period": {"min": 15, "max": 25, "step": 5},
                "threshold_low": {"min": -150, "max": -100, "step": 25},
                "threshold_high": {"min": 100, "max": 150, "step": 25}
            }
        },
        "results": {
            "entry_long": {
                "total_tested": 40,
                "statistics": {
                    "score_min": 45.2,
                    "score_max": config["entry_long_score"],
                    "score_avg": 62.5
                },
                "ranked_results": [
                {
                    "rank": 1,
                    "indicator": "RSI",
                    "indicator_id": "rsi_entry_long_1",
                    "params": {"period": 14, "oversold": 28, "overbought": 72},
                    "score": config["entry_long_score"],
                    "selected": True,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "rsi_14", "field": "value"},
                                "op": "lt",
                                "right": {"value": 28}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 45,
                        "trades": 45,
                        "win_rate": 0.62,
                        "profit_factor": 2.15,
                        "sharpe_ratio": 1.45,
                        "max_drawdown": 0.08,
                        "expectancy": 0.15,
                        "avg_win": 0.025,
                        "avg_loss": -0.012,
                        "avg_bars_in_trade": 12.5
                    },
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "rank": 2,
                    "indicator": "MACD",
                    "indicator_id": "macd_entry_long_2",
                    "params": {"fast": 12, "slow": 26, "signal": 9},
                    "score": config["entry_long_score"] - 6.2,
                    "selected": False,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "macd", "field": "histogram"},
                                "op": "crosses_above",
                                "right": {"value": 0}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 38,
                        "trades": 38,
                        "win_rate": 0.58,
                        "profit_factor": 1.89,
                        "sharpe_ratio": 1.22,
                        "max_drawdown": 0.12,
                        "expectancy": 0.12,
                        "avg_win": 0.022,
                        "avg_loss": -0.014,
                        "avg_bars_in_trade": 14.2
                    },
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "rank": 3,
                    "indicator": "EMA",
                    "indicator_id": "ema_entry_long_3",
                    "params": {"period": 21},
                    "score": config["entry_long_score"] - 12.5,
                    "selected": False,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "ema_9", "field": "value"},
                                "op": "crosses_above",
                                "right": {"indicator_id": "ema_21", "field": "value"}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 42,
                        "trades": 42,
                        "win_rate": 0.55,
                        "profit_factor": 1.72,
                        "sharpe_ratio": 1.05,
                        "max_drawdown": 0.14,
                        "expectancy": 0.09,
                        "avg_win": 0.020,
                        "avg_loss": -0.015,
                        "avg_bars_in_trade": 15.8
                    },
                    "timestamp": datetime.now().isoformat()
                }
                ]
            },
            "entry_short": {
                "total_tested": 40,
                "statistics": {
                    "score_min": 38.5,
                    "score_max": config["entry_short_score"],
                    "score_avg": 55.8
                },
                "ranked_results": [
                {
                    "rank": 1,
                    "indicator": "STOCH",
                    "indicator_id": "stoch_entry_short_1",
                    "params": {"k_period": 14, "d_period": 3, "overbought": 80},
                    "score": config["entry_short_score"],
                    "selected": True,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "stoch_k", "field": "value"},
                                "op": "gt",
                                "right": {"value": 80}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 28,
                        "trades": 28,
                        "win_rate": 0.54,
                        "profit_factor": 1.65,
                        "sharpe_ratio": 0.95,
                        "max_drawdown": 0.15,
                        "expectancy": 0.10,
                        "avg_win": 0.021,
                        "avg_loss": -0.016,
                        "avg_bars_in_trade": 10.5
                    },
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "rank": 2,
                    "indicator": "CCI",
                    "indicator_id": "cci_entry_short_2",
                    "params": {"period": 20, "overbought": 100},
                    "score": config["entry_short_score"] - 8.3,
                    "selected": False,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "cci_20", "field": "value"},
                                "op": "gt",
                                "right": {"value": 100}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 25,
                        "trades": 25,
                        "win_rate": 0.51,
                        "profit_factor": 1.48,
                        "sharpe_ratio": 0.78,
                        "max_drawdown": 0.18,
                        "expectancy": 0.07,
                        "avg_win": 0.019,
                        "avg_loss": -0.017,
                        "avg_bars_in_trade": 11.2
                    },
                    "timestamp": datetime.now().isoformat()
                }
                ]
            },
            "exit_long": {
                "total_tested": 40,
                "statistics": {
                    "score_min": 52.3,
                    "score_max": config["exit_long_score"],
                    "score_avg": 68.5
                },
                "ranked_results": [
                {
                    "rank": 1,
                    "indicator": "ATR",
                    "indicator_id": "atr_exit_long_1",
                    "params": {"period": 14, "multiplier": 2.0},
                    "score": config["exit_long_score"],
                    "selected": True,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "close", "field": "value"},
                                "op": "lt",
                                "right": {"indicator_id": "entry_price_minus_atr", "field": "value"}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 52,
                        "trades": 52,
                        "win_rate": 0.68,
                        "profit_factor": 2.45,
                        "sharpe_ratio": 1.65,
                        "max_drawdown": 0.06,
                        "expectancy": 0.18,
                        "avg_win": 0.028,
                        "avg_loss": -0.010,
                        "avg_bars_in_trade": 9.5
                    },
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "rank": 2,
                    "indicator": "BB",
                    "indicator_id": "bb_exit_long_2",
                    "params": {"period": 20, "std_dev": 2.0},
                    "score": config["exit_long_score"] - 7.5,
                    "selected": False,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "close", "field": "value"},
                                "op": "lt",
                                "right": {"indicator_id": "bb_lower", "field": "value"}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 48,
                        "trades": 48,
                        "win_rate": 0.63,
                        "profit_factor": 2.12,
                        "sharpe_ratio": 1.38,
                        "max_drawdown": 0.09,
                        "expectancy": 0.14,
                        "avg_win": 0.024,
                        "avg_loss": -0.011,
                        "avg_bars_in_trade": 10.2
                    },
                    "timestamp": datetime.now().isoformat()
                }
                ]
            },
            "exit_short": {
                "total_tested": 40,
                "statistics": {
                    "score_min": 42.8,
                    "score_max": config["exit_short_score"],
                    "score_avg": 61.2
                },
                "ranked_results": [
                {
                    "rank": 1,
                    "indicator": "BB",
                    "indicator_id": "bb_exit_short_1",
                    "params": {"period": 20, "std_dev": 2.0},
                    "score": config["exit_short_score"],
                    "selected": True,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "close", "field": "value"},
                                "op": "gt",
                                "right": {"indicator_id": "bb_upper", "field": "value"}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 31,
                        "trades": 31,
                        "win_rate": 0.59,
                        "profit_factor": 1.92,
                        "sharpe_ratio": 1.18,
                        "max_drawdown": 0.11,
                        "expectancy": 0.11,
                        "avg_win": 0.023,
                        "avg_loss": -0.013,
                        "avg_bars_in_trade": 8.5
                    },
                    "timestamp": datetime.now().isoformat()
                },
                {
                    "rank": 2,
                    "indicator": "ATR",
                    "indicator_id": "atr_exit_short_2",
                    "params": {"period": 14, "multiplier": 1.5},
                    "score": config["exit_short_score"] - 9.2,
                    "selected": False,
                    "conditions": {
                        "all": [
                            {
                                "left": {"indicator_id": "close", "field": "value"},
                                "op": "gt",
                                "right": {"indicator_id": "entry_price_plus_atr", "field": "value"}
                            }
                        ]
                    },
                    "metrics": {
                        "signals": 29,
                        "trades": 29,
                        "win_rate": 0.56,
                        "profit_factor": 1.75,
                        "sharpe_ratio": 0.98,
                        "max_drawdown": 0.13,
                        "expectancy": 0.09,
                        "avg_win": 0.020,
                        "avg_loss": -0.014,
                        "avg_bars_in_trade": 9.8
                    },
                    "timestamp": datetime.now().isoformat()
                }
                ]
            }
        }
    }


def create_indicator_sets_example(regime: str) -> Dict[str, Any]:
    """Create example indicator_sets.json"""

    regime_configs = {
        "BULL": {
            "color": "#26a69a",
            "entry_long_score": 78.5,
            "entry_short_enabled": False,
            "exit_long_score": 82.1,
            "exit_short_enabled": False
        },
        "BEAR": {
            "color": "#ef5350",
            "entry_long_score": 60.3,
            "entry_short_enabled": True,
            "exit_long_score": 68.5,
            "exit_short_enabled": True
        },
        "SIDEWAYS": {
            "color": "#9e9e9e",
            "entry_long_score": 68.7,
            "entry_short_enabled": True,
            "exit_long_score": 73.2,
            "exit_short_enabled": True
        }
    }

    config = regime_configs[regime]

    result = {
        "version": "2.0",
        "meta": {
            "stage": "indicator_sets",
            "regime": regime,
            "regime_color": config["color"],
            "created_at": datetime.now().isoformat(),
            "name": f"{regime} Indicator Sets",
            "regime_config_ref": f"optimized_regime_{regime}_BTCUSDT_5m.json",
            "optimization_results_ref": f"indicator_optimization_results_{regime}_BTCUSDT_5m.json",
            "source": {
                "symbol": "BTCUSDT",
                "timeframe": "5m"
            },
            "aggregate_metrics": {
                "total_signals_enabled": 2 if not config["entry_short_enabled"] else 4,
                "combined_win_rate": 0.65,
                "combined_profit_factor": 2.1
            }
        },
        "signal_sets": {
            "entry_long": {
                "enabled": True,
                "selected_rank": 1,
                "score": config["entry_long_score"],
                "indicator": "RSI",
                "indicator_id": "rsi_entry_long_1",
                "params": {
                    "period": 14,
                    "oversold": 28,
                    "overbought": 72
                },
                "conditions": {
                    "all": [
                        {
                            "left": {"indicator_id": "rsi_14", "field": "value"},
                            "op": "lt",
                            "right": {"value": 28}
                        }
                    ]
                },
                "metrics": {
                    "signals": 45,
                    "trades": 45,
                    "win_rate": 0.62,
                    "profit_factor": 2.15,
                    "sharpe_ratio": 1.45,
                    "max_drawdown": 0.08,
                    "expectancy": 0.15,
                    "avg_win": 0.025,
                    "avg_loss": -0.012
                },
                "research_notes": "RSI oversold condition performs best for long entries in {} regime".format(regime)
            },
            "exit_long": {
                "enabled": True,
                "selected_rank": 1,
                "score": config["exit_long_score"],
                "indicator": "ATR",
                "indicator_id": "atr_exit_long_1",
                "params": {
                    "period": 14,
                    "multiplier": 2.0
                },
                "conditions": {
                    "all": [
                        {
                            "left": {"indicator_id": "close", "field": "value"},
                            "op": "lt",
                            "right": {"indicator_id": "entry_price_minus_atr", "field": "value"}
                        }
                    ]
                },
                "metrics": {
                    "signals": 52,
                    "trades": 52,
                    "win_rate": 0.68,
                    "profit_factor": 2.45,
                    "sharpe_ratio": 1.65,
                    "max_drawdown": 0.06,
                    "expectancy": 0.18,
                    "avg_win": 0.028,
                    "avg_loss": -0.010
                },
                "research_notes": "ATR-based stop loss provides optimal risk management"
            }
        }
    }

    # Add entry_short only for BEAR and SIDEWAYS
    if config["entry_short_enabled"]:
        result["signal_sets"]["entry_short"] = {
            "enabled": True,
            "selected_rank": 1,
            "score": 75.8 if regime == "BEAR" else 67.4,
            "indicator": "STOCH",
            "indicator_id": "stoch_entry_short_1",
            "params": {
                "k_period": 14,
                "d_period": 3,
                "overbought": 80
            },
            "conditions": {
                "all": [
                    {
                        "left": {"indicator_id": "stoch_k", "field": "value"},
                        "op": "gt",
                        "right": {"value": 80}
                    }
                ]
            },
            "metrics": {
                "signals": 28,
                "trades": 28,
                "win_rate": 0.54,
                "profit_factor": 1.65,
                "sharpe_ratio": 0.95,
                "max_drawdown": 0.15,
                "expectancy": 0.10,
                "avg_win": 0.021,
                "avg_loss": -0.016
            },
            "research_notes": "Stochastic overbought signals work well for short entries in {} regime".format(regime)
        }
    else:
        result["signal_sets"]["entry_short"] = {
            "enabled": False
        }

    # Add exit_short only for BEAR and SIDEWAYS
    if config["exit_short_enabled"]:
        result["signal_sets"]["exit_short"] = {
            "enabled": True,
            "selected_rank": 1,
            "score": 79.2 if regime == "BEAR" else 72.1,
            "indicator": "BB",
            "indicator_id": "bb_exit_short_1",
            "params": {
                "period": 20,
                "std_dev": 2.0
            },
            "conditions": {
                "all": [
                    {
                        "left": {"indicator_id": "close", "field": "value"},
                        "op": "gt",
                        "right": {"indicator_id": "bb_upper", "field": "value"}
                    }
                ]
            },
            "metrics": {
                "signals": 31,
                "trades": 31,
                "win_rate": 0.59,
                "profit_factor": 1.92,
                "sharpe_ratio": 1.18,
                "max_drawdown": 0.11,
                "expectancy": 0.11,
                "avg_win": 0.023,
                "avg_loss": -0.013
            },
            "research_notes": "Bollinger Band upper breakout indicates good short exit points"
        }
    else:
        result["signal_sets"]["exit_short"] = {
            "enabled": False
        }

    return result


def main():
    """Generate all Stage-2 examples"""
    base_path = Path("01_Projectplan/260124 New Regime and Indicator Analyzer/examples/STUFE_2_Indicators")

    for regime in ["BULL", "BEAR", "SIDEWAYS"]:
        regime_path = base_path / regime
        regime_path.mkdir(parents=True, exist_ok=True)

        # Generate indicator_optimization_results
        results = create_indicator_optimization_results_example(regime)
        results_file = regime_path / f"indicator_optimization_results_{regime}_BTCUSDT_5m.json"
        with open(results_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        # Generate indicator_sets
        sets = create_indicator_sets_example(regime)
        sets_file = regime_path / f"indicator_sets_{regime}_BTCUSDT_5m.json"
        with open(sets_file, "w", encoding="utf-8") as f:
            json.dump(sets, f, indent=2, ensure_ascii=False)

        print(f"✓ Created {regime} examples:")
        print(f"  - {results_file.name}")
        print(f"  - {sets_file.name}")

    print("\n✓ All Stage-2 examples created successfully")


if __name__ == "__main__":
    main()
