"""Tests for trading mode configuration and validation.

Tests cover:
- TradingMode enum and ProfileConfig integration
- Mode-specific validation rules
- Safe mode switching
- Profile factory methods for each mode
"""

import pytest
from decimal import Decimal

from src.config import (
    BrokerType,
    ProfileConfig,
    TradingEnvironment,
    TradingMode,
    BrokerConfig,
    ExecutionConfig,
)


class TestTradingModeEnum:
    """Tests for TradingMode enum."""

    def test_trading_mode_values(self):
        """Test TradingMode enum values."""
        assert TradingMode.BACKTEST.value == "backtest"
        assert TradingMode.PAPER.value == "paper"
        assert TradingMode.LIVE.value == "live"

    def test_trading_mode_from_string(self):
        """Test creating TradingMode from string."""
        assert TradingMode("backtest") == TradingMode.BACKTEST
        assert TradingMode("paper") == TradingMode.PAPER
        assert TradingMode("live") == TradingMode.LIVE


class TestProfileConfigTradingMode:
    """Tests for ProfileConfig with trading_mode field."""

    def test_default_profile_has_paper_mode(self):
        """Test default profile uses paper mode."""
        profile = ProfileConfig()
        assert profile.trading_mode == TradingMode.PAPER

    def test_profile_with_backtest_mode(self):
        """Test creating profile with backtest mode."""
        profile = ProfileConfig(
            profile_name="test_backtest",
            trading_mode=TradingMode.BACKTEST
        )
        assert profile.trading_mode == TradingMode.BACKTEST

    def test_profile_mode_serialization(self):
        """Test trading_mode is properly serialized."""
        profile = ProfileConfig(
            trading_mode=TradingMode.LIVE,
            broker=BrokerConfig(broker_type=BrokerType.ALPACA, paper_trading=False),
            execution=ExecutionConfig(manual_approval_default=True)
        )
        data = profile.model_dump()
        # With use_enum_values=False, enums are kept as enum instances
        assert data["trading_mode"] == TradingMode.LIVE
        # For JSON serialization, use mode='json'
        json_data = profile.model_dump(mode='json')
        assert json_data["trading_mode"] == "live"


class TestBacktestModeValidation:
    """Tests for BACKTEST mode validation."""

    def test_backtest_mode_with_mock_broker(self):
        """Test backtest mode works with mock broker."""
        profile = ProfileConfig(
            profile_name="backtest",
            trading_mode=TradingMode.BACKTEST,
            broker=BrokerConfig(broker_type=BrokerType.MOCK)
        )
        assert profile.trading_mode == TradingMode.BACKTEST

    def test_backtest_mode_warns_on_real_broker(self):
        """Test warning when using real broker in backtest mode."""
        # Should create but log warning
        profile = ProfileConfig(
            profile_name="backtest",
            trading_mode=TradingMode.BACKTEST,
            broker=BrokerConfig(broker_type=BrokerType.ALPACA)
        )
        assert profile.trading_mode == TradingMode.BACKTEST

    def test_backtest_profile_safety_check(self):
        """Test is_safe_for_mode for backtest."""
        profile = ProfileConfig(
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(broker_type=BrokerType.ALPACA)
        )

        # Not safe because broker is not MOCK
        is_safe, issues = profile.is_safe_for_mode(TradingMode.BACKTEST)
        assert not is_safe
        assert len(issues) > 0


class TestPaperModeValidation:
    """Tests for PAPER mode validation."""

    def test_paper_mode_with_paper_trading(self):
        """Test paper mode requires paper_trading=True."""
        profile = ProfileConfig(
            profile_name="paper",
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=True
            )
        )
        assert profile.trading_mode == TradingMode.PAPER

    def test_paper_mode_warns_without_paper_trading(self):
        """Test warning when paper_trading=False in paper mode."""
        # Should create but log warning
        profile = ProfileConfig(
            profile_name="paper_wrong",
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=False
            )
        )
        assert profile.trading_mode == TradingMode.PAPER

    def test_paper_profile_safety_check(self):
        """Test is_safe_for_mode for paper."""
        profile = ProfileConfig(
            trading_mode=TradingMode.BACKTEST,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=False
            )
        )

        # Not safe because paper_trading is False
        is_safe, issues = profile.is_safe_for_mode(TradingMode.PAPER)
        assert not is_safe
        assert "paper trading should be enabled" in issues[0].lower()


