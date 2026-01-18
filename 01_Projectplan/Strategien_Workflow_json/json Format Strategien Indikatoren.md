Trading-Bot Konfigurationsschema
Kurzkonzept

Schema-Version & Metadaten: Enthält schema_version zur Format-Versionierung und eine metadata-Sektion (Autor, Erstellungsdatum, Tags, Notizen, optional z.B. dataset_id für Backtests). Dies ermöglicht Kontextinformationen und zukünftige Erweiterungen ohne bestehende Struktur zu brechen.

Indikatoren: Eine Liste von indicators mit vordefinierten technischen Indikatoren, jeweils mit eindeutigem id, type (z.B. RSI, SMA, MACD, ATR), konfigurierenden params (z.B. Periodenlänge) und optionalem timeframe. Indikatoren sind wiederverwendbare Bausteine, auch Multi-Timeframe fähig (ein Indikator kann auf anderem Zeitrahmen basieren) und werden über ihre IDs referenziert.

Regimes (Marktphasen): Eine Liste von regimes, die Marktregime oder -situationen definieren (z.B. Seitwärtsmarkt, Trendmarkt, Low-Volume). Jedes Regime hat eine eindeutige id, einen name und Aktivierungsbedingungen (conditions). Die Bedingungen sind logische Regeln auf Indikator-Outputs (mit Operatoren gt, lt, eq, between) – z.B. “ADX > 25 auf mehreren Zeitrahmen” definiert einen Trendmarkt. Optional können Regimes ein priority-Level (zur Priorisierung bei Überlappungen) und einen scope (entry, exit, in_trade) erhalten, um ihren Geltungsbereich anzugeben. Mehrere Regimes können gleichzeitig aktiv sein (z.B. ein Entry-Regime und ein Exit-Regime parallel).

Strategien: Eine Liste von strategies beschreibt einzelne Handelsstrategien. Jede Strategie hat eine eindeutige id und einen name, sowie mindestens Felder für entry (wann eingestiegen wird), exit (wann ausgestiegen wird) und risk (Risikomanagement). entry und exit enthalten optional Bedingungen/Regeln (im gleichen Format wie Regime-Bedingungen) für Signale, während risk Parameter wie Stop-Loss, Take-Profit, Trailing-Stop etc. umfasst. Diese Struktur erlaubt die Abbildung von Entry/Exit-Logik und Risikoparametern einer Strategie, ohne eine komplexe DSL zu benötigen – Strategieregeln können entweder direkt konfiguriert oder in der Code-Logik hinterlegt sein, während das Schema zumindest die wichtigsten Parameter vorgibt.

Strategy-Sets: In strategy_sets werden Strategien zu Sets gebündelt, die in bestimmten Regime-Konstellationen aktiv sein sollen. Jedes Strategy-Set hat eine id, einen name und enthält eine Liste von strategies (Verweise auf Strategy-IDs). Zusätzlich können pro Set Parameter-Overrides definiert werden, um Strategien oder Indikatoren in diesem Kontext anzupassen, ohne sie zu duplizieren. Beispielsweise können in einem Trend-Set Indikator-Parameter (z.B. RSI-Periode) oder Strategie-Risiko-Einstellungen (z.B. engere Stop-Losses) überschrieben werden, um sie an die Marktphase anzupassen.

Routing (Regime → Strategiezuordnung): Die routing-Sektion enthält Regeln, welche Strategy-Sets aktiviert werden, abhängig von der aktuellen Kombination aktiver Regimes. Jede Routing-Regel besteht aus einem match-Kriterium und einem strategy_set_id. Das match-Objekt kann angeben, welche Regime-IDs gleichzeitig aktiv sein müssen (all_of), mindestens aktiv sein müssen (any_of) und nicht aktiv sein dürfen (none_of), damit die zugeordnete Strategiegruppe greift. Dadurch können komplexe Kombinationen abgebildet werden – z.B. “wenn Regime=Trend und kein Exit-Warnsignal-Regime aktiv, dann Strategy-Set A”, oder “wenn Regime=Trend und (LowVolume oder Trendwechsel-Regime aktiv), dann Strategy-Set B”. Mehrere Regime können also parallel berücksichtigt werden (z.B. getrennte Entry- und Exit-Regime), ohne das Schema zu verkomplizieren.

