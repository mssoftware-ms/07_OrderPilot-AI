Hier ist die Rechnung **nach Bitunix Gebührenstruktur** für **BTCUSDT-Futures** bei **20× Hebel**, wenn du mit **100€ (≈ 100 USDT) Margin** eine Position öffnest und sie später mit **130€ Kontostand (≈ +30€ Gewinn auf Margin)** wieder schließt.

Bitunix Futures-Gebühren (VIP 0) laut offizieller Bitunix-Tabelle:

* **Maker:** 0,02%
* **Taker:** 0,06% ([Bitunix Hilfezentrum][1])

---

## 1) Ausgangsdaten

* **Margin (Einsatz)**: 100
* **Hebel**: 20×
  ➡️ **Positionsgröße / Notional beim Einstieg**
  [
  Notional_{open} = 100 \times 20 = 2000
  ]

Du sagst: **100€ buy → 130€ sell** (also **+30% auf Margin**).
Bei Futures bedeutet das: der Basispreis (BTC) ist nur um
[
r = \frac{30%}{20} = 1{,}5%
]
gestiegen.

➡️ **Notional beim Schließen** (Position ist gleich groß, aber Preis höher):
[
Notional_{close} = 2000 \times (1+0{,}015) = 2030
]

---

## 2) Gebühren rechnen (Taker = Market Order, typisch beim Scalping)

**Bitunix Taker Fee = 0,06% = 0,0006** ([Bitunix Hilfezentrum][1])

### Einstieg (Buy / Open)

[
Fee_{open} = 2000 \times 0{,}0006 = 1{,}20
]

### Ausstieg (Sell / Close)

[
Fee_{close} = 2030 \times 0{,}0006 = 1{,}218
]

### Gesamtgebühr (Roundtrip)

[
Fee_{total} = 1{,}20 + 1{,}218 = 2{,}418
]

✅ **Ergebnis (Taker/Taker): ca. 2,42 Gebühren**

---

## 3) Gebühren rechnen (Maker = Limit Order, wenn du ins Orderbuch legst)

**Bitunix Maker Fee = 0,02% = 0,0002** ([Bitunix Hilfezentrum][1])

### Einstieg

[
Fee_{open} = 2000 \times 0{,}0002 = 0{,}40
]

### Ausstieg

[
Fee_{close} = 2030 \times 0{,}0002 = 0{,}406
]

### Gesamt

[
Fee_{total} = 0{,}40 + 0{,}406 = 0{,}806
]

✅ **Ergebnis (Maker/Maker): ca. 0,81 Gebühren**

---

## 4) Was bleibt von deinen +30€ Gewinn übrig?

Dein **Brutto-Gewinn auf Margin** wäre:
[
Profit_{gross} = 130 - 100 = 30
]

### Wenn du Taker/Taker machst:

[
Profit_{net} = 30 - 2{,}418 = 27{,}582
]
➡️ **Endstand ≈ 127,58** statt 130

### Wenn du Maker/Maker machst:

[
Profit_{net} = 30 - 0{,}806 = 29{,}194
]
➡️ **Endstand ≈ 129,19** statt 130

---

## Wichtiger Hinweis (realistisch in Futures)

Zusätzlich zu Trading Fees kann bei Perpetual Futures noch **Funding** anfallen (je nach Zeitpunkt/Haltedauer). Das ist **nicht** in der obigen Rechnung enthalten, weil du explizit nach **Gebühren** gefragt hast. ([Bitunix][2])

Wenn du willst, rechne ich dir als Nächstes noch **Funding + Slippage** realistisch mit rein (für Scalping macht das richtig Unterschied).

[1]: https://support.bitunix.com/hc/en-us/articles/14042741811865-Bitunix-Trading-Fees-and-VIP-System "Bitunix Trading Fees and VIP System – Bitunix Help Center"
[2]: https://blog.bitunix.com/en/copy-trading-fees-on-bitunix-what-you-pay-what-you-keep-and-how-to-plan/?utm_source=chatgpt.com "Copy Trading Fees Explained: What You Pay and What ..."
