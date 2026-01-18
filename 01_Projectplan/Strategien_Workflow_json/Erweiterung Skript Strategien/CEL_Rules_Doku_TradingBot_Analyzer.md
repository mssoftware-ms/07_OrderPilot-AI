# CEL-Regelwerk v1 für Trading Bot & Entry Analyzer
*(Script-/Rules-Dokumentation als Markdown)*

## 1) Ziel
Du willst für **Trading Bot** und **Entry Analyzer** eine gemeinsame, konfigurierbare „Skriptsprache“ für Regeln wie:
- **No-Trade**: „wenn Volumen < X und Volatilität < 0,2% => kein Trade“
- **Entry-Gates** je Marktregime
- **Exit/Notausstieg** in Echtzeit
- **Trade-Management** (Trailing Stop, Break-Even/Lock, Stop-Updates)

Dafür ist **CEL (Common Expression Language)** ideal: eine sichere, schnelle Ausdruckssprache, die als **einzelner Ausdruck** zu **einem Wert** evaluiert wird (perfekt für Policies/Constraints).

---

## 2) Architektur: Eine Rule-Engine für Analyzer UND Bot

### Komponenten
1) **Feature-Provider**
- Liefert alle Markt-/Regime-Features (z.B. `atrp`, `range_pct`, `bbwidth`, `obi`, …)

2) **CEL Engine**
- Compiliert Regeln einmal und evaluiert sie pro Tick/Bar

3) **RulePack**
- Persistierbare JSON-Datei mit Regelpaketen (`no_trade`, `entry`, `exit`, `update_stop`, `risk`)

### Ausführungsreihenfolge (fest im Code!)
1) **exit** (harte Exits; true => Position schließen)
2) **update_stop** (liefert neuen Stop; null => ignorieren)
3) **risk** (block/exit)
4) **no_trade / entry** (nur wenn kein Trade offen)

**Monotonic Stop (nie lockern!)**
- Long: `stop = max(old_stop, new_stop)`
- Short: `stop = min(old_stop, new_stop)`

---

## 3) RuleContext v1 (Variablenmodell)

### 3.1 Markt/Regime/Features (Top-Level Variablen)
| Variable | Typ | Bedeutung |
|---|---|---|
| `tf` | string | `"5m"`, `"1D"` |
| `regime` | string | `"R0".."R5"` |
| `direction` | string | `"UP"`, `"DOWN"`, `"NONE"` |
| `open`, `high`, `low`, `close` | number | Bar-Werte |
| `volume` | number | Candle-Volumen |
| `atrp` | number | ATR in % (0.60 = 0.60%) |
| `bbwidth` | number | Bollinger BandWidth |
| `range_pct` | number | Segment-Range in % |
| `squeeze_on` | bool | Kompression aktiv |
| `spread_bps` | number\|null | Spread (bps) |
| `depth_bid`, `depth_ask` | number\|null | Orderbuch-Tiefe |
| `obi` | number\|null | Orderbook Imbalance [-1..1] |

### 3.2 Trade-Variablen (aus deiner Trade-Tabelle; nested unter `trade`)
| Variable | Typ | Spalte / Bedeutung |
|---|---|---|
| `trade.id` | string | Type / interne ID |
| `trade.strategy` | string | Strategy |
| `trade.side` | string | `"long"` / `"short"` |
| `trade.entry_price` | number | Entry |
| `trade.current_price` | number | Current |
| `trade.stop_price` | number | Stop (aktueller SL) |
| `trade.sl_pct` | number | SL% (in %) |
| `trade.tr_pct` | number | TR% (Trailing-Abstand in %) |
| `trade.tra_pct` | number | TRA% (Trailing-Activation in %) |
| `trade.tr_lock_pct` | number | TR Lock (Lock/BE-Schwelle in %) |
| `trade.tr_stop_price` | number\|null | TR Stop (falls aktiv, sonst null) |
| `trade.status` | string | Status (OPEN/SL/TP/…) |
| `trade.pnl_pct` | number | P&L % |
| `trade.pnl_usdt` | number | P&L USDT |
| `trade.fees_pct` | number | trading fees % |
| `trade.fees_usdt` | number | Trading fees |
| `trade.invest_usdt` | number | Invest |
| `trade.stick` | number | Stick (deine interne Kennzahl) |
| `trade.leverage` | number | Hebel (z.B. 20) |

**Optional (sehr empfehlenswert, weil praktisch):**
- `trade.age_sec`: number (seit Entry)
- `trade.bars_in_trade`: int
- `trade.mfe_pct`: number (Max Favorable Excursion)
- `trade.mae_pct`: number (Max Adverse Excursion)
- `trade.is_open`: bool

