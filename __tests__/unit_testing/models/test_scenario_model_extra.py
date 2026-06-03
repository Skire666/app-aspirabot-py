"""Extra coverage for models/scenario_model.py lines 186-189 (_deserialize_steps ValueError)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from models.scenario_model import ScenarioModel


class TestDeserializeStepsWithInvalidJson:
    def test_step_with_invalid_step_type_is_skipped(self) -> None:
        """Lines 186-189: ValueError during import_from_data_json is caught."""
        data = {
            "id_file": "abc",
            "scenario_name": "Test",
            "scenario_desc": "",
            "version": "1.0.0",
            "steps": [{"step_type": "TOTALLY_INVALID_TYPE", "step_id": "x", "params": {}}],
        }
        result = ScenarioModel.import_from_data_json(data)
        assert result.steps == []

    def test_valid_and_invalid_steps_mixed(self) -> None:
        """Only valid steps survive deserialization."""
        data = {
            "id_file": "abc",
            "scenario_name": "Test",
            "scenario_desc": "",
            "version": "1.0.0",
            "steps": [
                "not-a-dict",
                {"step_type": "TOTALLY_INVALID", "step_id": "bad"},
                42,
            ],
        }
        result = ScenarioModel.import_from_data_json(data)
        assert result.steps == []
