# Chart Analysis Chatbot - Implementierungsplan

**Erstellt:** 2025-12-31
**Status:** Geplant
**Ziel:** KI-gestützter Chatbot zur Chart-Analyse mit Trading-Empfehlungen

---

## 1. Übersicht

Ein Dock-Widget rechts neben dem Chart, das:
- Den aktuell geöffneten Chart analysiert (OHLCV, Indikatoren, Patterns)
- Trading-Empfehlungen gibt (Entry/Exit, Risk Assessment)
- Konversations-basiert arbeitet (Fragen stellen, Follow-ups)
- Chat-Verlauf **pro Fenster (Symbol + Timeframe) persistiert**

---

## 2. Modulstruktur

```
src/chart_chat/
├── __init__.py              # Public API Exports
├── models.py                # Pydantic Models (~150 LOC)
├── context_builder.py       # Chart-Kontext für AI (~200 LOC)
├── analyzer.py              # AI Chart-Analyse (~180 LOC)
├── chat_service.py          # Konversations-Manager (~200 LOC)
├── history_store.py         # Persistenz pro Symbol (~120 LOC)
├── prompts.py               # Prompt Templates (~100 LOC)
├── widget.py                # PyQt6 Chat UI (~350 LOC)
└── mixin.py                 # ChartWindow Integration (~80 LOC)
```

**Gesamt: ~1380 LOC** (8 Dateien, alle unter 400 LOC)

---

## 3. Datenmodelle (`models.py`)

```python
class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = {}

class TrendDirection(Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class SignalStrength(Enum):
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"

class SupportResistanceLevel(BaseModel):
    price: float
    strength: SignalStrength
    level_type: str  # "support" | "resistance"

class EntryExitRecommendation(BaseModel):
    action: str  # "long_entry", "short_entry", "exit", "hold"
    price: float | None
    confidence: float  # 0.0-1.0
    reasoning: str

class RiskAssessment(BaseModel):
    stop_loss: float | None
    take_profit: float | None
    risk_reward_ratio: float | None

class ChartAnalysisResult(BaseModel):
    trend_direction: TrendDirection
    trend_strength: SignalStrength
    trend_description: str
    support_levels: list[SupportResistanceLevel]
    resistance_levels: list[SupportResistanceLevel]
    recommendation: EntryExitRecommendation
    risk_assessment: RiskAssessment
    patterns_identified: list[str]
    indicator_summary: str
    confidence_score: float
    warnings: list[str]
```

---

## 4. Komponenten-Design

### 4.1 ChartContextBuilder (`context_builder.py`)

Extrahiert Kontext aus dem Chart-Widget:

```python
@dataclass
class ChartContext:
    symbol: str
    timeframe: str
    current_price: float
    ohlcv_summary: dict  # Statistiken der letzten N Bars
    indicators: dict     # Aktive Indikator-Werte
    price_change_pct: float
    volatility_atr: float | None
    recent_high: float
    recent_low: float

class ChartContextBuilder:
    def __init__(self, chart_widget):
        self.chart = chart_widget

    def build_context(self, lookback_bars: int = 100) -> ChartContext:
        # Extrahiert: chart.data, chart.active_indicators,
        # chart.current_symbol, chart._last_price
```

**Datenquellen:**
- `chart.data` → pd.DataFrame mit OHLCV
- `chart.current_symbol` → Symbol-String
- `chart.current_timeframe` → Timeframe-String
- `chart._last_price` → Aktueller Preis
- `chart.active_indicators` → Dict der aktiven Indikatoren
- `chart.indicator_engine.calculate()` → Indikator-Berechnung

### 4.2 ChartAnalyzer (`analyzer.py`)

AI-gestützte Analyse:

```python
class ChartAnalyzer:
    def __init__(self, ai_service):
        self.ai_service = ai_service

    async def analyze_chart(self, context: ChartContext) -> ChartAnalysisResult:
        # Vollständige Chart-Analyse

    async def answer_question(
        self, question: str, context: ChartContext, history: list[ChatMessage]
    ) -> str:
        # Konversationelle Frage beantworten
```

**AI-Provider:** Nutzt `AIProviderFactory.create_service()` (konfigurierbar)

### 4.3 HistoryStore (`history_store.py`)

Persistenz pro Fenster (Symbol + Timeframe):

