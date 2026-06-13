"""Configuration management.

Reads settings from:
1. Environment variables (highest priority)
2. TOML config file at ~/.config/paper-aggregator/config.toml
3. Sensible defaults
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
import tomllib


def _default_config_path() -> Path:
    """Return the XDG-compliant config file path."""
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        return Path(xdg_config) / "paper-aggregator" / "config.toml"
    return Path.home() / ".config" / "paper-aggregator" / "config.toml"


def _default_data_dir() -> Path:
    """Return the XDG-compliant data directory."""
    xdg_data = os.environ.get("XDG_DATA_HOME")
    if xdg_data:
        return Path(xdg_data) / "paper-aggregator"
    return Path.home() / ".local" / "share" / "paper-aggregator"


@dataclass
class Settings:
    """Application settings with env-var override support."""

    api_key: str = field(default_factory=lambda: os.environ.get("PAPER_AGGREGATOR_API_KEY", ""))
    api_base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-5.4-nano"
    max_context_chars: int = 6000
    db_path: Path = field(default_factory=lambda: _default_data_dir() / "papers.db")
    pdf_storage_path: Path = field(default_factory=lambda: _default_data_dir() / "pdfs")

    @classmethod
    def load(cls) -> Settings:
        """Load settings from config file and environment, with env taking precedence."""
        config_path = _default_config_path()
        settings = cls()

        if config_path.exists():
            settings = cls._merge_from_file(settings, config_path)

        # Env vars always take precedence for select keys
        if os.environ.get("PAPER_AGGREGATOR_API_KEY"):
            settings.api_key = os.environ["PAPER_AGGREGATOR_API_KEY"]

        return settings

    @staticmethod
    def _merge_from_file(settings: Settings, path: Path) -> Settings:
        """Merge TOML config file values into a Settings instance."""
        with open(path, "rb") as f:
            data = tomllib.load(f)

        if "api_base_url" in data:
            settings.api_base_url = data["api_base_url"]
        if "model" in data:
            settings.model = data["model"]
        if "max_context_chars" in data:
            settings.max_context_chars = data["max_context_chars"]
        if "db_path" in data:
            settings.db_path = Path(data["db_path"]).expanduser()
        if "pdf_storage_path" in data:
            settings.pdf_storage_path = Path(data["pdf_storage_path"]).expanduser()

        return settings


# Global settings instance - populated at startup
settings = Settings.load()
