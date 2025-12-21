"""Tests for Cryptocurrency Trading Strategies.

Tests strategy loading, validation, and compilation for crypto-specific strategies.
"""

import pytest
from pathlib import Path

from src.core.strategy.loader import StrategyLoader
from src.core.strategy.definition import StrategyDefinition


@pytest.fixture
def strategy_loader():
    """Create strategy loader instance."""
    return StrategyLoader()


@pytest.fixture
def strategies_dir():
    """Get path to example strategies directory."""
    return Path("examples/strategies")


class TestCryptoStrategyLoading:
    """Tests for loading crypto strategy YAML files."""

    def test_load_volatility_breakout_strategy(self, strategy_loader, strategies_dir):
        """Test loading Crypto Volatility Breakout strategy."""
        strategy_path = strategies_dir / "crypto_volatility_breakout.yaml"

        assert strategy_path.exists(), f"Strategy file not found: {strategy_path}"

        # Load strategy
        strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

        assert strategy is not None
        assert strategy.name == "Crypto Volatility Breakout"
        assert strategy.version == "1.0.0"
        assert strategy.category == "Trend Following"
        assert strategy.asset_class == "crypto"

        # Check recommended symbols
        assert "BTC/USD" in strategy.recommended_symbols
        assert "ETH/USD" in strategy.recommended_symbols
        assert "SOL/USD" in strategy.recommended_symbols

        # Check indicators
        assert len(strategy.indicators) >= 3  # SMA, ATR, RSI minimum
        indicator_types = [ind.type for ind in strategy.indicators]
        assert "SMA" in indicator_types
        assert "ATR" in indicator_types
        assert "RSI" in indicator_types

        # Check entry conditions exist
        assert strategy.entry_long is not None
        assert strategy.exit_long is not None

    def test_load_mean_reversion_strategy(self, strategy_loader, strategies_dir):
        """Test loading Crypto Mean Reversion strategy."""
        strategy_path = strategies_dir / "crypto_mean_reversion.yaml"

        assert strategy_path.exists(), f"Strategy file not found: {strategy_path}"

        # Load strategy
        strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

        assert strategy is not None
        assert strategy.name == "Crypto Mean Reversion (Bollinger Bands)"
        assert strategy.version == "1.0.0"
        assert strategy.category == "Mean Reversion"
        assert strategy.asset_class == "crypto"

        # Check indicators
        indicator_types = [ind.type for ind in strategy.indicators]
        assert "BBANDS" in indicator_types
        assert "RSI" in indicator_types
        assert "ATR" in indicator_types

        # Check entry/exit logic
        assert strategy.entry_long is not None
        assert strategy.exit_long is not None
        assert strategy.entry_short is not None  # Mean reversion often uses shorts
        assert strategy.exit_short is not None

    def test_load_momentum_combo_strategy(self, strategy_loader, strategies_dir):
        """Test loading Crypto Momentum Combo strategy."""
        strategy_path = strategies_dir / "crypto_momentum_combo.yaml"

        assert strategy_path.exists(), f"Strategy file not found: {strategy_path}"

        # Load strategy
        strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

        assert strategy is not None
        assert strategy.name == "Crypto Momentum Combo (RSI + MACD)"
        assert strategy.version == "1.0.0"
        assert strategy.category == "Momentum"
        assert strategy.asset_class == "crypto"

        # Check indicators
        indicator_types = [ind.type for ind in strategy.indicators]
        assert "MACD" in indicator_types
        assert "RSI" in indicator_types
        assert "EMA" in indicator_types
        assert "ATR" in indicator_types

        # Check timeframes
        assert "1H" in strategy.recommended_timeframes
        assert "4H" in strategy.recommended_timeframes