### 3.3 Konfiguration (`cfg`)
Alles was „tuning“ ist, kommt in `cfg` statt hart in Regeln:
- `cfg.min_volume_pctl`, `cfg.min_volume_window`
- `cfg.min_atrp_pct`, `cfg.max_atrp_pct`
- `cfg.max_spread_bps`, `cfg.min_depth`
- `cfg.max_leverage`, `cfg.max_fees_pct`
- `cfg.no_trade_regimes`
- `cfg.min_obi`, `cfg.min_range_pct`

---

## 4) Beispiel: RuleContext als JSON (1:1 für Tests/Debug)

> Datei: `rule_context.example.json` (hier im Dokument eingebettet)

```json
{
  "tf": "5m",
  "regime": "R1",
  "direction": "UP",

  "open": 95250.0,
  "high": 95410.0,
  "low": 95120.0,
  "close": 95159.70,
  "volume": 1234.56,

  "atrp": 0.60,
  "bbwidth": 0.024,
  "range_pct": 1.85,
  "squeeze_on": false,

  "spread_bps": 2.1,
  "depth_bid": 125.0,
  "depth_ask": 132.0,
  "obi": null,

  "trade": {
    "id": "E:50",
    "strategy": "trend_following_conservative",
    "side": "long",

    "entry_price": 95336.1436,
    "current_price": 95159.70,

    "stop_price": 95171.63,
    "sl_pct": 0.17,

    "tr_pct": 1.00,
    "tra_pct": 0.50,
    "tr_lock_pct": 0.50,
    "tr_stop_price": null,

    "status": "OPEN",
    "pnl_pct": -0.18,
    "pnl_usdt": -0.18,

    "fees_pct": 0.080,
    "fees_usdt": 2.40,

    "invest_usdt": 100.00,
    "stick": 0.020978,
    "leverage": 20,

    "age_sec": 87,
    "bars_in_trade": 4,
    "mfe_pct": 0.22,
    "mae_pct": 0.25,
    "is_open": true
  },

  "cfg": {
    "min_volume_pctl": 20,
    "min_volume_window": 288,

    "min_atrp_pct": 0.20,
    "max_atrp_pct": 2.50,

    "max_spread_bps": 8.0,
    "min_depth": 60.0,

    "max_leverage": 50,
    "max_fees_pct": 0.15,

    "min_obi": 0.60,
    "min_range_pct": 0.60,

    "no_trade_regimes": ["R0"]
  }
}
```

---

## 5) RulePack JSON v1 (Standard-Format + Default-Regeln)

### 5.1 Regel-Objekt (Schema-Interpretation)
| Feld | Typ | Bedeutung |
|---|---|---|
| `id` | string | stabile ID für UI/Logs |
| `severity` | string | `block` / `exit` / `update_stop` |
| `expr` | string | CEL Ausdruck |
| `result_type` | string? | für `update_stop`: `number_or_null` |

### 5.2 Default RulePack (Startwerte für BTCUSDT 5m/1D)
> Datei: `rulepack.default.json` (hier eingebettet)

