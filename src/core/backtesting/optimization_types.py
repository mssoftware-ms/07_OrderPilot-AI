"""Parameter Optimization Types and Models.

Contains Pydantic models for parameter optimization.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel, Field

from src.core.models.backtest_models import BacktestResult


class ParameterRange(BaseModel):
    """Parameter range for optimization."""
    name: str = Field(..., description="Parameter name")
    values: list[Any] = Field(..., description="Values to test")
    type: str = Field("continuous", description="Parameter type: continuous, discrete, categorical")


class OptimizationMetric(BaseModel):
    """Metric for optimization."""
    name: str = Field(..., description="Metric name")
    weight: float = Field(1.0, description="Metric weight in multi-objective optimization")
    direction: str = Field("maximize", description="maximize or minimize")


class ParameterTest(BaseModel):
    """Single parameter test result."""
    parameters: dict[str, Any] = Field(..., description="Parameter values tested")
    result: BacktestResult | None = Field(None, description="Backtest result")
    score: float | None = Field(None, description="Optimization score")
    metrics: dict[str, float] = Field(default_factory=dict, description="Key metrics")
    error: str | None = Field(None, description="Error if test failed")


class OptimizationResult(BaseModel):
    """Complete optimization result."""
    best_parameters: dict[str, Any] = Field(..., description="Best parameter set found")
    best_score: float = Field(..., description="Best optimization score")
    best_result: BacktestResult | None = Field(None, description="Best backtest result")
    all_tests: list[ParameterTest] = Field(..., description="All parameter tests")
    total_tests: int = Field(..., description="Total number of tests run")
    successful_tests: int = Field(..., description="Number of successful tests")
    optimization_time_seconds: float = Field(..., description="Total optimization time")
    sensitivity_analysis: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description="Parameter sensitivity analysis"
    )


class AIOptimizationInsight(BaseModel):
    """AI-generated optimization insights."""
    summary: str = Field(..., description="Overall optimization summary")
    best_parameter_analysis: str = Field(..., description="Analysis of best parameters")
    parameter_importance: dict[str, float] = Field(
        ...,
        description="Parameter importance scores (0-1)"
    )
    sensitivity_insights: list[str] = Field(
        ...,
        description="Insights about parameter sensitivity"
    )
    recommendations: list[dict[str, Any]] = Field(
        ...,
        description="Specific recommendations for improvement"
    )
    next_parameters_to_test: dict[str, Any] | None = Field(
        None,
        description="Suggested parameters for next iteration"
    )
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in recommendations")


@dataclass
class OptimizerConfig:
    """Configuration for parameter optimizer."""
    max_workers: int = 4
    timeout_per_test: int = 300
    primary_metric: str = "sharpe_ratio"
    secondary_metrics: list[str] | None = None
    use_ai_guidance: bool = True
    ai_analysis_frequency: int = 10
    min_trades: int = 10
    max_drawdown_pct: float = -30.0
