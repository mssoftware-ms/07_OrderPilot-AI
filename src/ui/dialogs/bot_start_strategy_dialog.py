"""Bot Start Strategy Dialog for JSON-based strategy selection before bot start.

This dialog allows users to:
1. Select a JSON strategy configuration file
2. Analyze current market regime
3. Preview matched strategy
4. Apply strategy before bot start
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QFormLayout,
    QFileDialog,
    QMessageBox,
    QComboBox,
)

if TYPE_CHECKING:
    from src.ui.widgets.chart_window import ChartWindow

logger = logging.getLogger(__name__)


class BotStartStrategyDialog(QDialog):
    """Dialog for JSON-based strategy selection before bot start."""

    strategy_applied = pyqtSignal(str, object)  # config_path, matched_strategy_set

    def __init__(self, parent: ChartWindow | None = None):
        super().__init__(parent)
        self.setWindowTitle("Bot Start - Strategy Selection")
        self.setMinimumSize(800, 600)
        self.setModal(True)

        # Store matched strategy set
        self.matched_strategy_set = None
        self.config_path = ""
        self.config = None

        self._init_ui()

    def _init_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)

        # JSON Config Selection Group
        config_group = self._create_config_group()
        layout.addWidget(config_group)

        # Current Regime Display Group
        regime_group = self._create_regime_group()
        layout.addWidget(regime_group)

        # Matched Strategy Display Group
        strategy_group = self._create_strategy_group()
        layout.addWidget(strategy_group)

        # Buttons
        button_layout = self._create_buttons()
        layout.addLayout(button_layout)

    def _create_config_group(self) -> QGroupBox:
        """Create JSON config selection group."""
        group = QGroupBox("JSON Strategy Configuration")
        layout = QFormLayout(group)

        # Trading Style Selection (NEW)
        self.trading_style_combo = QComboBox()
        self.trading_style_combo.addItems([
            "Daytrading / Scalping",
            "Swing Trading",
            "Position Trading"
        ])
        self.trading_style_combo.setCurrentIndex(0)  # Default: Daytrading
        self.trading_style_combo.currentIndexChanged.connect(self._on_trading_style_changed)
        layout.addRow("Trading Style:", self.trading_style_combo)

        # Info label for trading style
        trading_style_info = QLabel(
            "Daytrading: Intraday trades, shorter timeframes (1m, 5m, 15m)\n"
            "Swing: Multi-day positions, longer timeframes (1h, 4h, 1D)\n"
            "Position: Long-term holds, weekly/monthly timeframes"
        )
        trading_style_info.setStyleSheet("color: #666; font-size: 11px;")
        trading_style_info.setWordWrap(True)
        layout.addRow("", trading_style_info)

        # Config file input
        file_layout = QHBoxLayout()
        self.config_file_input = QLineEdit()
        self.config_file_input.setPlaceholderText("Select a JSON strategy configuration file...")
        self.config_file_input.textChanged.connect(self._on_config_path_changed)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.clicked.connect(self._on_browse_clicked)

        file_layout.addWidget(self.config_file_input)
        file_layout.addWidget(self.browse_btn)

        layout.addRow("Config File:", file_layout)

        # Config preview
        self.config_preview = QTextEdit()
        self.config_preview.setReadOnly(True)
        self.config_preview.setMaximumHeight(150)
        self.config_preview.setPlaceholderText("Configuration preview will appear here...")
        layout.addRow("Preview:", self.config_preview)

        return group

    def _create_regime_group(self) -> QGroupBox:
        """Create current regime display group."""
        group = QGroupBox("Current Market Regime")
        layout = QVBoxLayout(group)

        # Regime label
        self.current_regime_label = QLabel("Click 'Analyze Current Market' to detect regime")
        self.current_regime_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.current_regime_label)

        # Regime details
        self.regime_details = QTextEdit()
        self.regime_details.setReadOnly(True)
        self.regime_details.setMaximumHeight(100)
        self.regime_details.setPlaceholderText("Regime details will appear here...")
        layout.addWidget(self.regime_details)

        return group

    def _create_strategy_group(self) -> QGroupBox:
        """Create matched strategy display group."""
        group = QGroupBox("Matched Strategy")
        layout = QVBoxLayout(group)

        # Strategy label
        self.matched_strategy_label = QLabel("No strategy matched")
        self.matched_strategy_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.matched_strategy_label)

        # Strategy conditions
        self.strategy_conditions = QTextEdit()
        self.strategy_conditions.setReadOnly(True)
        self.strategy_conditions.setPlaceholderText("Strategy entry/exit conditions will appear here...")
        layout.addWidget(self.strategy_conditions)

        return group

    def _create_buttons(self) -> QHBoxLayout:
        """Create dialog buttons."""
        layout = QHBoxLayout()

        # Left side: Analysis & Export/Reload
        left_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("🔍 Analyze Current Market")
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        self.analyze_btn.setEnabled(False)  # Enable after config loaded
        left_layout.addWidget(self.analyze_btn)

        # Export Strategy Button (7.1.1)
        self.export_btn = QPushButton("💾 Export Current")
        self.export_btn.setToolTip("Export current strategy configuration to JSON file")
        self.export_btn.clicked.connect(self._on_export_strategy_clicked)
        self.export_btn.setEnabled(False)  # Enable after config loaded
        left_layout.addWidget(self.export_btn)

        # Reload Strategy Button (7.1.2)
        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.setToolTip("Hot-reload strategy configuration from file")
        self.reload_btn.clicked.connect(self._on_reload_strategy_clicked)
        self.reload_btn.setEnabled(False)  # Enable after config loaded
        left_layout.addWidget(self.reload_btn)

        # Open Editor Button (7.1.3)
        self.editor_btn = QPushButton("📝 Edit")
        self.editor_btn.setToolTip("Open strategy in visual editor")
        self.editor_btn.clicked.connect(self._on_open_editor_clicked)
        self.editor_btn.setEnabled(False)  # Enable after config loaded
        left_layout.addWidget(self.editor_btn)

        layout.addLayout(left_layout)
        layout.addStretch()

        # Right side: Apply & Cancel
        self.apply_btn = QPushButton("✓ Apply Strategy & Start Bot")
        self.apply_btn.clicked.connect(self.accept)
        self.apply_btn.setEnabled(False)  # Enable after strategy matched

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)

        layout.addWidget(self.apply_btn)
        layout.addWidget(self.cancel_btn)

        return layout

    def _on_trading_style_changed(self, index: int) -> None:
        """Handle trading style selection change."""
        style_names = ["Daytrading", "Swing Trading", "Position Trading"]
        selected_style = style_names[index] if index < len(style_names) else "Daytrading"
        logger.info(f"Trading style changed to: {selected_style}")

        # Clear current config if trading style changes
        if self.config_path:
            self.config_file_input.clear()
            self.config_preview.clear()
            self.analyze_btn.setEnabled(False)

    def _get_config_directory_for_style(self) -> Path:
        """Get config directory based on selected trading style.

        Returns:
            Path to config directory for current trading style
        """
        project_root = Path(__file__).parent.parent.parent.parent
        base_dir = project_root / "03_JSON" / "Trading_Bot"

        # Get trading style index
        style_index = self.trading_style_combo.currentIndex()

        # Try subdirectories first (daytrading/, swing/, position/)
        if style_index == 0:  # Daytrading
            style_dir = base_dir / "daytrading"
            if style_dir.exists():
                return style_dir
        elif style_index == 1:  # Swing
            style_dir = base_dir / "swing"
            if style_dir.exists():
                return style_dir
        elif style_index == 2:  # Position
            style_dir = base_dir / "position"
            if style_dir.exists():
                return style_dir

        # Fallback to base directory
        if base_dir.exists():
            return base_dir

        # Fallback to project root
        return project_root

    def _on_browse_clicked(self) -> None:
        """Handle browse button click."""
        # Get directory based on trading style
        default_dir = self._get_config_directory_for_style()

        # Get trading style name for dialog title
        style_name = self.trading_style_combo.currentText()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select Strategy Configuration ({style_name})",
            str(default_dir),
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            self.config_file_input.setText(file_path)

    def _on_config_path_changed(self, path: str) -> None:
        """Handle config path change."""
        if not path or not os.path.exists(path):
            self.config_preview.clear()
            self.analyze_btn.setEnabled(False)
            return

        try:
            # Load and preview config
            from src.core.tradingbot.config.loader import ConfigLoader

            loader = ConfigLoader()
            self.config = loader.load_config(path)
            self.config_path = path

            # Display preview
            preview_text = self._format_config_preview(self.config)
            self.config_preview.setPlainText(preview_text)

            # Enable analyze button
            self.analyze_btn.setEnabled(True)

            logger.info(f"Loaded strategy config: {path}")

        except Exception as e:
            logger.error(f"Failed to load config: {e}", exc_info=True)
            QMessageBox.warning(
                self,
                "Config Load Error",
                f"Failed to load configuration:\n{e}"
            )
            self.config_preview.clear()
            self.analyze_btn.setEnabled(False)

    def _format_config_preview(self, config: Any) -> str:
        """Format config for preview display."""
        lines = []
        lines.append(f"Schema Version: {config.schema_version}")
        lines.append(f"\nIndicators: {len(config.indicators)}")
        for ind in config.indicators[:5]:  # Show first 5
            lines.append(f"  - {ind.id}: {ind.type} (TF: {ind.timeframe or '1m'})")
        if len(config.indicators) > 5:
            lines.append(f"  ... and {len(config.indicators) - 5} more")

        lines.append(f"\nRegimes: {len(config.regimes)}")
        for regime in config.regimes[:3]:  # Show first 3
            lines.append(f"  - {regime.id}: {regime.name}")
        if len(config.regimes) > 3:
            lines.append(f"  ... and {len(config.regimes) - 3} more")

        lines.append(f"\nStrategies: {len(config.strategies)}")
        for strat in config.strategies[:3]:
            lines.append(f"  - {strat.id}")
        if len(config.strategies) > 3:
            lines.append(f"  ... and {len(config.strategies) - 3} more")

        lines.append(f"\nStrategy Sets: {len(config.strategy_sets)}")
        lines.append(f"Routing Rules: {len(config.routing)}")

        return "\n".join(lines)

    def _on_analyze_clicked(self) -> None:
        """Handle analyze button click - detect current regime and match strategy."""
        if not self.config:
            QMessageBox.warning(self, "Error", "Please select a valid config file")
            return

        try:
            # Get parent chart window
            chart_window = self.parent()
            if not chart_window:
                QMessageBox.warning(self, "Error", "No chart window available")
                return

            # Get current market data from chart
            symbol = self._get_current_symbol(chart_window)
            features = self._get_current_features(chart_window)

            if not features:
                QMessageBox.warning(
                    self,
                    "Error",
                    "No market data available. Please ensure chart has loaded data."
                )
                return

            # Detect current regime
            from src.core.tradingbot.regime_engine import RegimeEngine

            regime_engine = RegimeEngine()
            current_regime = regime_engine.classify(features)

            # Update regime display
            self._update_regime_display(current_regime)

            # Route to strategy
            self._route_to_strategy(current_regime, features)

            logger.info(f"Market analysis complete: {current_regime.regime.name}")

        except Exception as e:
            logger.error(f"Market analysis failed: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Failed to analyze market:\n{e}"
            )

    def _get_current_symbol(self, chart_window: Any) -> str:
        """Get current symbol from chart window."""
        try:
            if hasattr(chart_window, 'symbol'):
                return chart_window.symbol
            elif hasattr(chart_window, 'get_symbol'):
                return chart_window.get_symbol()
            else:
                return "BTCUSD"  # Default fallback
        except Exception as e:
            logger.warning(f"Failed to get symbol: {e}")
            return "BTCUSD"

    def _get_current_features(self, chart_window: Any) -> Any:
        """Get current feature vector from chart window."""
        try:
            # Try to get from feature engine
            if hasattr(chart_window, 'feature_engine'):
                feature_engine = chart_window.feature_engine
                if hasattr(feature_engine, 'get_current_features'):
                    return feature_engine.get_current_features()

            # Try to compute from latest bar data
            if hasattr(chart_window, 'get_latest_bar_data'):
                bar_data = chart_window.get_latest_bar_data()
                if bar_data:
                    from src.core.tradingbot.feature_engine import FeatureEngine
                    feature_engine = FeatureEngine()
                    return feature_engine.process_bar(bar_data)

            return None

        except Exception as e:
            logger.error(f"Failed to get features: {e}", exc_info=True)
            return None

    def _update_regime_display(self, regime: Any) -> None:
        """Update regime display with detected regime."""
        # Update regime label
        regime_text = f"{regime.regime.name} - {regime.volatility.name}"
        self.current_regime_label.setText(regime_text)

        # Color code regime label
        if "UP" in regime.regime.name:
            color = "#26a69a"  # Green
        elif "DOWN" in regime.regime.name:
            color = "#ef5350"  # Red
        else:
            color = "#ffa726"  # Orange

        self.current_regime_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {color};"
        )

        # Update regime details
        details = []
        details.append(f"ADX: {regime.adx:.2f}")
        details.append(f"ATR%: {regime.atr_pct:.2f}%")
        details.append(f"Confidence: {regime.regime_confidence:.2%}")
        details.append(f"\nTrend Direction: {regime.trend_direction}")
        details.append(f"Volatility: {regime.volatility.name}")

        self.regime_details.setPlainText("\n".join(details))

    def _route_to_strategy(self, current_regime: Any, features: Any) -> None:
        """Route current regime to matching strategy."""
        try:
            from src.core.tradingbot.config.detector import RegimeDetector
            from src.core.tradingbot.config.router import StrategyRouter
            from src.core.tradingbot.config_integration_bridge import IndicatorValueCalculator

            # Calculate indicator values from features
            calculator = IndicatorValueCalculator()
            indicator_values = calculator.calculate(features)

            # Detect active regimes from JSON config
            detector = RegimeDetector(self.config.regimes)
            active_regimes = detector.detect_active_regimes(indicator_values, scope='entry')

            if not active_regimes:
                self.matched_strategy_label.setText("⚠ No regimes matched current market")
                self.matched_strategy_label.setStyleSheet("font-size: 14px; color: #ff9800;")
                self.apply_btn.setEnabled(False)
                return

            # Route to strategy set
            router = StrategyRouter(self.config.routing, self.config.strategy_sets)
            matched_set = router.route(active_regimes)

            if matched_set:
                self.matched_strategy_set = matched_set
                self._update_strategy_display(matched_set, active_regimes)
                self.apply_btn.setEnabled(True)
            else:
                self.matched_strategy_label.setText("⚠ No strategy matched active regimes")
                self.matched_strategy_label.setStyleSheet("font-size: 14px; color: #ff9800;")
                self.apply_btn.setEnabled(False)

        except Exception as e:
            logger.error(f"Strategy routing failed: {e}", exc_info=True)
            self.matched_strategy_label.setText(f"❌ Routing error: {str(e)[:50]}")
            self.matched_strategy_label.setStyleSheet("font-size: 14px; color: #f44336;")
            self.apply_btn.setEnabled(False)

    def _update_strategy_display(self, matched_set: Any, active_regimes: list) -> None:
        """Update strategy display with matched strategy."""
        # Update strategy label
        strategy_set_name = matched_set.strategy_set.name if hasattr(matched_set.strategy_set, 'name') else matched_set.strategy_set.id
        self.matched_strategy_label.setText(f"✓ Matched: {strategy_set_name}")
        self.matched_strategy_label.setStyleSheet("font-size: 14px; color: #26a69a;")

        # Format strategy conditions
        conditions_text = self._format_strategy_conditions(matched_set, active_regimes)
        self.strategy_conditions.setPlainText(conditions_text)

    def _format_strategy_conditions(self, matched_set: Any, active_regimes: list) -> str:
        """Format strategy conditions for display."""
        lines = []

        # Active regimes
        lines.append("Active Regimes:")
        for regime in active_regimes:
            lines.append(f"  - {regime.name}")

        lines.append(f"\nStrategy Set: {matched_set.strategy_set.name if hasattr(matched_set.strategy_set, 'name') else matched_set.strategy_set.id}")
        lines.append(f"Strategies in Set: {len(matched_set.strategy_set.strategies)}")

        # Show first strategy details
        if matched_set.strategy_set.strategies:
            first_strat_ref = matched_set.strategy_set.strategies[0]

            # Find strategy definition
            strategy_def = next(
                (s for s in self.config.strategies if s.id == first_strat_ref.strategy_id),
                None
            )

            if strategy_def:
                lines.append(f"\nPrimary Strategy: {strategy_def.id}")

                # Entry conditions
                if strategy_def.entry:
                    lines.append("\nEntry Conditions:")
                    lines.append(self._format_condition_group(strategy_def.entry, indent=2))

                # Exit conditions
                if strategy_def.exit:
                    lines.append("\nExit Conditions:")
                    lines.append(self._format_condition_group(strategy_def.exit, indent=2))

                # Risk settings
                if strategy_def.risk:
                    lines.append("\nRisk Settings:")
                    lines.append(f"  Risk per Trade: {strategy_def.risk.risk_per_trade_pct}%")
                    if strategy_def.risk.stop_loss_pct:
                        lines.append(f"  Stop Loss: {strategy_def.risk.stop_loss_pct}%")
                    if strategy_def.risk.take_profit_pct:
                        lines.append(f"  Take Profit: {strategy_def.risk.take_profit_pct}%")

        return "\n".join(lines)

    def _format_condition_group(self, group: Any, indent: int = 0) -> str:
        """Format condition group recursively."""
        lines = []
        prefix = "  " * indent

        if group.all:
            lines.append(f"{prefix}ALL of:")
            for cond in group.all:
                lines.append(f"{prefix}  - {self._format_condition(cond)}")

        if group.any:
            lines.append(f"{prefix}ANY of:")
            for cond in group.any:
                lines.append(f"{prefix}  - {self._format_condition(cond)}")

        return "\n".join(lines)

    def _format_condition(self, cond: Any) -> str:
        """Format single condition."""
        left = f"{cond.left.indicator_id}.{cond.left.field}" if cond.left.indicator_id else str(cond.left.value)

        if cond.op == "between":
            return f"{left} between {cond.right.min} and {cond.right.max}"
        else:
            right = f"{cond.right.indicator_id}.{cond.right.field}" if cond.right.indicator_id else str(cond.right.value)
            op_symbol = {"gt": ">", "lt": "<", "eq": "==", "gte": ">=", "lte": "<="}.get(cond.op, cond.op)
            return f"{left} {op_symbol} {right}"

    def _on_export_strategy_clicked(self) -> None:
        """Export current strategy configuration to JSON file (7.1.1)."""
        if not self.config or not self.config_path:
            QMessageBox.warning(
                self,
                "Export Failed",
                "No strategy loaded to export. Please select a config file first."
            )
            return

        try:
            # Get save path with timestamped default name
            default_name = f"strategy_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            default_dir = str(Path(self.config_path).parent)
            default_path = str(Path(default_dir) / default_name)

            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Strategy Configuration",
                default_path,
                "JSON Files (*.json);;All Files (*)"
            )

            if not file_path:
                return  # User cancelled

            # Convert config to dict for export
            config_dict = self.config.model_dump(mode='json', exclude_none=True)

            # Add export metadata
            config_dict['_export_metadata'] = {
                'exported_at': datetime.now().isoformat(),
                'source_file': str(self.config_path),
                'matched_strategy': self.matched_strategy_set.strategy_set.id if self.matched_strategy_set else None
            }

            # Write to file with formatting
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config_dict, f, indent=2, ensure_ascii=False)

            logger.info(f"Strategy exported to: {file_path}")
            QMessageBox.information(
                self,
                "Export Successful",
                f"Strategy configuration exported to:\n{file_path}"
            )

        except Exception as e:
            logger.error(f"Failed to export strategy: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export strategy:\n{str(e)}"
            )

    def _on_reload_strategy_clicked(self) -> None:
        """Hot-reload strategy configuration from file (7.1.2)."""
        if not self.config_path:
            QMessageBox.warning(
                self,
                "Reload Failed",
                "No config file selected to reload."
            )
            return

        try:
            # Confirm reload
            reply = QMessageBox.question(
                self,
                "Reload Strategy",
                f"Reload strategy from:\n{self.config_path}\n\nThis will discard any unsaved changes.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

            # Reload by triggering config path change
            logger.info(f"Hot-reloading strategy from: {self.config_path}")
            self._on_config_path_changed(self.config_path)

            # Re-analyze if parent available
            if self.parent():
                QMessageBox.information(
                    self,
                    "Reload Successful",
                    f"Strategy reloaded from:\n{self.config_path}\n\nClick 'Analyze Current Market' to re-evaluate."
                )
            else:
                QMessageBox.information(
                    self,
                    "Reload Successful",
                    f"Strategy reloaded from:\n{self.config_path}"
                )

        except Exception as e:
            logger.error(f"Failed to reload strategy: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Reload Error",
                f"Failed to reload strategy:\n{str(e)}"
            )

    def _on_open_editor_clicked(self) -> None:
        """Open strategy in visual editor (7.1.3)."""
        if not self.config_path:
            QMessageBox.warning(
                self,
                "Editor Failed",
                "No config file selected to edit."
            )
            return

        try:
            # Try to import strategy concept window
            try:
                from src.ui.dialogs.strategy_concept_window import StrategyConceptWindow

                # Open strategy editor with current config
                editor = StrategyConceptWindow(parent=self.parent())
                editor.load_config(self.config_path)
                editor.show()

                logger.info(f"Opened strategy editor for: {self.config_path}")

            except ImportError as e:
                # Fallback: Try to open CEL editor widget
                try:
                    from src.ui.widgets.cel_strategy_editor_widget import CELStrategyEditorWidget

                    editor = CELStrategyEditorWidget(parent=self.parent())
                    editor.load_config(self.config_path)
                    editor.show()

                    logger.info(f"Opened CEL editor for: {self.config_path}")

                except ImportError:
                    # Fallback: Open in system text editor
                    import subprocess
                    import sys

                    if sys.platform == 'win32':
                        os.startfile(self.config_path)
                    elif sys.platform == 'darwin':
                        subprocess.run(['open', self.config_path])
                    else:
                        subprocess.run(['xdg-open', self.config_path])

                    logger.info(f"Opened strategy in system editor: {self.config_path}")
                    QMessageBox.information(
                        self,
                        "Editor Opened",
                        f"Strategy opened in system text editor:\n{self.config_path}"
                    )

        except Exception as e:
            logger.error(f"Failed to open editor: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Editor Error",
                f"Failed to open strategy editor:\n{str(e)}"
            )

    def accept(self) -> None:
        """Handle accept - emit strategy applied signal."""
        if not self.matched_strategy_set or not self.config_path:
            QMessageBox.warning(self, "Error", "No strategy to apply")
            return

        self.strategy_applied.emit(self.config_path, self.matched_strategy_set)
        super().accept()
