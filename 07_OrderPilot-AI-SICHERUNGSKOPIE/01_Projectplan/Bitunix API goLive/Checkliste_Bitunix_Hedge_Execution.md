# ✅ Checkliste: Bitunix Hedge Execution (Single-Trade) + Adaptive Limit + Trailing SL

**Start:** 2026-01-13  
**Letzte Aktualisierung:** 2026-01-13  
**Gesamtfortschritt:** 0% (0/96 Tasks)

---

## 🛠️ CODE-QUALITÄTS-STANDARDS (vor jedem Task lesen!)

### ✅ ERFORDERLICH für jeden Task:
1. Vollständige Implementation – keine TODO/Platzhalter
2. Robustheit – Exceptions sauber behandeln (kein „except: pass“)
3. Input-Validation – alle User-/API-Parameter prüfen
4. Type Hints – öffentliche Funktionen typisieren
5. Logging – klare Log-Level, Tracebarkeit pro Trade (`clientId/orderId/positionId`)
6. Rate-Limit-Disziplin – Debounce/Backoff, keine Tick-Spam-Requests
7. Reconnect/Recovery – nach Neustart Zustand rekonstruieren
8. Tests – Unit + mindestens 1 Integrations-Test (Signatur + Dummy-HTTP)

### ❌ VERBOTEN:
1. Platzhalter-Code (`TODO`)
2. Silent Failures (`except: pass`)
3. Hardcoded Secrets (Keys niemals im Repo)
4. UI ohne Wirkung (Buttons ohne komplette Logik)
5. Blindes Vertrauen in REST-„Success“ ohne WS-Bestätigung citeturn1view2turn3view2

### 🔍 BEFORE MARKING COMPLETE:
- [ ] Live-Flow getestet (kleine Size)
- [ ] WS bestätigt Statusübergänge
- [ ] Single-Trade-Gate hält zuverlässig
- [ ] Cancel/Close Pfade funktionieren (inkl. Notfall)

---

## 📊 Status-Legende
- ⬜ Offen / Nicht begonnen
- 🔄 In Arbeit
- ✅ Abgeschlossen
- ❌ Fehler / Blockiert
- ⭐ Übersprungen / Nicht benötigt

## 🛠️ TRACKING-FORMAT (PFLICHT)

### Erfolgreicher Task:
```markdown
- [ ] **1.2.3 Task Name**  
  Status: ✅ Abgeschlossen (YYYY-MM-DD HH:MM) → *Was wurde implementiert*
  Code: `dateipfad:zeilen` (wo implementiert)
  Tests: `test_datei:TestClass` (welche Tests)
  Nachweis: Screenshot/Log-Ausgabe der Funktionalität
```

### Fehlgeschlagener Task:
```markdown
- [ ] **1.2.3 Task Name**  
  Status: ❌ Fehler (YYYY-MM-DD HH:MM) → *Fehlerbeschreibung*
  Fehler: `Exakte Error Message hier`
  Ursache: Was war das Problem
  Lösung: Wie wird es behoben
  Retry: Geplant für YYYY-MM-DD HH:MM
```

### Task in Arbeit:
```markdown
- [ ] **1.2.3 Task Name**  
  Status: 🔄 In Arbeit (Start: YYYY-MM-DD HH:MM) → *Aktueller Fortschritt*
  Fortschritt: 60% - X umgesetzt, Y ausstehend
  Blocker: —
```

---

## Phase 0: Vorbereitung & API-Readiness (10 Tasks)

- [ ] **0.1 API-Key/Secret aus Systemvariablen lesen + Validierung**  
  Status: ⬜ → *Key vorhanden, Secret vorhanden, Format geprüft*
- [ ] **0.2 Bitunix Base-URLs als Config (Futures REST + WS)**  
  Status: ⬜ → *keine Hardcodes im Code*
- [ ] **0.3 Signatur/Nonce/Timestamp Handler (Central)**  
  Status: ⬜ → *einheitlich für alle Requests*
- [ ] **0.4 REST-Client: Retry/Backoff/Timeouts**  
  Status: ⬜ → *429/5xx resilient*
- [ ] **0.5 Logging-Korrelation: trade_context (clientId/orderId/positionId)**  
  Status: ⬜ → *jede Logzeile zuordenbar*
- [ ] **0.6 Rate-Limit Guard (Token-Bucket pro Endpoint-Klasse)**  
  Status: ⬜ → *z.B. modify_order <= 4/s (config)*
- [ ] **0.7 Trading Pair Cache (symbols → precision/limits)** citeturn1view0  
  Status: ⬜ → *Cache + Refresh*
- [ ] **0.8 Healthcheck: get_single_account + market tickers** citeturn4search3turn2search16  
  Status: ⬜ → *UI zeigt „Connected“*
