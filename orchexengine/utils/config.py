"""Configuration utilities"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and manage configuration"""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize config loader.

        Args:
            config_path: Path to config file. If None, looks for ORCHEXENGINE_CONFIG env var,
                         then falls back to ./config.yaml
        """
        self.config_path = config_path or self._find_config()
        self._config: Optional[Dict[str, Any]] = None

    def _find_config(self) -> str:
        """Find config file in standard locations"""
        # Check environment variable
        env_path = os.getenv("ORCHEXENGINE_CONFIG")
        if env_path and os.path.exists(env_path):
            return env_path

        # Check current directory
        if os.path.exists("./config.yaml"):
            return "./config.yaml"

        # Check package directory
        package_dir = Path(__file__).parent.parent.parent
        config_path = package_dir / "config.yaml"
        if config_path.exists():
            return str(config_path)

        raise FileNotFoundError(
            "Config file not found. Set ORCHEXENGINE_CONFIG env var "
            "or place config.yaml in project root."
        )

    def load(self) -> Dict[str, Any]:
        """Load configuration from file"""
        if self._config is None:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f)
        return self._config

    def reload(self) -> Dict[str, Any]:
        """Force reload configuration"""
        self._config = None
        return self.load()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value by dot-notation key"""
        config = self.load()
        keys = key.split(".")
        value = config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value


# Global config instance
_config_loader: Optional[ConfigLoader] = None


def get_config() -> Dict[str, Any]:
    """Get global configuration"""
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader.load()


def reload_config() -> Dict[str, Any]:
    """Reload global configuration"""
    global _config_loader
    _config_loader = ConfigLoader()
    return _config_loader.load()
