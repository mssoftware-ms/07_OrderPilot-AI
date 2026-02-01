# 📝 Naming Conventions

## UI-Elemente (objectName)

| Typ      | Prefix  | Beispiel                              |
| -------- | ------- | ------------------------------------- |
| Button   | `btn_`  | `btn_start_bot`, `btn_close_position` |
| Label    | `lbl_`  | `lbl_current_price`, `lbl_pnl`        |
| LineEdit | `txt_`  | `txt_symbol`, `txt_quantity`          |
| ComboBox | `cmb_`  | `cmb_timeframe`, `cmb_strategy`       |
| CheckBox | `chk_`  | `chk_trailing_stop`, `chk_auto_close` |
| SpinBox  | `spn_`  | `spn_stop_loss`, `spn_take_profit`    |
| GroupBox | `grp_`  | `grp_position`, `grp_order_settings`  |
| Tab      | `tab_`  | `tab_trading`, `tab_backtest`         |
| Dock     | `dock_` | `dock_watchlist`, `dock_activity_log` |

## Widget-Hierarchie für F12 Inspector
```
{window}_{tab}_{group}_{element}
Beispiel: chart_window.trading_tab.position_group.lbl_pnl
```

## Python-Klassen

| Typ     | Pattern                 | Beispiel                          |
| ------- | ----------------------- | --------------------------------- |
| Mixin   | `*Mixin`                | `PanelsMixin`, `EventBusMixin`    |
| Widget  | `*Widget`               | `TradingWidget`, `ChartWidget`    |
| Dialog  | `*Dialog`               | `SettingsDialog`, `OrderDialog`   |
| Window  | `*Window`               | `ChartWindow`, `TradingBotWindow` |
| Service | `*Service` / `*Manager` | `OrderService`, `HistoryManager`  |

## Signale
```python
# Pattern: {action}_{object}
price_updated = pyqtSignal(float)
position_opened = pyqtSignal(dict)
order_filled = pyqtSignal(str, float)
```

## Dateien
- Mixins: `*_mixin.py`
- Setup-Helper: `*_setup.py`
- Handlers: `*_handlers.py`
