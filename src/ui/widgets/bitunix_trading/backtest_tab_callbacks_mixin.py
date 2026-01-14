from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGroupBox,
    QTableWidget, QTableWidgetItem, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFormLayout,
    QMessageBox, QFileDialog, QProgressBar, QTabWidget, QLineEdit,
    QHeaderView,
)

if TYPE_CHECKING:
    from src.core.market_data.history_provider import HistoryManager

logger = logging.getLogger(__name__)


class BacktestTabCallbacksMixin:
    """Button click callbacks and handlers"""

    def _on_batch_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Batch-Test."""
        logger.info("🔄 _on_batch_btn_clicked() - starting batch worker")
        self._log("🔄 Batch-Test wird gestartet...")

        if self._is_running:
            self._log("⚠️ Batch läuft bereits")
            return

        # Parse parameter space aus UI
        param_space_text = self.param_space_text.toPlainText().strip()
        if not param_space_text:
            param_space = {
                "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                "max_leverage": [5, 10, 20],
            }
            self._log("⚠️ Kein Parameter Space angegeben, verwende Standard")
        else:
            try:
                param_space = json.loads(param_space_text)
            except json.JSONDecodeError as exc:
                self._log(f"❌ Ungültiges JSON: {exc}")
                QMessageBox.critical(self, "Fehler", f"Ungültiges JSON für Parameter Space:\n{exc}")
                return

        try:
            base_config = self._build_backtest_config()
        except Exception as exc:
            logger.exception("Failed to build backtest config")
            self._log(f"❌ Fehler beim Erstellen der Backtest-Config: {exc}")
            QMessageBox.critical(self, "Backtest Fehler", str(exc))
            return

        # Determine search method
        method_text = self.batch_method.currentText()
        from src.core.backtesting import BatchConfig, SearchMethod

        if "Grid" in method_text:
            search_method = SearchMethod.GRID
        elif "Random" in method_text:
            search_method = SearchMethod.RANDOM
        else:
            search_method = SearchMethod.BAYESIAN

        # Determine target metric
        target_text = self.batch_target.currentText()
        target_map = {
            "Expectancy": "expectancy",
            "Profit Factor": "profit_factor",
            "Sharpe Ratio": "sharpe_ratio",
            "Min Drawdown": "max_drawdown_pct",
        }
        target_metric = target_map.get(target_text, "expectancy")
        minimize = "Drawdown" in target_text

        batch_config = BatchConfig(
            base_config=base_config,
            parameter_space=param_space,
            search_method=search_method,
            target_metric=target_metric,
            minimize=minimize,
            max_iterations=self.batch_iterations.value(),
        )

        self._log("🧭 Batch-Konfiguration erstellt")
        self._log(f"🔄 Methode: {search_method.value}")
        self._log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
        self._log(f"📋 Parameter Space: {list(param_space.keys()) or ['default']}")

        # Versuche Chart-Daten zu nutzen (User Request)
        initial_data = None
        try:
            chart_window = self._find_chart_window()
            if chart_window and hasattr(chart_window, 'chart_widget') and chart_window.chart_widget.data is not None:
                chart_data = chart_window.chart_widget.data
                if not chart_data.empty:
                    # Kopie erstellen um Original nicht zu verändern
                    initial_data = chart_data.copy()
                    
                    # Check ob timestamp im Index ist
                    if 'timestamp' not in initial_data.columns and initial_data.index.name == 'timestamp':
                        initial_data = initial_data.reset_index()
                        self._log("📊 Timestamp aus Index wiederhergestellt")
                    
                    self._log(f"📊 Nutze geladene Chart-Daten ({len(chart_data)} Bars)")
        except Exception as e:
            logger.warning(f"Could not get chart data: {e}")

        self._is_running = True
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("BATCH")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        self._batch_worker = BatchTestWorker(
            batch_config,
            signal_callback=self._get_signal_callback(initial_data),
            initial_data=initial_data,
            parent=self,
        )
        self._batch_worker.progress.connect(self.progress_updated.emit)
        self._batch_worker.log.connect(self._log)
        self._batch_worker.finished.connect(self._on_batch_worker_finished)
        self._batch_worker.error.connect(self._on_batch_worker_error)
        self._batch_worker.finished.connect(self._batch_worker.deleteLater)
        self._batch_worker.error.connect(self._batch_worker.deleteLater)
        self._batch_worker.start()

    async def _on_batch_clicked(self) -> None:
        """Startet Batch-Test mit Parameter-Optimierung (async)."""
        logger.info("🔄 _on_batch_clicked() called")
        self._log("🔄 Batch-Test async gestartet...")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        logger.info("Starting batch test...")
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("BATCH")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF9800;")

        try:
            # Parse parameter space aus UI
            param_space_text = self.param_space_text.toPlainText().strip()
            if not param_space_text:
                param_space = {
                    "risk_per_trade_pct": [0.5, 1.0, 1.5, 2.0],
                    "max_leverage": [5, 10, 20],
                }
                self._log("⚠️ Kein Parameter Space angegeben, verwende Standard")
            else:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError as e:
                    self._log(f"❌ Ungültiges JSON: {e}")
                    QMessageBox.critical(self, "Fehler", f"Ungültiges JSON für Parameter Space:\n{e}")
                    return

            # Build base config
            base_config = self._build_backtest_config()

            # Determine search method
            method_text = self.batch_method.currentText()
            from src.core.backtesting import BatchRunner, BatchConfig, SearchMethod

            if "Grid" in method_text:
                search_method = SearchMethod.GRID
            elif "Random" in method_text:
                search_method = SearchMethod.RANDOM
            else:
                search_method = SearchMethod.BAYESIAN

            # Determine target metric
            target_text = self.batch_target.currentText()
            target_map = {
                "Expectancy": "expectancy",
                "Profit Factor": "profit_factor",
                "Sharpe Ratio": "sharpe_ratio",
                "Min Drawdown": "max_drawdown_pct",
            }
            target_metric = target_map.get(target_text, "expectancy")
            minimize = "Drawdown" in target_text

            # Create BatchConfig
            batch_config = BatchConfig(
                base_config=base_config,
                parameter_space=param_space,
                search_method=search_method,
                target_metric=target_metric,
                minimize=minimize,
                max_iterations=self.batch_iterations.value(),
            )

            self._log(f"🔄 Starte Batch-Test: {search_method.value}")
            self._log(f"📊 Zielmetrik: {target_metric}, Iterationen: {batch_config.max_iterations}")
            self._log(f"📋 Parameter Space: {list(param_space.keys())}")

            # Create and run BatchRunner
            runner = BatchRunner(
                batch_config,
                signal_callback=self._get_signal_callback(),
            )
            runner.set_progress_callback(lambda p, m: self.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table
            self._update_batch_results_table(runner.results)

            # Log summary
            self._log(f"✅ Batch abgeschlossen: {summary.successful_runs}/{summary.total_runs} erfolgreich")
            if summary.best_run and summary.best_run.metrics:
                best = summary.best_run
                self._log(f"🏆 Bester Run: {best.parameters}")
                self._log(f"   {target_metric}: {getattr(best.metrics, target_metric, 'N/A')}")

            # Offer export
            reply = QMessageBox.question(
                self, "Export",
                f"Batch abgeschlossen!\n\n{summary.successful_runs} erfolgreiche Runs.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.batch_id
                exports = await runner.export_results(output_dir)
                self._log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Batch test failed")
            self._log(f"❌ Batch Fehler: {e}")
            QMessageBox.critical(self, "Batch Fehler", str(e))

        finally:
            self._is_running = False
            self.run_batch_btn.setEnabled(True)
            self.run_wf_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    def _on_wf_btn_clicked(self) -> None:
        """Synchroner Button-Handler, startet async Walk-Forward Test."""
        logger.info("🚶 _on_wf_btn_clicked() - scheduling async walk-forward")
        self._log("🚶 Walk-Forward wird gestartet...")

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._on_wf_clicked())
            else:
                logger.warning("Event loop not running, trying qasync")
                asyncio.ensure_future(self._on_wf_clicked())
        except Exception as e:
            logger.exception(f"Failed to schedule walk-forward: {e}")
            self._log(f"❌ Fehler beim Starten des Walk-Forward: {e}")

    async def _on_wf_clicked(self) -> None:
        """Startet Walk-Forward Analyse mit Rolling Windows (async)."""
        logger.info("🚶 _on_wf_clicked() called")

        if self._is_running:
            logger.info("Already running, returning")
            return

        self._is_running = True
        self.run_batch_btn.setEnabled(False)
        self.run_wf_btn.setEnabled(False)
        self.start_btn.setEnabled(False)
        self.status_label.setText("WALK-FWD")
        self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #9C27B0;")

        try:
            # Build base config
            base_config = self._build_backtest_config()

            # Parse parameter space für Re-Optimization
            param_space_text = self.param_space_text.toPlainText().strip()
            if param_space_text:
                try:
                    param_space = json.loads(param_space_text)
                except json.JSONDecodeError:
                    param_space = {}
            else:
                param_space = {}

            # Walk-Forward Config aus UI
            from src.core.backtesting import WalkForwardRunner, WalkForwardConfig, BatchConfig, SearchMethod

            # BatchConfig für Optimierung erstellen (falls Parameter Space vorhanden)
            batch_config = BatchConfig(
                base_config=base_config,
                search_method=SearchMethod.GRID if param_space else SearchMethod.GRID,
                parameter_space=param_space,
                target_metric="expectancy",
                minimize=False,
            )

            wf_config = WalkForwardConfig(
                base_config=base_config,
                batch_config=batch_config,
                train_window_days=self.wf_train_days.value(),
                test_window_days=self.wf_test_days.value(),
                step_size_days=self.wf_step_days.value(),
                reoptimize_each_fold=self.wf_reoptimize.isChecked(),
            )

            self._log(f"🚶 Starte Walk-Forward Analyse")
            self._log(f"📅 Train: {wf_config.train_window_days}d, Test: {wf_config.test_window_days}d, Step: {wf_config.step_size_days}d")
            self._log(f"🔄 Re-Optimize: {wf_config.reoptimize_each_fold}")

            # Create and run WalkForwardRunner
            runner = WalkForwardRunner(
                wf_config,
                signal_callback=self._get_signal_callback(),
            )
            runner.set_progress_callback(lambda p, m: self.progress_updated.emit(p, m))

            summary = await runner.run()

            # Update results table with fold results
            self._update_wf_results_table(summary.fold_results)

            # Log summary
            self._log(f"✅ Walk-Forward abgeschlossen: {summary.total_folds} Folds")
            self._log(f"📊 Aggregierte OOS-Performance:")
            if summary.aggregated_oos_metrics:
                agg = summary.aggregated_oos_metrics
                self._log(f"   Total Trades: {agg.total_trades}")
                self._log(f"   Win Rate: {agg.win_rate * 100:.1f}%")
                self._log(f"   Profit Factor: {agg.profit_factor:.2f}")
                self._log(f"   Max DD: {agg.max_drawdown_pct:.1f}%")

            # Stability info
            if summary.stable_parameters:
                self._log(f"🔒 Stabile Parameter: {len(summary.stable_parameters)}")
                for param, stability in list(summary.stable_parameters.items())[:3]:
                    self._log(f"   {param}: Stabilität {stability:.1%}")

            # Offer export
            reply = QMessageBox.question(
                self, "Export",
                f"Walk-Forward abgeschlossen!\n\n{summary.total_folds} Folds analysiert.\n\nErgebnisse exportieren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                output_dir = Path("data/backtest_results") / summary.wf_id
                exports = await runner.export_results(output_dir)
                self._log(f"📁 Exportiert nach: {output_dir}")

        except Exception as e:
            logger.exception("Walk-Forward failed")
            self._log(f"❌ Walk-Forward Fehler: {e}")
            QMessageBox.critical(self, "Walk-Forward Fehler", str(e))

        finally:
            self._is_running = False
            self.run_batch_btn.setEnabled(True)
            self.run_wf_btn.setEnabled(True)
            self.start_btn.setEnabled(True)
            self.status_label.setText("IDLE")
            self.status_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #888;")

    def _on_save_template_clicked(self) -> None:
        """
        Speichert die aktuelle Basistabelle als JSON-Template.

        Das Template enthält:
        - Alle Parameter-Spezifikationen
        - Aktuelle Werte aus Engine Settings
        - Metadaten (Timestamp, Name, Beschreibung)
        """
        self._log("💾 Speichere Template...")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()

            if not specs:
                QMessageBox.warning(
                    self, "Keine Daten",
                    "Bitte zuerst Engine Configs laden (Button 'Lade Engine Configs')."
                )
                return

            # Template-Struktur erstellen
            template = {
                'meta': {
                    'created_at': datetime.now().isoformat(),
                    'version': '1.0',
                    'type': 'backtest_config_template',
                    'description': '',
                    'name': '',
                },
                'parameters': {},
                'full_specs': specs,  # Komplette Spezifikation für Wiederherstellung
            }

            # Extrahiere Parameter-Werte
            for spec in specs:
                param_key = spec['parameter']
                template['parameters'][param_key] = {
                    'value': spec['current_value'],
                    'type': spec['type'],
                    'category': spec['category'],
                    'subcategory': spec['subcategory'],
                    'description': spec.get('description', ''),
                    'min': spec['min'],
                    'max': spec['max'],
                    'variations': spec.get('variations', []),
                }

            # Dialog für Template-Name und Beschreibung
            dialog = QDialog(self)
            dialog.setWindowTitle("💾 Template speichern")
            dialog.setMinimumWidth(400)

            dlg_layout = QVBoxLayout(dialog)

            # Name Input
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Name:"))
            name_input = QLineEdit()
            name_input.setPlaceholderText("z.B. 'Aggressive Trend Strategy'")
            name_layout.addWidget(name_input)
            dlg_layout.addLayout(name_layout)

            # Description Input
            desc_layout = QVBoxLayout()
            desc_layout.addWidget(QLabel("Beschreibung:"))
            desc_input = QTextEdit()
            desc_input.setMaximumHeight(80)
            desc_input.setPlaceholderText("Optionale Beschreibung des Templates...")
            desc_layout.addWidget(desc_input)
            dlg_layout.addLayout(desc_layout)

            # Info
            info_label = QLabel(f"📊 {len(specs)} Parameter werden gespeichert.")
            info_label.setStyleSheet("color: #888; font-size: 11px;")
            dlg_layout.addWidget(info_label)

            # Buttons
            btn_box = QDialogButtonBox(
                QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
            )
            btn_box.accepted.connect(dialog.accept)
            btn_box.rejected.connect(dialog.reject)
            dlg_layout.addWidget(btn_box)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Template-Metadaten aktualisieren
            template['meta']['name'] = name_input.text() or f"Template_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            template['meta']['description'] = desc_input.toPlainText()

            # Speichern mit FileDialog
            default_filename = f"backtest_template_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Template speichern",
                str(Path("config/backtest_templates") / default_filename),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filename:
                return

            # Verzeichnis erstellen falls nötig
            Path(filename).parent.mkdir(parents=True, exist_ok=True)

            # Speichern
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(template, f, indent=2, ensure_ascii=False)

            self._log(f"✅ Template gespeichert: {filename}")
            QMessageBox.information(
                self, "Template gespeichert",
                f"Template '{template['meta']['name']}' wurde gespeichert.\n\nDatei: {filename}"
            )

        except Exception as e:
            logger.exception("Failed to save template")
            self._log(f"❌ Template-Speicherung fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Template-Speicherung fehlgeschlagen:\n{e}")
    def _on_load_template_clicked(self) -> None:
        """
        Lädt ein gespeichertes JSON-Template.

        Stellt alle Parameter-Werte aus dem Template wieder her und
        aktualisiert die Basistabelle.
        """
        self._log("📂 Lade Template...")

        try:
            # FileDialog zum Öffnen
            filename, _ = QFileDialog.getOpenFileName(
                self,
                "Template laden",
                str(Path("config/backtest_templates")),
                "JSON Files (*.json);;All Files (*)"
            )

            if not filename:
                return

            # Template laden
            with open(filename, 'r', encoding='utf-8') as f:
                template = json.load(f)

            # Validiere Template-Struktur - Unterstütze V1 (parameters) UND V2 (entry_score, etc.) Format
            is_v1_format = 'parameters' in template
            is_v2_format = 'version' in template and ('entry_score' in template or 'strategy_profile' in template)

            if not is_v1_format and not is_v2_format:
                QMessageBox.warning(
                    self, "Ungültiges Template",
                    "Die ausgewählte Datei ist kein gültiges Backtest-Template.\n\n"
                    "Erwartet: V1-Format mit 'parameters' oder V2-Format mit 'entry_score'/'strategy_profile'."
                )
                return

            meta = template.get('meta', {})

            # V2-Format: Konvertiere zu V1-kompatiblem Format für die UI
            if is_v2_format:
                params = self._convert_v2_to_parameters(template)
                full_specs = []  # V2 hat keine full_specs
                self._log(f"📦 V2-Format erkannt (version: {template.get('version', 'unknown')})")
            else:
                params = template.get('parameters', {})
                full_specs = template.get('full_specs', [])

            # Falls full_specs vorhanden, diese für Tabelle verwenden
            if full_specs:
                specs = full_specs
            else:
                # Rekonstruiere specs aus parameters
                specs = []
                for param_key, param_data in params.items():
                    specs.append({
                        'parameter': param_key,
                        'display_name': param_key.replace('_', ' ').title(),
                        'current_value': param_data.get('value'),
                        'type': param_data.get('type', 'float'),
                        'category': param_data.get('category', 'Unknown'),
                        'subcategory': param_data.get('subcategory', ''),
                        'ui_tab': param_data.get('category', 'Unknown'),
                        'description': param_data.get('description', ''),
                        'min': param_data.get('min'),
                        'max': param_data.get('max'),
                        'variations': param_data.get('variations', []),
                    })

            # Tabelle aktualisieren
            self.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec.get('subcategory', '')}")
                )

                # Parameter
                self.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec.get('display_name', spec.get('parameter', '')))
                )

                # Wert
                value = spec.get('current_value')
                if spec.get('type') == 'float' and value is not None:
                    value_str = f"{value:.2f}"
                else:
                    value_str = str(value)
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#FF9800"))  # Orange für Template-Werte
                self.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec.get('ui_tab', ''))
                )

                # Beschreibung
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)
                self.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec.get('type', ''))
                )

                # Min/Max
                min_val = spec.get('min')
                max_val = spec.get('max')
                if min_val is not None and max_val is not None:
                    minmax_str = f"{min_val}-{max_val}"
                else:
                    minmax_str = "—"
                self.config_inspector_table.setItem(row, 6, QTableWidgetItem(minmax_str))

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.config_inspector_table.setItem(row, 7, QTableWidgetItem(var_str))

            # Parameter Space aus Template-Parametern erstellen
            param_space = {}
            for param_key, param_data in params.items():
                value = param_data.get('value')
                variations = param_data.get('variations', [])
                if variations:
                    param_space[param_key] = variations
                elif value is not None:
                    param_space[param_key] = [value]

            self.param_space_text.setText(json.dumps(param_space, indent=2))

            template_name = meta.get('name', 'Unbekannt')
            template_desc = meta.get('description', '')
            created_at = meta.get('created_at', '')

            self._log(f"✅ Template '{template_name}' geladen")
            self._log(f"   📅 Erstellt: {created_at[:10] if created_at else 'Unbekannt'}")
            self._log(f"   📊 {len(params)} Parameter")

            if template_desc:
                self._log(f"   📝 {template_desc[:50]}...")

        except Exception as e:
            logger.exception("Failed to load template")
            self._log(f"❌ Template-Laden fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Template-Laden fehlgeschlagen:\n{e}")
    def _on_derive_variant_clicked(self) -> None:
        """
        Erstellt eine Variante basierend auf der aktuellen Basistabelle.

        Öffnet einen Dialog zum Anpassen einzelner Parameter-Werte,
        wobei die Basis-Werte als Ausgangspunkt dienen.
        """
        self._log("📝 Variante ableiten...")

        # Prüfe ob Daten in Tabelle vorhanden
        if self.config_inspector_table.rowCount() == 0:
            QMessageBox.warning(
                self, "Keine Basisdaten",
                "Bitte zuerst Engine Configs laden oder ein Template öffnen."
            )
            return

        try:
            # Dialog für Varianten-Erstellung
            dialog = QDialog(self)
            dialog.setWindowTitle("📝 Variante aus Basis ableiten")
            dialog.setMinimumSize(600, 500)

            dlg_layout = QVBoxLayout(dialog)

            # Info
            info = QLabel(
                "Wähle Parameter aus der Basistabelle und passe deren Werte an.\n"
                "Nicht geänderte Werte werden von der Basis übernommen."
            )
            info.setStyleSheet("color: #888; font-size: 11px; margin-bottom: 10px;")
            dlg_layout.addWidget(info)

            # Varianten-Name
            name_layout = QHBoxLayout()
            name_layout.addWidget(QLabel("Varianten-Name:"))
            variant_name_input = QLineEdit()
            variant_name_input.setPlaceholderText("z.B. 'Aggressive V1'")
            name_layout.addWidget(variant_name_input)
            dlg_layout.addLayout(name_layout)

            # Parameter-Editor Tabelle (editierbar!)
            param_table = QTableWidget()
            param_table.setColumnCount(4)
            param_table.setHorizontalHeaderLabels(["Parameter", "Basis-Wert", "Neuer Wert", "Ändern?"])
            param_table.horizontalHeader().setStretchLastSection(True)

            # Extrahiere Parameter aus Basistabelle
            base_params = []
            for row in range(self.config_inspector_table.rowCount()):
                param_item = self.config_inspector_table.item(row, 1)
                value_item = self.config_inspector_table.item(row, 2)
                type_item = self.config_inspector_table.item(row, 5)

                if param_item and value_item:
                    base_params.append({
                        'name': param_item.text(),
                        'value': value_item.text(),
                        'type': type_item.text() if type_item else 'float',
                    })

            param_table.setRowCount(len(base_params))

            for row, param in enumerate(base_params):
                # Parameter-Name (read-only)
                name_item = QTableWidgetItem(param['name'])
                name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                param_table.setItem(row, 0, name_item)

                # Basis-Wert (read-only)
                base_item = QTableWidgetItem(param['value'])
                base_item.setFlags(base_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                base_item.setForeground(QColor("#888"))
                param_table.setItem(row, 1, base_item)

                # Neuer Wert (editierbar)
                new_item = QTableWidgetItem(param['value'])
                new_item.setForeground(QColor("#4CAF50"))
                param_table.setItem(row, 2, new_item)

                # Checkbox "Ändern?"
                checkbox_widget = QWidget()
                checkbox_layout = QHBoxLayout(checkbox_widget)
                checkbox_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                checkbox_layout.setContentsMargins(0, 0, 0, 0)
                checkbox = QCheckBox()
                checkbox_layout.addWidget(checkbox)
                param_table.setCellWidget(row, 3, checkbox_widget)

            dlg_layout.addWidget(param_table)

            # Quick-Actions
            quick_layout = QHBoxLayout()

            # "Alle auswählen" Button
            select_all_btn = QPushButton("Alle auswählen")
            select_all_btn.clicked.connect(
                lambda: self._select_all_variant_checkboxes(param_table, True)
            )
            quick_layout.addWidget(select_all_btn)

            # "Keine auswählen" Button
            select_none_btn = QPushButton("Keine auswählen")
            select_none_btn.clicked.connect(
                lambda: self._select_all_variant_checkboxes(param_table, False)
            )
            quick_layout.addWidget(select_none_btn)

            quick_layout.addStretch()
            dlg_layout.addLayout(quick_layout)

            # Buttons
            btn_box = QDialogButtonBox()

            create_btn = QPushButton("✅ Variante erstellen")
            create_btn.clicked.connect(dialog.accept)
            btn_box.addButton(create_btn, QDialogButtonBox.ButtonRole.AcceptRole)

            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(dialog.reject)
            btn_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

            dlg_layout.addWidget(btn_box)

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            # Variante aus Dialog-Daten erstellen
            variant_name = variant_name_input.text() or f"Variante_{datetime.now().strftime('%H%M%S')}"
            variant_params = {}

            for row in range(param_table.rowCount()):
                checkbox_widget = param_table.cellWidget(row, 3)
                if checkbox_widget:
                    checkbox = checkbox_widget.findChild(QCheckBox)
                    if checkbox and checkbox.isChecked():
                        param_name = param_table.item(row, 0).text()
                        new_value = param_table.item(row, 2).text()

                        # Versuche Wert zu konvertieren
                        try:
                            if '.' in new_value:
                                variant_params[param_name] = float(new_value)
                            elif new_value.isdigit():
                                variant_params[param_name] = int(new_value)
                            elif new_value.lower() in ('true', 'false'):
                                variant_params[param_name] = new_value.lower() == 'true'
                            else:
                                variant_params[param_name] = new_value
                        except ValueError:
                            variant_params[param_name] = new_value

            if not variant_params:
                QMessageBox.warning(
                    self, "Keine Änderungen",
                    "Bitte wähle mindestens einen Parameter zum Ändern aus."
                )
                return

            # Variante zu Parameter-Space hinzufügen
            try:
                current_space_text = self.param_space_text.toPlainText()
                if current_space_text.strip():
                    current_space = json.loads(current_space_text)
                else:
                    current_space = {}
            except json.JSONDecodeError:
                current_space = {}

            # Merge Varianten-Parameter in Space
            for param_name, param_value in variant_params.items():
                if param_name not in current_space:
                    current_space[param_name] = []
                if param_value not in current_space[param_name]:
                    current_space[param_name].append(param_value)

            self.param_space_text.setText(json.dumps(current_space, indent=2))

            self._log(f"✅ Variante '{variant_name}' erstellt mit {len(variant_params)} geänderten Parametern")
            for param, value in list(variant_params.items())[:5]:
                self._log(f"   {param}: {value}")
            if len(variant_params) > 5:
                self._log(f"   ... und {len(variant_params) - 5} weitere")

        except Exception as e:
            logger.exception("Failed to derive variant")
            self._log(f"❌ Varianten-Erstellung fehlgeschlagen: {e}")
            QMessageBox.critical(self, "Fehler", f"Varianten-Erstellung fehlgeschlagen:\n{e}")
    def _on_auto_generate_clicked(self) -> None:
        """
        Generiert automatisch Test-Varianten.

        Erstellt sinnvolle Kombinationen aus:
        - Vordefinierten Indikator-Sets
        - Algorithmisch variierten Parametern
        """
        self._log("🤖 Generiere Test-Varianten...")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()

            # Generiere Varianten
            num_variants = self.batch_iterations.value()
            num_variants = min(num_variants, 20)  # Max 20 für Auto-Generate

            variants = self.generate_ai_test_variants(specs, num_variants)

            # Zeige Dialog mit generierten Varianten
            dialog = QDialog(self)
            dialog.setWindowTitle("🤖 Generierte Test-Varianten")
            dialog.setMinimumSize(700, 500)

            dlg_layout = QVBoxLayout(dialog)

            # Info Label
            info = QLabel(f"✅ {len(variants)} Test-Varianten generiert:")
            info.setStyleSheet("font-weight: bold; color: #4CAF50;")
            dlg_layout.addWidget(info)

            # Varianten-Tabelle
            var_table = QTableWidget()
            var_table.setColumnCount(4)
            var_table.setHorizontalHeaderLabels(["ID", "Name", "Quelle", "Parameter"])
            var_table.horizontalHeader().setStretchLastSection(True)
            var_table.setRowCount(len(variants))

            for row, variant in enumerate(variants):
                var_table.setItem(row, 0, QTableWidgetItem(variant['id']))
                var_table.setItem(row, 1, QTableWidgetItem(variant['name']))
                var_table.setItem(row, 2, QTableWidgetItem(variant['source']))

                params_str = ", ".join([f"{k}={v}" for k, v in list(variant['parameters'].items())[:3]])
                if len(variant['parameters']) > 3:
                    params_str += "..."
                var_table.setItem(row, 3, QTableWidgetItem(params_str))

            dlg_layout.addWidget(var_table)

            # Buttons
            btn_box = QDialogButtonBox()

            use_btn = QPushButton("✅ Als Parameter Space verwenden")
            use_btn.clicked.connect(lambda: self._apply_variants_to_param_space(variants, dialog))
            btn_box.addButton(use_btn, QDialogButtonBox.ButtonRole.AcceptRole)

            export_btn = QPushButton("📄 Als JSON exportieren")
            export_btn.clicked.connect(lambda: self._export_variants_json(variants))
            btn_box.addButton(export_btn, QDialogButtonBox.ButtonRole.ActionRole)

            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(dialog.reject)
            btn_box.addButton(cancel_btn, QDialogButtonBox.ButtonRole.RejectRole)

            dlg_layout.addWidget(btn_box)

            dialog.exec()

        except Exception as e:
            logger.exception("Failed to generate variants")
            self._log(f"❌ Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Varianten-Generierung fehlgeschlagen:\n{e}")
    def _on_load_configs_clicked(self) -> None:
        """
        Lädt Engine-Configs und zeigt sie im Config Inspector an.

        Sammelt alle konfigurierbaren Parameter aus den Engine Settings Tabs
        und zeigt sie in der Tabelle an.
        """
        self._log("📥 Lade Engine Configs...")
        logger.info("Load Configs Button clicked - loading engine configurations")

        try:
            # Sammle Parameter-Spezifikation
            specs = self.get_parameter_specification()
            logger.info(f"Loaded {len(specs)} parameter specifications")

            # Tabelle aktualisieren
            self.config_inspector_table.setRowCount(len(specs))

            for row, spec in enumerate(specs):
                # Kategorie
                self.config_inspector_table.setItem(
                    row, 0, QTableWidgetItem(f"{spec['category']}/{spec['subcategory']}")
                )

                # Parameter
                self.config_inspector_table.setItem(
                    row, 1, QTableWidgetItem(spec['display_name'])
                )

                # Wert
                value_str = str(spec['current_value'])
                if spec['type'] == 'float':
                    value_str = f"{spec['current_value']:.2f}"
                value_item = QTableWidgetItem(value_str)
                value_item.setForeground(QColor("#4CAF50"))
                self.config_inspector_table.setItem(row, 2, value_item)

                # UI-Tab
                self.config_inspector_table.setItem(
                    row, 3, QTableWidgetItem(spec['ui_tab'])
                )

                # Beschreibung (neue Spalte)
                description = spec.get('description', '')
                desc_item = QTableWidgetItem(description[:40] + '...' if len(description) > 40 else description)
                desc_item.setToolTip(description)  # Volle Beschreibung als Tooltip
                self.config_inspector_table.setItem(row, 4, desc_item)

                # Typ
                self.config_inspector_table.setItem(
                    row, 5, QTableWidgetItem(spec['type'])
                )

                # Min/Max
                if spec['min'] is not None and spec['max'] is not None:
                    minmax_str = f"{spec['min']}-{spec['max']}"
                else:
                    minmax_str = "—"
                self.config_inspector_table.setItem(
                    row, 6, QTableWidgetItem(minmax_str)
                )

                # Variationen
                variations = spec.get('variations', [])
                if variations:
                    var_str = ", ".join([str(v)[:6] for v in variations[:4]])
                    if len(variations) > 4:
                        var_str += "..."
                else:
                    var_str = "—"
                self.config_inspector_table.setItem(
                    row, 7, QTableWidgetItem(var_str)
                )

            # Erstelle Parameter-Space aus Configs
            param_space = self.get_parameter_space_from_configs()

            if param_space:
                self.param_space_text.setText(json.dumps(param_space, indent=2))
                self._log(f"✅ {len(specs)} Parameter geladen, {len(param_space)} für Batch-Test")
            else:
                self._log("⚠️ Keine Parameter für Batch-Test verfügbar")

            # Wechsle automatisch zum Batch/WF Tab um die Config-Tabelle zu zeigen
            # Tab 3 ist "🔄 Batch/WF"
            self.sub_tabs.setCurrentIndex(3)
            logger.info("Switched to Batch/WF tab to show Config Inspector")

        except Exception as e:
            logger.exception("Failed to load configs")
            self._log(f"❌ Fehler: {e}")
            QMessageBox.critical(self, "Fehler", f"Config-Laden fehlgeschlagen:\n{e}")
    def _on_indicator_set_changed(self, index: int) -> None:
        """
        Handler für Indikator-Set Auswahl.

        Lädt ein vordefiniertes Indikator-Set und zeigt dessen Parameter an.
        """
        if index == 0:  # "-- Manuell --"
            return

        indicator_sets = self.get_available_indicator_sets()

        # Index anpassen (0 = Manuell, 1+ = Sets)
        set_index = index - 1

        if 0 <= set_index < len(indicator_sets):
            ind_set = indicator_sets[set_index]

            # Erstelle Parameter-Space aus Set
            param_space = {}

            # Weights
            for weight_name, weight_val in ind_set.get('weights', {}).items():
                param_space[f'weight_{weight_name}'] = [weight_val]

            # Andere Settings
            if 'min_score_for_entry' in ind_set:
                param_space['min_score_for_entry'] = [ind_set['min_score_for_entry']]
            if 'gates' in ind_set:
                for gate_name, gate_val in ind_set['gates'].items():
                    param_space[f'gate_{gate_name}'] = [gate_val]
            if 'leverage' in ind_set:
                for lev_name, lev_val in ind_set['leverage'].items():
                    param_space[lev_name] = [lev_val]
            if 'level_settings' in ind_set:
                for lvl_name, lvl_val in ind_set['level_settings'].items():
                    param_space[lvl_name] = [lvl_val]

            self.param_space_text.setText(json.dumps(param_space, indent=2))
            self._log(f"📊 Indikator-Set '{ind_set['name']}' geladen: {ind_set['description']}")

    # =========================================================================
    # TEMPLATE MANAGEMENT HANDLERS
    # =========================================================================