```json
{
  "rules_version": "1.0.0",
  "engine": "CEL",
  "packs": [
    {
      "pack_id": "no_trade",
      "enabled": true,
      "rules": [
        {
          "id": "NT_LOW_VOL_AND_LOW_VOLATILITY",
          "severity": "block",
          "expr": "volume < pctl(volume, cfg.min_volume_pctl, cfg.min_volume_window) && atrp < cfg.min_atrp_pct"
        },
        {
          "id": "NT_TOO_WILD",
          "severity": "block",
          "expr": "atrp > cfg.max_atrp_pct"
        },
        {
          "id": "NT_BAD_SPREAD_OR_DEPTH",
          "severity": "block",
          "expr": "(!isnull(spread_bps) && spread_bps > cfg.max_spread_bps) || (!isnull(depth_bid) && depth_bid < cfg.min_depth) || (!isnull(depth_ask) && depth_ask < cfg.min_depth)"
        },
        {
          "id": "NT_REGIME_BLOCK",
          "severity": "block",
          "expr": "regime in cfg.no_trade_regimes"
        },
        {
          "id": "NT_RANGE_TOO_TIGHT_FOR_FEES",
          "severity": "block",
          "expr": "regime == "R2" && range_pct < cfg.min_range_pct"
        }
      ]
    },

    {
      "pack_id": "entry",
      "enabled": true,
      "rules": [
        {
          "id": "EN_TREND_UP_ALLOWED",
          "severity": "block",
          "expr": "regime == "R1" && direction != "UP""
        },
        {
          "id": "EN_BREAKOUT_SETUP_ONLY",
          "severity": "block",
          "expr": "regime == "R3" && squeeze_on != true"
        },
        {
          "id": "EN_ORDERFLOW_CONFIRM",
          "severity": "block",
          "expr": "regime == "R5" && (isnull(obi) || abs(obi) < cfg.min_obi)"
        }
      ]
    },

    {
      "pack_id": "risk",
      "enabled": true,
      "rules": [
        {
          "id": "RK_MAX_LEVERAGE",
          "severity": "block",
          "expr": "trade.leverage > cfg.max_leverage"
        },
        {
          "id": "RK_MAX_FEES",
          "severity": "exit",
          "expr": "trade.fees_pct >= cfg.max_fees_pct"
        }
      ]
    },

    {
      "pack_id": "exit",
      "enabled": true,
      "rules": [
        {
          "id": "EX_STOP_HIT",
          "severity": "exit",
          "expr": "trade.side == "long" ? trade.current_price <= trade.stop_price : trade.current_price >= trade.stop_price"
        },
        {
          "id": "EX_REGIME_COLLAPSE_LOSS",
          "severity": "exit",
          "expr": "regime == "R2" && trade.pnl_pct < 0"
        }
      ]
    },

    {
      "pack_id": "update_stop",
      "enabled": true,
      "rules": [
        {
          "id": "US_BREAK_EVEN_LOCK",
          "severity": "update_stop",
          "result_type": "number_or_null",
          "expr": "trade.pnl_pct >= trade.tr_lock_pct ? (trade.side == "long" ? max(trade.stop_price, trade.entry_price) : min(trade.stop_price, trade.entry_price)) : null"
        },
        {
          "id": "US_TRAILING_AFTER_ACTIVATION",
          "severity": "update_stop",
          "result_type": "number_or_null",
          "expr": "trade.pnl_pct >= trade.tra_pct ? (trade.side == "long" ? max(trade.stop_price, trade.current_price * (1.0 - (trade.tr_pct/100.0))) : min(trade.stop_price, trade.current_price * (1.0 + (trade.tr_pct/100.0)))) : null"
        }
      ]
    }
  ]
}
```

**Wichtig:** Die `entry`-Regeln sind hier als **Blocker** formuliert („wenn Bedingung nicht passt => block“). Das ist in der Praxis stabiler, weil du beliebig viele Blocker addieren kannst, ohne dass Entry-Logik unübersichtlich wird.

---

## 6) CEL-Regeln als „One-Liner“ – Copy/Paste Beispiele

### 6.1 Dein Originalbeispiel (direkt)
```cel
volume < cfg.min_volume && atrp < 0.2
```

### 6.2 Stop Loss Hit (realtime)
```cel
trade.side == "long" ? trade.current_price <= trade.stop_price : trade.current_price >= trade.stop_price
```

### 6.3 Trailing Stop (liefert neuen Stop; monotonic im Code)
```cel
trade.side == "long"
  ? max(trade.stop_price, trade.current_price * (1.0 - trade.tr_pct/100.0))
  : min(trade.stop_price, trade.current_price * (1.0 + trade.tr_pct/100.0))
```

### 6.4 Break-Even / Lock
```cel
trade.pnl_pct >= trade.tr_lock_pct
  ? (trade.side == "long" ? max(trade.stop_price, trade.entry_price) : min(trade.stop_price, trade.entry_price))
  : null
```

---

## 7) Funktionen (Whitelist) – was du in CEL zulassen solltest
**Standard/CEL-nah:**
- `abs(x)`, `min(a,b)`, `max(a,b)`

**Trading-spezifisch (Custom Functions):**
- `pctl(series, p, window)`  *(Perzentil, z.B. für Volumenfilter)*
- `isnull(x)` / `nz(x, default)` / `coalesce(a,b,...)`

> Technisch: Bei der Python-CEL Implementierung kannst du Custom Functions registrieren.

---

## 8) Testbarkeit (Pflicht)
- Jede Regel muss in Unit-Tests laufen:
  - „Blockt wie erwartet“
  - „Exit triggert korrekt“
  - „Stop-Update ist monotonic“

Nutze dafür die `rule_context.example.json` als Fixture und ergänze Edgecases:
- `spread_bps=null` / `depth_* = null`
- `obi` verfügbar / nicht verfügbar
- very low volume / very high atrp

---

## 9) Quellen (als Codeblock, damit es in Markdown sauber bleibt)
```text
CEL Language Definition (Spec): https://github.com/google/cel-spec/blob/master/doc/langdef.md
Kubernetes: Common Expression Language in Kubernetes: https://kubernetes.io/docs/reference/using-api/cel/
Python CEL (PyPI): https://pypi.org/project/common-expression-language/
Python CEL Docs: https://python-common-expression-language.readthedocs.io/
```