- [ ] **0.9 Sandbox/Small-Size Safety Defaults (qty min, leverage low)**  
  Status: ⬜ → *konservativ*
- [ ] **0.10 Dokumentation: „Was passiert beim Klick?“ (intern)**  
  Status: ⬜ → *kurz, aber präzise*

---

## Phase 1: Hedge Mode + Leverage/Margin Setup (12 Tasks)

- [ ] **1.1 Hedge-Mode Status beim Start prüfen (get_pending_positions liefert positionMode)** citeturn1view4  
  Status: ⬜
- [ ] **1.2 Hedge Mode setzen Button (change_position_mode)** citeturn1view5  
  Status: ⬜
- [ ] **1.3 Fehlerfall: Hedge nicht setzbar wegen offenen Orders/Positionen → UI Warnung** citeturn1view5  
  Status: ⬜
- [ ] **1.4 Leverage setzen (change_leverage) + Validierung (max/min)** citeturn4search0turn1view0  
  Status: ⬜
- [ ] **1.5 Leverage/Margin Mode readback (get_leverage_margin_mode)** citeturn4search4  
  Status: ⬜
- [ ] **1.6 Optional: Margin Mode UI (ISOLATION/CROSS) + Warnung „nicht möglich bei offenen Positionen“** citeturn4search1  
  Status: ⬜
- [ ] **1.7 Trading Pair Limits in UI anzeigen (minTradeVolume, basePrecision, quotePrecision)** citeturn1view0  
  Status: ⬜
- [ ] **1.8 Offset-Range aus Trading Pair Limits ableiten (minBuyPriceOffset/maxSellPriceOffset)** citeturn1view0  
  Status: ⬜
- [ ] **1.9 Persistenz: letzte Werte (symbol/leverage/offset/qty)**  
  Status: ⬜
- [ ] **1.10 Unit Test: Limit/Precision Rounder**  
  Status: ⬜
- [ ] **1.11 Unit Test: Hedge Mode Guard (kein Trade bei falschem Mode)**  
  Status: ⬜
- [ ] **1.12 Audit Log Eintrag pro Konfig-Änderung**  
  Status: ⬜

---

## Phase 2: Single-Trade Controller + WebSocket Truth (18 Tasks)

- [ ] **2.1 State Machine: IDLE/ENTRY_PENDING/POSITION_OPEN/EXIT_PENDING/CLOSED/ERROR_LOCK**  
  Status: ⬜
- [ ] **2.2 Single-Trade Gate: „nur ein aktiver Trade“ (Mutex/Flag + Persistenz)**  
  Status: ⬜
- [ ] **2.3 WS Verbindung aufbauen (Prepare WebSocket + Auth Sign)** citeturn2search5turn2search6  
  Status: ⬜
- [ ] **2.4 Subscribe Order Channel** citeturn3view2  
  Status: ⬜
- [ ] **2.5 Order Events mappen (CREATE/UPDATE/CLOSE → Status)** citeturn3view2  
  Status: ⬜
- [ ] **2.6 OrderStatus Mapping (INIT/NEW/PART_FILLED/FILLED/… )** citeturn3view2  
  Status: ⬜
- [ ] **2.7 Reconnect: WS reconnect + resubscribe + state recovery**  
  Status: ⬜
- [ ] **2.8 Recovery: pending_orders + pending_positions beim Start** citeturn2search3turn1view4  
  Status: ⬜
- [ ] **2.9 UI Statusbar: orderId/positionId/orderStatus/lastEventTs** citeturn3view2  
  Status: ⬜
- [ ] **2.10 Fehlerklassifikation: Signature/Nonce/RateLimit/Validation**  
  Status: ⬜
- [ ] **2.11 Unit Test: State transitions (WS events)**  
  Status: ⬜
- [ ] **2.12 Integration Test: Mock WS + REST**  
  Status: ⬜
- [ ] **2.13 Logging: WS raw events (optional togglable)**  
  Status: ⬜
- [ ] **2.14 Order Correlation: clientId handling (optional)** citeturn1view2  
  Status: ⬜
- [ ] **2.15 “Unlock ERROR_LOCK” Button (mit Warnung)**  
  Status: ⬜
- [ ] **2.16 „Cancel pending order“ Flow (cancel_orders + WS confirm)** citeturn4search2turn3view2  
  Status: ⬜
- [ ] **2.17 Notfall: Flash Close Position Button (positionId)** citeturn3view1  
  Status: ⬜
- [ ] **2.18 Notfall: Close All Position (optional, gated)** citeturn2search1  
  Status: ⬜

---

## Phase 3: Entry Option A (Standard) (14 Tasks)

- [ ] **3.1 UI: Long/Short Pflichtfeld**  
  Status: ⬜
- [ ] **3.2 place_order Builder (HEDGE: side + tradeSide=OPEN)** citeturn1view1  
  Status: ⬜
