"""ui.py
PyQt6 UI-Komponente (einbettbar) für den Compounding-Rechner.

- 2 Tabs: (Eingaben + KPIs) und (Tabelle + Plot).
- Live-Updates; keine Signal-Endlosschleifen (QSignalBlocker/Guard).
- Theme-kompatibel: keine hardcodierten Farben; Qt-Palette wird übernommen.
- Matplotlib-Embedding via FigureCanvasQTAgg (backend_qtagg).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox, QLabel,
    QDoubleSpinBox, QSpinBox, QCheckBox, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QFileDialog, QSignalBlocker, QComboBox,
)

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from calculator import Params, simulate, solve_daily_profit_pct_for_target, to_csv_rows


def _to_dec(x: float) -> Decimal:
    return Decimal(str(x))


class MplCanvas(FigureCanvas):
    def __init__(self, parent: QWidget):
        self.fig = Figure()
        super().__init__(self.fig)
        self.setParent(parent)
        self.ax = self.fig.add_subplot(111)

    def apply_qt_palette(self, widget: QWidget) -> None:
        pal = widget.palette()
        window = pal.color(widget.backgroundRole())
        base = pal.color(pal.ColorRole.Base)
        text = pal.color(pal.ColorRole.Text)

        def qcol(c):
            return (c.redF(), c.greenF(), c.blueF(), 1.0)

        self.fig.set_facecolor(qcol(window))
        self.ax.set_facecolor(qcol(base))
        self.ax.tick_params(axis="both", colors=qcol(text))
        self.ax.xaxis.label.set_color(qcol(text))
        self.ax.yaxis.label.set_color(qcol(text))
        self.ax.title.set_color(qcol(text))
        for spine in self.ax.spines.values():
            spine.set_color(qcol(text))


class CompoundingPanel(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._last_edited: Optional[str] = None  # "daily" oder "target"
        self._suppress_updates: bool = False

        self.tabs = QTabWidget(self)
        self.tab_inputs = QWidget()
        self.tab_details = QWidget()
        self.tabs.addTab(self.tab_inputs, "Compounding")
        self.tabs.addTab(self.tab_details, "Details")

        root = QVBoxLayout(self)
        root.addWidget(self.tabs)

        self._build_tab_inputs()
        self._build_tab_details()
        self.recompute(origin="init")

    def _build_tab_inputs(self) -> None:
        layout = QVBoxLayout(self.tab_inputs)
        box = QGroupBox("Eingaben")
        form = QFormLayout(box)

        self.sp_start_capital = QDoubleSpinBox(); self.sp_start_capital.setRange(0, 1e9); self.sp_start_capital.setDecimals(2); self.sp_start_capital.setValue(100.0); self.sp_start_capital.setSuffix(" €")
        self.sp_fee_pct = QDoubleSpinBox(); self.sp_fee_pct.setRange(0, 100); self.sp_fee_pct.setDecimals(4); self.sp_fee_pct.setSingleStep(0.01); self.sp_fee_pct.setValue(0.08); self.sp_fee_pct.setSuffix(" %")
        self.sp_leverage = QDoubleSpinBox(); self.sp_leverage.setRange(0.01, 1000); self.sp_leverage.setDecimals(2); self.sp_leverage.setValue(20.0); self.sp_leverage.setSuffix(" x")
        self.sp_daily_profit_pct = QDoubleSpinBox(); self.sp_daily_profit_pct.setRange(-99.0, 1000.0); self.sp_daily_profit_pct.setDecimals(4); self.sp_daily_profit_pct.setValue(30.0); self.sp_daily_profit_pct.setSuffix(" %")
        self.sp_reinvest_pct = QDoubleSpinBox(); self.sp_reinvest_pct.setRange(0, 100); self.sp_reinvest_pct.setDecimals(2); self.sp_reinvest_pct.setValue(30.0); self.sp_reinvest_pct.setSuffix(" %")
        self.sp_tax_pct = QDoubleSpinBox(); self.sp_tax_pct.setRange(0, 100); self.sp_tax_pct.setDecimals(2); self.sp_tax_pct.setValue(25.0); self.sp_tax_pct.setSuffix(" %")
        self.sp_days = QSpinBox(); self.sp_days.setRange(1, 366); self.sp_days.setValue(30)

        self.cb_trading_days_preset = QComboBox()
        self.cb_trading_days_preset.addItems(["30 (Kalendertage)", "22 (typ. Börsentage)", "20 (typ. Börsentage)"])
        self.cb_trading_days_preset.setCurrentIndex(0)

        self.cb_apply_losses = QCheckBox("Verluste reduzieren Kapital (optional)")
        self.cb_apply_losses.setChecked(False)

        self.sp_target_month_net = QDoubleSpinBox(); self.sp_target_month_net.setRange(-1e9, 1e9); self.sp_target_month_net.setDecimals(2); self.sp_target_month_net.setValue(0.0); self.sp_target_month_net.setSuffix(" €")
        self.lbl_solver_status = QLabel(""); self.lbl_solver_status.setWordWrap(True)

        form.addRow("Startkapital", self.sp_start_capital)
        form.addRow("Gebühren", self.sp_fee_pct)
        form.addRow("Hebel", self.sp_leverage)
        form.addRow("Gewinn % / Tag", self.sp_daily_profit_pct)
        form.addRow("Reinvestition", self.sp_reinvest_pct)
        form.addRow("Steuern", self.sp_tax_pct)
        form.addRow("Tage (manuell)", self.sp_days)
        form.addRow("Preset Trading-Tage", self.cb_trading_days_preset)
        form.addRow("", self.cb_apply_losses)
        form.addRow("Ziel netto im Monat", self.sp_target_month_net)
        form.addRow("Status", self.lbl_solver_status)

        layout.addWidget(box)

        kpi_box = QGroupBox("Monats-KPIs")
        kpi_form = QFormLayout(kpi_box)
        self.kpi_end_capital = QLabel("—"); self.kpi_sum_gross = QLabel("—"); self.kpi_sum_fees = QLabel("—"); self.kpi_sum_taxes = QLabel("—")
        self.kpi_sum_net = QLabel("—"); self.kpi_sum_reinvest = QLabel("—"); self.kpi_sum_withdrawal = QLabel("—"); self.kpi_roi = QLabel("—")

        kpi_form.addRow("Endkapital", self.kpi_end_capital)
        kpi_form.addRow("Summe Brutto", self.kpi_sum_gross)
        kpi_form.addRow("Summe Gebühren", self.kpi_sum_fees)
        kpi_form.addRow("Summe Steuern", self.kpi_sum_taxes)
        kpi_form.addRow("Summe Netto", self.kpi_sum_net)
        kpi_form.addRow("Summe reinvestiert", self.kpi_sum_reinvest)
        kpi_form.addRow("Summe entnommen", self.kpi_sum_withdrawal)
        kpi_form.addRow("ROI", self.kpi_roi)

        layout.addWidget(kpi_box)
        layout.addStretch(1)

        # Signals
        self.sp_daily_profit_pct.valueChanged.connect(lambda _v: self._on_user_edited("daily"))
        self.sp_target_month_net.valueChanged.connect(lambda _v: self._on_user_edited("target"))

        for w in [self.sp_start_capital, self.sp_fee_pct, self.sp_leverage, self.sp_reinvest_pct, self.sp_tax_pct, self.sp_days]:
            w.valueChanged.connect(lambda _v: self.recompute(origin="param_change"))
        self.cb_apply_losses.stateChanged.connect(lambda _s: self.recompute(origin="param_change"))
        self.cb_trading_days_preset.currentIndexChanged.connect(self._apply_trading_days_preset)

    def _build_tab_details(self) -> None:
        layout = QVBoxLayout(self.tab_details)
        top = QHBoxLayout()
        self.cb_plot_mode = QComboBox()
        self.cb_plot_mode.addItems(["Täglicher Netto-Gewinn", "Kumuliertes Netto"])
        self.cb_plot_mode.currentIndexChanged.connect(lambda _i: self.recompute(origin="plot_mode"))

        self.btn_copy_csv = QPushButton("Tabelle kopieren"); self.btn_copy_csv.clicked.connect(self._copy_table_to_clipboard)
        self.btn_export_csv = QPushButton("CSV exportieren"); self.btn_export_csv.clicked.connect(self._export_csv)

        top.addWidget(QLabel("Plot:")); top.addWidget(self.cb_plot_mode); top.addStretch(1); top.addWidget(self.btn_copy_csv); top.addWidget(self.btn_export_csv)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels(["Tag","Startkapital","Brutto","Notional","Gebühren","Vor Steuern","Steuern","Netto","Reinvest","Entnahme","Endkapital"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        self.canvas = MplCanvas(self)
        self.canvas.setMinimumHeight(260)

        layout.addWidget(self.table, stretch=3)
        layout.addWidget(self.canvas, stretch=2)

    def _apply_trading_days_preset(self, idx: int) -> None:
        preset_map = {0: 30, 1: 22, 2: 20}
        val = preset_map.get(idx, 30)
        with QSignalBlocker(self.sp_days):
            self.sp_days.setValue(val)
        self.recompute(origin="preset_days")

    def _on_user_edited(self, key: str) -> None:
        self._last_edited = key
        self.recompute(origin=f"user_{key}")

    def _get_params(self) -> Params:
        return Params(
            start_capital=_to_dec(self.sp_start_capital.value()),
            fee_pct=_to_dec(self.sp_fee_pct.value()),
            leverage=_to_dec(self.sp_leverage.value()),
            daily_profit_pct=_to_dec(self.sp_daily_profit_pct.value()),
            reinvest_pct=_to_dec(self.sp_reinvest_pct.value()),
            tax_pct=_to_dec(self.sp_tax_pct.value()),
            days=int(self.sp_days.value()),
            apply_losses_to_capital=bool(self.cb_apply_losses.isChecked()),
        )

    def recompute(self, origin: str = "") -> None:
        if self._suppress_updates:
            return

        try:
            params = self._get_params()
            params.validate()
        except Exception as e:
            self.lbl_solver_status.setText(f"Eingaben ungültig: {e}")
            return

        if self._last_edited == "target" and origin.startswith("user_"):
            target = _to_dec(self.sp_target_month_net.value())
            st = solve_daily_profit_pct_for_target(params, target_monthly_net=target)
            if st.ok and st.daily_profit_pct is not None:
                self._suppress_updates = True
                try:
                    with QSignalBlocker(self.sp_daily_profit_pct):
                        self.sp_daily_profit_pct.setValue(float(st.daily_profit_pct))
                finally:
                    self._suppress_updates = False
                self.lbl_solver_status.setText(f"Solver OK (Iterationen: {st.iterations}). Monats-Netto: {st.achieved_monthly_net}€")
                params = self._get_params()
            else:
                msg = st.message
                if st.achieved_monthly_net is not None:
                    msg += f" (Nächstes Ergebnis: {st.achieved_monthly_net}€)"
                self.lbl_solver_status.setText(msg)

        try:
            days, kpis = simulate(params)
        except Exception as e:
            self.lbl_solver_status.setText(f"Berechnung fehlgeschlagen: {e}")
            return

        if self._last_edited == "daily" and origin.startswith("user_"):
            self._suppress_updates = True
            try:
                with QSignalBlocker(self.sp_target_month_net):
                    self.sp_target_month_net.setValue(float(kpis.sum_net))
            finally:
                self._suppress_updates = False
            self.lbl_solver_status.setText("Ziel netto im Monat aus Tagesgewinn% berechnet.")

        self._update_kpis(kpis)
        self._update_table(days)
        self._update_plot(days)

    def _update_kpis(self, k) -> None:
        self.kpi_end_capital.setText(f"{k.end_capital:.2f} €")
        self.kpi_sum_gross.setText(f"{k.sum_gross:.2f} €")
        self.kpi_sum_fees.setText(f"{k.sum_fees:.2f} €")
        self.kpi_sum_taxes.setText(f"{k.sum_taxes:.2f} €")
        self.kpi_sum_net.setText(f"{k.sum_net:.2f} €")
        self.kpi_sum_reinvest.setText(f"{k.sum_reinvest:.2f} €")
        self.kpi_sum_withdrawal.setText(f"{k.sum_withdrawal:.2f} €")
        self.kpi_roi.setText(f"{k.roi_pct} %")

    def _update_table(self, days) -> None:
        self.table.setRowCount(len(days))
        for r_i, r in enumerate(days):
            values = [r.day, r.start_capital, r.gross_profit, r.notional, r.fee_amount, r.profit_before_tax, r.tax_amount, r.net_profit, r.reinvest, r.withdrawal, r.end_capital]
            for c_i, v in enumerate(values):
                item = QTableWidgetItem(str(v) if c_i == 0 else f"{v:.2f}")
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.table.setItem(r_i, c_i, item)

    def _update_plot(self, days) -> None:
        self.canvas.ax.clear()
        self.canvas.apply_qt_palette(self)
        xs = [d.day for d in days]
        if self.cb_plot_mode.currentIndex() == 0:
            ys = [float(d.net_profit) for d in days]
            self.canvas.ax.set_ylabel("Netto-Gewinn (€)")
            self.canvas.ax.set_title("Täglicher Netto-Gewinn")
        else:
            cum = 0.0
            ys = []
            for d in days:
                cum += float(d.net_profit)
                ys.append(cum)
            self.canvas.ax.set_ylabel("Kumuliertes Netto (€)")
            self.canvas.ax.set_title("Kumuliertes Netto")
        self.canvas.ax.set_xlabel("Tag")
        self.canvas.ax.plot(xs, ys)
        self.canvas.ax.grid(True, alpha=0.3)
        self.canvas.fig.tight_layout()
        self.canvas.draw()

    def _export_csv(self) -> None:
        try:
            params = self._get_params()
            days, _k = simulate(params)
            rows = to_csv_rows(days)
            text = "\n".join([",".join(r) for r in rows])
        except Exception as e:
            QMessageBox.critical(self, "Export fehlgeschlagen", str(e))
            return

        path, _ = QFileDialog.getSaveFileName(self, "CSV speichern", "compounding_days.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        except Exception as e:
            QMessageBox.critical(self, "CSV speichern", str(e))

    def _copy_table_to_clipboard(self) -> None:
        try:
            params = self._get_params()
            days, _k = simulate(params)
            rows = to_csv_rows(days)
            text = "\n".join(["\t".join(r) for r in rows])
        except Exception as e:
            QMessageBox.critical(self, "Kopieren fehlgeschlagen", str(e))
            return
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Kopiert", "Tages-Tabelle wurde in die Zwischenablage kopiert.")


if __name__ == "__main__":
    import sys
    from PyQt6.QtWidgets import QApplication, QMainWindow

    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("CompoundingPanel Demo")
    win.setCentralWidget(CompoundingPanel())
    win.resize(1100, 750)
    win.show()
    sys.exit(app.exec())
