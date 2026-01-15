"""Order Dialog for OrderPilot-AI Trading Application."""

import asyncio
from decimal import Decimal

import qasync
from PyQt6.QtCore import pyqtSignal, pyqtSlot
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
)

from src.core.broker import OrderRequest
from src.database.models import OrderSide, OrderType, TimeInForce


class OrderDialog(QDialog):
    """Dialog for placing orders with AI analysis."""

    order_placed = pyqtSignal(dict)

    def __init__(self, broker, ai_service, parent=None):
        super().__init__(parent)
        self.broker = broker
        self.ai_service = ai_service
        self.setWindowTitle("New Order")
        self.setModal(True)
        self.init_ui()

    def init_ui(self):
        """Initialize the order dialog UI."""
        self.setMinimumSize(600, 500)
        layout = QVBoxLayout(self)

        # Order form
        form_group = QGroupBox("Order Details")
        form_layout = QFormLayout()

        # Symbol
        self.symbol_edit = QLineEdit()
        self.symbol_edit.setPlaceholderText("e.g., AAPL, MSFT, TSLA")
        form_layout.addRow("Symbol:", self.symbol_edit)

        # Side
        self.side_combo = QComboBox()
        self.side_combo.addItems(["BUY", "SELL"])
        form_layout.addRow("Side:", self.side_combo)

        # Order type
        self.type_combo = QComboBox()
        self.type_combo.addItems(["LIMIT", "MARKET", "STOP", "STOP_LIMIT"])
        self.type_combo.currentTextChanged.connect(self.on_order_type_changed)
        form_layout.addRow("Type:", self.type_combo)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 10000)
        self.quantity_spin.setValue(100)
        form_layout.addRow("Quantity:", self.quantity_spin)

        # Price
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setRange(0.01, 999999.99)
        self.price_spin.setDecimals(2)
        self.price_spin.setValue(100.00)
        form_layout.addRow("Price:", self.price_spin)

        # Time in Force
        self.tif_combo = QComboBox()
        self.tif_combo.addItems(["DAY", "GTC", "IOC", "FOK"])
        form_layout.addRow("Time in Force:", self.tif_combo)

        form_group.setLayout(form_layout)
        layout.addWidget(form_group)

        # AI Analysis section
        ai_group = QGroupBox("AI Analysis")
        ai_layout = QVBoxLayout()

        self.ai_analysis_text = QTextEdit()
        self.ai_analysis_text.setReadOnly(True)
        self.ai_analysis_text.setPlainText("Click 'Analyze with AI' to get AI insights...")
        self.ai_analysis_text.setMaximumHeight(150)
        ai_layout.addWidget(self.ai_analysis_text)

        analyze_btn = QPushButton("Analyze with AI")
        analyze_btn.clicked.connect(self.analyze_order)
        ai_layout.addWidget(analyze_btn)

        ai_group.setLayout(ai_layout)
        layout.addWidget(ai_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.place_btn = QPushButton("Place Order")
        self.place_btn.clicked.connect(self.place_order)
        button_layout.addWidget(self.place_btn)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    @pyqtSlot(str)
    def on_order_type_changed(self, order_type: str):
        """Handle order type changes."""
        # Enable/disable price input based on order type
        if order_type == "MARKET":
            self.price_spin.setEnabled(False)
        else:
            self.price_spin.setEnabled(True)

    @qasync.asyncSlot()
    async def analyze_order(self):
        """Analyze order with AI."""
        if not self.ai_service:
            self.ai_analysis_text.setPlainText(
                "AI service not available. Please configure OpenAI API key in settings."
            )
            return

        # Get order details
        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "Invalid Input", "Please enter a symbol")
            return

        side = self.side_combo.currentText()
        quantity = self.quantity_spin.value()
        price = self.price_spin.value()

        # Show analyzing message
        self.ai_analysis_text.setPlainText("Analyzing order with AI...\nThis may take a few seconds...")

        try:
            # Create analysis request
            analysis_request = {
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price,
                'order_type': self.type_combo.currentText()
            }

            # Call AI service (mock analysis for now, would use real AI service)
            analysis_result = await self._get_ai_analysis(analysis_request)

            # Display results
            confidence_pct = analysis_result.get('confidence', 0) * 100
            reasoning = analysis_result.get('reasoning', 'No analysis available')
            risks = analysis_result.get('risks_identified', [])
            opportunities = analysis_result.get('opportunities_identified', [])

            analysis_text = f"AI Analysis for {symbol}:\n\n"
            analysis_text += f"Confidence: {confidence_pct:.1f}%\n\n"
            analysis_text += f"Reasoning:\n{reasoning}\n\n"

            if risks:
                analysis_text += "Risks Identified:\n"
                for risk in risks:
                    analysis_text += f"  • {risk}\n"
                analysis_text += "\n"

            if opportunities:
                analysis_text += "Opportunities:\n"
                for opp in opportunities:
                    analysis_text += f"  • {opp}\n"

            self.ai_analysis_text.setPlainText(analysis_text)

        except Exception as e:
            self.ai_analysis_text.setPlainText(
                f"Error during AI analysis:\n{str(e)}\n\n"
                "The order can still be placed without AI analysis."
            )

    async def _get_ai_analysis(self, analysis_request):
        """Get AI analysis for the order."""
        # Simulate AI processing delay
        await asyncio.sleep(0.5)

        # Mock analysis (in real implementation, would call AI service)
        return {
            'confidence': 0.75,
            'reasoning': f"Based on current market conditions, this {analysis_request['side']} order for "
                        f"{analysis_request['symbol']} appears reasonable. The price of €{analysis_request['price']:.2f} "
                        f"is within normal trading range.",
            'risks_identified': [
                "Market volatility may affect execution price",
                "Consider current market hours for optimal execution"
            ],
            'opportunities_identified': [
                "Good entry point based on technical indicators",
                "Current market momentum supports this trade"
            ]
        }

    @qasync.asyncSlot()
    async def place_order(self):
        """Place the order via broker."""
        # Validate inputs
        symbol = self.symbol_edit.text().strip().upper()
        if not symbol:
            QMessageBox.warning(self, "Invalid Input", "Please enter a symbol")
            return

        quantity = self.quantity_spin.value()
        if quantity <= 0:
            QMessageBox.warning(self, "Invalid Input", "Quantity must be positive")
            return

        # Get order details
        side = OrderSide[self.side_combo.currentText()]
        order_type = OrderType[self.type_combo.currentText()]
        price = Decimal(str(self.price_spin.value())) if order_type != OrderType.MARKET else None
        tif = TimeInForce[self.tif_combo.currentText()]

        # Create order request
        order_request = OrderRequest(
            symbol=symbol,
            quantity=quantity,
            side=side,
            order_type=order_type,
            limit_price=price,
            time_in_force=tif
        )

        # Disable button during order placement
        self.place_btn.setEnabled(False)
        self.place_btn.setText("Placing order...")

        try:
            # Place order via broker
            response = await self.broker.place_order(order_request)

            if response.success:
                # Emit signal with order data
                order_data = {
                    "order_id": response.order_id,
                    "symbol": symbol,
                    "side": side.name,
                    "order_type": order_type.name,
                    "quantity": quantity,
                    "price": float(price) if price else 0.0,
                    "status": response.status.name if response.status else "SUBMITTED"
                }

                self.order_placed.emit(order_data)

                QMessageBox.information(
                    self, "Order Placed",
                    f"Order placed successfully!\n\n"
                    f"Order ID: {response.order_id}\n"
                    f"{side.name} {quantity} {symbol} @ €{price or 'MARKET'}"
                )

                self.accept()

            else:
                QMessageBox.critical(
                    self, "Order Failed",
                    f"Failed to place order:\n{response.message}"
                )
                self.place_btn.setEnabled(True)
                self.place_btn.setText("Place Order")

        except Exception as e:
            QMessageBox.critical(
                self, "Order Error",
                f"Error placing order:\n{str(e)}"
            )
            self.place_btn.setEnabled(True)
            self.place_btn.setText("Place Order")