- [ ] **3.3 OrderType: LIMIT/MARKET + effect (GTC/POST_ONLY/IOC/FOK)** citeturn1view1  
  Status: ⬜
- [ ] **3.4 TP/SL optional im place_order (tpPrice/slPrice + StopTypes)** citeturn1view1  
  Status: ⬜
- [ ] **3.5 Display: returned orderId** citeturn3view2  
  Status: ⬜
- [ ] **3.6 Guard: qty valid (minTradeVolume/basePrecision)** citeturn1view0  
  Status: ⬜
- [ ] **3.7 Guard: price valid (quotePrecision + offsets)** citeturn1view0  
  Status: ⬜
- [ ] **3.8 WS confirms entry order status** citeturn3view2  
  Status: ⬜
- [ ] **3.9 Fill → pending_positions poll to obtain positionId** citeturn1view4  
  Status: ⬜
- [ ] **3.10 Transition to POSITION_OPEN**  
  Status: ⬜
- [ ] **3.11 Unit Test: order payload correctness**  
  Status: ⬜
- [ ] **3.12 Integration Test: small-size end-to-end (mock exchange)**  
  Status: ⬜
- [ ] **3.13 UI: “Cancel Entry” for NEW/PART_FILLED** citeturn4search2turn3view2  
  Status: ⬜
- [ ] **3.14 Safety: max notional / leverage cap rule (config)**  
  Status: ⬜

---

## Phase 4: Entry Option B (Adaptive Limit) (18 Tasks)

- [ ] **4.1 UI: Offset Slider + Editfeld + Persistenz**  
  Status: ⬜
- [ ] **4.2 Preisformel: Long (1+offset), Short (1-offset)**  
  Status: ⬜
- [ ] **4.3 Quantisierung: quotePrecision** citeturn1view0  
  Status: ⬜
- [ ] **4.4 Debounce/Throttle Layer für modify_order (z.B. <=4/s)** citeturn1view2  
  Status: ⬜
- [ ] **4.5 Only-If-Changed: gleiche price nach rounding → kein API call**  
  Status: ⬜
- [ ] **4.6 place_order initial LIMIT (tradeSide=OPEN) → orderId** citeturn1view1  
  Status: ⬜
- [ ] **4.7 modify_order Loop (orderId, qty, price)** citeturn1view2  
  Status: ⬜
- [ ] **4.8 WS-driven stop condition: FILLED/ CANCELED** citeturn3view2  
  Status: ⬜
- [ ] **4.9 Partial fill handling (PART_FILLED)** citeturn3view2  
  Status: ⬜
- [ ] **4.10 Timeout: wenn nach N Sekunden nicht gefüllt → Cancel + ERROR/Retry** citeturn4search2  
  Status: ⬜
- [ ] **4.11 Offset Constraints: minBuyPriceOffset/maxSellPriceOffset** citeturn1view0  
  Status: ⬜
- [ ] **4.12 Rate-limit backoff: 429/5xx**  
  Status: ⬜
- [ ] **4.13 CPU/GUI: Tick-Handler entkoppeln (Queue) – keine UI Freezes**  
  Status: ⬜
- [ ] **4.14 Unit Test: throttle behavior**  
  Status: ⬜
- [ ] **4.15 Unit Test: price calc + rounding**  
  Status: ⬜
- [ ] **4.16 Integration Test: simulate ticks + verify modify calls**  
  Status: ⬜
- [ ] **4.17 UI: Anzeige „last recalculated price“ + „last modify ts“**  
  Status: ⬜
- [ ] **4.18 Safety: kill-switch „Stop Adaptive“**  
  Status: ⬜

---

## Phase 5: Trailing Stop → Exchange SL Sync (24 Tasks)

- [ ] **5.1 POSITION_OPEN: positionId vorhanden** citeturn1view4  
  Status: ⬜
- [ ] **5.2 place_position_tp_sl_order einmalig pro Position** citeturn3view0  
  Status: ⬜
- [ ] **5.3 Store tpslPositionOrderId + UI anzeigen** citeturn3view0  
  Status: ⬜
- [ ] **5.4 Trailing: neuer SL nur „besser“ (Long: höher, Short: niedriger)**  
  Status: ⬜
- [ ] **5.5 modify_position_tp_sl_order für SL Updates** citeturn1view3  
  Status: ⬜
- [ ] **5.6 StopType Default: MARK_PRICE** citeturn1view3turn1view1  
  Status: ⬜
- [ ] **5.7 Debounce SL Updates (z.B. <=2/s)**  
  Status: ⬜
- [ ] **5.8 UI: „Exchange SL aktuell“ + Timestamp**  
  Status: ⬜
- [ ] **5.9 WS: optional TpSl Channel subscribe (falls genutzt)** citeturn2search18  
  Status: ⬜
