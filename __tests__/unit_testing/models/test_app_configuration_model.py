"""Tests for models/app_configuration_model.py."""

from __future__ import annotations

import pytest
from models.app_configuration_model import AppConfigurationModel
from shared.exception_util import (
    EmptyScenarioIdError,
    InvalidFolderLogsError,
    InvalidGuiBootingPositionError,
    InvalidGuiBootingSizeError,
    InvalidLogLevelError,
)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset the AppConfigurationModel singleton before each test."""
    AppConfigurationModel._instance = None
    yield
    AppConfigurationModel._instance = None


class TestSingleton:
    def test_same_instance_returned(self) -> None:
        m1 = AppConfigurationModel()
        m2 = AppConfigurationModel()
        assert m1 is m2

    def test_get_instance_raises_before_init(self) -> None:
        with pytest.raises(RuntimeError):
            AppConfigurationModel.get_instance()

    def test_get_instance_returns_instance_after_init(self) -> None:
        m = AppConfigurationModel()
        assert AppConfigurationModel.get_instance() is m

    def test_second_init_does_not_reinit(self) -> None:
        m = AppConfigurationModel(log_level_enum="INFO")
        AppConfigurationModel(log_level_enum="DEBUG")
        assert m.log_level_enum == "INFO"


class TestLogLevel:
    def test_valid_levels(self) -> None:
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            AppConfigurationModel._instance = None
            m = AppConfigurationModel(log_level_enum=level)
            assert m.log_level_enum == level
            AppConfigurationModel._instance = None

    def test_invalid_level_raises(self) -> None:
        with pytest.raises(InvalidLogLevelError):
            AppConfigurationModel(log_level_enum="TRACE")

    def test_setter_valid(self) -> None:
        m = AppConfigurationModel()
        m.log_level_enum = "WARNING"
        assert m.log_level_enum == "WARNING"

    def test_setter_invalid_raises(self) -> None:
        m = AppConfigurationModel()
        with pytest.raises(InvalidLogLevelError):
            m.log_level_enum = "VERBOSE"


class TestFolderLogs:
    def test_empty_string_raises(self) -> None:
        with pytest.raises(InvalidFolderLogsError):
            AppConfigurationModel(folder_logs="")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(InvalidFolderLogsError):
            AppConfigurationModel(folder_logs="   ")

    def test_valid_path_accepted(self) -> None:
        from pathlib import Path

        m = AppConfigurationModel(folder_logs="/var/log")
        assert m.folder_logs == Path("/var/log")

    def test_setter_empty_raises(self) -> None:
        m = AppConfigurationModel()
        with pytest.raises(InvalidFolderLogsError):
            m.folder_logs = ""


class TestFolderScenarios:
    def test_empty_string_sets_none(self) -> None:
        m = AppConfigurationModel(folder_scenarios="")
        assert not m.is_folder_scenarios_configured

    def test_none_sets_none(self) -> None:
        m = AppConfigurationModel(folder_scenarios=None)
        assert not m.is_folder_scenarios_configured

    def test_whitespace_sets_none(self) -> None:
        m = AppConfigurationModel(folder_scenarios="   ")
        assert not m.is_folder_scenarios_configured

    def test_valid_path_accepted(self) -> None:
        from pathlib import Path

        m = AppConfigurationModel(folder_scenarios="/some/path")
        assert m.is_folder_scenarios_configured
        assert m.folder_scenarios == Path("/some/path")

    def test_access_without_config_raises(self) -> None:
        m = AppConfigurationModel(folder_scenarios="")
        with pytest.raises(AssertionError):
            _ = m.folder_scenarios


class TestGuiBootingSize:
    def test_valid_size(self) -> None:
        m = AppConfigurationModel(gui_booting_size="1280x720")
        assert m.gui_booting_size == "1280x720"

    def test_empty_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            AppConfigurationModel(gui_booting_size="")

    def test_no_x_separator_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            AppConfigurationModel(gui_booting_size="1280720")

    def test_non_digit_parts_raise(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            AppConfigurationModel(gui_booting_size="widexhigh")

    def test_too_many_parts_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingSizeError):
            AppConfigurationModel(gui_booting_size="1280x720x100")


class TestGuiBootingPosition:
    def test_empty_sets_empty_string(self) -> None:
        m = AppConfigurationModel(gui_booting_position="")
        assert m.gui_booting_position == ""

    def test_none_sets_empty_string(self) -> None:
        m = AppConfigurationModel(gui_booting_position=None)
        assert m.gui_booting_position == ""

    def test_valid_position(self) -> None:
        m = AppConfigurationModel(gui_booting_position="100,300")
        assert m.gui_booting_position == "100,300"

    def test_single_value_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingPositionError):
            AppConfigurationModel(gui_booting_position="100")

    def test_non_integer_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingPositionError):
            AppConfigurationModel(gui_booting_position="x,y")

    def test_too_many_parts_raises(self) -> None:
        with pytest.raises(InvalidGuiBootingPositionError):
            AppConfigurationModel(gui_booting_position="100,200,300")


class TestGuiBootingFullscreen:
    def test_true(self) -> None:
        m = AppConfigurationModel(gui_booting_fullscreen=True)
        assert m.gui_booting_fullscreen is True

    def test_false(self) -> None:
        m = AppConfigurationModel(gui_booting_fullscreen=False)
        assert m.gui_booting_fullscreen is False


class TestComputeFullpaths:
    def test_compute_fullpath_profile_empty_id_raises(self) -> None:
        m = AppConfigurationModel(folder_scenarios="/some/path")
        with pytest.raises(EmptyScenarioIdError):
            m.compute_fullpath_profile("")

    def test_compute_fullpath_profile_whitespace_raises(self) -> None:
        m = AppConfigurationModel(folder_scenarios="/some/path")
        with pytest.raises(EmptyScenarioIdError):
            m.compute_fullpath_profile("   ")

    def test_compute_fullpath_profile_valid(self) -> None:
        m = AppConfigurationModel(folder_scenarios="/scenarios")
        path = m.compute_fullpath_profile("scen01")
        assert "scen01" in str(path)

    def test_compute_fullpath_scenario_empty_id_raises(self) -> None:
        m = AppConfigurationModel(folder_scenarios="/some/path")
        with pytest.raises(EmptyScenarioIdError):
            m.compute_fullpath_scenario("")

    def test_compute_fullpath_scenario_valid(self) -> None:
        m = AppConfigurationModel(folder_scenarios="/scenarios")
        path = m.compute_fullpath_scenario("scen01")
        assert "scen01" in str(path)


class TestToDict:
    def test_to_dict_contains_all_keys(self) -> None:
        m = AppConfigurationModel(folder_scenarios="/sc")
        d = m.to_dict()
        assert "log_level_enum" in d
        assert "folder_logs" in d
        assert "folder_scenarios" in d
        assert "gui_booting_size" in d
        assert "gui_booting_fullscreen" in d

    def test_to_dict_folder_scenarios_none(self) -> None:
        m = AppConfigurationModel(folder_scenarios="")
        d = m.to_dict()
        assert d["folder_scenarios"] == ""
