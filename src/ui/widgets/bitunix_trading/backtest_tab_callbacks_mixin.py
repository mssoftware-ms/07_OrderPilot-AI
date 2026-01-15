from __future__ import annotations

import logging

from .backtest_callbacks_testing_mixin import BacktestCallbacksTestingMixin
from .backtest_callbacks_template_mixin import BacktestCallbacksTemplateMixin
from .backtest_callbacks_config_mixin import BacktestCallbacksConfigMixin

logger = logging.getLogger(__name__)


class BacktestTabCallbacksMixin(
    BacktestCallbacksTestingMixin,
    BacktestCallbacksTemplateMixin,
    BacktestCallbacksConfigMixin,
):
    """Backtest Tab Callbacks - Uses sub-mixin pattern for better modularity.

    Coordinates backtest callbacks by combining:
    - Testing: Batch and walk-forward testing callbacks
    - Template: Template saving, loading, and derivation
    - Config: Configuration management and auto-generation
    """
    pass
