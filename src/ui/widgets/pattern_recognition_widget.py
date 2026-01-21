"""Tab 1: Pattern Recognition Widget for Strategy Concept Window."""

from __future__ import annotations

from typing import Optional, List, TYPE_CHECKING
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QProgressBar, QGroupBox, QLabel
)
from PyQt6.QtCore import pyqtSignal, QThread
import asyncio
import logging

from src.ui.widgets.pattern_analysis_widgets import (
    PatternAnalysisSettings,
    PatternResultsDisplay,
    PatternMatchesTable
)
from src.ui.utils.chart_data_helper import ChartDataHelper
from src.core.pattern_db.pattern_service import PatternService
from src.core.pattern_db.pattern_update_worker import PatternUpdateManager
from src.common.event_bus import event_bus, EventType, Event
from datetime import datetime, timedelta

if TYPE_CHECKING:
    from src.analysis.patterns.base_detector import Pattern

logger = logging.getLogger(__name__)


class PatternAnalysisThread(QThread):
    """Background thread for running async pattern analysis."""

    # Signals
    progress_updated = pyqtSignal(int, str)  # (percentage, status_message)
    analysis_completed = pyqtSignal(object)  # PatternAnalysis result
    analysis_failed = pyqtSignal(str)  # Error message

    def __init__(self, bars, symbol, timeframe, settings):
        super().__init__()
        self.bars = bars
        self.symbol = symbol
        self.timeframe = timeframe
        self.settings = settings
        self.window_size = len(bars)

    def run(self):
        """Run pattern analysis in background thread with its own event loop."""
        try:
            # Step 1: Initialize PatternService (30%)
            self.progress_updated.emit(
                30,
                f"⚙️ Initialisiere Pattern Service ({self.window_size} bars)..."
            )

            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # Step 2: Run analysis (50%)
            self.progress_updated.emit(50, "🔎 Analysiere Patterns...")

            try:
                analysis = loop.run_until_complete(self._run_async_analysis())

                # Step 3: Analysis complete
                self.progress_updated.emit(
                    80,
                    f"📈 Analyse abgeschlossen - {analysis.similar_patterns_count} ähnliche Patterns gefunden"
                )
                self.analysis_completed.emit(analysis)

            finally:
                loop.close()

        except Exception as e:
            error_msg = f"Pattern analysis failed: {e}"
            logger.exception(error_msg)
            print(f"❌ FEHLER: {error_msg}")  # Print to console/CMD
            self.analysis_failed.emit(str(e))

    async def _run_async_analysis(self):
        """Async pattern analysis logic."""
        service = PatternService(
            window_size=self.window_size,
            min_similar_patterns=self.settings['min_matches'],
            similarity_threshold=self.settings['similarity_threshold']
        )
        await service.initialize()

        # Phase 3: Use partial pattern matching if enabled
        if self.settings.get('enable_partial', False):
            # Calculate minimum bars required based on percentage
            min_completion_pct = self.settings.get('min_completion_pct', 50)
            min_bars = max(int(self.window_size * min_completion_pct / 100), 10)

            # Use partial matching (allows incomplete patterns)
            return await service.analyze_partial_signal(
                bars=self.bars,
                symbol=self.symbol,
                timeframe=self.timeframe,
                signal_direction=self.settings['signal_direction'],
                cross_symbol_search=self.settings['cross_symbol'],
                target_timeframe=self.settings.get('target_timeframe')
            )
        else:
            # Use standard full-pattern matching
            return await service.analyze_signal(
                bars=self.bars,
                symbol=self.symbol,
                timeframe=self.timeframe,
                signal_direction=self.settings['signal_direction'],
                cross_symbol_search=self.settings['cross_symbol'],
                target_timeframe=self.settings.get('target_timeframe')  # Phase 2
            )