JSON Schema (Draft 2020-12)
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://example.com/trading-bot-config.schema.json",
  "title": "Trading Bot Configuration Schema",
  "description": "JSON Schema für die Konfiguration von Trading-Bot Indikatoren, Regimes und Strategien.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "schema_version",
    "indicators",
    "regimes",
    "strategies",
    "strategy_sets",
    "routing"
  ],
  "properties": {
    "schema_version": {
      "type": "string",
      "description": "Schema-/Konfigurations-Versionskennung für Kompatibilität."
    },
    "metadata": {
      "type": "object",
      "description": "Metadaten zur Konfiguration (Autor, Erstellungsdatum, Tags, Notizen, etc.).",
      "properties": {
        "author": {
          "type": "string",
          "description": "Autor oder Ersteller der Konfiguration."
        },
        "created_at": {
          "type": "string",
          "format": "date-time",
          "description": "Erstellungs- bzw. Zeitstempel der Konfiguration."
        },
        "tags": {
          "type": "array",
          "description": "Liste von Schlagwörtern/Tags für diese Konfiguration.",
          "items": {
            "type": "string"
          }
        },
        "notes": {
          "type": "string",
          "description": "Freitext-Notizen oder Beschreibung der Konfiguration."
        },
        "dataset_id": {
          "type": "string",
          "description": "Identifier des Datensatzes/Marktumfelds (z.B. für Backtests)."
        }
      },
      "additionalProperties": true
    },
    "indicators": {
      "type": "array",
      "description": "Liste der Indikator-Definitionen, die in Bedingungen referenziert werden können.",
      "items": {
        "type": "object",
        "required": ["id", "type", "params"],
        "properties": {
          "id": {
            "type": "string",
            "description": "Eindeutiger Bezeichner für den Indikator (wird in Bedingungen referenziert)."
          },
          "type": {
            "type": "string",
            "description": "Indikator-Typ/Name (z.B. RSI, SMA, MACD, ATR, Volume ...)."
          },
          "params": {
            "type": "object",
            "description": "Parameter des Indikators (z.B. Periodenlänge, etc.).",
            "additionalProperties": true
          },
          "timeframe": {
            "type": "string",
            "description": "Optionaler Zeitraum/Timeframe des Indikators (z.B. '5m', '1h', '1d'; wenn nicht angegeben, gilt der Standard-Zeitraum)."
          }
        },
        "additionalProperties": false
      }
    },
    "regimes": {
      "type": "array",
      "description": "Definitionen von Marktregimes (Marktphasen) mit Aktivierungsbedingungen.",
      "items": {
        "type": "object",
        "required": ["id", "name", "conditions"],
        "properties": {
          "id": {
            "type": "string",
            "description": "Eindeutiger Regime-Bezeichner."
          },
          "name": {
            "type": "string",
            "description": "Anzeigename des Regimes (für Logging/Dokumentation)."
          },
          "conditions": {
            "type": "object",
            "description": "Bedingungen, unter denen dieses Regime als 'aktiv' gilt.",
            "properties": {
              "all": {
                "type": "array",
                "description": "Alle Bedingungen in dieser Liste müssen erfüllt sein (logisches UND).",
                "items": { "$ref": "#/$defs/Condition" }
              },
              "any": {
                "type": "array",
                "description": "Mindestens eine der Bedingungen in dieser Liste muss erfüllt sein (logisches ODER).",
                "items": { "$ref": "#/$defs/Condition" }
              }
            },
            "additionalProperties": false
          },
          "priority": {
            "type": "number",
            "description": "Optionale Priorität des Regimes (höherer Wert = wichtiger bei Konflikten)."
          },
          "scope": {
            "type": "string",
            "description": "Optionaler Geltungsbereich des Regimes (z.B. 'entry', 'exit', 'in_trade'; ohne Angabe gilt global).",
            "enum": ["entry", "exit", "in_trade"]
          }
        },
        "additionalProperties": false
      }
    },
    "strategies": {
      "type": "array",
      "description": "Definition einzelner Handelsstrategien (Entry/Exit-Regeln und Risikoparameter).",
      "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
          "id": {
            "type": "string",
            "description": "Eindeutiger Strategie-Bezeichner."
          },
          "name": {
            "type": "string",
            "description": "Name der Strategie (beschreibend)."
          },
          "entry": {
            "description": "Einstiegssignal-Bedingungen der Strategie (wann gekauft wird).",
            "$ref": "#/$defs/ConditionGroup"
          },
          "exit": {
            "description": "Ausstiegssignal-Bedingungen der Strategie (wann verkauft wird).",
            "$ref": "#/$defs/ConditionGroup"
          },
          "risk": {
            "type": "object",
            "description": "Risikomanagement-Parameter der Strategie.",
            "properties": {
              "stop_loss_pct": {
                "type": "number",
                "description": "Stop-Loss in % vom Einstiegs-/Kaufpreis."
              },
              "take_profit_pct": {
                "type": "number",
                "description": "Take-Profit in % vom Einstiegs-/Kaufpreis."
              },
              "trailing_mode": {
                "type": "string",
                "description": "Trailing-Stop Modus (z.B. 'percent' oder 'atr')."
              },
              "trailing_multiplier": {
                "type": "number",
                "description": "Multiplikator für den Trailing-Stop (z.B. ATR-Faktor oder Prozentwert)."
              },
              "risk_per_trade_pct": {
                "type": "number",
                "description": "Max. pro Trade zu riskierender Anteil der Account-Equity (in %)."
              }
            },
            "additionalProperties": false
          }
        },
        "additionalProperties": false
      }
    },
    "strategy_sets": {
      "type": "array",
      "description": "Strategie-Sets (Bündel von Strategien) inklusive etwaiger Parameter-Überschreibungen für bestimmte Regime.",
      "items": {
        "type": "object",
        "required": ["id", "strategies"],
        "properties": {
          "id": {
            "type": "string",
            "description": "Eindeutiger Bezeichner des Strategy-Sets."
          },
          "name": {
            "type": "string",
            "description": "Anzeigename des Strategy-Sets."
          },
          "strategies": {
            "type": "array",
            "description": "Liste der in diesem Set aktiven Strategien (Verweis auf Strategy-IDs) mit möglichen Overrides.",
            "items": {
              "type": "object",
              "required": ["strategy_id"],
              "properties": {
                "strategy_id": {
                  "type": "string",
                  "description": "Referenz auf die ID einer Basis-Strategie."
                },
                "strategy_overrides": {
                  "type": "object",
                  "description": "Optionale Überschreibungen für Strategie-Parameter in diesem Set.",
                  "properties": {
                    "entry": {
                      "description": "Override der Entry-Bedingungen dieser Strategie im Set.",
                      "$ref": "#/$defs/ConditionGroup"
                    },
                    "exit": {
                      "description": "Override der Exit-Bedingungen dieser Strategie im Set.",
                      "$ref": "#/$defs/ConditionGroup"
                    },
                    "risk": {
                      "$ref": "#/$defs/RiskSettings",
                      "description": "Override der Risikoparameter dieser Strategie im Set."
                    }
                  },
                  "additionalProperties": false
                }
              },
              "additionalProperties": false
            }
          },
          "indicator_overrides": {
            "type": "array",
            "description": "Liste von Indikator-Parameter-Überschreibungen in diesem Set.",
            "items": {
              "type": "object",
              "required": ["indicator_id", "params"],
              "properties": {
                "indicator_id": {
                  "type": "string",
                  "description": "ID eines Indikators, der in diesem Set anders parametriert werden soll."
                },
                "params": {
                  "type": "object",
                  "description": "Neue Parameterwerte für den Indikator innerhalb dieses Sets.",
                  "additionalProperties": true
                }
              },
              "additionalProperties": false
            }
          }
        },
        "additionalProperties": false
      }
    },
    "routing": {
      "type": "array",
      "description": "Regeln zur Zuordnung von aktiven Regime-Kombinationen zu Strategy-Sets.",
      "items": {
        "type": "object",
        "required": ["strategy_set_id", "match"],
        "properties": {
          "strategy_set_id": {
            "type": "string",
            "description": "ID des Strategy-Sets, das aktiviert werden soll, wenn die Bedingung erfüllt ist."
          },
          "match": {
            "type": "object",
            "description": "Kriterium (aktive Regimes) für diese Routing-Regel.",
            "properties": {
              "all_of": {
                "type": "array",
                "description": "Liste von Regime-IDs, die alle aktiv sein müssen (UND-Bedingung).",
                "items": { "type": "string" }
              },
              "any_of": {
                "type": "array",
                "description": "Liste von Regime-IDs, von denen mindestens eine aktiv sein muss (ODER-Bedingung).",
                "items": { "type": "string" }
              },
              "none_of": {
                "type": "array",
                "description": "Liste von Regime-IDs, die **nicht** aktiv sein dürfen.",
                "items": { "type": "string" }
              }
            },
            "additionalProperties": false
          }
        },
        "additionalProperties": false
      }
    }
  },
  "$defs": {
    "Condition": {
      "type": "object",
      "description": "Einzelne Vergleichsbedingung zwischen einem Indikator-Output und einem Wert oder anderen Indikator.",
      "required": ["left", "op", "right"],
      "properties": {
        "left": {
          "description": "Linker Operand: Referenz auf Indikator-Wert oder Konstantwert.",
          "oneOf": [
            {
              "type": "object",
              "required": ["indicator_id", "field"],
              "properties": {
                "indicator_id": {
                  "type": "string",
                  "description": "Referenz auf eine Indikator-ID."
                },
                "field": {
                  "type": "string",
                  "description": "Ausgabefeld des Indikators (z.B. 'value', 'signal', 'histogram')."
                }
              },
              "additionalProperties": false
            },
            {
              "type": "object",
              "required": ["value"],
              "properties": {
                "value": {
                  "type": "number",
                  "description": "Konstanter Zahlenwert."
                }
              },
              "additionalProperties": false
            }
          ]
        },
        "op": {
          "type": "string",
          "description": "Vergleichsoperator: größer, kleiner, gleich oder zwischen zwei Werten.",
          "enum": ["gt", "lt", "eq", "between"]
        },
        "right": {
          "description": "Rechter Operand: Indikator-Referenz, Konstantwert oder Zahlenbereich (bei 'between')."
        }
      },
      "additionalProperties": false,
      "allOf": [
        {
          "if": {
            "properties": { "op": { "const": "between" } }
          },
          "then": {
            "properties": {
              "right": {
                "type": "object",
                "required": ["min", "max"],
                "properties": {
                  "min": {
                    "type": "number",
                    "description": "Minimalwert (inklusive) für 'between'-Vergleich."
                  },
                  "max": {
                    "type": "number",
                    "description": "Maximalwert (inklusive) für 'between'-Vergleich."
                  }
                },
                "additionalProperties": false
              }
            }
          },
          "else": {
            "properties": {
              "right": {
                "oneOf": [
                  {
                    "type": "object",
                    "required": ["indicator_id", "field"],
                    "properties": {
                      "indicator_id": { "type": "string" },
                      "field": { "type": "string" }
                    },
                    "additionalProperties": false
                  },
                  {
                    "type": "object",
                    "required": ["value"],
                    "properties": {
                      "value": { "type": "number" }
                    },
                    "additionalProperties": false
                  }
                ]
              }
            }
          }
        }
      ]
    },
    "ConditionGroup": {
      "type": "object",
      "description": "Gruppe von Bedingungen (all/any), die als Block ausgewertet werden.",
      "properties": {
        "all": {
          "type": "array",
          "description": "Alle aufgeführten Bedingungen müssen wahr sein.",
          "items": { "$ref": "#/$defs/Condition" }
        },
        "any": {
          "type": "array",
          "description": "Mindestens eine der aufgeführten Bedingungen muss wahr sein.",
          "items": { "$ref": "#/$defs/Condition" }
        }
      },
      "additionalProperties": false,
      "anyOf": [
        { "required": ["all"] },
        { "required": ["any"] }
      ]
    },
    "RiskSettings": {
      "type": "object",
      "description": "Risikoparameter-Überschreibungen.",
      "properties": {
        "stop_loss_pct": { "type": "number" },
        "take_profit_pct": { "type": "number" },
        "trailing_mode": { "type": "string" },
        "trailing_multiplier": { "type": "number" },
        "risk_per_trade_pct": { "type": "number" }
      },
      "additionalProperties": false
    }
  }
}

