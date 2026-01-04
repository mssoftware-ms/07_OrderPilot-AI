# GUI-Tab-Workflow (Tab2/Tab3/Tab4) – Analyse-Modul: Strategie → Timeframes → IndicatorSets → DataCollector → Summary

Dieses Dokument beschreibt den **konkreten GUI-Tab-Workflow** inkl. **Datenmodell (Pydantic)** und **Orchestrator-Fluss** für deine Tradingsoftware (PyQt6 + lightweight-charts).  
Prinzip: **Deterministik in Python** (Regime/Features/Validierung), **LLM nur für Nuancen & sprachliche Zusammenfassung**.

Quellen/Bezug: orientiert an deiner bestehenden Checklisten-/Framework-Logik (Validator → Regime → Features → Prompt → JSON Output).  
- KI-Analysemodul Checkliste: 【32†KI_Analysemodul_Checkliste.md】  
- Python Implementation Checklist: 【31†Python_Dev_Checklist.rtf】  
- BTC Trading System Framework (Regime/Setup-Bibliothek): 【30†BTC_Trading_System_Framework.rtf】  
- Algorithmisches Handelsprotokoll (Regime/Orderflow-Light/Validierung): 【28†01 Algorithmisches Handelsprotokoll .rtf】

---

## 1) Zielbild: Tabs & Zuständigkeiten

### **Tab2 – Strategie**
**Ziel:** Strategie wählen (**Scalping / Daytrading / Swingtrading**) und sofort sehen, ob sie zum aktuellen Markt-Regime passt (Trend/Range/High-Vol).  
**Output Tab2:** `StrategyConfig` aktiv + „Gating“-Status (Recommended/Warnung).

### **Tab3 – Timeframes / Charts**
**Ziel:** Multi-Timeframe-Kontext definieren (Execution/Context/Trend/Macro), inkl. Lookback und Collector-Modus (Cache/Provider/UI-Switch/Hidden Collector).  
**Output Tab3:** Liste `TimeframeSpec` für den Run + Validierungsstatus.

### **Tab4 – IndicatorSets (global)**
**Ziel:** Globale Indikator-Presets pro Strategie erstellen, speichern, exportieren/importieren – und im normalen Chartmodus wiederverwenden.  
**Output Tab4:** `IndicatorPreset` Store + Verknüpfung zu `StrategyConfig`.

### **(Panel/Abschnitt) DataCollector**
**Ziel:** Automatisches Sammeln der Daten je TF, Artefakte in temp Run-Ordner schreiben.  
**Output:** TF-Datasets + Feature-Files im Run-Ordner.

### **(Panel/Abschnitt) Summary**
**Ziel:** Finaler Merge + LLM Output + Report (`summary.md`) + Raw JSON.  
**Output:** `analysis_result.json` + `summary.md` + `RunArtifactIndex`.

---

## 2) Tab2 – Strategie (UI & Logik)

### UI-Elemente (Pflicht)
- Strategie-Dropdown: `Scalping | Daytrading | Swingtrading`
- Regime-Status (Read-only): `TREND_BULL | TREND_BEAR | RANGE | HIGH_VOL | NEUTRAL`
- „Erlaubte Setups“ (Read-only, aus Regime abgeleitet)
- Button: **Auto-Konfiguration** (setzt TFs + Preset IDs automatisch)
- LLM-Defaults pro Strategie: Model, Temperature, max_output_tokens, Timeout, Retries (optional override)
- Token-/Kosten-Schätzung (Prompt-Länge grob) als Label

### Logik
1. Regime-Erkennung deterministisch aus Higher-TF (Tab3-konfiguriert oder Default)
2. Strategie-Gating:
   - Wenn Regime nicht in `allowed_regimes`: **Warnung** („nicht empfohlen“)
3. Auto-Konfiguration:
   - Setzt Timeframes (Tab3) + Preset (Tab4) passend zur Strategie

