"""Regression tests — models/scenario_model.py.

Freezes the observable contract of ScenarioModel:
  - is_valid_id() edge cases (empty, whitespace, alphanumeric, non-alphanumeric)
  - get_default_data() field defaults
  - copy_business() name prefix 'Copie de', new ID, deep-copied steps
  - mark_as_created() / mark_as_modified() timestamp semantics
  - export/import round-trip preserves fields and steps
  - _deserialize_steps() skips invalid entries gracefully
"""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum


# ---------------------------------------------------------------------------
# is_valid_id — edge case contract
# ---------------------------------------------------------------------------


class TestIsValidId:
    @pytest.mark.parametrize(
        "value, expected",
        [
            ("", False),
            ("   ", False),
            ("\t", False),
            ("abc123", True),
            ("ABC", True),
            ("123", True),
            ("abc!def", False),
            ("abc def", False),
            ("abc-def", False),
            ("abc_def", False),
        ],
        ids=[
            "empty",
            "whitespace",
            "tab",
            "lowercase_alphanumeric",
            "uppercase",
            "digits_only",
            "exclamation",
            "space",
            "hyphen",
            "underscore",
        ],
    )
    def test_is_valid_id(self, value: str, expected: bool) -> None:
        assert ScenarioModel.is_valid_id(value) is expected, (
            f"is_valid_id({value!r}) must return {expected}"
        )

    def test_is_valid_id_strips_whitespace(self) -> None:
        assert ScenarioModel.is_valid_id("  abc123  ") is True, (
            "is_valid_id must strip leading/trailing whitespace before checking"
        )


# ---------------------------------------------------------------------------
# get_default_data — field contract
# ---------------------------------------------------------------------------


class TestGetDefaultData:
    def test_returns_scenario_model(self) -> None:
        s = ScenarioModel.get_default_data()
        assert isinstance(s, ScenarioModel)

    def test_default_name(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.scenario_name == "Nouv. scénario", "Default scenario name must be 'Nouv. scénario'"

    def test_default_desc(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.scenario_desc == "Description du scénario (ou URL)"

    def test_id_file_is_alphanumeric(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.id_file, "id_file must not be empty"
        assert s.id_file.isalnum(), f"id_file must be alphanumeric, got {s.id_file!r}"

    def test_timestamps_are_equal_on_creation(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.created_date_scenario is not None
        assert s.modified_date_scenario is not None
        assert s.created_date_scenario == s.modified_date_scenario, (
            "get_default_data must set created and modified to the same timestamp"
        )

    def test_steps_empty(self) -> None:
        s = ScenarioModel.get_default_data()
        assert s.steps == [], "get_default_data must produce an empty steps list"


# ---------------------------------------------------------------------------
# copy_business — name prefix, ID, independence
# ---------------------------------------------------------------------------


class TestCopyBusiness:
    def _make_scenario(self, name: str = "Mon scénario") -> ScenarioModel:
        s = ScenarioModel.get_default_data()
        s.scenario_name = name
        return s

    def test_copy_prefixes_name_with_copie_de(self) -> None:
        s = self._make_scenario("Alpha")
        copy = ScenarioModel.copy_business(s)
        assert copy.scenario_name == "Copie de Alpha", (
            "copy_business must prefix name with 'Copie de '"
        )

    def test_copy_has_different_id(self) -> None:
        s = self._make_scenario()
        copy = ScenarioModel.copy_business(s)
        assert copy.id_file != s.id_file, "copy_business must assign a new unique id_file"

    def test_copy_id_is_valid(self) -> None:
        s = self._make_scenario()
        copy = ScenarioModel.copy_business(s)
        assert ScenarioModel.is_valid_id(copy.id_file), "The copy's id_file must be valid"

    def test_copy_steps_are_independent(self) -> None:
        s = self._make_scenario()
        # Build a minimal mock step that can be deepcopied
        mock_step = MagicMock(spec=StepScrapingModel)
        mock_step.step_id = "abc1"
        mock_step.step_type = StepTypeEnum.E_SECTION_STEPS
        s.steps = [mock_step]

        copy = ScenarioModel.copy_business(s)
        copy.steps.append(MagicMock())
        assert len(s.steps) == 1, "Mutating copy's steps must not affect original"

    def test_copy_preserves_desc(self) -> None:
        s = self._make_scenario()
        s.scenario_desc = "My description"
        copy = ScenarioModel.copy_business(s)
        assert copy.scenario_desc == "My description"


# ---------------------------------------------------------------------------
# mark_as_created / mark_as_modified — timestamp semantics
# ---------------------------------------------------------------------------


class TestTimestamps:
    def test_mark_as_created_sets_both_timestamps_equal(self) -> None:
        s = ScenarioModel.get_default_data()
        s.mark_as_created()
        assert s.created_date_scenario is not None
        assert s.modified_date_scenario is not None
        assert s.created_date_scenario == s.modified_date_scenario, (
            "mark_as_created must set both timestamps to the same value"
        )

    def test_mark_as_modified_updates_modified_only(self) -> None:
        s = ScenarioModel.get_default_data()
        original_created = s.created_date_scenario
        s.mark_as_modified()
        assert s.created_date_scenario == original_created, (
            "mark_as_modified must NOT change created_date_scenario"
        )
        assert s.modified_date_scenario is not None


# ---------------------------------------------------------------------------
# export/import round-trip
# ---------------------------------------------------------------------------


class TestRoundTrip:
    def test_round_trip_basic_fields(self) -> None:
        s = ScenarioModel.get_default_data()
        s.scenario_name = "Test Scénario"
        s.scenario_desc = "Description test"

        data = s.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(data)

        assert restored.id_file == s.id_file
        assert restored.scenario_name == "Test Scénario"
        assert restored.scenario_desc == "Description test"

    def test_round_trip_timestamps_preserved(self) -> None:
        s = ScenarioModel.get_default_data()
        data = s.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(data)
        assert restored.created_date_scenario is not None
        assert restored.modified_date_scenario is not None

    def test_round_trip_empty_steps(self) -> None:
        s = ScenarioModel.get_default_data()
        s.steps = []
        data = s.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(data)
        assert restored.steps == []

    def test_import_from_empty_dict_does_not_raise(self) -> None:
        restored = ScenarioModel.import_from_data_json({})
        assert isinstance(restored, ScenarioModel)
        assert restored.steps == []

    def test_import_handles_missing_optional_fields(self) -> None:
        data = {"id_file": "abc123", "scenario_name": "Test"}
        restored = ScenarioModel.import_from_data_json(data)
        assert restored.id_file == "abc123"
        assert restored.scenario_name == "Test"
        assert restored.created_date_scenario is None
        assert restored.steps == []


# ---------------------------------------------------------------------------
# _deserialize_steps — robust to malformed input
# ---------------------------------------------------------------------------


class TestDeserializeSteps:
    def test_non_list_returns_empty(self) -> None:
        result = ScenarioModel._deserialize_steps("not a list")
        assert result == []

    def test_none_returns_empty(self) -> None:
        result = ScenarioModel._deserialize_steps(None)
        assert result == []

    def test_list_with_non_dict_entries_skipped(self) -> None:
        result = ScenarioModel._deserialize_steps([None, 42, "string", True])
        assert result == []

    def test_empty_list_returns_empty(self) -> None:
        result = ScenarioModel._deserialize_steps([])
        assert result == []