Beispiel A: Grundkonfiguration (Indikatoren & Regimes mit Multi-Timeframe)
{
  "schema_version": "1.0",
  "metadata": {
    "author": "Max Mustermann",
    "created_at": "2026-01-17T22:31:48Z",
    "tags": ["example", "strategy", "regimes"],
    "notes": "Example A: Basic setup with multi-timeframe indicators and simple regimes."
  },
  "indicators": [
    { "id": "rsi14_1h", "type": "RSI", "params": { "period": 14 }, "timeframe": "1h" },
    { "id": "adx14_1h", "type": "ADX", "params": { "period": 14 }, "timeframe": "1h" },
    { "id": "adx14_4h", "type": "ADX", "params": { "period": 14 }, "timeframe": "4h" },
    { "id": "vol_ratio_1h", "type": "VolumeRatio", "params": { "period": 20 }, "timeframe": "1h" }
  ],
  "regimes": [
    {
      "id": "trend",
      "name": "Trending Market",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "adx14_1h", "field": "value" }, "op": "gt", "right": { "value": 25 } },
          { "left": { "indicator_id": "adx14_4h", "field": "value" }, "op": "gt", "right": { "value": 25 } }
        ]
      }
    },
    {
      "id": "range",
      "name": "Range-Bound Market",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "adx14_1h", "field": "value" }, "op": "lt", "right": { "value": 20 } },
          { "left": { "indicator_id": "adx14_4h", "field": "value" }, "op": "lt", "right": { "value": 20 } }
        ]
      }
    },
    {
      "id": "low_vol",
      "name": "Low Volume",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "vol_ratio_1h", "field": "value" }, "op": "lt", "right": { "value": 0.5 } }
        ]
      }
    }
  ],
  "strategies": [
    {
      "id": "trend_follow",
      "name": "Trend Following",
      "entry": {
        "all": [
          { "left": { "indicator_id": "adx14_1h", "field": "value" }, "op": "gt", "right": { "value": 25 } },
          { "left": { "indicator_id": "rsi14_1h", "field": "value" }, "op": "gt", "right": { "value": 60 } }
        ]
      },
      "exit": {
        "any": [
          { "left": { "indicator_id": "adx14_1h", "field": "value" }, "op": "lt", "right": { "value": 20 } },
          { "left": { "indicator_id": "rsi14_1h", "field": "value" }, "op": "lt", "right": { "value": 40 } }
        ]
      },
      "risk": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 5.0
      }
    },
    {
      "id": "mean_reversion",
      "name": "Mean Reversion",
      "entry": {
        "any": [
          { "left": { "indicator_id": "rsi14_1h", "field": "value" }, "op": "lt", "right": { "value": 30 } },
          { "left": { "indicator_id": "rsi14_1h", "field": "value" }, "op": "gt", "right": { "value": 70 } }
        ]
      },
      "exit": {
        "all": [
          { "left": { "indicator_id": "rsi14_1h", "field": "value" }, "op": "between", "right": { "min": 45, "max": 55 } }
        ]
      },
      "risk": {
        "stop_loss_pct": 1.5,
        "take_profit_pct": 3.0
      }
    }
  ],
  "strategy_sets": [
    {
      "id": "set_trend",
      "name": "Trending Strategies",
      "strategies": [
        {
          "strategy_id": "trend_follow",
          "strategy_overrides": {
            "risk": {
              "stop_loss_pct": 3.0,
              "take_profit_pct": 6.0
            }
          }
        }
      ],
      "indicator_overrides": [
        {
          "indicator_id": "rsi14_1h",
          "params": { "period": 21 }
        }
      ]
    },
    {
      "id": "set_range",
      "name": "Range Strategies",
      "strategies": [
        {
          "strategy_id": "mean_reversion"
        }
      ],
      "indicator_overrides": [
        {
          "indicator_id": "rsi14_1h",
          "params": { "period": 7 }
        }
      ]
    }
  ],
  "routing": [
    {
      "strategy_set_id": "set_trend",
      "match": { "all_of": ["trend"] }
    },
    {
      "strategy_set_id": "set_range",
      "match": { "all_of": ["range"] }
    }
  ]
}

