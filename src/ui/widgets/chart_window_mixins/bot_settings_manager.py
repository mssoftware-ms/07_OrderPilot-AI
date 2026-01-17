"""Bot Settings Manager - Settings Persistence Module.

Handles saving, loading, and applying bot configuration settings.
Extracted from BotUIControlMixin for Single Responsibility.

Module 3/4 of bot_ui_control_mixin.py split.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

logger = logging.getLogger(__name__)


class BotSettingsManager:
    """Settings manager for bot configuration persistence.

    Handles:
    - Collecting current settings from UI widgets
    - Applying settings to UI widgets
    - Saving/loading defaults to/from JSON file
    - Factory reset to default values
    """

    # Factory Defaults für Micro-Account (100€ Kapital)
    # Issue #16: Keys müssen mit widget_map übereinstimmen!
    FACTORY_DEFAULTS = {
        'meta': {'type': 'factory_defaults'},
        'settings': {
            # Bot Settings - Keys müssen mit widget_map übereinstimmen
            'ki_mode': 'NO_KI',
            'trade_direction': 'AUTO',  # Wird durch Backtesting ermittelt
            'trailing_mode': 'ATR',
            'initial_sl_pct': 2.0,  # Issue #16: Korrigiert von 'initial_sl'
            'bot_capital': 100,  # Issue #16: Korrigiert von 'capital'
            'risk_per_trade_pct': 50.0,  # Issue #16: Korrigiert von 'risk_per_trade'
            'max_trades_per_day': 10,  # Issue #16: Korrigiert von 'max_trades'
            'max_daily_loss_pct': 5.0,  # Issue #16: Korrigiert von 'max_daily_loss'
            'disable_restrictions': True,
            'disable_macd_exit': True,
            'disable_macd_entry': False,  # Issue #16: Hinzugefügt
            'disable_rsi_exit': True,
            'disable_rsi_entry': False,  # Issue #16: Hinzugefügt
            'enable_derivathandel': False,
            # Leverage Override
            'leverage_override_enabled': True,
            'leverage_value': 20,
            # Trailing Settings (optimiert für enge Stops)
            'regime_adaptive': True,
            'tra_percent': 0.3,
            'trailing_distance': 1.0,  # Eng!
            'atr_multiplier': 1.5,  # Eng!
            'atr_trending': 1.2,  # Sehr eng bei Trend
            'atr_ranging': 2.0,
            'volatility_bonus': 0.3,
            'min_step': 0.2,
            # Pattern Validation
            'min_score': 55,
            'use_pattern': False,
            'pattern_similarity': 0.70,
            'pattern_matches': 5,
            'pattern_winrate': 55,
            # Display
            'show_entry_markers': True,
            'show_stop_lines': True,
            'show_debug_hud': False,
            # BitUnix Fees (Issue #30)
            'futures_maker_fee': 0.02,  # VIP 0 default
            'futures_taker_fee': 0.06,  # VIP 0 default
        }
    }

    def __init__(self, parent):
        """Initialize settings manager.

        Args:
            parent: Parent widget (typically BotUIControlMixin)
        """
        self.parent = parent

    def get_bot_settings(self) -> dict:
        """Sammelt alle Bot-Einstellungen in einem Dict."""
        settings = {
            'meta': {
                'saved_at': datetime.now().isoformat(),
                'version': '1.0',
                'type': 'bot_control_settings',
            },
            'settings': {}
        }

        # Alle SpinBox/DoubleSpinBox/ComboBox/CheckBox Werte sammeln
        widget_map = {
            # Bot Settings
            'ki_mode': ('ki_mode_combo', 'combo'),
            'trade_direction': ('trade_direction_combo', 'combo'),
            'trailing_mode': ('trailing_mode_combo', 'combo'),
            'initial_sl_pct': ('initial_sl_spin', 'double'),
            'bot_capital': ('bot_capital_spin', 'double'),
            'risk_per_trade_pct': ('risk_per_trade_spin', 'double'),
            'max_trades_per_day': ('max_trades_spin', 'int'),
            'max_daily_loss_pct': ('max_daily_loss_spin', 'double'),
            'disable_restrictions': ('disable_restrictions_cb', 'check'),
            'disable_macd_exit': ('disable_macd_exit_cb', 'check'),
            'disable_macd_entry': ('disable_macd_entry_cb', 'check'),
            'disable_rsi_exit': ('disable_rsi_exit_cb', 'check'),
            'disable_rsi_entry': ('disable_rsi_entry_cb', 'check'),
            'enable_derivathandel': ('enable_derivathandel_cb', 'check'),
            # Leverage Override
            'leverage_override_enabled': ('leverage_override_cb', 'check'),
            'leverage_value': ('leverage_slider', 'slider'),
            # Trailing Settings
            'regime_adaptive': ('regime_adaptive_cb', 'check'),
            'tra_percent': ('tra_percent_spin', 'double'),
            'trailing_distance': ('trailing_distance_spin', 'double'),
            'atr_multiplier': ('atr_multiplier_spin', 'double'),
            'atr_trending': ('atr_trending_spin', 'double'),
            'atr_ranging': ('atr_ranging_spin', 'double'),
            'volatility_bonus': ('volatility_bonus_spin', 'double'),
            'min_step': ('min_step_spin', 'double'),
            # Pattern Validation
            'min_score': ('min_score_spin', 'int'),
            'use_pattern': ('use_pattern_cb', 'check'),
            'pattern_similarity': ('pattern_similarity_spin', 'double'),
            'pattern_matches': ('pattern_matches_spin', 'int'),
            'pattern_winrate': ('pattern_winrate_spin', 'int'),
            # Display
            'show_entry_markers': ('show_entry_markers_cb', 'check'),
            'show_stop_lines': ('show_stop_lines_cb', 'check'),
            'show_debug_hud': ('show_debug_hud_cb', 'check'),
            # BitUnix Fees (Issue #30)
            'futures_maker_fee': ('futures_maker_fee_spin', 'double'),
            'futures_taker_fee': ('futures_taker_fee_spin', 'double'),
        }

        for key, (widget_name, widget_type) in widget_map.items():
            if hasattr(self.parent, widget_name):
                widget = getattr(self.parent, widget_name)
                try:
                    if widget_type == 'combo':
                        settings['settings'][key] = widget.currentText()
                    elif widget_type == 'check':
                        settings['settings'][key] = widget.isChecked()
                    elif widget_type == 'int':
                        settings['settings'][key] = widget.value()
                    elif widget_type == 'double':
                        settings['settings'][key] = widget.value()
                    elif widget_type == 'slider':
                        settings['settings'][key] = widget.value()
                except Exception as e:
                    logger.warning(f"Could not read {widget_name}: {e}")

        return settings

    def apply_bot_settings(self, settings: dict) -> None:
        """Wendet gespeicherte Bot-Einstellungen an."""
        data = settings.get('settings', {})

        widget_map = {
            'ki_mode': ('ki_mode_combo', 'combo'),
            'trade_direction': ('trade_direction_combo', 'combo'),
            'trailing_mode': ('trailing_mode_combo', 'combo'),
            'initial_sl_pct': ('initial_sl_spin', 'double'),
            'bot_capital': ('bot_capital_spin', 'double'),
            'risk_per_trade_pct': ('risk_per_trade_spin', 'double'),
            'max_trades_per_day': ('max_trades_spin', 'int'),
            'max_daily_loss_pct': ('max_daily_loss_spin', 'double'),
            'disable_restrictions': ('disable_restrictions_cb', 'check'),
            'disable_macd_exit': ('disable_macd_exit_cb', 'check'),
            'disable_macd_entry': ('disable_macd_entry_cb', 'check'),
            'disable_rsi_exit': ('disable_rsi_exit_cb', 'check'),
            'disable_rsi_entry': ('disable_rsi_entry_cb', 'check'),
            'enable_derivathandel': ('enable_derivathandel_cb', 'check'),
            'leverage_override_enabled': ('leverage_override_cb', 'check'),
            'leverage_value': ('leverage_slider', 'slider'),
            'regime_adaptive': ('regime_adaptive_cb', 'check'),
            'tra_percent': ('tra_percent_spin', 'double'),
            'trailing_distance': ('trailing_distance_spin', 'double'),
            'atr_multiplier': ('atr_multiplier_spin', 'double'),
            'atr_trending': ('atr_trending_spin', 'double'),
            'atr_ranging': ('atr_ranging_spin', 'double'),
            'volatility_bonus': ('volatility_bonus_spin', 'double'),
            'min_step': ('min_step_spin', 'double'),
            'min_score': ('min_score_spin', 'int'),
            'use_pattern': ('use_pattern_cb', 'check'),
            'pattern_similarity': ('pattern_similarity_spin', 'double'),
            'pattern_matches': ('pattern_matches_spin', 'int'),
            'pattern_winrate': ('pattern_winrate_spin', 'int'),
            'show_entry_markers': ('show_entry_markers_cb', 'check'),
            'show_stop_lines': ('show_stop_lines_cb', 'check'),
            'show_debug_hud': ('show_debug_hud_cb', 'check'),
            # BitUnix Fees (Issue #30)
            'futures_maker_fee': ('futures_maker_fee_spin', 'double'),
            'futures_taker_fee': ('futures_taker_fee_spin', 'double'),
        }

        for key, (widget_name, widget_type) in widget_map.items():
            if key in data and hasattr(self.parent, widget_name):
                widget = getattr(self.parent, widget_name)
                value = data[key]
                try:
                    if widget_type == 'combo':
                        idx = widget.findText(value)
                        if idx >= 0:
                            widget.setCurrentIndex(idx)
                    elif widget_type == 'check':
                        widget.setChecked(bool(value))
                    elif widget_type in ('int', 'double', 'slider'):
                        widget.setValue(value)
                except Exception as e:
                    logger.warning(f"Could not apply {widget_name}: {e}")

    def on_save_defaults_clicked(self) -> None:
        """Speichert aktuelle Einstellungen als Standard."""
        try:
            settings = self.get_bot_settings()

            # Default-Speicherort
            config_dir = Path("config/bot_configs")
            config_dir.mkdir(parents=True, exist_ok=True)

            default_file = config_dir / "bot_defaults.json"

            with open(default_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, indent=2, ensure_ascii=False)

            logger.info(f"Bot-Einstellungen gespeichert: {default_file}")
            QMessageBox.information(
                self.parent, "Gespeichert",
                f"Einstellungen wurden als Standard gespeichert.\n\n"
                f"Datei: {default_file}\n"
                f"Felder: {len(settings['settings'])}"
            )

            self._sync_symbol_settings()

        except Exception as e:
            logger.exception("Failed to save defaults")
            QMessageBox.critical(self.parent, "Fehler", f"Speichern fehlgeschlagen:\n{e}")

    def _sync_symbol_settings(self) -> None:
        """Sync defaults to current symbol settings to prevent overrides on restart."""
        if not hasattr(self.parent, "_save_bot_settings"):
            return

        symbol = None
        if hasattr(self.parent, "_resolve_bot_symbol"):
            try:
                symbol = self.parent._resolve_bot_symbol()
            except Exception:
                symbol = None

        if not symbol:
            symbol = getattr(self.parent, "_current_bot_symbol", None)

        if not symbol and hasattr(self.parent, "current_symbol"):
            symbol = getattr(self.parent, "current_symbol", None)

        if not symbol and hasattr(self.parent, "chart_widget"):
            symbol = getattr(self.parent.chart_widget, "current_symbol", None)

        if not symbol and hasattr(self.parent, "bot_symbol_label"):
            label_text = self.parent.bot_symbol_label.text()
            symbol = label_text if label_text and label_text != "-" else None

        if not symbol:
            return

        try:
            self.parent._save_bot_settings(symbol)
            logger.info("Synced bot defaults to symbol settings for %s", symbol)
        except Exception as e:
            logger.warning("Failed to sync symbol settings after saving defaults: %s", e)

    def on_load_defaults_clicked(self) -> None:
        """Lädt gespeicherte Standard-Einstellungen."""
        try:
            default_file = Path("config/bot_configs/bot_defaults.json")

            if not default_file.exists():
                QMessageBox.warning(
                    self.parent, "Keine Defaults",
                    "Keine gespeicherten Standard-Einstellungen gefunden.\n\n"
                    "Bitte zuerst 'Speichern' klicken."
                )
                return

            with open(default_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)

            self.apply_bot_settings(settings)

            meta = settings.get('meta', {})
            saved_at = meta.get('saved_at', 'Unbekannt')

            logger.info(f"Bot-Einstellungen geladen: {default_file}")
            QMessageBox.information(
                self.parent, "Geladen",
                f"Standard-Einstellungen wurden geladen.\n\n"
                f"Gespeichert: {saved_at[:19] if len(saved_at) > 19 else saved_at}\n"
                f"Parameter: {len(settings.get('settings', {}))}"
            )

        except Exception as e:
            logger.exception("Failed to load defaults")
            QMessageBox.critical(self.parent, "Fehler", f"Laden fehlgeschlagen:\n{e}")

    def on_reset_defaults_clicked(self) -> None:
        """Setzt alle Einstellungen auf Factory-Defaults zurück."""
        reply = QMessageBox.question(
            self.parent, "Reset bestätigen",
            "Alle Einstellungen auf Factory-Defaults zurücksetzen?\n\n"
            "Dies setzt die Einstellungen auf optimierte Micro-Account Werte:\n"
            "- Kapital: 100€\n"
            "- Hebel: 20x\n"
            "- Risk/Trade: 50%\n"
            "- Initial SL: 2%\n"
            "- Trailing: ATR-basiert",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.apply_bot_settings(self.FACTORY_DEFAULTS)
        logger.info("Factory-Defaults angewendet")

        QMessageBox.information(
            self.parent, "Reset",
            "Einstellungen wurden auf Micro-Account Factory-Defaults zurückgesetzt."
        )