- [ ] **5.10 Cancel TP/SL Order on close (optional)** citeturn4search5  
  Status: ⬜
- [ ] **5.11 Exit Flow: Flash close oder CLOSE order (je nach Design)** citeturn3view1turn1view1  
  Status: ⬜
- [ ] **5.12 Cleanup: Controller reset auf CLOSED**  
  Status: ⬜
- [ ] **5.13 Integration Test: Trailing updates under ticks**  
  Status: ⬜
- [ ] **5.14 Failure Mode: WS down → fallback polling pending_positions** citeturn1view4  
  Status: ⬜
- [ ] **5.15 Failure Mode: modify SL rejected (validation) → lock + warn**  
  Status: ⬜
- [ ] **5.16 Risk: liquidation proximity warn (liqPrice/marginRate)** citeturn1view4  
  Status: ⬜
- [ ] **5.17 UI: show liqPrice + marginRate** citeturn1view4  
  Status: ⬜
- [ ] **5.18 Persist last good SL + restore after restart**  
  Status: ⬜
- [ ] **5.19 Tick/WS time drift detection (timestamp sanity)**  
  Status: ⬜
- [ ] **5.20 Metrics: counts (modify_order calls, sl updates, rate-limit hits)**  
  Status: ⬜
- [ ] **5.21 Load test: 8h run, no memory leak, stable WS**  
  Status: ⬜
- [ ] **5.22 Final manual QA checklist**  
  Status: ⬜
- [ ] **5.23 Documentation: user workflow in Trading Bot tab**  
  Status: ⬜
- [ ] **5.24 Release: feature flags + safe default off**  
  Status: ⬜


---

## 📈 Fortschritts-Tracking

### Gesamt-Statistik
- **Total Tasks:** 96
- **Abgeschlossen:** 0 (0%)
- **In Arbeit:** 0 (0%)
- **Offen:** 96 (100%)

### Phase-Statistik
| Phase | Tasks | Abgeschlossen | Fortschritt |
|------:|------:|--------------:|:-----------|
| Phase 0 | 10 | 0 | ⬜ 0% |
| Phase 1 | 12 | 0 | ⬜ 0% |
| Phase 2 | 18 | 0 | ⬜ 0% |
| Phase 3 | 14 | 0 | ⬜ 0% |
| Phase 4 | 18 | 0 | ⬜ 0% |
| Phase 5 | 24 | 0 | ⬜ 0% |

### Zeitschätzung (realistisch, ohne Schönreden)
- **Geschätzt:** 40–70 Stunden (je nach vorhandener REST/WS-Basis in deiner Software)
- **Kritisch:** WS-Integration + Recovery + Rate-Limit-Disziplin

---

## 🔥 Kritische Pfade

1) **Phase 0 → Phase 2**: Ohne zentrale Signatur/Retry/RateLimit + WS-State-Machine ist alles andere instabil. citeturn1view2turn3view2  
2) **Phase 4**: Adaptive Limit funktioniert nur, wenn `modify_order` sauber gedrosselt und WS-getrieben ist. citeturn1view2turn3view2  
3) **Phase 5**: Trailing Stop ist nur seriös, wenn „1 Position-TP/SL pro Position“ eingehalten wird. citeturn3view0  

---

## 📝 Notizen & Risiken

### Identifizierte Risiken
1. **REST Success ≠ Trade Success** → ohne WS bestätigst du falsche Zustände. citeturn1view2turn3view2  
2. **Rate-Limit/Spam** bei tickbasiertem modify → 429/Lockouts/Verzögerungen. citeturn1view2turn1view0  
3. **Partial Fills** → falsches Nachziehen oder falsche Qty-Logik. citeturn3view2  
4. **Mode-Switch Fail** (HEDGE) wenn Orders/Positionen offen sind. citeturn1view5  
5. **Time Drift** (Client ↔ Exchange) → Signaturfehler/Nonce-Fehler.

### Mitigation
- WS als Wahrheit, REST nur als Trigger. citeturn3view2  
- Token-Bucket + Debounce + Only-If-Changed.
- Recovery beim Start: pending_orders/pending_positions laden. citeturn2search3turn1view4  
- Klare ERROR_LOCK + Unlock nur manuell.

---

## 🎯 Qualitätsziele

### Performance Targets
- **UI Responsiveness:** <100ms (Tick-Handler darf UI nie blockieren)
- **Adaptive Limit Updates:** max. 2–4 modify/s (konfigurierbar)
- **WS Uptime:** stabil 8h (Reconnect getestet)

### Safety Targets
- **Kein zweiter Trade möglich** solange einer aktiv ist (Single-Trade-Gate).
- **SL Pflicht** (Default: MARK_PRICE) citeturn1view1turn1view3  
- **Notfall-Button:** Flash Close verfügbar. citeturn3view1  