Beispiel B: Regime-Routing mit Entry- und Exit-Regimes (gleichzeitig aktive Regimes)
{
  "schema_version": "1.0",
  "metadata": {
    "author": "Max Mustermann",
    "created_at": "2026-01-17T22:31:48Z",
    "tags": ["example", "routing", "multi-regime"],
    "notes": "Example B: Routing with simultaneous entry/exit regimes."
  },
  "indicators": [
    { "id": "rsi14", "type": "RSI", "params": { "period": 14 }, "timeframe": "1h" },
    { "id": "adx14", "type": "ADX", "params": { "period": 14 }, "timeframe": "1h" },
    { "id": "vol_ratio", "type": "VolumeRatio", "params": { "period": 20 }, "timeframe": "1h" }
  ],
  "regimes": [
    {
      "id": "entry_trend",
      "name": "Entry Regime - Trending",
      "scope": "entry",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "adx14", "field": "value" }, "op": "gt", "right": { "value": 25 } }
        ]
      }
    },
    {
      "id": "entry_range",
      "name": "Entry Regime - Range",
      "scope": "entry",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "adx14", "field": "value" }, "op": "lt", "right": { "value": 20 } }
        ]
      }
    },
    {
      "id": "exit_low_vol",
      "name": "Exit Regime - Low Volume",
      "scope": "exit",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "vol_ratio", "field": "value" }, "op": "lt", "right": { "value": 0.5 } }
        ]
      }
    },
    {
      "id": "exit_trend_reversal",
      "name": "Exit Regime - Trend Reversal",
      "scope": "exit",
      "conditions": {
        "all": [
          { "left": { "indicator_id": "adx14", "field": "value" }, "op": "lt", "right": { "value": 20 } }
        ]
      }
    }
  ],
  "strategies": [
    {
      "id": "trend_follow",
      "name": "Trend Following",
      "entry": {
        "all": [
          { "left": { "indicator_id": "adx14", "field": "value" }, "op": "gt", "right": { "value": 25 } },
          { "left": { "indicator_id": "rsi14", "field": "value" }, "op": "gt", "right": { "value": 60 } }
        ]
      },
      "exit": {
        "any": [
          { "left": { "indicator_id": "adx14", "field": "value" }, "op": "lt", "right": { "value": 20 } },
          { "left": { "indicator_id": "rsi14", "field": "value" }, "op": "lt", "right": { "value": 40 } }
        ]
      },
      "risk": {
        "stop_loss_pct": 2.0,
        "take_profit_pct": 5.0
      }
    },
    {
      "id": "mean_reversion",
      "name": "Mean Reversion",
      "entry": {
        "any": [
          { "left": { "indicator_id": "rsi14", "field": "value" }, "op": "lt", "right": { "value": 30 } },
          { "left": { "indicator_id": "rsi14", "field": "value" }, "op": "gt", "right": { "value": 70 } }
        ]
      },
      "exit": {
        "all": [
          { "left": { "indicator_id": "rsi14", "field": "value" }, "op": "between", "right": { "min": 45, "max": 55 } }
        ]
      },
      "risk": {
        "stop_loss_pct": 1.5,
        "take_profit_pct": 3.0
      }
    }
  ],
  "strategy_sets": [
    {
      "id": "set_trend_normal",
      "name": "Trend - Normal Conditions",
      "strategies": [
        { "strategy_id": "trend_follow" }
      ]
    },
    {
      "id": "set_trend_exit",
      "name": "Trend - Exit Signals Active",
      "strategies": [
        {
          "strategy_id": "trend_follow",
          "strategy_overrides": {
            "risk": {
              "stop_loss_pct": 1.0,
              "take_profit_pct": 2.0
            }
          }
        }
      ]
    },
    {
      "id": "set_range_normal",
      "name": "Range - Normal Conditions",
      "strategies": [
        { "strategy_id": "mean_reversion" }
      ]
    },
    {
      "id": "set_range_exit",
      "name": "Range - Exit Signals Active",
      "strategies": [
        {
          "strategy_id": "mean_reversion",
          "strategy_overrides": {
            "risk": {
              "stop_loss_pct": 1.0,
              "take_profit_pct": 2.0
            }
          }
        }
      ]
    }
  ],
  "routing": [
    {
      "strategy_set_id": "set_trend_normal",
      "match": {
        "all_of": ["entry_trend"],
        "none_of": ["exit_low_vol", "exit_trend_reversal"]
      }
    },
    {
      "strategy_set_id": "set_trend_exit",
      "match": {
        "all_of": ["entry_trend"],
        "any_of": ["exit_low_vol", "exit_trend_reversal"]
      }
    },
    {
      "strategy_set_id": "set_range_normal",
      "match": {
        "all_of": ["entry_range"],
        "none_of": ["exit_low_vol", "exit_trend_reversal"]
      }
    },
    {
      "strategy_set_id": "set_range_exit",
      "match": {
        "all_of": ["entry_range"],
        "any_of": ["exit_low_vol", "exit_trend_reversal"]
      }
    }
  ]
}