### Akzeptanzkriterien
- Strategie-Wechsel friert UI nicht ein (keine Live-Reload-Orgie).
- Gating ist klar sichtbar, ohne Strategy zu blockieren (Warnung statt Hard Lock).

---

## 3) Tab3 – Timeframes / Charts (UI & Logik)

### UI-Elemente
- Tabelle „Timeframes pro Run“ (editable):
  - `purpose`: `EXECUTION | CONTEXT | TREND | MACRO`
  - `tf`: `1m, 3m, 5m, 15m, 30m, 1h, 4h, 1D, 1W, 1M`
  - Lookback: `bars` oder `duration` (z.B. `14d`, `3mo`)
  - `warmup_bars` (z.B. 300–1000 für EMA200)
  - Provider: `BITUNIX/ALPACA/DB/YAHOO/CUSTOM`
  - Collector-Mode: `CACHE_ONLY | SWITCH_CHART | HIDDEN_COLLECTOR`
  - `parallel_ok`
- Button: **Timeframes aus Strategie übernehmen**
- Toggle: „Nur Trendkontext“ (schnell) vs „Full Run“
- Toggle: „Marktstruktur-Extraktion aktiv“ (Swings/HHHL)

### Logik
- Validate-Konfiguration:
  - pro TF: Mindest-Bars für Indikatoren (z.B. EMA200 braucht genügend warmup)
- Run nutzt genau diese Liste, schreibt pro TF Artefakte.

### Akzeptanzkriterien
- TF-Liste pro Strategie speicherbar.
- Validierung verhindert Run-Start mit kaputten Parametern.

---

## 4) Tab4 – IndicatorSets (global) (UI & Logik)

### UI-Elemente
- Preset-Liste (links): `Scalping_Default`, `Day_Default`, `_ATTACHMENT`, …
- Preset-Editor (rechts):
  - Indikator hinzufügen: `SMA/EMA/RSI/MACD/BB/ATR/STOCH/ADX/CCI`
  - Parameter (Perioden, stddev, source)
  - Feature-Flags (Token-sparsam): `state`, `distance_pct`, `bandwidth`, `divergence_possible`, …
  - Purpose-Scopes: gilt für `EXECUTION/CONTEXT/TREND/MACRO`
- Buttons: **Speichern**, **Duplizieren**, **Export/Import JSON**, optional „Auf Chart anwenden“

### Persistenz (Best Practice)
- `config/indicator_presets.json` (statt QSettings-Monster), optional mit Versionierung.
- Chart-Modus und Analyse-Modus referenzieren nur `preset_id` → keine Drift.

### Akzeptanzkriterien
- Preset wirkt im Analyse-Run und im normalen Chartmodus identisch.
- Keine Doppel-Implementierung der Indikatorberechnung (bestehende Engine wiederverwenden).

---

## 5) DataCollector – Automatisches Sammeln (Automatismus)

### Ziel
Je Strategie/Run automatisiert:
- benötigte TFs laden
- validieren
- Indikatoren berechnen
- Features extrahieren
- alles als Artefakte in temp Run-Ordner schreiben

### UI-Elemente
- Progress-Status:
  - `Collecting TF ...`
  - `Validating ...`
  - `Computing indicators ...`
  - `Merging ...`
  - `LLM request ...`
  - `Done`
- Toggle: Parallel sammeln (nur wenn Provider/CPU OK)
- Cancel-Button (Run abbrechen)

### Concurrency/Performance
- Per Symbol nur **1 Run** gleichzeitig.
- Pro TF eigene Task/Worker (QThread oder asyncio + Qt-Signals).

---

## 6) Summary – Ergebnisdarstellung & Artefakte

### UI-Elemente
- gerendertes Markdown `summary.md`
- Raw JSON Panel + Copy Button
- Button „Run-Ordner öffnen“

