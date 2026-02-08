from __future__ import annotations

import logging
from pathlib import Path

from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from .chart_js_template import get_chart_html_template
from .embedded_tradingview_bridge import ChartBridge

logger = logging.getLogger(__name__)

class EmbeddedTradingViewChartUIMixin:
    """EmbeddedTradingViewChartUIMixin extracted from EmbeddedTradingViewChart."""
    def _show_error_ui(self):
        """Show error message if WebEngine not available."""
        layout = QVBoxLayout(self)
        error_label = QLabel(
            "⚠️ PyQt6-WebEngine not installed\n\n"
            "Run: pip install PyQt6-WebEngine"
        )
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        error_label.setStyleSheet("color: red; font-size: 14pt;")
        layout.addWidget(error_label)
    def _setup_ui(self):
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar (from ToolbarMixin) - Two rows
        toolbar1, toolbar2 = self._create_toolbar()
        self.toolbar_row1 = toolbar1
        self.toolbar_row2 = toolbar2
        layout.addWidget(toolbar1)
        layout.addWidget(toolbar2)

        # Issue #26: OHLC Info Label (unter Toolbar)
        self.ohlc_info_label = QLabel("O -- | H -- | L -- | C -- | -- % | V --")
        self.ohlc_info_label.setStyleSheet("""
            color: #E0E0E0;
            background-color: #2D2D2D;
            font-family: monospace;
            font-size: 11px;
            font-weight: bold;
            padding: 5px 10px;
            border-bottom: 1px solid #3D3D3D;
        """)
        layout.addWidget(self.ohlc_info_label)

        # Web view for chart
        self.web_view = QWebEngineView()
        self.web_view.loadFinished.connect(self._on_page_loaded)
        # Load template with injected zone primitives
        template_dir = Path(__file__).parent  # points to src/ui/widgets
        base_url = QUrl.fromLocalFile(str(template_dir) + "/")
        self.web_view.setHtml(get_chart_html_template(), base_url)
        layout.addWidget(self.web_view, stretch=1)

        # Setup WebChannel for JavaScript to Python communication
        self._chart_bridge = ChartBridge(self)
        self._chart_bridge.stop_line_moved.connect(self._on_bridge_stop_line_moved)
        self._chart_bridge.zone_deleted.connect(self._on_bridge_zone_deleted)
        # Phase 5.7: Connect zone click handler for level interactions
        if hasattr(self._chart_bridge, "zone_clicked"):
            self._chart_bridge.zone_clicked.connect(self._on_zone_clicked)
        # Issue #24: Connect line draw request handler for label input
        if hasattr(self._chart_bridge, "line_draw_requested"):
            self._chart_bridge.line_draw_requested.connect(self._on_line_draw_requested)
        if hasattr(self._chart_bridge, "vline_draw_requested"):
            self._chart_bridge.vline_draw_requested.connect(self._on_vline_draw_requested)
        # Also expose as self.bridge for compatibility
        self.bridge = self._chart_bridge
        self._web_channel = QWebChannel(self.web_view.page())
        self._web_channel.registerObject("pyBridge", self._chart_bridge)
        self.web_view.page().setWebChannel(self._web_channel)

        # Issue #26: Info panel mit 4 Labels (Last Price, DB Status, Stretch, Price)
        info_layout = QHBoxLayout()

        # Last Price Label (ganz links)
        self.info_label = QLabel("Last Price: --")
        self.info_label.setStyleSheet("""
            color: #aaa;
            font-family: monospace;
            font-size: 10px;
            padding: 5px;
        """)
        info_layout.addWidget(self.info_label)

        # DB Status Label (links, nach Last Price)
        self.db_status_label = QLabel("DB: 0 Einträge")
        self.db_status_label.setStyleSheet("""
            color: #888;
            font-family: monospace;
            font-size: 10px;
            padding: 5px;
        """)
        info_layout.addWidget(self.db_status_label)

        # Stretch (Push price label nach rechts)
        info_layout.addStretch()

        # Price Label (unten rechts) - Zeigt Tagesveränderung seit 0 Uhr
        self.price_info_label = QLabel("Preis: --")
        self.price_info_label.setStyleSheet("""
            color: #26a69a;
            font-family: monospace;
            font-size: 10px;
            font-weight: bold;
            padding: 5px;
        """)
        info_layout.addWidget(self.price_info_label)

        layout.addLayout(info_layout)

        # Setup context menu for chart markings
        self._setup_context_menu()
    def _setup_context_menu(self):
        """Setup context menu for chart marking operations."""
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtCore import Qt

        self.web_view.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.web_view.customContextMenuRequested.connect(self._show_marking_context_menu)

    def _export_chart_with_overlays(self) -> None:
        """Export the current chart (incl. overlays) to a PNG via JS snapshot."""
        try:
            self._save_chart_png()
        except Exception as e:
            logger.error(f"Export failed: {e}", exc_info=True)

    def _export_chart_as_json(self) -> None:
        """Export current chart (candles + drawings) as JSON snapshot.

        Note: Since Lightweight Charts v4+, accessing data from JS side is restricted.
        We combine JS drawings with Python-side candle data (self.data).
        """
        try:
            js = """
            (() => {
                if (!window.chartAPI || !window.chartAPI.exportJson) return null;
                return window.chartAPI.exportJson();
            })();
            """

            def _on_eval_finished(result):
                if not result:
                    logger.warning("Chart JSON export failed (no data from JS)")
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.warning(self, "Export Failed", "Could not retrieve drawing data from chart.")
                    return
                try:
                    import json
                    from pathlib import Path
                    import time as _time

                    # Parse JS result
                    snapshot = json.loads(result)

                    # Inject Python-side data if available (LWC v4+ fix)
                    if hasattr(self, 'data') and self.data is not None and not snapshot.get('series'):
                        try:
                            # Convert DataFrame to records
                            # Check for 'time' column or index
                            df = self.data.copy()
                            if 'time' not in df.columns and hasattr(df.index, 'name') and df.index.name == 'date':
                                df = df.reset_index()
                                df.rename(columns={'date': 'time'}, inplace=True)

                            # Ensure timestamp format compatible with LWC (seconds)
                            if 'time' in df.columns:
                                # Simple check if generic datetime objects need conversion
                                if pd.api.types.is_datetime64_any_dtype(df['time']):
                                    df['time'] = df['time'].astype('int64') // 10**9

                            snapshot['series'] = df.to_dict(orient='records')
                            logger.info(f"Injected {len(snapshot['series'])} candles from Python data")
                        except Exception as e:
                            logger.warning(f"Failed to inject Python data into export: {e}")

                    ts = _time.strftime("%Y%m%d_%H%M%S")
                    export_dir = Path(".AI_Exchange/export")
                    # FIX: Create parent directories if they don't exist
                    export_dir.mkdir(parents=True, exist_ok=True)

                    path = export_dir / f"chart_export_{ts}.json"
                    path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")

                    logger.info(f"Chart JSON export saved to {path}")
                    self._notify_export_success(path, "JSON")

                    # Also export PNG with same timestamp for pairing
                    self._save_chart_png(ts=ts)
                except Exception as e:
                    logger.error(f"Failed to save chart JSON export: {e}", exc_info=True)
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.critical(self, "Export Error", f"Failed to save export:\n{str(e)}")

            self.web_view.page().runJavaScript(js, _on_eval_finished)
        except Exception as e:
            logger.error(f"JSON export failed: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export Error", f"Failed to initiate export:\n{str(e)}")

    def _save_chart_png(self, ts: str | None = None) -> None:
        """Helper: capture chart PNG via JS and save to exports/ with optional timestamp."""
        import time as _time

        ts_used = ts or _time.strftime("%Y%m%d_%H%M%S")

        js = """
        (async () => {
            if (!window.chartAPI || !window.chartAPI.exportPng) {
                return null;
            }
            const dataUrl = await window.chartAPI.exportPng();
            return dataUrl;
        })();
        """

        def _on_png(result):
            if not result:
                logger.warning("Chart PNG export failed (no dataURL)")
                return
            try:
                import base64
                from pathlib import Path

                header = "data:image/png;base64,"
                b64 = result[len(header) :] if result.startswith(header) else result
                png_bytes = base64.b64decode(b64)
                export_dir = Path(".AI_Exchange/export")
                # FIX: Create parent directories
                export_dir.mkdir(parents=True, exist_ok=True)

                path = export_dir / f"chart_export_{ts_used}.png"
                path.write_bytes(png_bytes)
                logger.info(f"Chart export saved to {path}")
                self._notify_export_success(path, "PNG")
            except Exception as e:
                logger.error(f"Failed to save chart export: {e}", exc_info=True)
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.critical(self, "Export Error", f"Failed to save PNG export:\n{str(e)}")

        self.web_view.page().runJavaScript(js, _on_png)

    def _notify_export_success(self, path, kind: str) -> None:
        """Show a small message after export completes."""
        try:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, f"{kind} Export", f"Export gespeichert:\n{path}")
        except Exception:
            print(f"[EXPORT] {kind} saved to {path}", flush=True)

    def _show_marking_context_menu(self, pos):
        """Show context menu for chart markings."""
        from PyQt6.QtWidgets import QMenu, QInputDialog
        from PyQt6.QtGui import QAction
        import time

        menu = QMenu(self)

        zones_at_price = self._get_zones_at_price()
        if zones_at_price:
            self._add_zone_management_menu(menu, zones_at_price)

        # Entry Analyzer (new feature)
        self._add_entry_analyzer_menu(menu)
        menu.addSeparator()

        self._add_entry_menu(menu)
        self._add_zone_menu(menu)
        self._add_structure_menu(menu)
        self._add_lines_menu(menu)

        # Indicators Toggle
        menu.addSeparator()
        self._add_indicators_toggle_menu(menu)

        # Export menu
        export_action = QAction("📤 Chart exportieren (PNG)", self)
        export_action.triggered.connect(self._export_chart_with_overlays)
        menu.addSeparator()
        menu.addAction(export_action)

        export_json_action = QAction("📄 Chart exportieren (JSON)", self)
        export_json_action.triggered.connect(self._export_chart_as_json)
        menu.addAction(export_json_action)

        export_csv_action = QAction("📊 Daten exportieren (CSV)", self)
        export_csv_action.triggered.connect(self._export_data_as_csv)
        menu.addAction(export_csv_action)

        self._add_clear_actions(menu)

        # Chart Markings Manager
        menu.addSeparator()
        manager_action = QAction("📋 Manage All Markings...", self)
        manager_action.triggered.connect(self._show_markings_manager)
        menu.addAction(manager_action)

        menu.exec(self.web_view.mapToGlobal(pos))

    def _export_data_as_csv(self) -> None:
        """Export current chart data (self.data) as CSV.

        Exports the 1-to-1 data used for the chart display.
        """
        try:
            if not hasattr(self, 'data') or self.data is None or self.data.empty:
                from PyQt6.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Export Failed", "No chart data available to export.")
                return

            import time as _time
            from pathlib import Path

            # Construct filename with metadata
            ts = _time.strftime("%Y%m%d_%H%M%S")
            symbol = getattr(self, 'current_symbol', 'UnknownSymbol').replace('/', '_')
            tf = getattr(self, 'current_timeframe', 'UnknownTF')

            filename = f"data_export_{symbol}_{tf}_{ts}.csv"
            export_dir = Path(".AI_Exchange/export")
            export_dir.mkdir(parents=True, exist_ok=True)
            path = export_dir / filename

            # Export DataFrame to CSV
            # self.data is expected to have a DatetimeIndex
            self.data.to_csv(path)

            logger.info(f"Chart data exported to {path}")
            self._notify_export_success(path, "CSV")

        except Exception as e:
            logger.error(f"CSV export failed: {e}", exc_info=True)
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{str(e)}")

    def _get_zones_at_price(self):
        if hasattr(self, "_last_price") and self._last_price is not None:
            return self._zones.get_zones_at_price(self._last_price)
        return []

    def _add_zone_management_menu(self, menu, zones_at_price):
        from PyQt6.QtGui import QAction

        zone_mgmt_menu = menu.addMenu(f"📍 Zones at Price ({len(zones_at_price)})")

        for zone in zones_at_price:
            zone_label = zone.label or zone.id
            zone_type_icon = {
                "support": "🟢",
                "resistance": "🔴",
                "demand": "🟢",
                "supply": "🔴",
            }.get(zone.zone_type.value, "📊")

            # Add lock indicator to submenu title
            lock_icon = "🔒" if zone.is_locked else "🔓"
            zone_submenu = zone_mgmt_menu.addMenu(f"{zone_type_icon} {lock_icon} {zone_label}")

            # Lock/Unlock action (first position)
            lock_action = QAction(
                f"{'🔓 Unlock' if zone.is_locked else '🔒 Lock'} Zone",
                self
            )
            lock_action.triggered.connect(lambda checked, z=zone: self._toggle_zone_lock(z))
            zone_submenu.addAction(lock_action)

            zone_submenu.addSeparator()

            # Edit action (disabled if locked)
            edit_action = QAction("✏️ Edit Zone...", self)
            edit_action.triggered.connect(lambda checked, z=zone: self._edit_zone(z))
            edit_action.setEnabled(not zone.is_locked)
            zone_submenu.addAction(edit_action)

            # Extend action (disabled if locked)
            extend_action = QAction("➡️ Extend to Now", self)
            extend_action.triggered.connect(lambda checked, z=zone: self._extend_zone_to_now(z))
            extend_action.setEnabled(not zone.is_locked)
            zone_submenu.addAction(extend_action)

            zone_submenu.addSeparator()

            # Delete action (NOT disabled - user wants only edit/move locked, not delete)
            delete_action = QAction("🗑️ Delete Zone", self)
            delete_action.triggered.connect(lambda checked, z=zone: self._delete_zone(z))
            zone_submenu.addAction(delete_action)

        menu.addSeparator()

    def _add_entry_menu(self, menu):
        from PyQt6.QtGui import QAction

        entry_menu = menu.addMenu("Add Entry Marker")
        long_action = QAction("Long Entry (Arrow Up)", self)
        long_action.triggered.connect(lambda: self._add_test_entry_marker("long"))
        entry_menu.addAction(long_action)

        short_action = QAction("Short Entry (Arrow Down)", self)
        short_action.triggered.connect(lambda: self._add_test_entry_marker("short"))
        entry_menu.addAction(short_action)

    def _add_zone_menu(self, menu):
        from PyQt6.QtGui import QAction

        zone_menu = menu.addMenu("Add Zone")
        support_action = QAction("🟢 Support Zone", self)
        support_action.triggered.connect(lambda: self._add_test_zone("support"))
        zone_menu.addAction(support_action)

        resistance_action = QAction("🔴 Resistance Zone", self)
        resistance_action.triggered.connect(lambda: self._add_test_zone("resistance"))
        zone_menu.addAction(resistance_action)

        zone_menu.addSeparator()

        demand_action = QAction("🟢 Demand Zone (Bullish)", self)
        demand_action.triggered.connect(lambda: self._add_test_zone("demand"))
        zone_menu.addAction(demand_action)

        supply_action = QAction("🔴 Supply Zone (Bearish)", self)
        supply_action.triggered.connect(lambda: self._add_test_zone("supply"))
        zone_menu.addAction(supply_action)

    def _add_structure_menu(self, menu):
        from PyQt6.QtGui import QAction

        structure_menu = menu.addMenu("Add Structure Break")
        bos_bull_action = QAction("BoS Bullish", self)
        bos_bull_action.triggered.connect(lambda: self._add_test_structure("bos", True))
        structure_menu.addAction(bos_bull_action)

        bos_bear_action = QAction("BoS Bearish", self)
        bos_bear_action.triggered.connect(lambda: self._add_test_structure("bos", False))
        structure_menu.addAction(bos_bear_action)

        choch_bull_action = QAction("CHoCH Bullish", self)
        choch_bull_action.triggered.connect(lambda: self._add_test_structure("choch", True))
        structure_menu.addAction(choch_bull_action)

        choch_bear_action = QAction("CHoCH Bearish", self)
        choch_bear_action.triggered.connect(lambda: self._add_test_structure("choch", False))
        structure_menu.addAction(choch_bear_action)

        structure_menu.addSeparator()

        msb_bull_action = QAction("⬆️ MSB Bullish", self)
        msb_bull_action.triggered.connect(lambda: self._add_test_structure("msb", True))
        structure_menu.addAction(msb_bull_action)

        msb_bear_action = QAction("⬇️ MSB Bearish", self)
        msb_bear_action.triggered.connect(lambda: self._add_test_structure("msb", False))
        structure_menu.addAction(msb_bear_action)

    def _add_lines_menu(self, menu):
        from PyQt6.QtGui import QAction

        lines_menu = menu.addMenu("📏 Add Line")

        vertical_line = QAction("📏 Vertikale Linie", self)
        vertical_line.triggered.connect(self._add_vertical_line_interactive)
        lines_menu.addAction(vertical_line)

        lines_menu.addSeparator()
        sl_long_action = QAction("🔴 Stop Loss (Long Position)", self)
        sl_long_action.triggered.connect(lambda: self._add_test_line("sl", True))
        lines_menu.addAction(sl_long_action)

        sl_short_action = QAction("🔴 Stop Loss (Short Position)", self)
        sl_short_action.triggered.connect(lambda: self._add_test_line("sl", False))
        lines_menu.addAction(sl_short_action)

        lines_menu.addSeparator()

        tp_long_action = QAction("🟢 Take Profit (Long Position)", self)
        tp_long_action.triggered.connect(lambda: self._add_test_line("tp", True))
        lines_menu.addAction(tp_long_action)

        tp_short_action = QAction("🟢 Take Profit (Short Position)", self)
        tp_short_action.triggered.connect(lambda: self._add_test_line("tp", False))
        lines_menu.addAction(tp_short_action)

        lines_menu.addSeparator()

        entry_long_action = QAction("🔵 Entry Line (Long)", self)
        entry_long_action.triggered.connect(lambda: self._add_test_line("entry", True))
        lines_menu.addAction(entry_long_action)

        entry_short_action = QAction("🔵 Entry Line (Short)", self)
        entry_short_action.triggered.connect(lambda: self._add_test_line("entry", False))
        lines_menu.addAction(entry_short_action)

        lines_menu.addSeparator()

        trailing_action = QAction("🟡 Trailing Stop", self)
        trailing_action.triggered.connect(lambda: self._add_test_line("trailing", True))
        lines_menu.addAction(trailing_action)

    def _add_clear_actions(self, menu):
        from PyQt6.QtGui import QAction

        menu.addSeparator()
        clear_markers_action = QAction("Clear All Markers", self)
        clear_markers_action.triggered.connect(self._clear_all_markers)
        menu.addAction(clear_markers_action)

        clear_zones_action = QAction("Clear All Zones", self)
        clear_zones_action.triggered.connect(self._clear_zones_with_js)
        menu.addAction(clear_zones_action)

        clear_lines_action = QAction("Clear All Lines", self)
        clear_lines_action.triggered.connect(self._clear_lines_with_js)
        menu.addAction(clear_lines_action)

        clear_drawings_action = QAction("Clear All Drawings", self)
        clear_drawings_action.triggered.connect(self._clear_all_drawings)
        menu.addAction(clear_drawings_action)

        clear_all_action = QAction("Clear Everything", self)
        clear_all_action.triggered.connect(self._clear_all_markings)
        menu.addAction(clear_all_action)

    def _clear_zones_with_js(self):
        """Clear all zones (Python-managed and JS-side)."""
        self.clear_zones()
        # Also explicitly call JS clearZones for any orphaned zones
        if hasattr(self, '_execute_js'):
            self._execute_js("window.chartAPI?.clearZones();")

    def _clear_lines_with_js(self):
        """Clear all lines (Python-managed and JS-side hlines)."""
        self.clear_stop_loss_lines()
        # Also explicitly call JS clearLines for drawing tool lines
        if hasattr(self, '_execute_js'):
            self._execute_js("window.chartAPI?.clearLines();")

    def _show_markings_manager(self):
        """Show the Chart Markings Manager dialog."""
        from src.ui.dialogs import ChartMarkingsManagerDialog

        dialog = ChartMarkingsManagerDialog(self, self)
        dialog.exec()

    def _add_entry_analyzer_menu(self, menu):
        """Add Entry Analyzer menu item to context menu."""
        from PyQt6.QtGui import QAction

        analyzer_action = QAction("🎯 Analyze Visible Range...", self)
        analyzer_action.triggered.connect(self._show_entry_analyzer)
        menu.addAction(analyzer_action)

    def _show_entry_analyzer(self):
        """Show the Entry Analyzer popup."""
        if hasattr(self, "show_entry_analyzer"):
            self.show_entry_analyzer()
        else:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.warning(
                self,
                "Feature Not Available",
                "Entry Analyzer mixin not loaded.",
            )

    def _add_indicators_toggle_menu(self, menu):
        """Add indicator visibility controls to context menu."""
        try:
            from PyQt6.QtGui import QAction

            # Check if indicators exist
            if not hasattr(self, 'active_indicators'):
                return

            # Get active indicators count
            active_count = len(getattr(self, "active_indicators", {}))
            if active_count == 0:
                return

            indicators_menu = menu.addMenu(f"📊 Indicators ({active_count})")

            # Hide All action
            hide_all_action = QAction("🔒 Hide All Indicators", self)
            hide_all_action.triggered.connect(self._hide_all_indicators)
            indicators_menu.addAction(hide_all_action)

            # Show All action (in case some were hidden)
            show_all_action = QAction("👁️ Show All Indicators", self)
            show_all_action.triggered.connect(self._show_all_indicators)
            indicators_menu.addAction(show_all_action)

            # Individual toggles
            indicators_menu.addSeparator()

            for instance_id, indicator_data in self.active_indicators.items():
                # Extract indicator name and params
                ind_id = indicator_data.get('ind_id', instance_id)
                params = indicator_data.get('params', {})

                # Format display name
                if params:
                    params_str = ', '.join(f"{k}={v}" for k, v in params.items())
                    display_name = f"{ind_id}({params_str})"
                else:
                    display_name = ind_id

                # Add checkbox action for each indicator
                toggle_action = QAction(f"☑️ {display_name}", self)
                toggle_action.setCheckable(True)
                toggle_action.setChecked(indicator_data.get('visible', True))
                toggle_action.triggered.connect(
                    lambda checked, iid=instance_id: self._toggle_indicator_visibility(iid, checked)
                )
                indicators_menu.addAction(toggle_action)
        except Exception as e:
            # Log error but don't break the context menu
            logger.error(f"Error adding indicators toggle menu: {e}", exc_info=True)

    def _hide_all_indicators(self):
        """Hide all active indicators from chart (visual only, keep instance data)."""
        if not hasattr(self, 'active_indicators') or not hasattr(self, '_chart_ops'):
            return

        hidden_count = 0
        for instance_id, inst in list(self.active_indicators.items()):
            try:
                # Mark as hidden
                inst['visible'] = False

                # Remove from chart VISUALLY only (don't delete from active_indicators)
                display_name = inst.get('display_name', instance_id)
                is_overlay = inst.get('is_overlay', True)
                self._chart_ops.remove_indicator_from_chart(instance_id, display_name, is_overlay)

                hidden_count += 1
            except Exception as e:
                logger.warning(f"Could not hide indicator {instance_id}: {e}")

        logger.info(f"Hidden {hidden_count} indicators (kept in active_indicators)")

        # Update button badge
        self._update_indicators_button_badge()

    def _show_all_indicators(self):
        """Show all hidden indicators on chart (re-create visuals with same instance data)."""
        if not hasattr(self, 'active_indicators') or not hasattr(self, '_instance_mgr'):
            return

        shown_count = 0
        for instance_id, inst in self.active_indicators.items():
            try:
                # Check if hidden
                if not inst.get('visible', True):
                    # Re-create chart visual with EXISTING instance data
                    # This keeps the same instance_id and display_name
                    self._instance_mgr.add_indicator_instance_to_chart(inst)
                    inst['visible'] = True
                    shown_count += 1
            except Exception as e:
                logger.warning(f"Could not show indicator {instance_id}: {e}")

        logger.info(f"Shown {shown_count} indicators with existing instance IDs")

        # Update button badge
        self._update_indicators_button_badge()

    def _toggle_indicator_visibility(self, instance_id: str, visible: bool):
        """Toggle visibility of a single indicator (visual only, keep instance data)."""
        if not hasattr(self, 'active_indicators') or not hasattr(self, '_instance_mgr'):
            return

        if instance_id not in self.active_indicators:
            return

        try:
            inst = self.active_indicators[instance_id]

            if visible:
                # Show indicator - re-create visual with EXISTING instance data
                self._instance_mgr.add_indicator_instance_to_chart(inst)
                inst['visible'] = True
                logger.info(f"Showing indicator: {instance_id}")
            else:
                # Hide indicator - remove visual only
                display_name = inst.get('display_name', instance_id)
                is_overlay = inst.get('is_overlay', True)
                self._chart_ops.remove_indicator_from_chart(instance_id, display_name, is_overlay)
                inst['visible'] = False
                logger.info(f"Hiding indicator: {instance_id}")

            # Update button badge
            self._update_indicators_button_badge()

        except Exception as e:
            logger.error(f"Error toggling indicator {instance_id}: {e}")
