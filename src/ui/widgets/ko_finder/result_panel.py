"""
Ergebnis-Panel für KO-Finder.

Enthält:
- Tabellen für Long/Short Produkte
- Meta-Informationen (Stand, Dauer, Fehler)
- Disclaimer
"""

from __future__ import annotations

import logging
import webbrowser
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTabWidget,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .table_model import KOProductTableModel

if TYPE_CHECKING:
    from src.derivatives.ko_finder.models import KnockoutProduct, SearchResponse

logger = logging.getLogger(__name__)


class KOResultPanel(QWidget):
    """
    Ergebnis-Panel mit Tabellen und Meta-Infos.

    Signals:
        product_selected: Emittiert WKN bei Produkt-Auswahl
        refresh_ko_distance_requested: Emittiert bei Klick auf KO-Abstand Refresh
    """

    product_selected = pyqtSignal(str)  # WKN
    refresh_ko_distance_requested = pyqtSignal()  # Request current price for KO distance

    def __init__(self, parent=None) -> None:
        """Initialisiere Panel."""
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        """Erstelle UI-Elemente."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Tab-Widget für Long/Short
        self.tabs = QTabWidget()

        # Long-Tab
        self.long_model = KOProductTableModel()
        self.long_table = self._create_table(self.long_model)
        self.tabs.addTab(self.long_table, "Long (0)")

        # Short-Tab
        self.short_model = KOProductTableModel()
        self.short_table = self._create_table(self.short_model)
        self.tabs.addTab(self.short_table, "Short (0)")

        layout.addWidget(self.tabs, stretch=1)

        # Meta-Info Bar
        meta_frame = QFrame()
        meta_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        meta_layout = QHBoxLayout(meta_frame)
        meta_layout.setContentsMargins(5, 3, 5, 3)

        self.status_label = QLabel("Keine Daten")
        meta_layout.addWidget(self.status_label)

        meta_layout.addStretch()

        # Refresh KO-Abstand Button
        self.refresh_ko_btn = QPushButton("⟳ KO-Abstand")
        self.refresh_ko_btn.setToolTip(
            "Berechne KO-Abstand % neu mit aktuellem Underlying-Kurs"
        )
        self.refresh_ko_btn.setMaximumWidth(120)
        self.refresh_ko_btn.clicked.connect(self._on_refresh_ko_clicked)
        self.refresh_ko_btn.setEnabled(False)  # Erst bei Daten aktivieren
        meta_layout.addWidget(self.refresh_ko_btn)

        self.time_label = QLabel("")
        meta_layout.addWidget(self.time_label)

        self.source_label = QLabel("Quelle: Onvista")
        self.source_label.setStyleSheet("color: gray; font-size: 10px;")
        meta_layout.addWidget(self.source_label)

        layout.addWidget(meta_frame)

        # Disclaimer
        disclaimer = QLabel(
            "Hinweis: Keine Anlageberatung. Daten können verzögert sein. "
            "Bitte vor Handelsentscheidungen verifizieren."
        )
        disclaimer.setStyleSheet(
            "color: #666; font-size: 9px; padding: 2px; "
            "background-color: #f5f5f5; border-radius: 3px;"
        )
        disclaimer.setWordWrap(True)
        layout.addWidget(disclaimer)

    def _create_table(self, model: KOProductTableModel) -> QTableView:
        """Erstelle konfigurierte TableView."""
        table = QTableView()
        table.setModel(model)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setSortingEnabled(True)
        table.setShowGrid(True)

        # Header konfigurieren
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

        # Doppelklick Handler
        table.doubleClicked.connect(lambda idx: self._on_row_double_clicked(model, idx.row()))

        # Context Menu
        table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        table.customContextMenuRequested.connect(
            lambda pos: self._show_context_menu(table, model, pos)
        )

        return table

    def set_response(self, response: SearchResponse) -> None:
        """
        Setze Suchergebnis.

        Args:
            response: SearchResponse mit Long/Short Produkten
        """
        # Tabellen aktualisieren
        self.long_model.set_products(response.long)
        self.short_model.set_products(response.short)

        # Tab-Titel aktualisieren
        self.tabs.setTabText(0, f"Long ({len(response.long)})")
        self.tabs.setTabText(1, f"Short ({len(response.short)})")

        # Meta-Infos
        self._update_meta(response)

        # Refresh-Button aktivieren wenn Daten vorhanden
        has_data = len(response.long) > 0 or len(response.short) > 0
        self.refresh_ko_btn.setEnabled(has_data)

    def clear(self) -> None:
        """Lösche alle Daten."""
        self.long_model.clear()
        self.short_model.clear()
        self.tabs.setTabText(0, "Long (0)")
        self.tabs.setTabText(1, "Short (0)")
        self.status_label.setText("Keine Daten")
        self.status_label.setStyleSheet("color: gray;")
        self.time_label.setText("")
        self.refresh_ko_btn.setEnabled(False)

    def set_status(self, message: str, status_type: str = "info") -> None:
        """
        Setze kurze Status-Meldung.

        Args:
            message: Kurze Status-Nachricht
            status_type: "success", "warning", "error", "info"
        """
        self.status_label.setText(message)

        colors = {
            "success": "color: green;",
            "warning": "color: orange;",
            "error": "color: red;",
            "info": "color: gray;",
        }
        self.status_label.setStyleSheet(colors.get(status_type, "color: gray;"))

    def _update_meta(self, response: SearchResponse) -> None:
        """Aktualisiere Meta-Anzeige (nur Zeit-Info, Status separat)."""
        meta = response.meta

        # Zeit und Dauer
        time_str = response.as_of.strftime("%H:%M:%S")
        cache_info = " Cache" if meta.cache_hit else ""
        duration = f"{meta.fetch_time_ms}ms" if meta.fetch_time_ms > 0 else ""
        self.time_label.setText(f"Stand: {time_str} ({duration}{cache_info})")

    def _on_row_double_clicked(self, model: KOProductTableModel, row: int) -> None:
        """Handler für Doppelklick auf Zeile."""
        product = model.get_product(row)
        if product:
            self._open_product_detail(product)

    def _open_product_detail(self, product: KnockoutProduct) -> None:
        """Öffne Produkt-Detailseite auf Onvista."""
        if product.source_url:
            webbrowser.open(product.source_url)
        else:
            # Fallback: WKN-Suche
            url = f"https://www.onvista.de/derivate/{product.wkn}"
            webbrowser.open(url)

    def _show_context_menu(
        self,
        table: QTableView,
        model: KOProductTableModel,
        pos,
    ) -> None:
        """Zeige Kontextmenü."""
        from PyQt6.QtWidgets import QMenu

        index = table.indexAt(pos)
        if not index.isValid():
            return

        product = model.get_product(index.row())
        if not product:
            return

        menu = QMenu(self)

        # WKN kopieren
        copy_wkn = menu.addAction("WKN kopieren")
        copy_wkn.triggered.connect(
            lambda: QApplication.clipboard().setText(product.wkn)
        )

        # ISIN kopieren (wenn vorhanden)
        if product.isin:
            copy_isin = menu.addAction("ISIN kopieren")
            copy_isin.triggered.connect(
                lambda: QApplication.clipboard().setText(product.isin)
            )

        menu.addSeparator()

        # Auf Onvista öffnen
        open_onvista = menu.addAction("Auf Onvista öffnen")
        open_onvista.triggered.connect(lambda: self._open_product_detail(product))

        menu.addSeparator()

        # Details anzeigen
        show_details = menu.addAction("Details anzeigen")
        show_details.triggered.connect(lambda: self._show_product_details(product))

        menu.exec(table.viewport().mapToGlobal(pos))

    def _show_product_details(self, product: KnockoutProduct) -> None:
        """Zeige Produkt-Details in Dialog."""
        flags_str = ", ".join(f.value for f in product.flags) or "keine"

        details = (
            f"WKN: {product.wkn}\n"
            f"Name: {product.name}\n"
            f"Emittent: {product.issuer}\n"
            f"Richtung: {product.direction.name}\n\n"
            f"Hebel: {product.leverage:.1f}\n"
            f"KO-Level: {product.knockout_level:.2f}\n"
            f"KO-Abstand: {product.ko_distance_pct:.2f}%\n\n"
            f"Bid: {product.quote.bid:.2f}\n"
            f"Ask: {product.quote.ask:.2f}\n"
            f"Spread: {product.spread_pct:.2f}%\n\n"
            f"Score: {product.score:.1f}\n"
            f"Parser Confidence: {product.parser_confidence:.2f}\n"
            f"Flags: {flags_str}\n\n"
            f"Quelle: {product.source}\n"
            f"Abgerufen: {product.fetched_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )

        QMessageBox.information(self, f"KO-Produkt {product.wkn}", details)

    def _on_refresh_ko_clicked(self) -> None:
        """Handler für Refresh KO-Abstand Button."""
        self.refresh_ko_distance_requested.emit()

    def update_ko_distance(self, underlying_price: float) -> None:
        """
        Aktualisiere KO-Abstand für alle Produkte mit neuem Kurs.

        Args:
            underlying_price: Aktueller Underlying-Kurs
        """
        if underlying_price <= 0:
            logger.warning("Invalid underlying price for KO distance update: %s", underlying_price)
            return

        # Alle Produkte in beiden Models aktualisieren
        updated = 0
        for product in self.long_model._products:
            product.update_ko_distance(underlying_price)
            updated += 1

        for product in self.short_model._products:
            product.update_ko_distance(underlying_price)
            updated += 1

        # Models refreshen um UI zu aktualisieren
        if updated > 0:
            self.long_model.layoutChanged.emit()
            self.short_model.layoutChanged.emit()
            logger.info(
                "Updated KO distance for %d products with price %.2f",
                updated,
                underlying_price,
            )

    def highlight_product(self, wkn: str) -> bool:
        """
        Highlight a product by WKN in the tables.

        Args:
            wkn: WKN of product to highlight

        Returns:
            True if product found and highlighted
        """
        # Search in Long table
        for row, product in enumerate(self.long_model._products):
            if product.wkn == wkn:
                self.tabs.setCurrentIndex(0)  # Switch to Long tab
                self.long_table.selectRow(row)
                self.long_table.scrollTo(self.long_model.index(row, 0))
                logger.info("Highlighted product %s in Long table (row %d)", wkn, row)
                return True

        # Search in Short table
        for row, product in enumerate(self.short_model._products):
            if product.wkn == wkn:
                self.tabs.setCurrentIndex(1)  # Switch to Short tab
                self.short_table.selectRow(row)
                self.short_table.scrollTo(self.short_model.index(row, 0))
                logger.info("Highlighted product %s in Short table (row %d)", wkn, row)
                return True

        logger.warning("Product %s not found for highlighting", wkn)
        return False