### Artefakte (pro Run)
- `meta.json` (symbol, provider, strategy, tf specs, timestamps)
- `ohlcv_<tf>.json` (optional, wenn du es brauchst – normalerweise weglassen)
- `features_<tf>.json` (komprimierte Features je TF)
- `levels_<tf>.json` (Swingpoints, S/R, Range-Grenzen)
- `merge_payload.json` (Final Merge, LLM Input)
- `analysis_result.json` (LLM Output, strikt validiert)
- `summary.md` (Human-Report)
- `run_index.json` (RunArtifactIndex)

---

## 7) Datenmodell (Pydantic) – stabiler Vertrag

### Enums & Kern-Typen
```python
from __future__ import annotations
from typing import Literal, Optional, Dict, List, Any
from pydantic import BaseModel, Field

StrategyType = Literal["SCALPING", "DAYTRADING", "SWINGTRADING"]
PurposeType  = Literal["EXECUTION", "CONTEXT", "TREND", "MACRO"]
Timeframe    = Literal["1m","3m","5m","15m","30m","1h","4h","1D","1W","1M"]
ProviderType = Literal["BITUNIX","ALPACA","DB","YAHOO","CUSTOM"]
RegimeType   = Literal["TREND_BULL","TREND_BEAR","RANGE","HIGH_VOL","NEUTRAL"]
```

### IndicatorSpec & Preset
```python
class IndicatorSpec(BaseModel):
    name: Literal["SMA","EMA","RSI","MACD","BB","ATR","STOCH","ADX","CCI"]
    params: Dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

    # Feature-Flags: Token sparen (nur das exportieren, was du wirklich brauchst)
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    # z.B. {"state": True, "distance_pct": True, "bandwidth": True}

class IndicatorPreset(BaseModel):
    preset_id: str
    name: str
    strategy: StrategyType
    description: str = ""
    applies_to_purposes: List[PurposeType] = Field(
        default_factory=lambda: ["EXECUTION","CONTEXT","TREND","MACRO"]
    )
    indicators: List[IndicatorSpec]
    version: int = 1
```

### TimeframeSpec
```python
class TimeframeSpec(BaseModel):
    tf: Timeframe
    purpose: PurposeType
    provider: ProviderType

    lookback_bars: Optional[int] = None
    lookback_duration: Optional[str] = None  # z.B. "14d", "3mo"
    warmup_bars: int = 300

    indicator_preset_id: Optional[str] = None  # preset override, sonst StrategyConfig default

    collector_mode: Literal["SWITCH_CHART","HIDDEN_COLLECTOR","CACHE_ONLY"] = "CACHE_ONLY"
    parallel_ok: bool = False
```

### StrategyConfig (global defaults)
```python
class StrategyConfig(BaseModel):
    strategy: StrategyType
    default_timeframes: List[TimeframeSpec]
    default_indicator_preset_id: str

    allowed_regimes: List[RegimeType]

    llm_model: str
    temperature: float = 0.2
    max_output_tokens: int = 800
    timeout_s: int = 25
    retries: int = 2

    max_candles_in_prompt: int = 30
    include_raw_ohlcv: bool = False
```

### RunArtifactIndex (Ablage/Run-Verwaltung)
```python
class RunArtifactIndex(BaseModel):
    run_id: str
    created_at_utc: str
    symbol: str
    provider: ProviderType
    strategy: StrategyType
    regime: RegimeType

    run_dir: str
    files: Dict[str, str] = Field(default_factory=dict)  # logical_name -> filepath

    stats: Dict[str, Any] = Field(default_factory=dict)
```

### Final Merge Payload (LLM Input)
```python
class AnalysisMergePayload(BaseModel):
    symbol: str
    strategy: StrategyType
    regime: RegimeType
    trend_context: Dict[str, Any]
    timeframe_features: Dict[str, Dict[str, Any]]  # tf -> features dict
    key_levels: Dict[str, Any]
    tasks: List[str]
```

---

## 8) Orchestrator-Fluss (Chart-Automation, Sammeln, Final Merge, LLM)

### Schrittfolge (deterministisch → LLM)
1. **Run init**
   - `run_id` generieren
   - temp Ordner: `tmp/analysis_runs/<symbol>/<run_id>/`
   - `meta.json` schreiben (Config Snapshot)

