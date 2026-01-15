"""Tab 3: Indicator Configuration."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QListWidget, QLabel, QSplitter
)
from src.core.analysis.context import AnalysisContext
from src.core.analysis.models import IndicatorPreset

class IndicatorsTab(QWidget):
    """UI for viewing/editing the active indicator preset."""

    def __init__(self, context: AnalysisContext):
        super().__init__()
        self.context = context
        self.context.preset_changed.connect(self._update_display)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.preset_label = QLabel("Aktives Preset: (keines)")
        self.preset_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(self.preset_label)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)

    def _update_display(self, preset: IndicatorPreset):
        self.preset_label.setText(f"Aktives Preset: {preset.name}")
        self.list_widget.clear()
        
        for ind in preset.indicators:
            # Format nicely: "RSI (period=14)"
            params_str = ", ".join(f"{k}={v}" for k,v in ind.params.items())
            text = f"{ind.name} ({params_str})"
            if ind.feature_flags:
                text += f" [Flags: {', '.join(ind.feature_flags.keys())}]"
            self.list_widget.addItem(text)