class TestLiveModeValidation:
    """Tests for LIVE mode validation and safety."""

    def test_live_mode_requires_manual_approval(self):
        """Test live mode requires manual approval."""
        with pytest.raises(ValueError, match="manual_approval_default"):
            ProfileConfig(
                profile_name="live_unsafe",
                trading_mode=TradingMode.LIVE,
                broker=BrokerConfig(
                    broker_type=BrokerType.ALPACA,
                    paper_trading=False
                ),
                execution=ExecutionConfig(
                    manual_approval_default=False  # ❌ Not allowed
                )
            )

    def test_live_mode_rejects_paper_trading(self):
        """Test live mode rejects paper_trading=True."""
        with pytest.raises(ValueError, match="incompatible with paper_trading"):
            ProfileConfig(
                profile_name="live_paper",
                trading_mode=TradingMode.LIVE,
                broker=BrokerConfig(
                    broker_type=BrokerType.ALPACA,
                    paper_trading=True  # ❌ Not allowed
                ),
                execution=ExecutionConfig(
                    manual_approval_default=True
                )
            )

    def test_live_mode_with_correct_settings(self):
        """Test live mode with proper safety settings."""
        profile = ProfileConfig(
            profile_name="live_safe",
            trading_mode=TradingMode.LIVE,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=False
            ),
            execution=ExecutionConfig(
                manual_approval_default=True,
                emergency_stop_active=True
            )
        )
        assert profile.trading_mode == TradingMode.LIVE

    def test_live_profile_safety_check_all_issues(self):
        """Test is_safe_for_mode detects all live mode issues."""
        profile = ProfileConfig(
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(
                broker_type=BrokerType.MOCK,  # ❌ Wrong broker
                paper_trading=True  # ❌ Should be False
            ),
            execution=ExecutionConfig(
                manual_approval_default=False,  # ❌ Should be True
                emergency_stop_active=False  # ❌ Should be True
            )
        )

        is_safe, issues = profile.is_safe_for_mode(TradingMode.LIVE)
        assert not is_safe
        assert len(issues) == 4  # All 4 issues detected


class TestModeSwitching:
    """Tests for switching between trading modes."""

    def test_switch_from_paper_to_backtest(self):
        """Test switching from paper to backtest mode."""
        profile = ProfileConfig(
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(broker_type=BrokerType.MOCK)
        )

        profile.switch_to_mode(TradingMode.BACKTEST, validate=False)
        assert profile.trading_mode == TradingMode.BACKTEST

    def test_switch_to_live_fails_validation(self):
        """Test switching to live mode fails with invalid config."""
        profile = ProfileConfig(
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=True
            ),
            execution=ExecutionConfig(
                manual_approval_default=False
            )
        )

        with pytest.raises(ValueError, match="Cannot switch to live mode"):
            profile.switch_to_mode(TradingMode.LIVE, validate=True)

    def test_switch_to_live_succeeds_with_valid_config(self):
        """Test switching to live mode succeeds with valid config."""
        profile = ProfileConfig(
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(
                broker_type=BrokerType.ALPACA,
                paper_trading=False
            ),
            execution=ExecutionConfig(
                manual_approval_default=True,
                emergency_stop_active=True
            )
        )

        profile.switch_to_mode(TradingMode.LIVE, validate=True)
        assert profile.trading_mode == TradingMode.LIVE

    def test_switch_without_validation(self):
        """Test switching mode without validation (unsafe)."""
        profile = ProfileConfig(
            trading_mode=TradingMode.PAPER,
            broker=BrokerConfig(paper_trading=True)
        )

        # Allow unsafe switch
        profile.switch_to_mode(TradingMode.LIVE, validate=False)
        assert profile.trading_mode == TradingMode.LIVE