2. **DataCollector**
   - pro `TimeframeSpec` OHLCV holen (Cache → Provider → DB)
   - je nach `collector_mode`: UI-Switch oder Hidden Collector

3. **Preflight/Validation (hart)**
   - Lücken (Gaps), Outliers, Null-Volumen, Timestamp-Lag, Bad Ticks  
   - ggf. TF degradieren (wenn purpose != EXECUTION), sonst abort

4. **Indicator Compute**
   - bestehende IndicatorEngine verwenden
   - Preset: TF override oder Strategy default

5. **Feature Engineering (token-sparsam)**
   - States statt Serien: RSI state, EMA distance %, BBWidth, ATR normalized, ADX bucket
   - Strukturpunkte: Swings, HH/HL/LH/LL, Range hi/lo, BOS Flags

6. **Regime & Trendkontext**
   - aus TREND/MACRO TFs (z.B. 4h/1D/1W)
   - Ergebnis: `regime`, `trend_direction`, `major_levels`, `no_go_zones`

7. **Final Merge**
   - `AnalysisMergePayload` bauen
   - `merge_payload.json` schreiben

8. **LLM Call (optional, aber strikt)**
   - JSON-only Output, Pydantic validieren
   - `analysis_result.json` schreiben

9. **Summary**
   - `summary.md` schreiben
   - `run_index.json` finalisieren

---

## 9) Default-Konfigurationen (direkt als StrategyConfig umsetzbar)

### Scalping Default
- TFs:
  - EXECUTION: `1m` (lookback 6–24h)
  - CONTEXT: `5m` (2–7d)
  - TREND: `1h` (2–4w)
  - MACRO: `1D` (3–6mo)
- Preset: `EMA9/21, RSI14, BB(20,2), ATR14, Stoch(14,3,3), ADX14, Volume`
- Allowed Regimes: `RANGE`, `NEUTRAL`, (optional `TREND_*` nur für Counter-Pullback)

### Daytrading Default
- TFs:
  - EXECUTION: `5m` oder `15m` (2–10d)
  - CONTEXT: `1h` (2–8w)
  - TREND: `4h` (3–6mo)
  - MACRO: `1D` (6–12mo)
- Preset: `EMA20/50/200, RSI14, MACD(12,26,9), BB(20,2), ATR14, ADX14, Volume`
- Allowed Regimes: `TREND_BULL`, `TREND_BEAR`, `RANGE` (mit Range-Setup)

### Swing Default
- TFs:
  - EXECUTION: `4h` oder `1D`
  - CONTEXT: `1D`
  - TREND: `1W`
  - MACRO: `1M`
- Preset: `EMA20/50/200, RSI14, MACD(12,26,9), ATR14, ADX14, Volume (BB optional)`
- Allowed Regimes: `TREND_*`, (optional `NEUTRAL` wenn Squeeze/Breakout geplant)

---

## 10) Definition of Done (DoD) – pragmatisch

- Strategie-Tab wählt StrategyConfig, zeigt Regime & Gating zuverlässig
- Timeframes-Tab lädt/validiert alle TFs reproduzierbar
- IndicatorSets sind global persistiert und im Chartmodus wiederverwendbar
- DataCollector schreibt Run-Artefakte in temp Ordner, UI bleibt responsiv
- Final Merge + LLM Output sind strikt validiert (JSON-only)
- Summary (MD) + Raw JSON sind in der UI verfügbar

---

## 11) Nächster Schritt (wenn du es willst)
- Ableitung einer konkreten **Datei-/Modulstruktur** in deinem Repo (src/core/ai_analysis/…)
- Methodensignaturen passend zu deinen vorhandenen Klassen (IndicatorEngine, ChartWindow, Provider, Cache)
- Beispiel-Konfig-Dateien:
  - `config/strategy_configs.json`
  - `config/indicator_presets.json`
- „Run Manager“ + Cleanup-Policy (z.B. nur letzte 50 Runs behalten)

