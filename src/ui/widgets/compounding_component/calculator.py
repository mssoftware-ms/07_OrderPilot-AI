"""calculator.py
Pure Berechnungs-Engine für Zinseszins/Compounding im Trading.

- Keine Qt-Imports (UI-unabhängig).
- Reproduzierbare, prüfbare Logik.
- Rundung: Cent-genau (2 Nachkommastellen) per Decimal ROUND_HALF_UP.

Formeln (Tag d, 1-indexiert):
Startkapital: capital[d]
Brutto-Gewinn (auf Margin-Kapital): gross_profit = capital[d] * (daily_profit_pct/100)
Notional (für Gebühren): notional_open = capital[d] * leverage
Preisänderung (Underlying): price_change = (daily_profit_pct/100) / leverage
Notional beim Schließen: notional_close = notional_open * (1 + price_change)
Gebühren (Roundtrip): fee_amount = (notional_open * fee_open_pct/100) + (notional_close * fee_close_pct/100)
Gewinn vor Steuern: profit_before_tax = gross_profit - fee_amount
Steuern (monatlich, am Ende): month_tax = max(sum(profit_before_tax), 0) * (tax_pct/100)
Netto pro Tag: net_profit = profit_before_tax  (Steuern erst am Monatsende)
Reinvest: reinvest = max(net_profit, 0) * (reinvest_pct/100)
Entnahme: withdrawal = max(net_profit, 0) - reinvest
Kapital nächster Tag:
  - Standard (apply_losses_to_capital=False): capital[d+1] = capital[d] + reinvest
  - Optional (apply_losses_to_capital=True):  capital[d+1] = capital[d] + reinvest + min(net_profit, 0)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import List, Tuple, Optional

CENT = Decimal("0.01")

def _d(x) -> Decimal:
    """Sichere Decimal-Konvertierung (UI kann floats liefern)."""
    try:
        return Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError) as e:
        raise ValueError(f"Ungültiger Zahlenwert: {x!r}") from e

def money(x: Decimal) -> Decimal:
    """Rundet auf Cent (ROUND_HALF_UP)."""
    return x.quantize(CENT, rounding=ROUND_HALF_UP)

def pct(x: Decimal) -> Decimal:
    """Rundet Prozentwerte intern moderat (6 Nachkommastellen)."""
    return x.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

@dataclass(frozen=True)
class Params:
    start_capital: Decimal = Decimal("100")
    fee_open_pct: Decimal = Decimal("0.06")
    fee_close_pct: Decimal = Decimal("0.06")
    leverage: Decimal = Decimal("20")
    daily_profit_pct: Decimal = Decimal("30")
    reinvest_pct: Decimal = Decimal("30")
    tax_pct: Decimal = Decimal("25")
    days: int = 30
    apply_losses_to_capital: bool = False

    def validate(self) -> None:
        if self.days <= 0 or self.days > 366:
            raise ValueError("days muss zwischen 1 und 366 liegen.")
        if self.start_capital < 0:
            raise ValueError("start_capital darf nicht negativ sein.")
        if self.leverage <= 0:
            raise ValueError("leverage muss > 0 sein.")
        for name, v, lo, hi in [
            ("fee_open_pct", self.fee_open_pct, Decimal("0"), Decimal("100")),
            ("fee_close_pct", self.fee_close_pct, Decimal("0"), Decimal("100")),
            ("daily_profit_pct", self.daily_profit_pct, Decimal("-99.999999"), Decimal("1000")),
            ("reinvest_pct", self.reinvest_pct, Decimal("0"), Decimal("100")),
            ("tax_pct", self.tax_pct, Decimal("0"), Decimal("100")),
        ]:
            if v < lo or v > hi:
                raise ValueError(f"{name} muss zwischen {lo} und {hi} liegen.")

@dataclass(frozen=True)
class DayResult:
    day: int
    start_capital: Decimal
    gross_profit: Decimal
    notional: Decimal
    fee_amount: Decimal
    profit_before_tax: Decimal
    tax_amount: Decimal
    net_profit: Decimal
    reinvest: Decimal
    withdrawal: Decimal
    end_capital: Decimal

@dataclass(frozen=True)
class MonthKpis:
    end_capital: Decimal
    sum_gross: Decimal
    sum_fees: Decimal
    sum_taxes: Decimal
    sum_net: Decimal
    sum_reinvest: Decimal
    sum_withdrawal: Decimal
    roi_pct: Decimal

def simulate(params: Params) -> Tuple[List[DayResult], MonthKpis]:
    """Simuliert params.days Tage. Alle Geldwerte Cent-genau gerundet."""
    params.validate()

    days: List[DayResult] = []
    capital = money(_d(params.start_capital))

    dp = _d(params.daily_profit_pct) / Decimal("100")
    fp_open = _d(params.fee_open_pct) / Decimal("100")
    fp_close = _d(params.fee_close_pct) / Decimal("100")
    rp = _d(params.reinvest_pct) / Decimal("100")
    tp = _d(params.tax_pct) / Decimal("100")
    lev = _d(params.leverage)

    sum_gross = Decimal("0")
    sum_fees = Decimal("0")
    sum_taxes = Decimal("0")
    sum_net = Decimal("0")
    sum_reinvest = Decimal("0")
    sum_withdrawal = Decimal("0")

    for d in range(1, params.days + 1):
        start_cap = capital
        gross = money(start_cap * dp)
        notional = money(start_cap * lev)
        price_change = dp / lev
        notional_close = money(notional * (Decimal("1") + price_change))
        fee_open = money(notional * fp_open)
        fee_close = money(notional_close * fp_close)
        fee = money(fee_open + fee_close)
        pbt = money(gross - fee)
        tax = Decimal("0")
        net = money(pbt)
        reinv = money((net if net > 0 else Decimal("0")) * rp)
        withdrawal = money((net if net > 0 else Decimal("0")) - reinv)

        if params.apply_losses_to_capital:
            capital_next = money(start_cap + reinv + (net if net < 0 else Decimal("0")))
        else:
            capital_next = money(start_cap + reinv)

        days.append(
            DayResult(
                day=d,
                start_capital=start_cap,
                gross_profit=gross,
                notional=notional,
                fee_amount=fee,
                profit_before_tax=pbt,
                tax_amount=tax,
                net_profit=net,
                reinvest=reinv,
                withdrawal=withdrawal,
                end_capital=capital_next,
            )
        )

        sum_gross += gross
        sum_fees += fee
        sum_taxes += tax
        sum_net += net
        sum_reinvest += reinv
        sum_withdrawal += withdrawal
        capital = capital_next

    # Apply taxes at month end (only if total profit before tax is positive).
    month_tax = money((sum_net if sum_net > 0 else Decimal("0")) * tp)
    sum_taxes = month_tax
    capital = money(capital - month_tax)
    sum_net = money(sum_net - month_tax)
    if days:
        last = days[-1]
        days[-1] = DayResult(
            day=last.day,
            start_capital=last.start_capital,
            gross_profit=last.gross_profit,
            notional=last.notional,
            fee_amount=last.fee_amount,
            profit_before_tax=last.profit_before_tax,
            tax_amount=last.tax_amount,
            net_profit=last.net_profit,
            reinvest=last.reinvest,
            withdrawal=last.withdrawal,
            end_capital=capital,
        )

    roi = Decimal("0")
    if params.start_capital > 0:
        roi = pct((capital - money(_d(params.start_capital))) / money(_d(params.start_capital)) * Decimal("100"))

    kpis = MonthKpis(
        end_capital=money(capital),
        sum_gross=money(sum_gross),
        sum_fees=money(sum_fees),
        sum_taxes=money(sum_taxes),
        sum_net=money(sum_net),
        sum_reinvest=money(sum_reinvest),
        sum_withdrawal=money(sum_withdrawal),
        roi_pct=roi,
    )
    return days, kpis

@dataclass(frozen=True)
class SolveStatus:
    ok: bool
    daily_profit_pct: Optional[Decimal]
    achieved_monthly_net: Optional[Decimal]
    message: str
    iterations: int

def monthly_net_for_daily_pct(base_params: Params, daily_profit_pct: Decimal) -> Decimal:
    p = Params(
        start_capital=base_params.start_capital,
        fee_open_pct=base_params.fee_open_pct,
        fee_close_pct=base_params.fee_close_pct,
        leverage=base_params.leverage,
        daily_profit_pct=daily_profit_pct,
        reinvest_pct=base_params.reinvest_pct,
        tax_pct=base_params.tax_pct,
        days=base_params.days,
        apply_losses_to_capital=base_params.apply_losses_to_capital,
    )
    _days, kpis = simulate(p)
    return kpis.sum_net

def solve_daily_profit_pct_for_target(
    base_params: Params,
    target_monthly_net: Decimal,
    lo: Decimal = Decimal("-99"),
    hi: Decimal = Decimal("1000"),
    tol_eur: Decimal = Decimal("0.01"),
    max_iter: int = 80,
) -> SolveStatus:
    base_params.validate()
    target = money(_d(target_monthly_net))
    lo = _d(lo)
    hi = _d(hi)
    tol_eur = money(_d(tol_eur))
    if lo >= hi:
        return SolveStatus(False, None, None, "Solver: lo muss < hi sein.", 0)

    f_lo = monthly_net_for_daily_pct(base_params, lo)
    f_hi = monthly_net_for_daily_pct(base_params, hi)
    increasing = f_hi >= f_lo
    min_f = f_lo if increasing else f_hi
    max_f = f_hi if increasing else f_lo

    if target < min_f - tol_eur or target > max_f + tol_eur:
        return SolveStatus(
            False, None, None,
            f"Ziel nicht erreichbar innerhalb der Grenzen [{lo}%, {hi}%]. Erreichbar: {money(min_f)}€ .. {money(max_f)}€.",
            0,
        )

    left, right = lo, hi
    best_mid, best_val = None, None

    for i in range(1, max_iter + 1):
        mid = (left + right) / Decimal("2")
        val = monthly_net_for_daily_pct(base_params, mid)

        if best_val is None or abs(val - target) < abs(best_val - target):
            best_mid, best_val = mid, val

        if abs(val - target) <= tol_eur:
            return SolveStatus(True, pct(mid), money(val), "OK", i)

        if increasing:
            if val < target:
                left = mid
            else:
                right = mid
        else:
            if val > target:
                left = mid
            else:
                right = mid

    return SolveStatus(
        False,
        pct(best_mid) if best_mid is not None else None,
        money(best_val) if best_val is not None else None,
        f"Solver nicht konvergiert in {max_iter} Iterationen.",
        max_iter,
    )

def to_csv_rows(days: List[DayResult]) -> List[List[str]]:
    header = [
        "Tag","Startkapital","Brutto-Gewinn","Notional","Gebühren",
        "Gewinn vor Steuern","Steuern","Netto-Gewinn","Reinvest","Entnahme","Endkapital",
    ]
    rows = [header]
    for r in days:
        rows.append([
            str(r.day),
            f"{r.start_capital:.2f}",
            f"{r.gross_profit:.2f}",
            f"{r.notional:.2f}",
            f"{r.fee_amount:.2f}",
            f"{r.profit_before_tax:.2f}",
            f"{r.tax_amount:.2f}",
            f"{r.net_profit:.2f}",
            f"{r.reinvest:.2f}",
            f"{r.withdrawal:.2f}",
            f"{r.end_capital:.2f}",
        ])
    return rows