Design-Notizen

Versionierung & Erweiterbarkeit: Das Schema enthält ein Feld schema_version, um künftige Änderungen im Konfigurationsformat zu kennzeichnen. Neue Felder und Werte können als optionale Felder hinzugefügt werden (anstatt bestehende zu ändern oder zu entfernen), was Abwärtskompatibilität erleichtert. Beispiel: Weitere Indikator-Typen, zusätzliche Regime-Scopes oder neue Risiko-Parameter können ergänzt werden, ohne alte Konfigurationen ungültig zu machen. Clients können anhand der schema_version entscheiden, wie eine Konfiguration interpretiert wird, und bei größeren Änderungen kann die Version hochgesetzt werden.

Eindeutige IDs & Referenzen: Alle wichtigen Objekte (Indikatoren, Regimes, Strategien, Strategy-Sets) besitzen eindeutige id-Felder. Diese IDs dienen als stabile Referenzen im gesamten Schema (z.B. in Bedingungen oder Routing-Regeln). Dadurch sind die Elemente voneinander entkoppelt und wiederverwendbar – man kann frei neue Indikatoren, Regimes oder Strategien hinzufügen und in den Bedingungen/Zuordnungen referenzieren, ohne andere Teile zu duplizieren oder zu ändern. Namenskonvention: Es bietet sich an, IDs sprechend und konsistent zu wählen (z.B. Kleinschreibung und Unterstriche, ggf. Timeframe/Perioden in der ID wie rsi14_1h), damit Verweise eindeutig und verständlich bleiben.

