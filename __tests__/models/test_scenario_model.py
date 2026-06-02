"""Tests for models/scenario_model.py."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from models.scenario_model import ScenarioModel


def _make_scenario(**kwargs: object) -> ScenarioModel:
    defaults: dict[str, object] = {
        "id_file": "abcd1234",
        "scenario_name": "Test scenario",
        "scenario_desc": "A test description",
        "created_date_scenario": datetime(2024, 1, 1),
        "modified_date_scenario": datetime(2024, 1, 1),
        "version": "1.0.0",
        "steps": [],
    }
    defaults.update(kwargs)
    return ScenarioModel(**defaults)  # type: ignore[arg-type]


class TestGetDefaultData:
    def test_returns_scenario_model(self) -> None:
        result = ScenarioModel.get_default_data()
        assert isinstance(result, ScenarioModel)

    def test_has_non_empty_id(self) -> None:
        result = ScenarioModel.get_default_data()
        assert result.id_file
        assert len(result.id_file) > 0

    def test_has_name(self) -> None:
        result = ScenarioModel.get_default_data()
        assert result.scenario_name

    def test_version_is_set(self) -> None:
        result = ScenarioModel.get_default_data()
        assert result.version == "1.0.0"

    def test_timestamps_set(self) -> None:
        result = ScenarioModel.get_default_data()
        assert isinstance(result.created_date_scenario, datetime)
        assert isinstance(result.modified_date_scenario, datetime)

    def test_steps_empty_by_default(self) -> None:
        result = ScenarioModel.get_default_data()
        assert result.steps == []

    def test_two_defaults_have_different_ids(self) -> None:
        a = ScenarioModel.get_default_data()
        b = ScenarioModel.get_default_data()
        assert a.id_file != b.id_file


class TestMarkAsCreated:
    def test_sets_both_timestamps(self) -> None:
        scenario = _make_scenario(
            created_date_scenario=datetime(2020, 1, 1),
            modified_date_scenario=datetime(2020, 1, 1),
        )
        before = datetime.now()
        scenario.mark_as_created()
        after = datetime.now()

        assert before <= scenario.created_date_scenario <= after
        assert before <= scenario.modified_date_scenario <= after

    def test_created_and_modified_are_synchronized(self) -> None:
        scenario = _make_scenario()
        scenario.mark_as_created()
        assert scenario.created_date_scenario == scenario.modified_date_scenario


class TestMarkAsModified:
    def test_updates_modified_not_created(self) -> None:
        original_created = datetime(2024, 1, 1)
        scenario = _make_scenario(created_date_scenario=original_created)
        scenario.mark_as_modified()
        assert scenario.created_date_scenario == original_created
        assert scenario.modified_date_scenario != original_created

    def test_modified_date_is_recent(self) -> None:
        scenario = _make_scenario()
        before = datetime.now()
        scenario.mark_as_modified()
        after = datetime.now()
        assert before <= scenario.modified_date_scenario <= after


class TestIsValidId:
    def test_alphanumeric_string(self) -> None:
        assert ScenarioModel.is_valid_id("abc123")

    def test_hex_string(self) -> None:
        assert ScenarioModel.is_valid_id("1a2b3c4d")

    def test_empty_string_returns_false(self) -> None:
        assert not ScenarioModel.is_valid_id("")

    def test_whitespace_only_returns_false(self) -> None:
        assert not ScenarioModel.is_valid_id("   ")

    def test_string_with_spaces_returns_false(self) -> None:
        assert not ScenarioModel.is_valid_id("abc 123")

    def test_string_with_dash_returns_false(self) -> None:
        assert not ScenarioModel.is_valid_id("abc-123")

    def test_strip_and_lower_applied(self) -> None:
        assert ScenarioModel.is_valid_id("  ABC  ")


class TestCopyBusiness:
    def test_copy_has_different_id(self) -> None:
        original = _make_scenario(id_file="original1")
        copy = ScenarioModel.copy_business(original)
        assert copy.id_file != original.id_file

    def test_copy_has_copie_de_prefix(self) -> None:
        original = _make_scenario(scenario_name="Mon scénario")
        copy = ScenarioModel.copy_business(original)
        assert copy.scenario_name.startswith("Copie de ")
        assert "Mon scénario" in copy.scenario_name

    def test_copy_preserves_desc(self) -> None:
        original = _make_scenario(scenario_desc="My desc")
        copy = ScenarioModel.copy_business(original)
        assert copy.scenario_desc == "My desc"

    def test_copy_is_independent(self) -> None:
        original = _make_scenario()
        copy = ScenarioModel.copy_business(original)
        copy.scenario_name = "Changed"
        assert original.scenario_name != "Changed"


class TestExportToDataJson:
    def test_returns_dict(self) -> None:
        scenario = _make_scenario()
        result = scenario.export_to_data_json()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        scenario = _make_scenario()
        result = scenario.export_to_data_json()
        for key in ("id_file", "scenario_name", "scenario_desc", "version", "steps"):
            assert key in result

    def test_id_preserved(self) -> None:
        scenario = _make_scenario(id_file="test_id_42")
        assert scenario.export_to_data_json()["id_file"] == "test_id_42"

    def test_steps_is_list(self) -> None:
        scenario = _make_scenario(steps=[])
        assert scenario.export_to_data_json()["steps"] == []


class TestImportFromDataJson:
    def test_round_trip(self) -> None:
        original = _make_scenario()
        data = original.export_to_data_json()
        reconstructed = ScenarioModel.import_from_data_json(data)
        assert reconstructed.id_file == original.id_file
        assert reconstructed.scenario_name == original.scenario_name
        assert reconstructed.version == original.version

    def test_missing_steps_defaults_to_empty(self) -> None:
        data = {
            "id_file": "abc",
            "scenario_name": "Test",
            "scenario_desc": "",
            "version": "1.0.0",
        }
        result = ScenarioModel.import_from_data_json(data)
        assert result.steps == []

    def test_non_list_steps_ignored(self) -> None:
        data = {
            "id_file": "abc",
            "scenario_name": "Test",
            "scenario_desc": "",
            "version": "1.0.0",
            "steps": "not-a-list",
        }
        result = ScenarioModel.import_from_data_json(data)
        assert result.steps == []

    def test_invalid_step_dicts_skipped(self) -> None:
        data = {
            "id_file": "abc",
            "scenario_name": "Test",
            "scenario_desc": "",
            "version": "1.0.0",
            "steps": ["not-a-dict", 42, None],
        }
        result = ScenarioModel.import_from_data_json(data)
        assert result.steps == []
