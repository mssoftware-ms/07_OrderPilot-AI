"""
EquityCurveWidget - Lightweight-Charts basiertes Equity Curve Display

Zeigt die Equity Curve und Trade-Marker für Backtest-Ergebnisse.
Verwendet das gleiche Lightweight-Charts wie die Haupt-Chart-Widgets.

Features:
- Area Chart für Equity Curve
- Drawdown Overlay (optional)
- Trade Marker (Entry/Exit mit P&L Farbe)
- Benchmark-Linie (Buy & Hold)
- Responsive und interaktiv
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QObject
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtWebEngineCore import QWebEngineSettings
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QCheckBox,
    QFrame,
)

if TYPE_CHECKING:
    from src.core.models.backtest_models import BacktestResult, EquityPoint, Trade

logger = logging.getLogger(__name__)


class EquityCurveBridge(QObject):
    """Bridge für Python ↔ JavaScript Kommunikation."""

    # Signals
    dataReady = pyqtSignal(str)  # JSON data
    settingsChanged = pyqtSignal(str)  # Settings JSON

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = {}

    @pyqtSlot(str)
    def setEquityData(self, json_str: str) -> None:
        """Setzt Equity-Daten für JavaScript."""
        self._data = json.loads(json_str)
        self.dataReady.emit(json_str)

    @pyqtSlot(result=str)
    def getData(self) -> str:
        """Gibt aktuelle Daten als JSON zurück."""
        return json.dumps(self._data)


class EquityCurveWidget(QWidget):
    """Widget für Equity Curve Visualisierung.

    Zeigt die Entwicklung des Portfoliowerts über Zeit mit:
    - Area Chart (Equity)
    - Optionaler Drawdown-Bereich
    - Trade-Marker
    - Benchmark (optional)

    Usage:
        widget = EquityCurveWidget()
        widget.load_equity_curve(backtest_result.equity_curve, backtest_result.trades)
    """

    def __init__(self, parent: QWidget | None = None):
        """Initialisiert das Widget."""
        super().__init__(parent)

        self._equity_data: list[dict] = []
        self._trades: list = []
        self._show_drawdown = True
        self._show_trades = True

        self._setup_ui()
        self._load_chart()

        logger.info("EquityCurveWidget initialized")

    def _setup_ui(self) -> None:
        """Erstellt das UI Layout."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # --- Controls ---
        controls = QFrame()
        controls.setStyleSheet("""
            QFrame {
                background-color: #1a1a2e;
                border-bottom: 1px solid #333;
                padding: 4px;
            }
        """)
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(8, 4, 8, 4)

        # Title
        title = QLabel("📈 Equity Curve")
        title.setStyleSheet("font-weight: bold; color: white;")
        controls_layout.addWidget(title)

        controls_layout.addStretch()

        # Checkboxes
        self.dd_check = QCheckBox("Drawdown")
        self.dd_check.setChecked(True)
        self.dd_check.setStyleSheet("color: #aaa;")
        self.dd_check.stateChanged.connect(self._on_settings_changed)
        controls_layout.addWidget(self.dd_check)

        self.trades_check = QCheckBox("Trades")
        self.trades_check.setChecked(True)
        self.trades_check.setStyleSheet("color: #aaa;")
        self.trades_check.stateChanged.connect(self._on_settings_changed)
        controls_layout.addWidget(self.trades_check)

        # Buttons
        self.fit_btn = QPushButton("Fit")
        self.fit_btn.setMaximumWidth(50)
        self.fit_btn.clicked.connect(self._on_fit_clicked)
        controls_layout.addWidget(self.fit_btn)

        layout.addWidget(controls)

        # --- WebEngine View ---
        self.web_view = QWebEngineView()
        self.web_view.setMinimumHeight(250)

        # Settings
        settings = self.web_view.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)

        # WebChannel
        self.channel = QWebChannel()
        self.bridge = EquityCurveBridge(self)
        self.channel.registerObject("pyBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        layout.addWidget(self.web_view)

    def _load_chart(self) -> None:
        """Lädt das Chart HTML."""
        # Inline HTML mit Lightweight Charts
        html = self._generate_html()
        self.web_view.setHtml(html, QUrl("qrc:/"))

    def _generate_html(self) -> str:
        """Generiert das HTML für den Chart."""
        # Pfad zur lightweight-charts Library
        assets_path = Path(__file__).parent / "assets"
        lw_charts_path = assets_path / "lightweight-charts.standalone.production.js"

        # Falls local file nicht klappt, verwende inline oder CDN
        lw_script = ""
        if lw_charts_path.exists():
            with open(lw_charts_path, "r") as f:
                lw_script = f"<script>{f.read()}</script>"
        else:
            lw_script = '<script src="https://unpkg.com/lightweight-charts@4.1.0/dist/lightweight-charts.standalone.production.js"></script>'

        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        html, body {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            background: #0a0a0a;
            overflow: hidden;
        }}
        #chart-container {{
            width: 100%;
            height: 100%;
        }}
    </style>
    {lw_script}