class PatternRecognitionWidget(QWidget):
    """Tab 1: Pattern Recognition using existing PatternService and shared widgets."""

    patterns_detected = pyqtSignal(list)  # Emits List[Pattern]
    analysis_completed = pyqtSignal(object)  # Emits PatternAnalysis

    def __init__(self, parent=None, chart_window=None):
        super().__init__(parent)
        self.chart_window = chart_window
        self.detected_patterns: List[Pattern] = []
        self.current_analysis = None

        # Pattern Update Manager for database refresh
        self.update_manager = PatternUpdateManager()

        # Event Bus Integration (Phase 1)
        self._last_market_bar_time = None
        self._auto_update_enabled = False
        self._auto_update_interval = timedelta(minutes=5)  # Update every 5 minutes
        self._pending_bars_count = 0
        self._pending_bars_threshold = 5  # Auto-update after 5 new bars

        self._setup_ui()
        self._setup_event_subscriptions()

    def closeEvent(self, event):
        """Clean up resources when widget is closed."""
        # Unsubscribe from event bus
        self._unsubscribe_events()

        # Stop update worker if running
        if self.update_manager.is_running:
            logger.info("Stopping Pattern Update Worker on widget close...")
            self.update_manager.stop()

        event.accept()

    def _setup_ui(self):
        """Setup UI with two-column layout (30% left, 70% right)."""
        main_layout = QHBoxLayout(self)

        # Left column (30%) - Settings and Results
        left_column = QWidget()
        left_column.setMaximumWidth(400)
        left_layout = QVBoxLayout(left_column)

        # Header
        header = QLabel("🔍 Pattern Recognition")
        header.setProperty("class", "header")
        left_layout.addWidget(header)

        # Pattern analysis settings
        settings_group = QGroupBox("Analysis Settings")
        settings_layout = QVBoxLayout(settings_group)
        self.settings = PatternAnalysisSettings(parent=self)
        settings_layout.addWidget(self.settings)
        left_layout.addWidget(settings_group)

        # Analyze button + progress
        self.analyze_btn = QPushButton("🔍 Analyze Patterns")
        self.analyze_btn.setProperty("class", "primary")
        self.analyze_btn.clicked.connect(self._on_analyze_clicked)
        left_layout.addWidget(self.analyze_btn)

        # Progress area (status label + progress bar)
        progress_group = QGroupBox("Analysis Progress")
        progress_layout = QVBoxLayout(progress_group)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setProperty("class", "status-label")
        progress_layout.addWidget(self.status_label)

        # Progress bar
        self.progress = QProgressBar()
        # Theme handles styling
        self.progress.setVisible(False)
        progress_layout.addWidget(self.progress)

        progress_group.setVisible(False)  # Hidden initially
        self.progress_group = progress_group
        left_layout.addWidget(progress_group)

        # Results display
        results_group = QGroupBox("Analysis Results")
        results_layout = QVBoxLayout(results_group)
        self.results = PatternResultsDisplay(parent=self)
        results_layout.addWidget(self.results)
        left_layout.addWidget(results_group)

        # Action buttons
        action_layout = QHBoxLayout()

        self.draw_btn = QPushButton("📍 Draw")
        self.draw_btn.setProperty("class", "info")
        self.draw_btn.clicked.connect(self._on_draw_patterns_clicked)
        self.draw_btn.setEnabled(False)
        action_layout.addWidget(self.draw_btn)

        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setProperty("class", "danger")
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        action_layout.addWidget(self.clear_btn)

        self.export_btn = QPushButton("💾 Export")
        self.export_btn.setProperty("class", "success")
        self.export_btn.clicked.connect(self._on_export_clicked)
        self.export_btn.setEnabled(False)
        action_layout.addWidget(self.export_btn)

        left_layout.addLayout(action_layout)

        # Database refresh section
        db_group = QGroupBox("Database Management")
        db_layout = QVBoxLayout(db_group)

        # Refresh button
        self.refresh_db_btn = QPushButton("🔄 Refresh Database")
        self.refresh_db_btn.setProperty("class", "warning")
        self.refresh_db_btn.clicked.connect(self._on_refresh_database_clicked)
        db_layout.addWidget(self.refresh_db_btn)

        # Database update progress
        self.db_status_label = QLabel("Database Status: Ready")
        self.db_status_label.setProperty("class", "status-label")
        db_layout.addWidget(self.db_status_label)

        self.db_progress = QProgressBar()
        # Theme handles styling
        self.db_progress.setVisible(False)
        db_layout.addWidget(self.db_progress)

        db_group.setVisible(True)
        left_layout.addWidget(db_group)

        left_layout.addStretch()

        # Right column (70%) - Matches Table
        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)

        matches_label = QLabel("Similar Patterns (Historical)")
        matches_label.setProperty("class", "header")
        right_layout.addWidget(matches_label)

        self.matches_table = PatternMatchesTable(parent=self)
        self.matches_table.itemDoubleClicked.connect(self._on_pattern_double_clicked)
        right_layout.addWidget(self.matches_table)

        # Add columns to main layout with proportions
        main_layout.addWidget(left_column, 30)  # 30% width
        main_layout.addWidget(right_column, 70)  # 70% width

    def _on_analyze_clicked(self):
        """Run pattern analysis using background thread."""
        try:
            # Step 1: Initialize (0%)
            self._update_progress(0, "🔍 Initialisiere Analyse...")
            self.progress_group.setVisible(True)
            self.progress.setVisible(True)
            self.progress.setRange(0, 100)
            self.analyze_btn.setEnabled(False)

            # Debug: Check chart_window availability
            if self.chart_window is None:
                logger.error("chart_window is None in PatternRecognitionWidget")
                print("❌ FEHLER: chart_window is None")
            else:
                logger.info(f"chart_window available: {type(self.chart_window).__name__}")
                if hasattr(self.chart_window, 'chart_widget'):
                    logger.info(f"chart_widget available: {type(self.chart_window.chart_widget).__name__}")
                else:
                    logger.warning("chart_window has no chart_widget attribute")
                    print("⚠️ WARNUNG: chart_window has no chart_widget attribute")

            # Step 2: Load chart data (10%)
            self._update_progress(10, "📊 Lade Chart-Daten...")
            settings = self.settings.get_settings()
            bars, symbol, timeframe = ChartDataHelper.get_bars_from_chart(
                self,
                window_size=None  # Use all visible bars from chart
            )

            if bars is None:
                logger.error("No chart data available for pattern analysis")
                print("❌ FEHLER: No chart data available")
                QMessageBox.warning(
                    self,
                    "No Data",
                    "No chart data available for pattern analysis."
                )
                self.progress_group.setVisible(False)
                self.analyze_btn.setEnabled(True)
                return

            # Calculate actual window size from extracted bars
            actual_window_size = len(bars)
            logger.info(f"Using {actual_window_size} bars from visible chart")
            print(f"✓ Lade {actual_window_size} bars von Chart")

            # Create and start analysis thread
            self.analysis_thread = PatternAnalysisThread(bars, symbol, timeframe, settings)
            self.analysis_thread.progress_updated.connect(self._on_thread_progress_updated)
            self.analysis_thread.analysis_completed.connect(self._on_thread_analysis_completed)
            self.analysis_thread.analysis_failed.connect(self._on_thread_analysis_failed)
            self.analysis_thread.finished.connect(self._on_thread_finished)

            logger.info("Starting pattern analysis thread...")
            print("🔄 Starte Pattern-Analyse Thread...")
            self.analysis_thread.start()

        except Exception as e:
            error_msg = f"Failed to start pattern analysis: {e}"
            logger.exception(error_msg)
            print(f"❌ FEHLER: {error_msg}")
            self._update_progress(0, f"❌ Fehler: {str(e)[:50]}...")
            QMessageBox.critical(
                self,
                "Analysis Error",
                f"Failed to start pattern analysis:\n{e}"
            )
            self.analyze_btn.setEnabled(True)
            self.progress_group.setVisible(False)

    def _on_thread_progress_updated(self, percentage: int, status: str):
        """Handle progress updates from analysis thread."""
        self._update_progress(percentage, status)
        logger.debug(f"Progress: {percentage}% - {status}")

    def _on_thread_analysis_completed(self, analysis):
        """Handle successful analysis completion from thread."""
        try:
            # Step 5: Process results (80%)
            self._update_progress(80, "📈 Verarbeite Ergebnisse...")

            # Store results
            self.current_analysis = analysis

            # Display results
            self.results.update_from_analysis(analysis)
            self.matches_table.populate_from_matches(analysis.best_matches)

            # Enable action buttons
            self.draw_btn.setEnabled(True)
            self.export_btn.setEnabled(True)

            # Emit signal
            self.analysis_completed.emit(analysis)

            # Step 6: Complete (100%)
            self._update_progress(
                100,
                f"✓ Analyse abgeschlossen - {analysis.similar_patterns_count} ähnliche Patterns gefunden"
            )

            logger.info(f"Pattern analysis completed: {analysis.similar_patterns_count} matches")
            print(f"✓ Analyse abgeschlossen: {analysis.similar_patterns_count} Patterns gefunden")

        except Exception as e:
            error_msg = f"Failed to process analysis results: {e}"
            logger.exception(error_msg)
            print(f"❌ FEHLER: {error_msg}")
            self._update_progress(0, f"❌ Fehler: {str(e)[:50]}...")

    def _on_thread_analysis_failed(self, error_message: str):
        """Handle analysis failure from thread."""
        logger.error(f"Pattern analysis failed: {error_message}")
        print(f"❌ FEHLER: Pattern analysis failed: {error_message}")
        self._update_progress(0, f"❌ Fehler: {error_message[:50]}...")
        QMessageBox.critical(
            self,
            "Analysis Error",
            f"Pattern analysis failed:\n{error_message}"
        )

    def _on_thread_finished(self):
        """Handle thread cleanup when finished."""
        logger.info("Analysis thread finished")
        print("✓ Analyse Thread beendet")
        self.analyze_btn.setEnabled(True)

    def _update_progress(self, value: int, status: str):
        """Update progress bar and status label.

        Args:
            value: Progress percentage (0-100)
            status: Status message to display
        """
        self.progress.setValue(value)
        self.status_label.setText(status)
        self.status_label.setStyleSheet(
            "font-size: 12px; color: #26a69a; padding: 5px; font-weight: bold;"
            if value == 100
            else "font-size: 12px; color: #b0b0b0; padding: 5px;"
        )
        # Force UI update
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    def _on_pattern_double_clicked(self, item):
        """Show pattern details (Strategy Concept specific)."""
        row = item.row()
        symbol = self.matches_table.item(row, 0).text()
        date = self.matches_table.item(row, 2).text()
        similarity = self.matches_table.item(row, 3).text()
        trend = self.matches_table.item(row, 4).text()
        return_pct = self.matches_table.item(row, 6).text()

        # TODO: Show detailed pattern visualization dialog
        QMessageBox.information(
            self,
            "Pattern Details",
            f"Similar Pattern:\n\n"
            f"Symbol: {symbol}\n"
            f"Date: {date}\n"
            f"Similarity: {similarity}\n"
            f"Trend: {trend}\n"
            f"Return: {return_pct}\n\n"
            f"Detailed visualization coming in Phase 3..."
        )

    def _on_draw_patterns_clicked(self):
        """Draw detected patterns on chart."""
        if not self.detected_patterns:
            QMessageBox.information(
                self,
                "No Patterns",
                "No patterns detected yet. Run analysis first."
            )
            return

        # TODO: Integrate with chart overlay (from Entry Analyzer MVP)
        QMessageBox.information(
            self,
            "Draw Patterns",
            f"Drawing {len(self.detected_patterns)} patterns on chart...\n\n"
            f"Chart integration coming in Phase 5."
        )

    def _on_clear_clicked(self):
        """Clear all results."""
        self.detected_patterns.clear()
        self.current_analysis = None
        self.results.clear()
        self.matches_table.clear_table()
        self.draw_btn.setEnabled(False)
        self.export_btn.setEnabled(False)

    def _on_export_clicked(self):
        """Export detected patterns."""
        if not self.current_analysis:
            QMessageBox.information(
                self,
                "No Analysis",
                "No analysis results to export. Run analysis first."
            )
            return

        # TODO: Implement pattern export (JSON/CSV)
        QMessageBox.information(
            self,
            "Export Patterns",
            f"Exporting {self.current_analysis.similar_patterns_count} pattern matches...\n\n"
            f"Export functionality coming in Phase 4."
        )

    # === Database Refresh Methods ===

    def _on_refresh_database_clicked(self):
        """Refresh pattern database by filling gaps."""
        try:
            # Disable button during update
            self.refresh_db_btn.setEnabled(False)
            self.db_progress.setVisible(True)
            self.db_progress.setRange(0, 0)  # Indeterminate progress

            # Get current chart symbol and timeframe
            symbol = None
            timeframe = None

            if self.chart_window and hasattr(self.chart_window, 'chart_widget'):
                try:
                    # Try to get symbol/timeframe from chart
                    if hasattr(self.chart_window.chart_widget, 'symbol'):
                        symbol = self.chart_window.chart_widget.symbol
                    if hasattr(self.chart_window.chart_widget, 'timeframe'):
                        timeframe = self.chart_window.chart_widget.timeframe
                except Exception as e:
                    logger.warning(f"Could not get symbol/timeframe from chart: {e}")

            # Use default symbols/timeframes if not available from chart
            symbols = [symbol] if symbol else ["BTCUSDT", "ETHUSDT"]
            timeframes = [timeframe] if timeframe else ["1m", "5m", "15m"]

            # Start update worker
            logger.info(f"Starting database refresh for {symbols} x {timeframes}")
            self._update_db_status("🔄 Starting database refresh...")

            # Connect worker signals
            if self.update_manager.worker:
                self.update_manager.worker.progress.connect(self._on_db_update_progress)
                self.update_manager.worker.update_completed.connect(self._on_db_symbol_completed)
                self.update_manager.worker.error_occurred.connect(self._on_db_update_error)
                self.update_manager.worker.scan_completed.connect(self._on_db_scan_completed)

            # Start worker (this will trigger immediate scan)
            success = self.update_manager.start(
                symbols=symbols,
                timeframes=timeframes,
                scan_interval=300  # 5 minutes between scans
            )

            if success:
                self._update_db_status("🔄 Scanning for gaps...")
            else:
                self._update_db_status("❌ Failed to start update worker")
                self.refresh_db_btn.setEnabled(True)
                self.db_progress.setVisible(False)

        except Exception as e:
            error_msg = f"Failed to start database refresh: {e}"
            logger.exception(error_msg)
            QMessageBox.critical(
                self,
                "Database Refresh Error",
                f"Failed to start database refresh:\n{e}"
            )
            self.refresh_db_btn.setEnabled(True)
            self.db_progress.setVisible(False)

    def _on_db_update_progress(self, status: str, current: int, total: int):
        """Handle database update progress from worker.

        Args:
            status: Status message (e.g., "BTCUSDT 1m: 📥 Filling gap...")
            current: Current progress value
            total: Total progress value
        """
        self._update_db_status(status)

        # Set determinate progress if total > 0
        if total > 0:
            self.db_progress.setRange(0, total)
            self.db_progress.setValue(current)
        else:
            # Indeterminate progress
            self.db_progress.setRange(0, 0)

        logger.debug(f"DB Progress: {current}/{total} - {status}")

    def _on_db_symbol_completed(self, symbol: str, timeframe: str, patterns_inserted: int):
        """Handle completion of single symbol/timeframe update.

        Args:
            symbol: Completed symbol
            timeframe: Completed timeframe
            patterns_inserted: Number of patterns inserted
        """
        logger.info(f"✅ Completed {symbol} {timeframe}: {patterns_inserted} patterns")
        self._update_db_status(f"✅ {symbol} {timeframe}: {patterns_inserted} patterns")

    def _on_db_update_error(self, symbol: str, timeframe: str, error_msg: str):
        """Handle database update error.

        Args:
            symbol: Symbol with error
            timeframe: Timeframe with error
            error_msg: Error message
        """
        logger.error(f"❌ Error for {symbol} {timeframe}: {error_msg}")
        self._update_db_status(f"❌ {symbol} {timeframe}: {error_msg[:50]}")

    def _on_db_scan_completed(self, symbols_scanned: int, total_patterns: int):
        """Handle completion of full database scan.

        Args:
            symbols_scanned: Number of symbol/timeframe pairs scanned
            total_patterns: Total patterns inserted
        """
        logger.info(f"✅ Database refresh completed: {symbols_scanned} pairs, {total_patterns} patterns")

        # Update UI
        self._update_db_status(
            f"✅ Refresh complete: {total_patterns:,} patterns added"
        )
        self.db_progress.setVisible(False)
        self.refresh_db_btn.setEnabled(True)

        # Show completion message
        QMessageBox.information(
            self,
            "Database Refresh Complete",
            f"Successfully refreshed database:\n\n"
            f"Symbol/Timeframe pairs: {symbols_scanned}\n"
            f"New patterns inserted: {total_patterns:,}\n\n"
            f"The worker will continue running in the background,\n"
            f"automatically checking for gaps every 5 minutes."
        )

    def _update_db_status(self, status: str):
        """Update database status label.

        Args:
            status: Status message
        """
        self.db_status_label.setText(f"Database Status: {status}")

        # Style based on status
        if "✅" in status or "complete" in status.lower():
            color = "#26a69a"  # Green
        elif "❌" in status or "error" in status.lower():
            color = "#ef5350"  # Red
        elif "🔄" in status:
            color = "#ffa726"  # Orange
        else:
            color = "#b0b0b0"  # Gray

        self.db_status_label.setStyleSheet(
            f"font-size: 11px; color: {color}; padding: 5px; font-weight: bold;"
        )

        # Force UI update
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()

    # ========================================================================
    # EVENT BUS INTEGRATION (Phase 1 - Live Data Updates)
    # ========================================================================

    def _setup_event_subscriptions(self):
        """Subscribe to event bus for auto-updates on new market data."""
        try:
            # Subscribe to MARKET_BAR for automatic pattern DB updates
            event_bus.subscribe(EventType.MARKET_BAR, self._on_market_bar)

            # Subscribe to pattern DB update events for progress tracking
            event_bus.subscribe(EventType.PATTERN_DB_UPDATE_STARTED, self._on_db_update_started)
            event_bus.subscribe(EventType.PATTERN_DB_UPDATE_PROGRESS, self._on_db_update_progress)
            event_bus.subscribe(EventType.PATTERN_DB_UPDATE_COMPLETE, self._on_db_update_complete)
            event_bus.subscribe(EventType.PATTERN_DB_UPDATE_ERROR, self._on_db_update_error)

            logger.info("Event bus subscriptions established for Pattern Recognition Widget")

        except Exception as e:
            logger.error(f"Failed to set up event subscriptions: {e}", exc_info=True)

    def _unsubscribe_events(self):
        """Unsubscribe from all event bus events."""
        try:
            event_bus.unsubscribe(EventType.MARKET_BAR, self._on_market_bar)
            event_bus.unsubscribe(EventType.PATTERN_DB_UPDATE_STARTED, self._on_db_update_started)
            event_bus.unsubscribe(EventType.PATTERN_DB_UPDATE_PROGRESS, self._on_db_update_progress)
            event_bus.unsubscribe(EventType.PATTERN_DB_UPDATE_COMPLETE, self._on_db_update_complete)
            event_bus.unsubscribe(EventType.PATTERN_DB_UPDATE_ERROR, self._on_db_update_error)

            logger.info("Event bus unsubscribed for Pattern Recognition Widget")

        except Exception as e:
            logger.error(f"Error unsubscribing from events: {e}", exc_info=True)

    def _on_market_bar(self, event: Event):
        """Handle MARKET_BAR event - trigger auto-update if conditions met.

        Auto-update triggers when:
        1. Auto-update is enabled
        2. At least 5 new bars have been received OR
        3. At least 5 minutes have passed since last update

        Args:
            event: Market bar event with new OHLCV data
        """
        try:
            if not self._auto_update_enabled:
                return

            # Get chart window's symbol to filter events
            if self.chart_window and hasattr(self.chart_window, 'symbol'):
                chart_symbol = self.chart_window.symbol
                event_symbol = event.data.get("symbol")

                if event_symbol and event_symbol != chart_symbol:
                    return  # Ignore events for other symbols

            # Track new bars
            self._pending_bars_count += 1
            current_time = datetime.now()

            # Check if update should be triggered
            should_update = False

            # Condition 1: Enough new bars accumulated
            if self._pending_bars_count >= self._pending_bars_threshold:
                should_update = True
                reason = f"{self._pending_bars_count} new bars"

            # Condition 2: Time-based update
            if self._last_market_bar_time:
                time_elapsed = current_time - self._last_market_bar_time
                if time_elapsed >= self._auto_update_interval:
                    should_update = True
                    reason = f"{time_elapsed.total_seconds() / 60:.1f} minutes elapsed"

            # Trigger update if conditions met
            if should_update:
                logger.info(f"Auto-update triggered: {reason}")

                # Emit update request event
                event_bus.emit(Event(
                    type=EventType.PATTERN_DB_UPDATE_REQUESTED,
                    timestamp=current_time,
                    data={
                        "symbol": event.data.get("symbol"),
                        "timeframe": event.data.get("timeframe"),
                        "trigger": "auto",
                        "reason": reason
                    },
                    source="pattern_recognition_widget"
                ))

                # Trigger background update
                self._trigger_background_update()

                # Reset counters
                self._pending_bars_count = 0
                self._last_market_bar_time = current_time

        except Exception as e:
            logger.error(f"Error handling MARKET_BAR event: {e}", exc_info=True)

    def _trigger_background_update(self):
        """Trigger background pattern DB update via UpdateManager."""
        try:
            if not self.update_manager.is_running:
                logger.warning("Update manager not running, starting it now...")
                self.update_manager.start()

            # Get chart context
            if self.chart_window:
                symbol = getattr(self.chart_window, 'symbol', None)
                timeframe = getattr(self.chart_window, 'timeframe', None)

                if symbol and timeframe:
                    logger.info(f"Triggering background update for {symbol}/{timeframe}")

                    # The update manager will handle the update in background
                    # and emit progress events that we're subscribed to
                else:
                    logger.warning("Cannot trigger update: symbol/timeframe not available")

        except Exception as e:
            logger.error(f"Error triggering background update: {e}", exc_info=True)

    def _on_db_update_started(self, event: Event):
        """Handle PATTERN_DB_UPDATE_STARTED event."""
        try:
            self._update_db_status("🔄 Database update started...")
            self.db_progress.setVisible(True)
            self.db_progress.setValue(0)

            logger.info("Pattern DB update started")

        except Exception as e:
            logger.error(f"Error handling DB update started: {e}", exc_info=True)

    def _on_db_update_progress(self, event: Event):
        """Handle PATTERN_DB_UPDATE_PROGRESS event."""
        try:
            progress = event.data.get("progress", 0)
            status = event.data.get("status", "Updating...")

            self.db_progress.setValue(int(progress))
            self._update_db_status(f"🔄 {status}")

            logger.debug(f"Pattern DB update progress: {progress}%")

        except Exception as e:
            logger.error(f"Error handling DB update progress: {e}", exc_info=True)

    def _on_db_update_complete(self, event: Event):
        """Handle PATTERN_DB_UPDATE_COMPLETE event."""
        try:
            patterns_added = event.data.get("patterns_added", 0)

            self._update_db_status(f"✅ Update complete: {patterns_added:,} patterns added")
            self.db_progress.setVisible(False)

            logger.info(f"Pattern DB update complete: {patterns_added} patterns added")

            # Auto-refresh analysis if active
            if self.current_analysis and self._auto_update_enabled:
                logger.info("Auto-refreshing pattern analysis after DB update...")
                self._on_analyze_clicked()

        except Exception as e:
            logger.error(f"Error handling DB update complete: {e}", exc_info=True)

    def _on_db_update_error(self, event: Event):
        """Handle PATTERN_DB_UPDATE_ERROR event."""
        try:
            error = event.data.get("error", "Unknown error")

            self._update_db_status(f"❌ Update failed: {error}")
            self.db_progress.setVisible(False)

            logger.error(f"Pattern DB update error: {error}")

        except Exception as e:
            logger.error(f"Error handling DB update error: {e}", exc_info=True)

    def enable_auto_update(self, enabled: bool = True):
        """Enable or disable automatic pattern DB updates.

        Args:
            enabled: True to enable auto-updates, False to disable
        """
        self._auto_update_enabled = enabled
        logger.info(f"Auto-update {'enabled' if enabled else 'disabled'}")

    def set_auto_update_interval(self, minutes: int):
        """Set the auto-update interval in minutes.

        Args:
            minutes: Update interval in minutes (default: 5)
        """
        self._auto_update_interval = timedelta(minutes=minutes)
        logger.info(f"Auto-update interval set to {minutes} minutes")

    def set_pending_bars_threshold(self, bars: int):
        """Set the threshold for triggering updates based on new bars.

        Args:
            bars: Number of new bars before triggering update (default: 5)
        """
        self._pending_bars_threshold = bars
        logger.info(f"Pending bars threshold set to {bars} bars")