class TestProfileFactoryMethods:
    """Tests for profile creation factory methods."""

    def test_create_backtest_profile(self):
        """Test creating backtest profile."""
        profile = ProfileConfig.create_backtest_profile(
            name="my_backtest",
            initial_capital=Decimal("50000")
        )

        assert profile.profile_name == "my_backtest"
        assert profile.trading_mode == TradingMode.BACKTEST
        assert profile.environment == TradingEnvironment.DEVELOPMENT
        assert profile.broker.broker_type == BrokerType.MOCK
        assert profile.backtest.initial_capital == Decimal("50000")
        assert not profile.execution.manual_approval_default

    def test_create_paper_profile(self):
        """Test creating paper trading profile."""
        profile = ProfileConfig.create_paper_profile(
            name="my_paper",
            broker_type=BrokerType.ALPACA
        )

        assert profile.profile_name == "my_paper"
        assert profile.trading_mode == TradingMode.PAPER
        assert profile.environment == TradingEnvironment.PAPER
        assert profile.broker.broker_type == BrokerType.ALPACA
        assert profile.broker.paper_trading is True
        assert profile.execution.manual_approval_default is True

    def test_create_live_profile(self):
        """Test creating live trading profile."""
        profile = ProfileConfig.create_live_profile(
            name="my_live",
            broker_type=BrokerType.ALPACA
        )

        assert profile.profile_name == "my_live"
        assert profile.trading_mode == TradingMode.LIVE
        assert profile.environment == TradingEnvironment.PRODUCTION
        assert profile.broker.broker_type == BrokerType.ALPACA
        assert profile.broker.paper_trading is False
        assert profile.execution.manual_approval_default is True
        assert profile.execution.emergency_stop_active is True
        assert profile.trading.max_daily_loss == Decimal("500")

    def test_all_factory_profiles_are_valid(self):
        """Test all factory-created profiles pass validation."""
        backtest = ProfileConfig.create_backtest_profile()
        paper = ProfileConfig.create_paper_profile()
        live = ProfileConfig.create_live_profile()

        # All should be valid for their respective modes
        assert backtest.is_safe_for_mode(TradingMode.BACKTEST)[0]
        assert paper.is_safe_for_mode(TradingMode.PAPER)[0]
        assert live.is_safe_for_mode(TradingMode.LIVE)[0]


class TestModeConfigIntegration:
    """Integration tests for mode configuration."""

    def test_backtest_profile_loads_from_yaml(self, tmp_path):
        """Test loading backtest profile from YAML."""
        yaml_content = """
profile_name: backtest_test
trading_mode: backtest
broker:
  broker_type: mock
  paper_trading: true
execution:
  manual_approval_default: false
"""
        yaml_file = tmp_path / "backtest_test.yaml"
        yaml_file.write_text(yaml_content)

        import yaml
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            profile = ProfileConfig(**data)

        assert profile.trading_mode == TradingMode.BACKTEST
        assert profile.broker.broker_type == BrokerType.MOCK

    def test_paper_profile_loads_from_yaml(self, tmp_path):
        """Test loading paper profile from YAML."""
        yaml_content = """
profile_name: paper_test
trading_mode: paper
broker:
  broker_type: alpaca
  paper_trading: true
execution:
  manual_approval_default: true
"""
        yaml_file = tmp_path / "paper_test.yaml"
        yaml_file.write_text(yaml_content)

        import yaml
        with open(yaml_file) as f:
            data = yaml.safe_load(f)
            profile = ProfileConfig(**data)

        assert profile.trading_mode == TradingMode.PAPER
        assert profile.broker.paper_trading is True

    def test_mode_validation_in_loaded_profile(self, tmp_path):
        """Test that validation works on loaded profiles."""
        # Create invalid live config
        yaml_content = """
profile_name: live_invalid
trading_mode: live
broker:
  broker_type: alpaca
  paper_trading: true
execution:
  manual_approval_default: false
"""
        yaml_file = tmp_path / "live_invalid.yaml"
        yaml_file.write_text(yaml_content)

        import yaml
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        # Should raise validation error
        with pytest.raises(ValueError):
            ProfileConfig(**data)
