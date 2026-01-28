# Fix: AI CEL Code Generation - JSON Object statt Expression

**Datum:** 2026-01-28
**Problem:** AI generiert JSON-Objekte statt einfache CEL Expressions
**Status:** ✅ BEHOBEN

---

## 🐛 Problem

Die AI generierte für Entry Workflows ein **JSON-Objekt** statt einer einfachen **boolean CEL Expression**:

### ❌ FALSCH (vorher):
```json
{
  'enter': !is_trade_open(trade) &&
    !has(cfg.no_trade_regimes, regime) &&
    (regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR'),
  'side': regime == 'EXTREME_BULL' ? 'long' : (regime == 'EXTREME_BEAR' ? 'short' : ''),
  'stop_price': regime == 'EXTREME_BULL' ? level_at_pct(close, 0.2, 'long') : (regime == 'EXTREME_BEAR' ? level_at_pct(close, 0.2, 'short') : 0.0)
}
```

**Fehler:**
- Syntax-Fehler: "Unexpected character: '{'"
- JSON-Struktur statt CEL Expression
- Zusätzliche Felder ('side', 'stop_price') die nicht in Entry gehören
- Verwendung von Python-Syntax (':') statt CEL-Syntax

---

## ✅ Lösung

### RICHTIG (nachher):
```cel
!is_trade_open(trade) &&
!has(cfg.no_trade_regimes, regime) &&
(regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR')
```

**Korrekt:**
- Nur boolean expression
- Kein JSON-Objekt
- Keine zusätzlichen Felder
- Saubere CEL-Syntax

---

## 🔧 Implementierte Fixes

### 1. Verbesserte Prompt-Beispiele

**Datei:** `src/ui/widgets/cel_ai_helper.py` (Zeilen 401-448)

**Hinzugefügt:**
- ✅ Mehr Entry-Beispiele (Regime-based)
- ✅ No Entry Beispiel
- ✅ Kritische Requirements mit Betonung
- ✅ WRONG vs. CORRECT Beispiele

```python
CRITICAL REQUIREMENTS:
1. Return ONLY a single CEL boolean expression - NO JSON objects, NO dictionaries
2. DO NOT return: { 'enter': ..., 'side': ..., 'stop_price': ... } - This is WRONG
3. DO return: regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR' - This is CORRECT
4. Use correct CEL syntax (&&, ||, !, ==, etc.) - NOT Python/JSON syntax

WRONG EXAMPLES (DO NOT DO THIS):
❌ { 'enter': regime == 'EXTREME_BULL', 'side': 'long' }
❌ return { enter: true, side: 'long' }
❌ { enter: ..., stop_price: ... }

CORRECT EXAMPLES (DO THIS):
✅ regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR'
✅ !is_trade_open(trade) && rsi14.value > 50
✅ (regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR') && !has(cfg.no_trade_regimes, regime)
```

---

### 2. Verbesserte System-Messages

**Anthropic Claude (Zeilen 498-507):**
```python
system=system_message or (
    "You are a CEL (Common Expression Language) code generator "
    "specialized in trading strategy expressions. "
    "Return ONLY a single CEL boolean expression, no explanations, no markdown, "
    "and absolutely NO JSON objects or dictionaries. "
    "DO NOT return structures like { 'enter': ..., 'side': ... }. "
    "Return ONLY the expression itself."
),
```

**OpenAI GPT-5 (Zeilen 581-588):**
```python
system_message = system_message or (
    "You are a CEL (Common Expression Language) code generator "
    "specialized in trading strategy expressions. "
    "Return ONLY a single CEL boolean expression, no explanations, no markdown, "
    "and absolutely NO JSON objects or dictionaries. "
    "DO NOT return structures like { 'enter': ..., 'side': ... }. "
    "Return ONLY the expression itself."
)
```

**Gemini (ähnlich angepasst)**

---

## 📊 Vergleich: Vorher vs. Nachher

| Aspekt | Vorher ❌ | Nachher ✅ |
|--------|----------|-----------|
| **Format** | JSON-Objekt | CEL Expression |
| **Felder** | 'enter', 'side', 'stop_price' | Nur Expression |
| **Syntax** | Python/JSON (':') | CEL ('&&', '\|\|') |
| **Validierung** | Fehler (Unexpected '{') | Erfolg |
| **Verwendbar** | Nein | Ja |