```python
class HistoryStore:
    def __init__(self, storage_dir: Path = None):
        # Default: ~/.orderpilot/chat_history/

    def _make_key(self, symbol: str, timeframe: str) -> str:
        # z.B. "BTC_USD_1H" → "BTC_USD_1H.json"
        safe_symbol = symbol.replace("/", "_").replace(":", "_")
        return f"{safe_symbol}_{timeframe}"

    def save_history(self, symbol: str, timeframe: str, messages: list[ChatMessage]) -> None:
        # Speichert als JSON: {symbol}_{timeframe}.json

    def load_history(self, symbol: str, timeframe: str) -> list[ChatMessage]:
        # Lädt History für Fenster (Symbol + Timeframe)

    def clear_history(self, symbol: str, timeframe: str) -> None:
        # Löscht History für Fenster

    def list_charts_with_history(self) -> list[tuple[str, str]]:
        # Alle (Symbol, Timeframe) Kombinationen mit History
```

**Beispiel-Dateien:**
- `~/.orderpilot/chat_history/BTC_USD_1T.json`
- `~/.orderpilot/chat_history/BTC_USD_1H.json`
- `~/.orderpilot/chat_history/AAPL_1D.json`

### 4.4 ChatService (`chat_service.py`)

Orchestriert alles:

```python
class ChatService:
    def __init__(self, chart_widget, on_message: Callable):
        self.chart_widget = chart_widget
        self.context_builder = ChartContextBuilder(chart_widget)
        self.analyzer: ChartAnalyzer | None = None
        self.history_store = HistoryStore()
        self.history: list[ChatMessage] = []
        self._current_symbol: str | None = None
        self._current_timeframe: str | None = None

    async def initialize(self) -> None:
        # Lazy AI-Service Initialisierung
        # Lädt History für aktuelles Fenster (Symbol + Timeframe)

    async def send_message(self, user_message: str) -> ChatMessage:
        # User-Nachricht verarbeiten, AI-Antwort generieren

    async def analyze_chart(self) -> ChartAnalysisResult:
        # Vollständige Chart-Analyse auslösen

    def on_chart_changed(self, new_symbol: str, new_timeframe: str) -> None:
        # Speichert alte History, lädt neue für neues Fenster
        # Wird aufgerufen bei Symbol- ODER Timeframe-Wechsel

    def export_history(self) -> str:
        # Exportiert als Markdown
```

**Wichtig:** Bei Timeframe-Wechsel im gleichen Fenster wird auch die History gewechselt!

### 4.5 ChartChatWidget (`widget.py`)

PyQt6 UI:

```
┌─────────────────────────────────┐
│  Chart Analysis Chat        [X] │  ← Header mit Close
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │ Assistant                 │  │  ← Message Bubbles
│  │ Trend is bullish...       │  │    (scrollbar)
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ You                       │  │
│  │ What's the RSI?           │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│ [Analyze Chart] [Clear] [Export]│  ← Quick Actions
├─────────────────────────────────┤
│ ┌─────────────────────┐ [Send]  │  ← Input Area
│ │ Ask about the chart │         │
│ └─────────────────────┘         │
└─────────────────────────────────┘
```

**Features:**
- Message Bubbles (User = rechts/blau, Assistant = links/grau)
- "Analyze Chart" Button → Vollständige Analyse
- "Clear" Button → History löschen
- "Export" Button → Als Markdown speichern
- Loading-Indikator während AI-Calls
- Auto-Scroll zu neuen Nachrichten

### 4.6 ChartChatMixin (`mixin.py`)

Integration in ChartWindow:

```python
class ChartChatMixin:
    def _init_chart_chat(self) -> None:
        # Erstellt Dock-Widget

    def _create_chat_dock(self) -> QDockWidget:
        dock = QDockWidget("Chart Analysis Chat", self)
        dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.chat_widget = ChartChatWidget(self.chart_widget)
        dock.setWidget(self.chat_widget)
        return dock

    def _toggle_chat_dock(self) -> None:
        # Toggle Sichtbarkeit
```

---

## 5. Datenfluss

```
┌──────────────────────────────────────────────────────────────────┐
│                         ChartWindow                               │
│  ┌────────────────────┐         ┌─────────────────────────────┐  │
│  │ EmbeddedTradingView│         │     ChartChatWidget         │  │
│  │      Chart         │◄────────│     (Right Dock)            │  │
│  │                    │  data   │                             │  │
│  │  chart.data        │         │  ┌─────────────────────┐    │  │
│  │  chart.symbol      │         │  │  ChatService        │    │  │
│  │  chart.indicators  │         │  │   └─ Analyzer       │    │  │
│  └────────────────────┘         │  │   └─ ContextBuilder │    │  │
│                                  │  │   └─ HistoryStore   │    │  │
│                                  │  └──────────┬──────────┘    │  │
│                                  └─────────────┼───────────────┘  │
└────────────────────────────────────────────────┼──────────────────┘
                                                 │
                                                 ▼
                                  ┌──────────────────────────┐
                                  │   AIProviderFactory      │
                                  │   (OpenAI/Anthropic/     │
                                  │    Gemini)               │
                                  └──────────────────────────┘
```

