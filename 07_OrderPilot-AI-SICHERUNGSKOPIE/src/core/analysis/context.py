"""Analysis Context for sharing state between UI tabs.

Acts as a central bus for the AI Analysis module.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from typing import Optional, Any

from .models import InitialAnalysisResult, AnalysisStrategyConfig, TimeframeConfig, IndicatorPreset
from .config_store import AnalysisConfigStore

class AnalysisContext(QObject):
    """Shared state for the AI Analysis module."""
    
    # Signals
    regime_changed = pyqtSignal(str) # "NEUTRAL", "TREND_BULL", etc.
    strategy_changed = pyqtSignal(object) # AnalysisStrategyConfig
    timeframes_changed = pyqtSignal(list) # List[TimeframeConfig]
    preset_changed = pyqtSignal(object) # IndicatorPreset
    
    def __init__(self):
        super().__init__()
        self._current_symbol: str = "Unknown"
        self._current_regime: str = "UNKNOWN"
        self._initial_analysis: Optional[InitialAnalysisResult] = None
        
        self._selected_strategy: Optional[AnalysisStrategyConfig] = None
        self._active_timeframes: list[TimeframeConfig] = []
        self._active_preset: Optional[IndicatorPreset] = None

        # Data Fetching Context
        self.history_manager: Any = None
        self.asset_class: Any = None
        self.data_source: Any = None

    def set_market_context(self, history_manager, symbol: str, asset_class, data_source):
        """Injects dependencies required for data fetching."""
        self.history_manager = history_manager
        self._current_symbol = symbol
        self.asset_class = asset_class
        self.data_source = data_source

    def set_initial_analysis(self, result: InitialAnalysisResult):
        """Updates context from Tab 0 result."""
        self._initial_analysis = result
        new_regime = result.extract_regime()
        if new_regime != self._current_regime:
            self._current_regime = new_regime
            self.regime_changed.emit(new_regime)

    def set_symbol(self, symbol: str):
        self._current_symbol = symbol

    def get_regime(self) -> str:
        return self._current_regime

    def set_strategy(self, strategy_name: str):
        """Sets the active strategy by name."""
        strategies = AnalysisConfigStore.get_default_strategies()
        for strat in strategies:
            if strat.name == strategy_name:
                self._selected_strategy = strat
                self.strategy_changed.emit(strat)
                return
        
    def apply_auto_config(self):
        """Applies defaults from the selected strategy to timeframes and presets."""
        if not self._selected_strategy:
            return
            
        # Set Timeframes
        self._active_timeframes = list(self._selected_strategy.timeframes)
        self.timeframes_changed.emit(self._active_timeframes)
        
        # Set Preset
        preset_id = self._selected_strategy.indicator_preset_id
        presets = AnalysisConfigStore.get_default_presets()
        for p in presets:
            if p.preset_id == preset_id:
                self._active_preset = p
                self.preset_changed.emit(p)
                break

    def get_selected_strategy(self) -> Optional[AnalysisStrategyConfig]:
        return self._selected_strategy

    def get_active_timeframes(self) -> list[TimeframeConfig]:
        return self._active_timeframes

    def get_active_preset(self) -> Optional[IndicatorPreset]:
        return self._active_preset
