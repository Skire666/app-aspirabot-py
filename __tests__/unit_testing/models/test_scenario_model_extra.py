"""Additional tests for models/scenario_model.py."""

from __future__ import annotations

from datetime import datetime

import pytest

from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel


class TestGetDefaultData:
    def test_returns_scenario_model(self) -> None:
        s = ScenarioModel.get_default_data()
        assert isinstance(s, ScenarioModel)

    def test_default_has_name(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.scenario_name

    def test_default_has_timestamps(self) -> None:
        s = ScenarioModel.get_default_data()
        assert isinstance(s.created_date_scenario, datetime)
        assert isinstance(s.modified_date_scenario, datetime)

    def test_default_has_id(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.id_file


class TestMarkAsCreated:
    def test_sets_timestamps(self) -> None:
        s = ScenarioModel.get_default_data()
        s.created_date_scenario = None
        s.modified_date_scenario = None
        s.mark_as_created()
        assert s.created_date_scenario is not None
        assert s.modified_date_scenario is not None

    def test_both_timestamps_equal(self) -> None:
        s = ScenarioModel.get_default_data()
        s.mark_as_created()
        assert s.created_date_scenario == s.modified_date_scenario


class TestMarkAsModified:
    def test_sets_modified_timestamp(self) -> None:
        s = ScenarioModel.get_default_data()
        original_created = s.created_date_scenario
        s.mark_as_modified()
        assert s.modified_date_scenario is not None
        assert s.created_date_scenario == original_created


class TestIsValidId:
    @pytest.mark.parametrize("value,expected", [
        ("", False),
        ("   ", False),
        ("abc123", True),
        ("ABC123", True),
        ("valid_id_123", False),  # underscore not alnum
        ("123", True),
    ])
    def test_is_valid_id(self, value: str, expected: bool) -> None:
        assert ScenarioModel.is_valid_id(value) == expected


class TestCopyBusiness:
    def test_copy_has_different_id(self) -> None:
        source = ScenarioModel.get_default_data()
        copy = ScenarioModel.copy_business(source)
        assert copy.id_file != source.id_file

    def test_copy_name_prefixed(self) -> None:
        source = ScenarioModel.get_default_data()
        source.scenario_name = "Test"
        copy = ScenarioModel.copy_business(source)
        assert "Copie de" in copy.scenario_name

    def test_copy_is_independent(self) -> None:
        source = ScenarioModel.get_default_data()
        copy = ScenarioModel.copy_business(source)
        source.scenario_name = "Changed"
        assert "Changed" not in copy.scenario_name


class TestImportExport:
    def test_export_then_import_roundtrip(self) -> None:
        s = ScenarioModel.get_default_data()
        s.scenario_name = "My Scenario"
        data = s.export_to_data_json()
        s2 = ScenarioModel.import_from_data_json(data)
        assert s2.scenario_name == "My Scenario"
        assert s2.id_file == s.id_file

    def test_import_missing_fields_uses_defaults(self) -> None:
        s = ScenarioModel.import_from_data_json({})
        assert s.id_file == ""
        assert s.scenario_name == ""

    def test_deserialize_steps_non_list_returns_empty(self) -> None:
        result = ScenarioModel._deserialize_steps("not a list")
        assert result == []

    def test_deserialize_steps_non_dict_items_skipped(self) -> None:
        result = ScenarioModel._deserialize_steps([1, 2, "text"])
        assert result == []