Flache Hierarchien & Stabilität: Die JSON-Struktur wurde bewusst wenig tief verschachtelt und mit klaren, festen Feldnamen gestaltet. Dies erleichtert dem Bot das Parsen und macht die Konfigurationsdatei übersichtlich. Durch die Nutzung von Arrays mit Objekten und separaten Referenz-IDs wird vermieden, dass Einstellungen mehrfach an unterschiedlichen Stellen gepflegt werden müssen. Änderungen an einem Indikator (z.B. Parameter-Override in einem Set) erfolgen an einer Stelle und propagieren über Referenzen, anstatt überall kopiert zu werden.

Einfache Regellogik: Anstatt einer komplexen DSL wurden einfache, gut validierbare Vergleiche (gt, lt, eq, between) und logische Verknüpfungen (all, any) gewählt. Damit können gängige Bedingungen (Schwellenwerte, Indikator-Kreuzungen via >/<, Wertebereiche) flexibel formuliert werden, ohne den Parser oder Nutzer zu überfordern. Kombinierte Bedingungen (UND/ODER) sind durch strukturierte Objekte abgedeckt. Bei Bedarf ließe sich dieses Schema durch weitere Operatoren oder Bedingungstypen erweitern, ohne die Grundstruktur zu ändern (z.B. könnte man einen cross-Operator hinzufügen).

