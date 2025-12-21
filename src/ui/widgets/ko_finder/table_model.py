"""
QAbstractTableModel für KO-Produkte.

Implementiert Model-View Pattern für effiziente Darstellung
großer Produktlisten in QTableView.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PyQt6.QtGui import QBrush, QColor

if TYPE_CHECKING:
    from src.derivatives.ko_finder.models import KnockoutProduct


class KOProductTableModel(QAbstractTableModel):
    """
    TableModel für KO-Produkte.

    Spalten:
    - WKN, Emittent, Richtung, Hebel, Spread%, KO-Level, KO-Abstand%, Bid, Ask, Score
    """

    COLUMNS = [
        ("WKN", "wkn"),
        ("Emittent", "issuer"),
        ("Richtung", "direction"),
        ("Hebel", "leverage"),
        ("Spread %", "spread_pct"),
        ("KO-Level", "knockout_level"),
        ("KO-Abstand %", "ko_distance_pct"),
        ("Bid", "bid"),
        ("Ask", "ask"),
        ("Score", "score"),
    ]

    def __init__(self, parent=None) -> None:
        """Initialisiere Model."""
        super().__init__(parent)
        self._products: list[KnockoutProduct] = []

    def set_products(self, products: list[KnockoutProduct]) -> None:
        """
        Setze Produktliste.

        Args:
            products: Neue Produktliste
        """
        self.beginResetModel()
        self._products = products
        self.endResetModel()

    def clear(self) -> None:
        """Lösche alle Produkte."""
        self.beginResetModel()
        self._products = []
        self.endResetModel()

    def get_product(self, row: int) -> KnockoutProduct | None:
        """Hole Produkt für Zeile."""
        if 0 <= row < len(self._products):
            return self._products[row]
        return None

    # Qt Model Interface
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Anzahl Zeilen."""
        return len(self._products)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Anzahl Spalten."""
        return len(self.COLUMNS)

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Header-Daten."""
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self.COLUMNS):
                    return self.COLUMNS[section][0]
            else:
                return section + 1
        return None

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        """Zellen-Daten."""
        if not index.isValid():
            return None

        row = index.row()
        col = index.column()

        if row >= len(self._products):
            return None

        product = self._products[row]

        if role == Qt.ItemDataRole.DisplayRole:
            return self._get_display_value(product, col)

        elif role == Qt.ItemDataRole.TextAlignmentRole:
            # Zahlen rechtsbündig
            if col >= 3:  # Ab "Hebel"
                return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter

        elif role == Qt.ItemDataRole.BackgroundRole:
            return self._get_background_color(product, col)

        elif role == Qt.ItemDataRole.ForegroundRole:
            return self._get_foreground_color(product, col)

        elif role == Qt.ItemDataRole.ToolTipRole:
            return self._get_tooltip(product, col)

        return None

    def _get_display_value(self, product: KnockoutProduct, col: int) -> str:
        """Hole Anzeigewert für Zelle."""
        _, attr = self.COLUMNS[col]

        if attr == "direction":
            return product.direction.name

        if attr == "spread_pct":
            val = product.spread_pct
            return f"{val:.2f}%" if val is not None else "-"

        if attr == "leverage":
            val = product.leverage
            return f"{val:.1f}" if val is not None else "-"

        if attr == "knockout_level":
            val = product.knockout_level
            return f"{val:.2f}" if val is not None else "-"

        if attr == "ko_distance_pct":
            val = product.ko_distance_pct
            return f"{val:.2f}%" if val is not None else "-"

        if attr == "bid":
            val = product.quote.bid
            return f"{val:.2f}" if val is not None else "-"

        if attr == "ask":
            val = product.quote.ask
            return f"{val:.2f}" if val is not None else "-"

        if attr == "score":
            val = product.score
            return f"{val:.1f}" if val is not None else "-"

        return str(getattr(product, attr, "-"))

    def _get_background_color(
        self,
        product: KnockoutProduct,
        col: int,
    ) -> QBrush | None:
        """Hintergrundfarbe basierend auf Werten."""
        _, attr = self.COLUMNS[col]

        # Score-Heatmap
        if attr == "score" and product.score is not None:
            if product.score >= 80:
                return QBrush(QColor(200, 255, 200))  # Hellgrün
            elif product.score >= 60:
                return QBrush(QColor(255, 255, 200))  # Hellgelb
            elif product.score < 40:
                return QBrush(QColor(255, 200, 200))  # Hellrot

        # KO-Abstand Warnung
        if attr == "ko_distance_pct" and product.ko_distance_pct is not None:
            if product.ko_distance_pct < 2:
                return QBrush(QColor(255, 200, 200))  # Rot - gefährlich nah

        # Spread Warnung
        if attr == "spread_pct" and product.spread_pct is not None:
            if product.spread_pct > 1.5:
                return QBrush(QColor(255, 230, 200))  # Orange - hoher Spread

        return None

    def _get_foreground_color(
        self,
        product: KnockoutProduct,
        col: int,
    ) -> QBrush | None:
        """Textfarbe - automatischer Kontrast bei hellem Hintergrund."""
        _, attr = self.COLUMNS[col]

        # Richtung farbig
        if attr == "direction":
            if product.direction.name == "LONG":
                return QBrush(QColor(0, 150, 0))  # Grün
            else:
                return QBrush(QColor(200, 0, 0))  # Rot

        # Automatischer Kontrast: Wenn Hintergrund gesetzt, passende Textfarbe wählen
        bg_brush = self._get_background_color(product, col)
        if bg_brush is not None:
            bg_color = bg_brush.color()
            # W3C Luminanz-Formel: L = 0.2126*R + 0.7152*G + 0.0722*B
            luminance = (
                0.2126 * bg_color.red()
                + 0.7152 * bg_color.green()
                + 0.0722 * bg_color.blue()
            ) / 255.0
            # Bei hellem Hintergrund (L > 0.5) schwarzen Text verwenden
            if luminance > 0.5:
                return QBrush(QColor(0, 0, 0))

        return None

    def _get_tooltip(self, product: KnockoutProduct, col: int) -> str | None:
        """Tooltip für Zelle."""
        _, attr = self.COLUMNS[col]

        if attr == "wkn":
            return f"WKN: {product.wkn}\nName: {product.name}"

        if attr == "score":
            flags = ", ".join(f.value for f in product.flags)
            return (
                f"Score: {product.score:.1f}\n"
                f"Parser Confidence: {product.parser_confidence:.2f}\n"
                f"Flags: {flags or 'keine'}"
            )

        if attr == "ko_distance_pct":
            if product.ko_distance_pct is not None and product.ko_distance_pct < 3:
                return "WARNUNG: KO-Schwelle sehr nah!"

        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        """Sortiere nach Spalte."""
        if column < 0 or column >= len(self.COLUMNS):
            return

        _, attr = self.COLUMNS[column]
        reverse = order == Qt.SortOrder.DescendingOrder

        self.beginResetModel()

        def get_sort_key(product: KnockoutProduct) -> Any:
            if attr == "direction":
                return product.direction.name
            if attr in ("spread_pct", "bid", "ask"):
                val = getattr(product.quote, attr.replace("_pct", ""), None)
                if val is None:
                    val = getattr(product, attr, None)
                return val if val is not None else float("inf")
            val = getattr(product, attr, None)
            return val if val is not None else float("inf")

        self._products.sort(key=get_sort_key, reverse=reverse)
        self.endResetModel()
