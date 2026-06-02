"""Tests for models/app_configuration_model.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from models.app_configuration_model import AppConfigurationModel
from shared.exception_util import (
    InvalidBrowserEngineError,
    InvalidFolderLogsError,
    InvalidFolderScenariosError,
    InvalidFolderScrapingError,
    InvalidGuiBootingSizeError,
    InvalidLogLevelError,
)


def _make_config(**kwargs: object) -> AppConfigurationModel:
    defaults: dict[str, object] = {
        "log_level_enum": "DEBUG",
        "folder_logs": "tmp_logs",
        "folder_scenarios": "data_scenarios",
        "folder_scraping": "data_scraping",
        "gui_booting_size": "1000x800",
        "gui_booting_fullscreen": False,
        "browser_engine": "Playwright",
    }
    defaults.update(kwargs)
    return AppConfigurationModel(**defaults)  # type: ignore[arg-type]


class TestInit:
    def test_default_construction(self) -> None:
        cfg = AppConfigurationModel()
        assert cfg.log_level_enum == "DEBUG"
        assert cfg.browser_engine == "Playwright"

    def test_custom_values(self) -> None:
        cfg = _make_config(log_level_enum="INFO")
        assert cfg.log_level_enum == "INFO"


class TestLogLevelEnum:
    @pytest.mark.parametrize("level", ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    def test_all_valid_levels(self, level: str) -> None:
        cfg = _make_config(log_level_enum=level)
        assert cfg.log_level_enum == level

    def test_invalid_level_raises(self) -> None:
        with pytest.raises(InvalidLogLevelError):
            _make_config(log_level_enum="VERBOSE")

    def test_lowercase_raises(self) -> None:
        with pytest.raises(InvalidLogLevelError):
            _make_config(log_level_enum="debug")


class TestFolderLogs:
    def test_string_path_converted(self) -> None:
        cfg = _make_config(folder_logs="my_logs")
        assert isinstance(cfg.folder_logs, Path)
        assert cfg.folder_logs == Path("my_logs")

    def test_path_object_accepted(self) -> None:
        cfg = _make_config(folder_logs=Path("/tmp/logs"))
        assert cfg.folder_logs == Path("/tmp/logs")

    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidFolderLogsError):
            _make_config(folder_logs="")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(InvalidFolderLogsError):
            _make_config(folder_logs="   ")


class TestFolderScenarios:
    def test_valid_string(self) -> None:
        cfg = _make_config(folder_scenarios="scenarios")
        assert cfg.folder_scenarios == Path("scenarios")

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidFolderScenariosError):
            _make_config(folder_scenarios="")

    def test_whitespace_raises(self) -> None:
        with pytest.raises(InvalidFolderScenariosError):
            _make_config(folder_scenarios="  ")


class TestFolderScraping:
    def test_valid_string(self) -> None:
        cfg = _make_config(folder_scraping="scraping")
        assert cfg.folder_scraping == Path("scraping")

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidFolderScrapingError):
            _make_config(folder_scraping="")

    def test_whitespace_raises(self) -> None:
        with pytest.raises(InvalidFolderScrapingError):
            _make_config(folder_scraping="  ")


class TestGuiBootingSize:
    def test_valid_format(self) -> None:
        cfg = _make_config(gui_booting_size="1920x1080")
        assert cfg.gui_booting_size == "1920x1080"

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            _make_config(gui_booting_size="")

    def test_no_x_separator_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            _make_config(gui_booting_size="1920-1080")

    def test_non_numeric_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            _make_config(gui_booting_size="WIDTHxHEIGHT")

    def test_only_one_part_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            _make_config(gui_booting_size="1920")


class TestBrowserEngine:
    def test_playwright_valid(self) -> None:
        cfg = _make_config(browser_engine="Playwright")
        assert cfg.browser_engine == "Playwright"

    def test_invalid_engine_raises(self) -> None:
        with pytest.raises(InvalidBrowserEngineError):
            _make_config(browser_engine="Firefox")

    def test_lowercase_playwright_raises(self) -> None:
        with pytest.raises(InvalidBrowserEngineError):
            _make_config(browser_engine="playwright")


class TestToDict:
    def test_returns_dict(self) -> None:
        cfg = _make_config()
        result = cfg.to_dict()
        assert isinstance(result, dict)

    def test_contains_all_keys(self) -> None:
        cfg = _make_config()
        result = cfg.to_dict()
        expected_keys = {
            "log_level_enum", "folder_logs", "folder_scenarios", "folder_scraping",
            "gui_booting_size", "gui_booting_fullscreen", "browser_engine",
            "chromium_persistant_dir", "chromium_extensions_dir",
        }
        assert expected_keys.issubset(result.keys())

    def test_folder_paths_are_strings(self) -> None:
        cfg = _make_config()
        result = cfg.to_dict()
        assert isinstance(result["folder_logs"], str)
        assert isinstance(result["folder_scenarios"], str)
