"""Tests for models/app_configuration_model.py."""

from __future__ import annotations

from pathlib import Path

import pytest
from models.app_configuration_model import AppConfigurationModel
from shared.exception_util import (
    InvalidFolderLogsError,
    InvalidFolderScenariosError,
    InvalidGuiBootingSizeError,
    InvalidLogLevelError,
)


def _make_config(**kwargs) -> AppConfigurationModel:
    defaults: dict = {
        "log_level_enum": "INFO",
        "folder_logs": "logs",
        "folder_scenarios": "scenarios",
        "gui_booting_size": "1280x720",
    }
    defaults.update(kwargs)
    return AppConfigurationModel(**defaults)


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


class TestToDict:
    def test_returns_dict(self) -> None:
        cfg = _make_config()
        result = cfg.to_dict()
        assert isinstance(result, dict)

    def test_folder_paths_are_strings(self) -> None:
        cfg = _make_config()
        result = cfg.to_dict()
        assert isinstance(result["folder_logs"], str)
        assert isinstance(result["folder_scenarios"], str)