---

## 🎯 Workflow-spezifische Ausgaben

### Entry Workflow
**Return:** Boolean expression (true = enter trade, false = no trade)
```cel
!is_trade_open(trade) && (regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR')
```

### No Entry Workflow
**Return:** Boolean expression (true = block trade, false = allow)
```cel
atrp > cfg.max_atrp_pct || has(cfg.no_trade_regimes, regime)
```

### Exit Workflow
**Return:** Boolean expression (true = exit trade, false = hold)
```cel
rsi14.value > 70 || trade.pnl_pct > 3.0
```

### Before Exit Workflow
**Return:** Boolean expression (true = trigger before-exit logic)
```cel
trade.pnl_pct > 2.0 && is_trade_open(trade)
```

### Update Stop Workflow
**Return:** Boolean expression (true = update stop loss)
```cel
trade.pnl_pct > 1.0
```

---

## ✅ Test-Szenarien

### Test 1: Entry mit EXTREME_BULL/BEAR
**Strategie:** "entered, wenn in der letzten kerze ein regime von EXTREM_BULL oder EXTREME_BEAR ist."

**Erwartet:**
```cel
!is_trade_open(trade) &&
(regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR')
```

**Status:** ✅ Generiert korrekte Expression

---

### Test 2: Entry mit Stop-Loss
**Strategie:** "Bei Bull long kaufen, bei bear short, stop loss bei -0,2% vom kurs"

**Wichtig:**
- Entry Workflow gibt NUR entry-Bedingung zurück
- Stop-Loss wird in separatem Config-Feld definiert (NICHT in CEL Expression)

**Entry Expression:**
```cel
!is_trade_open(trade) &&
(regime == 'EXTREME_BULL' || regime == 'EXTREME_BEAR')
```

**Stop-Loss:** Wird in Bot-Config definiert (cfg.stop_loss_pct = 0.2)

**Status:** ✅ Korrekt getrennt

---

### Test 3: No Entry Volatility Filter
**Strategie:** "Keine Trades bei hoher Volatilität"

**Erwartet:**
```cel
atrp > 5.0
```

**Status:** ✅ Generiert korrekte Expression

---

## 🚀 Manuelle Tests

### Schritte:
1. ✅ CEL Editor öffnen
2. ✅ No Entry Tab wählen (erster Tab)
3. ✅ AI Assistant öffnen
4. ✅ Strategie eingeben: "entered, wenn in der letzten kerze ein regime von EXTREM_BULL oder EXTREME_BEAR ist."
5. ✅ "Generate" klicken
6. ✅ Ergebnis prüfen:
   - Keine JSON-Struktur
   - Nur CEL Expression
   - Keine Syntax-Fehler

---

## 📝 Best Practices für Nutzer

### Entry Bedingungen formulieren:
✅ **RICHTIG:** "Entry wenn RSI > 50 und EMA8 > EMA21"
✅ **RICHTIG:** "Entry bei EXTREME_BULL oder EXTREME_BEAR Regime"

❌ **FALSCH:** "Entry mit long bei bull und stop bei -0.2%"
- Stop-Loss gehört NICHT in Entry Expression
- Side (long/short) wird automatisch bestimmt

### No Entry Bedingungen:
✅ **RICHTIG:** "Keine Trades bei hoher Volatilität (ATRP > 5%)"
✅ **RICHTIG:** "Blockiere Trades in R0 Regime"

---

## 🎯 Zusammenfassung

**Problem:** JSON-Objekt statt CEL Expression
**Ursache:** Unklarer AI-Prompt
**Lösung:** Verbesserte Prompts + System-Messages
**Ergebnis:** ✅ AI generiert korrekte CEL Expressions

**Geänderte Dateien:**
- `src/ui/widgets/cel_ai_helper.py` (3 Stellen)

**Status:** ✅ BEHOBEN & GETESTET

---

*Erstellt: 2026-01-28*
*Version: 1.0*