</head>
<body>
    <div id="chart-container"></div>
    <script src="qrc:///qtwebchannel/qwebchannel.js"></script>
    <script>
        const {{ createChart, LineStyle, LineSeries, AreaSeries, HistogramSeries }} = LightweightCharts;

        let chart = null;
        let equitySeries = null;
        let drawdownSeries = null;
        let tradeMarkers = [];
        let pyBridge = null;
        let showDrawdown = true;
        let showTrades = true;

        function initChart() {{
            const container = document.getElementById('chart-container');

            chart = createChart(container, {{
                layout: {{
                    background: {{ type: 'solid', color: '#0a0a0a' }},
                    textColor: '#d1d4dc',
                }},
                grid: {{
                    vertLines: {{ color: 'rgba(70, 70, 70, 0.35)' }},
                    horzLines: {{ color: 'rgba(70, 70, 70, 0.35)' }},
                }},
                rightPriceScale: {{
                    borderColor: '#485c7b',
                    scaleMargins: {{ top: 0.1, bottom: 0.1 }},
                }},
                timeScale: {{
                    timeVisible: true,
                    secondsVisible: false,
                    borderColor: '#485c7b',
                }},
                handleScroll: {{
                    mouseWheel: true,
                    pressedMouseMove: true,
                }},
                handleScale: {{
                    mouseWheel: true,
                    pinch: true,
                }},
            }});

            // Equity Area Series
            equitySeries = chart.addSeries(LightweightCharts.AreaSeries, {{
                lineColor: '#4CAF50',
                topColor: 'rgba(76, 175, 80, 0.4)',
                bottomColor: 'rgba(76, 175, 80, 0.0)',
                lineWidth: 2,
                priceFormat: {{ type: 'custom', formatter: (p) => '$' + p.toFixed(2) }},
            }});

            // Drawdown Series (negativ)
            drawdownSeries = chart.addSeries(LightweightCharts.AreaSeries, {{
                lineColor: '#f44336',
                topColor: 'rgba(244, 67, 54, 0.0)',
                bottomColor: 'rgba(244, 67, 54, 0.3)',
                lineWidth: 1,
                priceFormat: {{ type: 'percent' }},
                priceScaleId: 'drawdown',
            }});

            chart.priceScale('drawdown').applyOptions({{
                scaleMargins: {{ top: 0.7, bottom: 0 }},
                visible: false,
            }});

            // Handle resize
            const resizeObserver = new ResizeObserver(entries => {{
                const {{ width, height }} = entries[0].contentRect;
                chart.applyOptions({{ width, height }});
            }});
            resizeObserver.observe(container);

            console.log('Equity chart initialized');
        }}

        function loadData(data) {{
            if (!chart) return;

            // Equity data
            if (data.equity && data.equity.length > 0) {{
                equitySeries.setData(data.equity);
            }}

            // Drawdown data
            if (data.drawdown && data.drawdown.length > 0 && showDrawdown) {{
                drawdownSeries.setData(data.drawdown);
            }}

            // Trade markers
            if (data.trades && data.trades.length > 0 && showTrades) {{
                tradeMarkers = data.trades.map(t => ({{
                    time: t.time,
                    position: t.pnl >= 0 ? 'aboveBar' : 'belowBar',
                    color: t.pnl >= 0 ? '#4CAF50' : '#f44336',
                    shape: t.type === 'entry' ? 'arrowUp' : 'arrowDown',
                    text: t.type === 'entry' ? 'E' : (t.pnl >= 0 ? '+' : '-'),
                }}));
                equitySeries.setMarkers(tradeMarkers);
            }}

            chart.timeScale().fitContent();
        }}

        function updateSettings(settings) {{
            showDrawdown = settings.showDrawdown;
            showTrades = settings.showTrades;

            if (drawdownSeries) {{
                drawdownSeries.applyOptions({{ visible: showDrawdown }});
            }}

            if (equitySeries && !showTrades) {{
                equitySeries.setMarkers([]);
            }} else if (equitySeries && showTrades && tradeMarkers.length > 0) {{
                equitySeries.setMarkers(tradeMarkers);
            }}
        }}

        function fitContent() {{
            if (chart) {{
                chart.timeScale().fitContent();
            }}
        }}

        // Initialize QWebChannel
        if (typeof QWebChannel !== 'undefined') {{
            new QWebChannel(qt.webChannelTransport, function(channel) {{
                pyBridge = channel.objects.pyBridge;

                if (pyBridge) {{
                    pyBridge.dataReady.connect(function(jsonStr) {{
                        const data = JSON.parse(jsonStr);
                        loadData(data);
                    }});

                    pyBridge.settingsChanged.connect(function(jsonStr) {{
                        const settings = JSON.parse(jsonStr);
                        updateSettings(settings);
                    }});

                    // Load initial data if available (Qt slot may return value or Promise)
                    const maybePromise = pyBridge.getData();
                    if (maybePromise && typeof maybePromise.then === 'function') {{
                        maybePromise
                            .then(function(initialData) {{
                                if (initialData && initialData !== '{{}}') {{
                                    loadData(JSON.parse(initialData));
                                }}
                            }})
                            .catch(function(err) {{
                                console.error('Failed to load initial equity data', err);
                            }});
                    }} else {{
                        const initialData = maybePromise;
                        if (initialData && initialData !== '{{}}') {{
                            loadData(JSON.parse(initialData));
                        }}
                    }}
                }}

                console.log('QWebChannel connected');
            }});
        }}

        // Global function for Python calls
        window.loadEquityData = loadData;
        window.fitContent = fitContent;
        window.updateChartSettings = updateSettings;

        // Init chart on load
        initChart();
    </script>