Strategy-Overrides & keine Duplikate: Das Schema erlaubt es, Konfigurationen für unterschiedliche Marktphasen anzupassen, ohne redundante Einträge. Durch strategy_sets können mehrere Strategien gemeinsam aktiviert oder deaktiviert werden. Über die Felder strategy_overrides und indicator_overrides in einem Set lassen sich bestimmte Parameter an die Situation anpassen (z.B. aggressivere Stops in volatileren Phasen, andere Indikator-Perioden in Trendphasen), ohne die Basis-Strategie oder den Indikator mehrfach definieren zu müssen. So bleiben alte Konfigurationen gültig, da neue Anpassungen als zusätzliche optionale Layer erfolgen.

Wartbarkeit & Rückwärtskompatibilität: Dank der JSON Schema-Definition (Draft 2020-12) kann jede Konfigurationsdatei automatisch validiert werden, was Tippfehler oder strukturelle Fehler frühzeitig aufdeckt. Sollten zukünftige Änderungen nötig sein, können diese entweder durch optionale Felder oder neue Versionen umgesetzt werden. Altere Bots können anhand von schema_version nicht unterstützte Konfigurationen ablehnen oder ignorieren, während neuere Bots zusätzliche Felder einfach lesen können. Insgesamt wurde das Format bewusst so gestaltet, dass Erweiterungen (neue Indikatoren, Regimes, Strategien, Felder) möglich sind, ohne bestehende Felder zu verändern – dies minimiert Breaking Changes und unterstützt eine schrittweise Evolution der Konfigurationsmöglichkeiten.