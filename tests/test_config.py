"""Tests for Configuration Management."""

import tempfile
from pathlib import Path

import pytest
import yaml

from src.config.loader import (
    AIConfig,
    BrokerConfig,
    BrokerType,
    ConfigManager,
    ProfileConfig,
    TradingEnvironment,
)


class TestConfiguration:
    """Test configuration loading and management."""

    def setup_method(self):
        """Setup test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_dir = Path(self.temp_dir)

    def test_default_config_creation(self):
        """Test default configuration creation."""
        loader = ConfigManager(str(self.config_dir))
        config = loader.load_profile("paper")

        assert config.profile_name == "paper"
        assert config.environment == TradingEnvironment.PAPER
        assert config.broker.broker_type == BrokerType.MOCK
        assert config.ai.model == "gpt-4-turbo-preview"

    def test_profile_loading(self):
        """Test loading specific profile."""
        # Create test profile
        profile_data = {
            "profile_name": "test_profile",
            "environment": "paper",
            "broker": {
                "broker_type": "ibkr",
                "host": "127.0.0.1",
                "port": 7497,
                "paper_trading": True
            },
            "ai": {
                "model": "gpt-4-turbo-preview",
                "temperature": 0.2
            }
        }

        # Save to file
        profile_path = self.config_dir / "test_profile.yaml"
        with open(profile_path, "w") as f:
            yaml.dump(profile_data, f)

        # Load profile
        loader = ConfigManager(str(self.config_dir))
        config = loader.load_profile("test_profile")

        assert config.profile_name == "test_profile"
        assert config.environment == TradingEnvironment.PAPER.value
        # broker_type is loaded as enum, not string
        assert config.broker.broker_type == BrokerType.IBKR

    def test_save_config(self):
        """Test saving configuration."""
        loader = ConfigManager(str(self.config_dir))
        config = loader.load_profile("test_save")

        # Modify config
        config.environment = TradingEnvironment.PRODUCTION
        config.broker.port = 7496

        # Save
        loader.save_profile(config)

        # Reload
        loader2 = ConfigManager(str(self.config_dir))
        loaded = loader2.load_profile("test_save")

        assert loaded.environment == TradingEnvironment.PRODUCTION.value
        assert loaded.broker.port == 7496

    def test_config_validation(self):
        """Test configuration validation."""
        config = ProfileConfig(
            profile_name="test",
            environment=TradingEnvironment.PAPER
        )

        # Should have defaults
        assert config.broker is not None
        assert config.ai is not None
        assert config.trading is not None

    def test_environment_specific_settings(self):
        """Test environment-specific settings."""
        # Paper trading config
        paper_config = ProfileConfig(
            profile_name="paper",
            environment=TradingEnvironment.PAPER
        )
        assert paper_config.environment == TradingEnvironment.PAPER.value

        # Production config
        prod_config = ProfileConfig(
            profile_name="prod",
            environment=TradingEnvironment.PRODUCTION
        )
        assert prod_config.environment == TradingEnvironment.PRODUCTION.value
        # Production should have manual approval by default
        assert prod_config.execution.manual_approval_default is True

    def test_broker_config(self):
        """Test broker configuration."""
        broker = BrokerConfig(
            broker_type=BrokerType.IBKR,
            host="127.0.0.1",
            port=7497,
            paper_trading=True
        )

        assert broker.broker_type == BrokerType.IBKR
        assert broker.paper_trading is True

    def test_ai_config(self):
        """Test AI configuration."""
        ai = AIConfig(
            enabled=True,
            model="gpt-4-turbo-preview",
            temperature=0.3
        )

        assert ai.enabled is True
        assert ai.model == "gpt-4-turbo-preview"
        assert ai.temperature == 0.3

    def test_list_profiles(self):
        """Test listing available profiles."""
        loader = ConfigManager(str(self.config_dir))

        # Create some profiles
        loader.load_profile("profile1")
        loader.load_profile("profile2")

        profiles = loader.list_profiles()
        assert "profile1" in profiles
        assert "profile2" in profiles

    def test_export_config(self):
        """Test exporting configuration."""
        loader = ConfigManager(str(self.config_dir))
        config = loader.load_profile("export_test")

        export_path = self.config_dir / "export.json"
        loader.export_config(export_path)

        assert export_path.exists()

        import json
        with open(export_path) as f:
            exported = json.load(f)

        assert exported["profile_name"] == "export_test"
        assert "exported_at" in exported
        assert "version" in exported
