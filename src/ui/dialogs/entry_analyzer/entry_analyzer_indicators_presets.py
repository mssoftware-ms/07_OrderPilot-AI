"""Entry Analyzer - Indicator Parameter Presets Mixin.

New module for regime-based parameter preset management.
Provides optimal parameter ranges for different market conditions:
- Trending Markets (Trend Up/Down)
- Ranging Markets
- High Volatility Markets
- Squeeze/Consolidation

Based on 2025 research on optimal technical indicator parameters.

Date: 2026-01-21
LOC: ~450
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from PyQt6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

# Import icon provider (Issue #12)
from src.ui.icons import get_icon

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


# ==================== Parameter Preset Definitions ====================

REGIME_PRESETS = {
    'trend_up': {
        'name': 'Trending Up Market',
        'description': 'Optimized for bullish trending markets with momentum confirmation',
        'indicators': {
            'RSI': {
                'period': (10, 21, 2),  # (min, max, step)
                'notes': 'Longer periods (14-21) for trend confirmation'
            },
            'MACD': {
                'fast': (8, 16, 2),
                'slow': (20, 30, 5),
                'signal': (7, 11, 2),
                'notes': 'Faster settings (8,17,7) for quicker signals in trends'
            },
            'EMA': {
                'period': (20, 50, 5),
                'notes': 'Shorter EMAs (20-50) for trend following'
            },
            'SMA': {
                'period': (50, 100, 10),
                'notes': 'Medium-term SMAs for trend confirmation'
            },
            'ADX': {
                'period': (10, 20, 2),
                'notes': 'Standard ADX for trend strength confirmation'
            },
            'BB': {
                'period': (15, 25, 5),
                'std': (1.5, 2.5, 0.5),
                'notes': 'Tighter bands for trend breakouts'
            },
            'ATR': {
                'period': (10, 20, 2),
                'notes': 'Standard ATR for volatility-based stops'
            },
        }
    },
    'trend_down': {
        'name': 'Trending Down Market',
        'description': 'Optimized for bearish trending markets with momentum confirmation',
        'indicators': {
            'RSI': {
                'period': (10, 21, 2),
                'notes': 'Longer periods (14-21) for trend confirmation'
            },
            'MACD': {
                'fast': (8, 16, 2),
                'slow': (20, 30, 5),
                'signal': (7, 11, 2),
                'notes': 'Faster settings (8,17,7) for quicker signals in trends'
            },
            'EMA': {
                'period': (20, 50, 5),
                'notes': 'Shorter EMAs (20-50) for trend following'
            },
            'SMA': {
                'period': (50, 100, 10),
                'notes': 'Medium-term SMAs for trend confirmation'
            },
            'ADX': {
                'period': (10, 20, 2),
                'notes': 'Standard ADX for trend strength confirmation'
            },
            'BB': {
                'period': (15, 25, 5),
                'std': (1.5, 2.5, 0.5),
                'notes': 'Tighter bands for trend breakouts'
            },
            'ATR': {
                'period': (10, 20, 2),
                'notes': 'Standard ATR for volatility-based stops'
            },
        }
    },
    'range': {
        'name': 'Ranging Market',
        'description': 'Optimized for sideways/ranging markets with clear support/resistance',
        'indicators': {
            'RSI': {
                'period': (9, 14, 1),
                'notes': 'Shorter periods (9-10) for faster mean reversion signals. Use 75/25 levels.'
            },
            'MACD': {
                'fast': (12, 17, 2),
                'slow': (26, 35, 5),
                'signal': (9, 12, 1),
                'notes': 'Standard to slower MACD (12,26,9 or 15,30,12) for cleaner signals'
            },
            'EMA': {
                'period': (10, 30, 5),
                'notes': 'Shorter EMAs for mean reversion'
            },
            'SMA': {
                'period': (20, 50, 10),
                'notes': 'Short-term SMAs for range support/resistance'
            },
            'BB': {
                'period': (20, 30, 5),
                'std': (2.0, 2.5, 0.25),
                'notes': 'Standard Bollinger Bands (20,2) work beautifully in ranges'
            },
            'STOCH': {
                'k_period': (10, 18, 2),
                'd_period': (3, 5, 1),
                'notes': 'Effective for overbought/oversold in ranging markets'
            },
            'KC': {
                'period': (20, 30, 5),
                'atr_mult': (1.5, 2.5, 0.5),
                'notes': 'Keltner Channels for range boundaries'
            },
            'ATR': {
                'period': (14, 20, 2),
                'notes': 'Standard ATR for range-based stops'
            },
        }
    },
    'high_vol': {
        'name': 'High Volatility Market',
        'description': 'Optimized for volatile markets with wider filters and adaptive thresholds',
        'indicators': {
            'RSI': {
                'period': (7, 12, 1),
                'notes': 'Shorter periods (7-9) for faster signals. Use 80/20 or 75/25 levels.'
            },
            'MACD': {
                'fast': (8, 14, 2),
                'slow': (17, 26, 3),
                'signal': (7, 10, 1),
                'notes': 'Faster MACD (8,17,7) for quick volatile moves'
            },
            'EMA': {
                'period': (30, 100, 10),
                'notes': 'Longer EMAs to smooth out volatility noise'
            },
            'SMA': {
                'period': (50, 150, 20),
                'notes': 'Longer SMAs for volatility smoothing'
            },
            'BB': {
                'period': (20, 30, 5),
                'std': (2.5, 3.5, 0.5),
                'notes': 'Wider bands (2.5-3.0 std) for volatility expansion'
            },
            'ATR': {
                'period': (7, 14, 2),
                'notes': 'Shorter ATR (7-10) with wider multipliers for volatile stops'
            },
            'ADX': {
                'period': (10, 18, 2),
                'notes': 'Standard ADX to confirm strong volatile moves'
            },
            'KC': {
                'period': (15, 25, 5),
                'atr_mult': (2.0, 3.5, 0.5),
                'notes': 'Wider Keltner multipliers for volatility'
            },
        }
    },
    'squeeze': {
        'name': 'Squeeze/Consolidation',
        'description': 'Optimized for low volatility squeeze patterns anticipating breakouts',
        'indicators': {
            'RSI': {
                'period': (14, 21, 2),
                'notes': 'Standard to longer periods for breakout confirmation'
            },
            'MACD': {
                'fast': (12, 17, 2),
                'slow': (26, 35, 5),
                'signal': (9, 12, 1),
                'notes': 'Standard MACD for breakout detection'
            },
            'BB': {
                'period': (20, 30, 5),
                'std': (1.5, 2.0, 0.25),
                'notes': 'Tighter bands to detect squeeze (BB Width indicator)'
            },
            'BB_WIDTH': {
                'period': (20, 30, 5),
                'std': (1.5, 2.0, 0.25),
                'notes': 'BB Width to measure squeeze intensity'
            },
            'KC': {
                'period': (20, 30, 5),
                'atr_mult': (1.5, 2.0, 0.25),
                'notes': 'Keltner Channels to confirm squeeze (inside BB)'
            },
            'ATR': {
                'period': (14, 20, 2),
                'notes': 'ATR to measure volatility compression'
            },
            'ADX': {
                'period': (14, 20, 2),
                'notes': 'Low ADX (<20) confirms consolidation'
            },
            'CHOP': {
                'period': (12, 18, 2),
                'notes': 'Choppiness Index to confirm ranging/consolidation'
            },
        }
    },
    'no_trade': {
        'name': 'No Trade Zone',
        'description': 'Conservative settings for uncertain market conditions',
        'indicators': {
            'RSI': {
                'period': (14, 21, 2),
                'notes': 'Longer periods for conservative signals'
            },
            'MACD': {
                'fast': (15, 20, 2),
                'slow': (30, 40, 5),
                'signal': (10, 14, 2),
                'notes': 'Slower MACD (15,30,12) for filtered signals'
            },
            'EMA': {
                'period': (50, 150, 20),
                'notes': 'Long EMAs for major trend confirmation only'
            },
            'SMA': {
                'period': (100, 200, 20),
                'notes': 'Long-term SMAs for conservative entries'
            },
            'ADX': {
                'period': (14, 25, 2),
                'notes': 'Higher ADX threshold (>25) for strong trends only'
            },
        }
    },
    'scalping': {
        'name': 'Scalping (5-min)',
        'description': 'Ultra-fast parameters for 5-minute scalping strategies',
        'indicators': {
            'RSI': {
                'period': (5, 9, 1),
                'notes': 'Very short RSI (5-7) with 80/20 levels for scalping'
            },
            'MACD': {
                'fast': (5, 10, 1),
                'slow': (12, 20, 2),
                'signal': (5, 8, 1),
                'notes': 'Ultra-fast MACD for quick entries/exits'
            },
            'EMA': {
                'period': (5, 20, 5),
                'notes': 'Very short EMAs (5-20) for immediate signals'
            },
            'BB': {
                'period': (10, 20, 5),
                'std': (1.5, 2.0, 0.25),
                'notes': 'Tight bands for scalping breakouts'
            },
            'ATR': {
                'period': (7, 10, 1),
                'notes': 'Short ATR (7-10) for tight stops'
            },
        }
    },
}


class IndicatorsPresetsMixin:
    """Indicator parameter presets functionality.

    Provides regime-based parameter presets with:
    - 7 market regime presets (Trending Up/Down, Ranging, High Vol, Squeeze, No Trade, Scalping)
    - Auto-apply based on detected regime
    - Detailed notes and research-backed parameter ranges
    - One-click preset application

    Research Sources (2025):
    - Medium: High-Frequency RSI-MACD-EMA Composite Strategy
    - Mind Math Money: Trading Indicators Masterclass 2025
    - QuantifiedStrategies: 100 Best Trading Indicators 2025
    - TradingView: MACD & RSI Strategies
    """

    # Type hints for parent class attributes (from IndicatorsSetupMixin)
    _param_widgets: dict[str, dict[str, dict[str, Any]]]
    _regime_label: Any  # QLabel with current regime

    def _setup_parameter_presets_tab(self, tab: QWidget) -> None:
        """Setup Parameter Presets tab.

        Features:
        - Regime-based preset selector
        - Auto-apply button based on current regime
        - Detailed preset descriptions
        - Apply button to update optimization ranges
        """
        layout = QVBoxLayout(tab)

        # Header
        header = QLabel(
            "<h3>📋 Parameter Presets</h3>"
            "<p>Research-backed parameter ranges optimized for different market regimes.</p>"
        )
        header.setWordWrap(True)
        layout.addWidget(header)

        # Preset Selection
        preset_group = QGroupBox("Select Preset")
        preset_layout = QVBoxLayout(preset_group)

        # Preset selector
        preset_select_layout = QHBoxLayout()
        preset_select_layout.addWidget(QLabel("Market Regime:"))

        self._preset_combo = QComboBox()
        for regime_key, preset_data in REGIME_PRESETS.items():
            self._preset_combo.addItem(preset_data['name'], regime_key)
        self._preset_combo.currentIndexChanged.connect(self._on_preset_selected)
        preset_select_layout.addWidget(self._preset_combo)

        # Auto button (detects current regime) - Issue #12: Material Design icon + theme
        auto_btn = QPushButton(" Auto (Use Current Regime)")
        auto_btn.setIcon(get_icon("auto_awesome"))
        auto_btn.setProperty("class", "info")  # Use theme
        auto_btn.setToolTip("Automatically select preset based on currently detected market regime")
        auto_btn.clicked.connect(self._on_auto_preset_clicked)
        preset_select_layout.addWidget(auto_btn)

        preset_layout.addLayout(preset_select_layout)
        layout.addWidget(preset_group)

        # Issue #11: Preset Details as Table (for calculations)
        details_group = QGroupBox("Preset Details")
        details_layout = QVBoxLayout(details_group)

        # Create table with 4 columns: Indicator, Parameter, Range, Notes
        self._preset_details_table = QTableWidget()
        self._preset_details_table.setColumnCount(4)
        self._preset_details_table.setHorizontalHeaderLabels(['Indicator', 'Parameter', 'Range', 'Notes'])

        # Set column widths
        header = self._preset_details_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Indicator
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Parameter
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Range
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)  # Notes (stretch)

        # Set alternating row colors for better readability
        self._preset_details_table.setAlternatingRowColors(True)
        self._preset_details_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Read-only
        self._preset_details_table.setMaximumHeight(300)

        details_layout.addWidget(self._preset_details_table)
        layout.addWidget(details_group)

        # Apply Button
        apply_layout = QHBoxLayout()
        apply_layout.addStretch()

        # Issue #12: Material Design icon + theme color
        apply_btn = QPushButton(" Apply Preset to Optimization")
        apply_btn.setIcon(get_icon("check_circle"))
        apply_btn.setProperty("class", "success")  # Use theme success color
        apply_btn.clicked.connect(self._on_apply_preset_clicked)
        apply_layout.addWidget(apply_btn)

        apply_layout.addStretch()
        layout.addLayout(apply_layout)

        # Research Sources
        sources_label = QLabel(
            "<p><b>Research Sources (2025):</b></p>"
            "<ul>"
            "<li><a href='https://medium.com/@FMZQuant/high-frequency-rsi-macd-ema-composite-technical-analysis-strategy-with-adaptive-stop-loss-76cbf3be25c8'>High-Frequency RSI-MACD-EMA Composite Strategy</a></li>"
            "<li><a href='https://www.mindmathmoney.com/articles/the-complete-trading-indicators-masterclass-transform-your-technical-analysis-in-2025'>Trading Indicators Masterclass 2025</a></li>"
            "<li><a href='https://www.quantifiedstrategies.com/trading-indicators/'>100 Best Trading Indicators 2025</a></li>"
            "<li><a href='https://www.quantifiedstrategies.com/macd-and-rsi-strategy/'>MACD and RSI Strategy: 73% Win Rate</a></li>"
            "<li><a href='https://eplanetbrokers.com/en-US/training/best-rsi-settings-for-5-minute-charts'>Best RSI Settings for 5-Minute Charts 2025</a></li>"
            "</ul>"
        )
        sources_label.setOpenExternalLinks(True)
        sources_label.setWordWrap(True)
        layout.addWidget(sources_label)

        layout.addStretch()

        # Load first preset by default
        self._on_preset_selected(0)

    def _on_preset_selected(self, index: int) -> None:
        """Handle preset selection change.

        Issue #11: Populates table widget instead of HTML text display.
        """
        regime_key = self._preset_combo.currentData()
        if not regime_key or regime_key not in REGIME_PRESETS:
            # BUG-004 FIX: Provide user feedback when preset is invalid
            from PyQt6.QtWidgets import QMessageBox
            logger.warning(f"Invalid preset selected: {regime_key}")
            if regime_key:  # Only show message if something was selected
                QMessageBox.warning(
                    self._preset_details_table,
                    "Ungültiges Preset",
                    f"Das ausgewählte Preset '{regime_key}' konnte nicht geladen werden."
                )
            return

        preset = REGIME_PRESETS[regime_key]

        # Count total rows needed
        total_rows = sum(
            len([k for k in ind_config.keys() if k != 'notes'])
            for ind_config in preset['indicators'].values()
        )

        # Clear and resize table
        self._preset_details_table.setRowCount(total_rows)

        # Populate table
        row_idx = 0
        for ind_name, ind_config in preset['indicators'].items():
            params = [k for k in ind_config.keys() if k != 'notes']
            param_count = len(params)
            notes = ind_config.get('notes', '')

            for param_idx, param_name in enumerate(params):
                # Indicator column (only on first param)
                if param_idx == 0:
                    indicator_item = QTableWidgetItem(ind_name)
                    self._preset_details_table.setItem(row_idx, 0, indicator_item)
                    if param_count > 1:
                        self._preset_details_table.setSpan(row_idx, 0, param_count, 1)

                # Parameter column
                param_item = QTableWidgetItem(param_name)
                self._preset_details_table.setItem(row_idx, 1, param_item)

                # Range column
                min_val, max_val, step = ind_config[param_name]
                range_item = QTableWidgetItem(f"{min_val} - {max_val} (step {step})")
                self._preset_details_table.setItem(row_idx, 2, range_item)

                # Notes column (only on first param)
                if param_idx == 0:
                    notes_item = QTableWidgetItem(notes)
                    self._preset_details_table.setItem(row_idx, 3, notes_item)
                    if param_count > 1:
                        self._preset_details_table.setSpan(row_idx, 3, param_count, 1)

                row_idx += 1

        logger.debug(f"Loaded preset '{preset['name']}' with {total_rows} parameter rows")

    def _on_auto_preset_clicked(self) -> None:
        """Auto-select preset based on currently detected regime.

        Reads regime from _regime_label and selects matching preset.
        """
        # Extract current regime from label
        if not hasattr(self, '_regime_label') or not self._regime_label:
            logger.warning("No regime label available for auto-preset")
            return

        regime_text = self._regime_label.text()
        logger.info(f"Auto-preset: Current regime text = '{regime_text}'")

        # Parse regime (e.g., "Regime: Trend Up" -> "trend_up")
        if ":" not in regime_text:
            logger.warning(f"Cannot parse regime from: {regime_text}")
            return

        regime_display = regime_text.split(":", 1)[1].strip().lower()
        regime_key = regime_display.replace(" ", "_")

        logger.info(f"Auto-preset: Detected regime key = '{regime_key}'")

        # Find matching preset
        if regime_key in REGIME_PRESETS:
            # Set combo to this regime
            for i in range(self._preset_combo.count()):
                if self._preset_combo.itemData(i) == regime_key:
                    self._preset_combo.setCurrentIndex(i)
                    logger.info(f"Auto-preset: Applied preset for '{regime_key}'")
                    return

        logger.warning(f"No preset found for regime '{regime_key}'")

    def _on_apply_preset_clicked(self) -> None:
        """Apply selected preset to parameter range widgets.

        Updates all Min/Max/Step spinboxes in the optimization setup.
        """
        regime_key = self._preset_combo.currentData()
        if not regime_key or regime_key not in REGIME_PRESETS:
            logger.warning("No valid preset selected")
            return

        preset = REGIME_PRESETS[regime_key]
        logger.info(f"Applying preset: {preset['name']}")

        applied_count = 0

        # Update parameter widgets
        for ind_name, ind_config in preset['indicators'].items():
            if ind_name not in self._param_widgets:
                continue

            for param_name, param_range in ind_config.items():
                if param_name == 'notes':
                    continue

                if param_name not in self._param_widgets[ind_name]:
                    continue

                min_val, max_val, step = param_range
                widgets = self._param_widgets[ind_name][param_name]

                # Update spinboxes
                widgets['min'].setValue(min_val)
                widgets['max'].setValue(max_val)
                widgets['step'].setValue(step)

                applied_count += 1

        logger.info(f"Applied {applied_count} parameter ranges from preset '{preset['name']}'")

        # Show confirmation (optional)
        if hasattr(self, '_optimization_progress'):
            self._optimization_progress.setText(
                f"✅ Applied preset: {preset['name']} ({applied_count} parameters)"
            )