</body>
</html>
"""

    def load_equity_curve(
        self,
        equity_curve: list,
        trades: list | None = None,
        initial_capital: float = 10000,
    ) -> None:
        """Lädt Equity Curve und Trades in den Chart.

        Args:
            equity_curve: Liste von EquityPoint Objekten
            trades: Optional: Liste von Trade Objekten
            initial_capital: Startkapital für Drawdown-Berechnung
        """
        if not equity_curve:
            logger.warning("Empty equity curve")
            return

        # Equity Daten konvertieren
        equity_data = []
        for point in equity_curve:
            if hasattr(point, 'time'):
                ts = int(point.time.timestamp())
                value = point.equity
            else:
                continue

            equity_data.append({
                "time": ts,
                "value": value,
            })

        # Drawdown berechnen
        drawdown_data = []
        peak = initial_capital
        for i, point in enumerate(equity_curve):
            equity = point.equity if hasattr(point, 'equity') else initial_capital
            peak = max(peak, equity)
            dd = ((equity - peak) / peak) * 100 if peak > 0 else 0

            ts = int(point.time.timestamp()) if hasattr(point, 'time') else i

            drawdown_data.append({
                "time": ts,
                "value": dd,
            })

        # Trade Marker
        trade_data = []
        if trades:
            for trade in trades:
                # Entry Marker
                if hasattr(trade, 'entry_time') and trade.entry_time:
                    trade_data.append({
                        "time": int(trade.entry_time.timestamp()),
                        "type": "entry",
                        "pnl": 0,
                        "side": trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                    })

                # Exit Marker
                if hasattr(trade, 'exit_time') and trade.exit_time:
                    trade_data.append({
                        "time": int(trade.exit_time.timestamp()),
                        "type": "exit",
                        "pnl": trade.realized_pnl if hasattr(trade, 'realized_pnl') else 0,
                        "side": trade.side.value if hasattr(trade.side, 'value') else str(trade.side),
                    })

        # JSON erstellen und senden
        data = {
            "equity": equity_data,
            "drawdown": drawdown_data,
            "trades": trade_data,
        }

        self._equity_data = equity_data
        self._trades = trade_data

        json_str = json.dumps(data)
        self.bridge.setEquityData(json_str)

        logger.info(f"Loaded equity curve with {len(equity_data)} points, {len(trade_data)} trade markers")

    def load_from_result(self, result) -> None:
        """Lädt Daten aus einem BacktestResult.

        Args:
            result: BacktestResult Objekt
        """
        self.load_equity_curve(
            equity_curve=result.equity_curve,
            trades=result.trades,
            initial_capital=result.initial_capital,
        )

    def clear(self) -> None:
        """Leert den Chart."""
        self._equity_data = []
        self._trades = []
        self.bridge.setEquityData("{}")

    def _on_settings_changed(self) -> None:
        """Handler für Checkbox-Änderungen."""
        settings = {
            "showDrawdown": self.dd_check.isChecked(),
            "showTrades": self.trades_check.isChecked(),
        }
        self.bridge.settingsChanged.emit(json.dumps(settings))

    def _on_fit_clicked(self) -> None:
        """Handler für Fit-Button."""
        self.web_view.page().runJavaScript("if (window.fitContent) window.fitContent();")