---

## 6. Prompt-Strategie (`prompts.py`)

### System Prompt (Analyse):
```
Du bist ein erfahrener technischer Analyst. Analysiere den Chart und gib
konkrete, umsetzbare Empfehlungen.

REGELN:
- Nenne konkrete Preisniveaus
- Gib Konfidenz-Level an (0-100%)
- Berücksichtige Risk/Reward
- Warne bei hohem Risiko
- Keine USD-Positionsgrößen empfehlen
```

### User Prompt Template:
```
Analysiere {symbol} auf {timeframe} Timeframe.

AKTUELLER PREIS: {current_price}

OHLCV (letzte {lookback} Bars):
- High: {high} | Low: {low}
- Durchschnitt: {avg_close}
- Volatilität (ATR): {atr}

INDIKATOREN:
{indicators}

Liefere:
1. Trend-Richtung und Stärke
2. Support/Resistance Levels
3. Entry/Exit Empfehlung
4. Risk Assessment
5. Erkannte Patterns
```

---

## 7. Kritische Dateien (zu modifizieren)

| Datei | Änderung |
|-------|----------|
| `src/ui/widgets/chart_window.py` | ChartChatMixin hinzufügen, Dock erstellen |
| `src/ui/widgets/chart_window_mixins/__init__.py` | Export aktualisieren |
| `src/common/event_bus.py` | Optional: CHART_CHAT Events |
| `ARCHITECTURE.md` | Chart-Chat Modul dokumentieren |

---

## 8. Implementierungsreihenfolge

### Phase 1: Core (Dateien 1-4)
- [ ] `src/chart_chat/__init__.py`
- [ ] `src/chart_chat/models.py`
- [ ] `src/chart_chat/prompts.py`
- [ ] `src/chart_chat/context_builder.py`

### Phase 2: Services (Dateien 5-6)
- [ ] `src/chart_chat/history_store.py`
- [ ] `src/chart_chat/analyzer.py`
- [ ] `src/chart_chat/chat_service.py`

### Phase 3: UI (Dateien 7-8)
- [ ] `src/chart_chat/widget.py`
- [ ] `src/chart_chat/mixin.py`

### Phase 4: Integration
- [ ] ChartWindow modifizieren
- [ ] Toggle-Button in Toolbar/Menü
- [ ] ARCHITECTURE.md aktualisieren

---

## 9. Threading-Strategie

AI-Calls blockieren → QThread verwenden:

```python
class ChatWorker(QThread):
    finished = pyqtSignal(object)  # ChatMessage oder ChartAnalysisResult
    error = pyqtSignal(str)

    def __init__(self, chat_service, operation: str, **kwargs):
        self.chat_service = chat_service
        self.operation = operation
        self.kwargs = kwargs

    def run(self):
        loop = asyncio.new_event_loop()
        try:
            if self.operation == "analyze":
                result = loop.run_until_complete(
                    self.chat_service.analyze_chart()
                )
            elif self.operation == "message":
                result = loop.run_until_complete(
                    self.chat_service.send_message(self.kwargs["message"])
                )
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))
```

---

## 10. Risiken & Mitigationen

| Risiko | Mitigation |
|--------|------------|
| AI-Calls kosten Geld | CostTracker nutzen, Budget-Warning |
| Langsame Antworten | Loading-Indikator, Streaming optional |
| Veralteter Kontext | Context bei jedem Request neu bauen |
| Thread-Safety | QThread + Signals, keine direkte UI-Manipulation |
| Große History | Max 50 Messages pro Symbol, FIFO |

---

## 11. Geschätzter Aufwand

| Phase | Aufwand |
|-------|---------|
| Phase 1: Core | ~2h |
| Phase 2: Services | ~3h |
| Phase 3: UI | ~4h |
| Phase 4: Integration | ~1h |
| **Gesamt** | **~10h** |

---

## 12. Akzeptanzkriterien

- [ ] Dock-Widget öffnet rechts neben Chart
- [ ] "Analyze Chart" liefert strukturierte Analyse
- [ ] Konversation funktioniert (Fragen stellen)
- [ ] History wird pro Symbol gespeichert
- [ ] Symbol-Wechsel lädt korrekte History
- [ ] Export als Markdown funktioniert
- [ ] Keine UI-Freezes während AI-Calls
- [ ] Fehler werden user-freundlich angezeigt
