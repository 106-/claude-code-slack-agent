import yaml
import sys
import os
from unittest.mock import patch, mock_open

# Add the parent directory to the Python path to import main module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import main  # noqa: E402
from main import load_config, setup_logging  # noqa: E402


def test_load_config_success():
    """Test successful configuration loading."""
    mock_config = {
        "slack": {
            "bot_token": "test_token",
            "signing_secret": "test_secret",
            "app_token": "test_app_token",
        },
        "bot": {"system_prompt": "test", "allowed_tools": [], "max_turns": 2},
        "logging": {"level": "INFO", "format": "test_format"},
        "messages": {
            "empty_message": "Empty",
            "processing_message": "Processing",
            "general_error": "Error",
        },
    }

    with patch("builtins.open", mock_open(read_data=yaml.dump(mock_config))):
        config = load_config()
        assert config is not None
        assert config["slack"]["bot_token"] == "test_token"


def test_load_config_file_not_found():
    """Test configuration loading when file doesn't exist."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        config = load_config()
        assert config is None


def test_load_config_yaml_error():
    """Test configuration loading with invalid YAML."""
    with patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")):
        config = load_config()
        assert config is None


def test_setup_logging():
    """Test logging setup."""
    with patch("logging.basicConfig") as mock_basic_config:
        setup_logging("INFO")
        mock_basic_config.assert_called_once()


def test_import_main_module():
    """Test that the main module can be imported without errors."""
    assert hasattr(main, "main")
    assert hasattr(main, "ClaudeSlackApp")
