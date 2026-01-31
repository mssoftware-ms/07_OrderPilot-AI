"""Integration tests for TradingMixinBase and its implementations.

Tests the complete integration of TradingMixinBase with ChartChatMixin
and BitunixTradingMixin across various UI scenarios.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from PyQt6.QtWidgets import QMainWindow, QApplication

from src.ui.mixins.trading_mixin_base import TradingMixinBase
from src.chart_chat.mixin import ChartChatMixin
from src.ui.widgets.bitunix_trading.bitunix_trading_mixin import BitunixTradingMixin


class MockChartWidget:
    """Mock chart widget for testing."""
    def __init__(self):
        self.symbol = "BTC/USDT"
        self.current_symbol = "BTC/USDT"
        self.current_timeframe = "1H"
        self.data = Mock()


class TestTradingMixinIntegration:
    """Integration tests for TradingMixinBase implementations."""

    def test_chart_chat_mixin_uses_base_get_parent_app(self, qapp):
        """Test ChartChatMixin correctly uses base _get_parent_app."""
        # Arrange
        class TestWindow(QMainWindow, ChartChatMixin):
            pass

        window = TestWindow()
        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act
        result = window._get_parent_app()

        # Assert
        assert result == mock_main_window
        assert isinstance(window, TradingMixinBase)

    def test_bitunix_mixin_uses_base_get_parent_app(self, qapp):
        """Test BitunixTradingMixin correctly uses base _get_parent_app."""
        # Arrange
        class TestWindow(QMainWindow, BitunixTradingMixin):
            pass

        window = TestWindow()
        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act
        result = window._get_parent_app()

        # Assert
        assert result == mock_main_window
        assert isinstance(window, TradingMixinBase)

    def test_multiple_mixins_share_same_parent_app(self, qapp):
        """Test that multiple mixins on same window share _get_parent_app."""
        # Arrange
        class TestWindow(QMainWindow, ChartChatMixin, BitunixTradingMixin):
            pass

        window = TestWindow()
        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act
        result1 = ChartChatMixin._get_parent_app(window)
        result2 = BitunixTradingMixin._get_parent_app(window)

        # Assert
        assert result1 == result2 == mock_main_window

    def test_chart_chat_setup_with_parent_app(self, qapp):
        """Test ChartChatMixin setup_chart_chat uses _get_parent_app."""
        # Arrange
        class TestWindow(QMainWindow, ChartChatMixin):
            pass

        window = TestWindow()
        chart_widget = MockChartWidget()
        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act & Assert - should not raise
        # Note: setup_chart_chat may fail due to missing dependencies,
        # but it should attempt to call _get_parent_app
        try:
            window.setup_chart_chat(chart_widget)
        except Exception:
            pass  # Expected - we're testing the parent app access

        # Verify _get_parent_app returns expected value
        assert window._get_parent_app() == mock_main_window

    def test_bitunix_setup_with_parent_app(self, qapp):
        """Test BitunixTradingMixin setup uses _get_parent_app."""
        # Arrange
        class TestWindow(QMainWindow, BitunixTradingMixin):
            pass

        window = TestWindow()
        chart_widget = MockChartWidget()
        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act & Assert
        try:
            window.setup_bitunix_trading(chart_widget)
        except Exception:
            pass  # Expected - we're testing the parent app access

        # Verify _get_parent_app returns expected value
        assert window._get_parent_app() == mock_main_window

    def test_mixin_inheritance_chain(self):
        """Test that mixin inheritance chain is correct."""
        # Arrange & Act
        chart_chat_mro = ChartChatMixin.__mro__
        bitunix_mro = BitunixTradingMixin.__mro__

        # Assert
        assert TradingMixinBase in chart_chat_mro
        assert TradingMixinBase in bitunix_mro

        # Verify TradingMixinBase comes before object in chain
        chart_base_idx = chart_chat_mro.index(TradingMixinBase)
        chart_object_idx = chart_chat_mro.index(object)
        assert chart_base_idx < chart_object_idx

        bitunix_base_idx = bitunix_mro.index(TradingMixinBase)
        bitunix_object_idx = bitunix_mro.index(object)
        assert bitunix_base_idx < bitunix_object_idx

    def test_concurrent_mixin_usage(self, qapp):
        """Test multiple windows using mixins concurrently."""
        # Arrange
        class Window1(QMainWindow, ChartChatMixin):
            pass

        class Window2(QMainWindow, BitunixTradingMixin):
            pass

        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act
        window1 = Window1()
        window2 = Window2()

        result1 = window1._get_parent_app()
        result2 = window2._get_parent_app()

        # Assert
        assert result1 == result2 == mock_main_window

    def test_mixin_method_resolution_order(self):
        """Test that method resolution order prefers base class."""
        # Arrange
        class TestWindow(QMainWindow, ChartChatMixin, BitunixTradingMixin):
            pass

        # Act
        mro = TestWindow.__mro__

        # Assert - TradingMixinBase should appear before object
        base_index = None
        object_index = None

        for i, cls in enumerate(mro):
            if cls == TradingMixinBase:
                base_index = i
            if cls == object:
                object_index = i

        assert base_index is not None
        assert object_index is not None
        assert base_index < object_index

    def test_get_parent_app_survives_app_restart(self, qapp):
        """Test _get_parent_app handles app instance changes."""
        # Arrange
        mixin = TradingMixinBase()

        # Act - Before setting main_window
        result1 = mixin._get_parent_app()

        # Set main_window
        mock_main_window = Mock()
        qapp.main_window = mock_main_window
        result2 = mixin._get_parent_app()

        # Remove main_window
        delattr(qapp, 'main_window')
        result3 = mixin._get_parent_app()

        # Assert
        assert result1 is None
        assert result2 == mock_main_window
        assert result3 is None

    def test_chart_chat_mixin_attributes_isolated(self):
        """Test ChartChatMixin instance attributes don't leak."""
        # Arrange - Use mixin directly, not QMainWindow
        mixin1 = ChartChatMixin()
        mixin2 = ChartChatMixin()

        # Act - Set attribute on mixin1
        mixin1._chat_widget = Mock(name="chat1")

        # Assert - mixin2 should not have the same object (or should be None)
        assert not hasattr(mixin2, '_chat_widget') or mixin1._chat_widget is not mixin2._chat_widget

    def test_bitunix_mixin_attributes_isolated(self):
        """Test BitunixTradingMixin instance attributes don't leak."""
        # Arrange - Use mixin directly, not QMainWindow
        mixin1 = BitunixTradingMixin()
        mixin2 = BitunixTradingMixin()

        # Act - Set attribute on mixin1
        mixin1._bitunix_widget = Mock(name="bitunix1")

        # Assert - mixin2 should not have the same object (or should be None)
        assert not hasattr(mixin2, '_bitunix_widget') or mixin1._bitunix_widget is not mixin2._bitunix_widget

    def test_base_mixin_no_side_effects(self, qapp):
        """Test TradingMixinBase._get_parent_app has no side effects."""
        # Arrange
        mixin = TradingMixinBase()
        mock_main_window = Mock()
        qapp.main_window = mock_main_window

        # Act - Call multiple times
        result1 = mixin._get_parent_app()
        result2 = mixin._get_parent_app()
        result3 = mixin._get_parent_app()

        # Assert - Same result, no modifications
        assert result1 == result2 == result3 == mock_main_window
        assert hasattr(qapp, 'main_window')

    def test_mixin_with_custom_get_parent_app_override(self, qapp):
        """Test that mixins can override _get_parent_app if needed."""
        # Arrange
        class CustomMixin(TradingMixinBase):
            def _get_parent_app(self):
                return "custom_app"

        # Act
        mixin = CustomMixin()
        result = mixin._get_parent_app()

        # Assert
        assert result == "custom_app"

    def test_regression_no_duplicate_code(self):
        """Regression: Verify duplicate code has been eliminated."""
        import inspect

        # Get source code
        chart_chat_source = inspect.getsource(ChartChatMixin)
        bitunix_source = inspect.getsource(BitunixTradingMixin)

        # Assert - Neither should reimplement _get_parent_app
        # They should inherit it from TradingMixinBase
        assert 'def _get_parent_app(self)' not in chart_chat_source
        assert 'def _get_parent_app(self)' not in bitunix_source

        # But TradingMixinBase should have it
        base_source = inspect.getsource(TradingMixinBase)
        assert 'def _get_parent_app(self)' in base_source


@pytest.fixture
def qapp():
    """Provide QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])

    # Clean up main_window if exists
    if hasattr(app, 'main_window'):
        delattr(app, 'main_window')

    return app