class TestCryptoStrategyValidation:
    """Tests for validating crypto strategy definitions."""

    def test_all_strategies_have_asset_class(self, strategy_loader, strategies_dir):
        """Verify all crypto strategies have asset_class set to 'crypto'."""
        crypto_strategy_files = [
            "crypto_volatility_breakout.yaml",
            "crypto_mean_reversion.yaml",
            "crypto_momentum_combo.yaml"
        ]

        for filename in crypto_strategy_files:
            strategy_path = strategies_dir / filename
            if not strategy_path.exists():
                pytest.skip(f"Strategy file not found: {filename}")

            strategy = strategy_loader.load_strategy_from_file(str(strategy_path))
            assert strategy.asset_class == "crypto", \
                f"{filename} should have asset_class='crypto'"

    def test_all_strategies_have_recommended_symbols(self, strategy_loader, strategies_dir):
        """Verify all strategies have recommended crypto symbols."""
        crypto_strategy_files = [
            "crypto_volatility_breakout.yaml",
            "crypto_mean_reversion.yaml",
            "crypto_momentum_combo.yaml"
        ]

        for filename in crypto_strategy_files:
            strategy_path = strategies_dir / filename
            if not strategy_path.exists():
                pytest.skip(f"Strategy file not found: {filename}")

            strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

            # Check that recommended symbols are crypto pairs (contain "/")
            assert len(strategy.recommended_symbols) > 0, \
                f"{filename} should have recommended_symbols"

            for symbol in strategy.recommended_symbols:
                assert "/" in symbol, \
                    f"Crypto symbol should contain '/': {symbol} in {filename}"

    def test_all_strategies_have_risk_management(self, strategy_loader, strategies_dir):
        """Verify all strategies have risk management defined."""
        crypto_strategy_files = [
            "crypto_volatility_breakout.yaml",
            "crypto_mean_reversion.yaml",
            "crypto_momentum_combo.yaml"
        ]

        for filename in crypto_strategy_files:
            strategy_path = strategies_dir / filename
            if not strategy_path.exists():
                pytest.skip(f"Strategy file not found: {filename}")

            strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

            assert strategy.risk_management is not None, \
                f"{filename} should have risk_management"

            # Check key risk parameters exist
            rm = strategy.risk_management
            assert hasattr(rm, 'position_size_pct')
            # Either stop_loss_pct or stop_loss_atr_multiplier should be set
            assert (hasattr(rm, 'stop_loss_pct') or
                    hasattr(rm, 'stop_loss_atr_multiplier'))


class TestCryptoStrategyCompilation:
    """Tests for compiling crypto strategies to executable format."""

    def test_compile_volatility_breakout(self, strategy_loader, strategies_dir):
        """Test compiling Volatility Breakout strategy."""
        strategy_path = strategies_dir / "crypto_volatility_breakout.yaml"

        if not strategy_path.exists():
            pytest.skip("Strategy file not found")

        strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

        # Import compiler
        from src.core.strategy.compiler import StrategyCompiler

        compiler = StrategyCompiler()

        # Compile strategy (should not raise errors)
        try:
            compiled_strategy = compiler.compile(strategy)
            assert compiled_strategy is not None
        except Exception as e:
            pytest.fail(f"Strategy compilation failed: {e}")

    def test_compile_mean_reversion(self, strategy_loader, strategies_dir):
        """Test compiling Mean Reversion strategy."""
        strategy_path = strategies_dir / "crypto_mean_reversion.yaml"

        if not strategy_path.exists():
            pytest.skip("Strategy file not found")

        strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

        from src.core.strategy.compiler import StrategyCompiler

        compiler = StrategyCompiler()

        try:
            compiled_strategy = compiler.compile(strategy)
            assert compiled_strategy is not None
        except Exception as e:
            pytest.fail(f"Strategy compilation failed: {e}")

    def test_compile_momentum_combo(self, strategy_loader, strategies_dir):
        """Test compiling Momentum Combo strategy."""
        strategy_path = strategies_dir / "crypto_momentum_combo.yaml"

        if not strategy_path.exists():
            pytest.skip("Strategy file not found")

        strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

        from src.core.strategy.compiler import StrategyCompiler

        compiler = StrategyCompiler()

        try:
            compiled_strategy = compiler.compile(strategy)
            assert compiled_strategy is not None
        except Exception as e:
            pytest.fail(f"Strategy compilation failed: {e}")


class TestCryptoStrategyMetadata:
    """Tests for crypto strategy metadata and documentation."""

    def test_all_strategies_have_description(self, strategy_loader, strategies_dir):
        """Verify all strategies have description."""
        crypto_strategy_files = [
            "crypto_volatility_breakout.yaml",
            "crypto_mean_reversion.yaml",
            "crypto_momentum_combo.yaml"
        ]

        for filename in crypto_strategy_files:
            strategy_path = strategies_dir / filename
            if not strategy_path.exists():
                pytest.skip(f"Strategy file not found: {filename}")

            strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

            assert strategy.description is not None
            assert len(strategy.description) > 0

    def test_all_strategies_have_notes(self, strategy_loader, strategies_dir):
        """Verify all strategies have usage notes."""
        crypto_strategy_files = [
            "crypto_volatility_breakout.yaml",
            "crypto_mean_reversion.yaml",
            "crypto_momentum_combo.yaml"
        ]

        for filename in crypto_strategy_files:
            strategy_path = strategies_dir / filename
            if not strategy_path.exists():
                pytest.skip(f"Strategy file not found: {filename}")

            strategy = strategy_loader.load_strategy_from_file(str(strategy_path))

            assert strategy.notes is not None
            assert len(strategy.notes) > 50  # Should have substantial notes


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
