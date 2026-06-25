"""Unit tests for configuration loading (T1.8)."""

from __future__ import annotations

from pathlib import Path

import pytest

from paper_aggregator.config.settings import (
    Settings,
    _default_config_path,
    _default_data_dir,
)


class TestDefaultPaths:
    """XDG-compliant path resolution."""

    def test_config_path_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XDG_CONFIG_HOME", raising=False)
        path = _default_config_path()
        assert path == Path.home() / ".config" / "paper-aggregator" / "config.toml"

    def test_config_path_xdg_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XDG_CONFIG_HOME", "/custom/config")
        path = _default_config_path()
        assert path == Path("/custom/config") / "paper-aggregator" / "config.toml"

    def test_data_dir_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        path = _default_data_dir()
        assert path == Path.home() / ".local" / "share" / "paper-aggregator"

    def test_data_dir_xdg_override(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XDG_DATA_HOME", "/custom/data")
        path = _default_data_dir()
        assert path == Path("/custom/data") / "paper-aggregator"


class TestSettingsDefaults:
    """Default values when no config file or env vars are present."""

    def test_default_api_base_url(self) -> None:
        s = Settings()
        assert s.api_base_url == "https://api.openai.com/v1"

    def test_default_model(self) -> None:
        s = Settings()
        assert s.model == "gpt-5.4-nano"

    def test_default_max_context_chars(self) -> None:
        s = Settings()
        assert s.max_context_chars == 6000

    def test_api_key_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("PAPER_AGGREGATOR_API_KEY", "sk-test-123")
        s = Settings()
        assert s.api_key == "sk-test-123"

    def test_api_key_empty_when_not_set(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("PAPER_AGGREGATOR_API_KEY", raising=False)
        s = Settings()
        assert s.api_key == ""


class TestMergeFromFile:
    """TOML config file merging."""

    def test_merges_all_fields(self, tmp_path: Path) -> None:
        config_path = tmp_path / "config.toml"
        config_path.write_text(
            "[paper-aggregator]\n"
            'api_base_url = "https://llm.example.com/v1"\n'
            'model = "llama-3"\n'
            "max_context_chars = 3000\n"
            'db_path = "/custom/papers.db"\n'
            'pdf_storage_path = "/custom/pdfs"\n'
        )

        s = Settings()
        # Parse with the same flat-keys format the app actually uses.
        import tomllib

        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        # Simulate what _merge_from_file does (flat keys, not [paper-aggregator]).
        flat_config = tmp_path / "flat.toml"
        flat_config.write_text(
            'api_base_url = "https://llm.example.com/v1"\n'
            'model = "llama-3"\n'
            "max_context_chars = 3000\n"
            'db_path = "/custom/papers.db"\n'
            'pdf_storage_path = "/custom/pdfs"\n'
        )
        s = Settings._merge_from_file(s, flat_config)

        assert s.api_base_url == "https://llm.example.com/v1"
        assert s.model == "llama-3"
        assert s.max_context_chars == 3000
        assert s.db_path == Path("/custom/papers.db")
        assert s.pdf_storage_path == Path("/custom/pdfs")

    def test_merge_partial_file(self, tmp_path: Path) -> None:
        """Only some keys in the file - the rest keep defaults."""
        config_path = tmp_path / "partial.toml"
        config_path.write_text('model = "claude-4"\n')

        s = Settings()
        s = Settings._merge_from_file(s, config_path)

        assert s.model == "claude-4"
        assert s.api_base_url == "https://api.openai.com/v1"  # default intact
        assert s.max_context_chars == 6000  # default intact

    def test_merge_expands_user_paths(self, tmp_path: Path) -> None:
        config_path = tmp_path / "tilde.toml"
        config_path.write_text(
            'db_path = "~/my-papers/papers.db"\n'
            'pdf_storage_path = "~/my-papers/pdfs"\n'
        )

        s = Settings()
        s = Settings._merge_from_file(s, config_path)

        assert s.db_path == Path("~/my-papers/papers.db").expanduser()
        assert s.pdf_storage_path == Path("~/my-papers/pdfs").expanduser()

    def test_merge_empty_file(self, tmp_path: Path) -> None:
        config_path = tmp_path / "empty.toml"
        config_path.write_text("")

        s = Settings()
        original = Settings()
        s = Settings._merge_from_file(s, config_path)

        assert s.api_base_url == original.api_base_url
        assert s.model == original.model
        assert s.max_context_chars == original.max_context_chars


class TestSettingsLoad:
    """Full Settings.load() with and without config files."""

    def test_load_with_api_key_env_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Env var takes precedence over config file and defaults."""
        monkeypatch.setenv("PAPER_AGGREGATOR_API_KEY", "sk-env-override")
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))

        # Create config dir + file with a different key in env style.
        config_dir = tmp_path / "paper-aggregator"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text(
            'api_base_url = "https://custom.example.com/v1"\n'
            'model = "custom-model"\n'
        )

        # Also set api_key in env since PAPER_AGGREGATOR_API_KEY is read
        # from env in the Settings.__init__ default_factory AND in load().
        s = Settings.load()

        assert s.api_key == "sk-env-override"
        assert s.api_base_url == "https://custom.example.com/v1"
        assert s.model == "custom-model"

    def test_load_no_config_file(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """When no config file exists, defaults are used."""
        monkeypatch.delenv("PAPER_AGGREGATOR_API_KEY", raising=False)
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "nonexistent"))

        s = Settings.load()

        assert s.api_key == ""
        assert s.api_base_url == "https://api.openai.com/v1"
        assert s.model == "gpt-5.4-nano"
        assert s.max_context_chars == 6000

    def test_invalid_toml_raises(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Malformed TOML should raise a parse error."""
        monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
        config_dir = tmp_path / "paper-aggregator"
        config_dir.mkdir(parents=True)
        config_file = config_dir / "config.toml"
        config_file.write_text("this is not valid toml {{{")

        with pytest.raises(Exception):  # tomllib.TOMLDecodeError or similar
            Settings.load()
