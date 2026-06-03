"""Extra coverage for models/step_scraping_model.py — import_from_data_json lines 61-66."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import patch

import pytest

from models.step_scraping_model import StepScrapingModel
from models.steps.section_params import SectionParams
from shared.enums import StepTypeEnum


class TestImportFromDataJson:
    def test_import_with_registered_builder(self) -> None:
        """Lines 61-66: import_from_data_json full path with mocked build_params."""
        params = SectionParams(title="Imported", comment="")

        # build_params is a local import inside the method — patch the registry function
        with patch("shared.step_registry.build_params", return_value=params) as mock_build:
            data = {
                "step_type": StepTypeEnum.E_SECTION_STEPS.value,
                "step_id": "abc1",
                "is_active": True,
                "modified_date": "2024-01-15 10:00:00",
                "params": {"title": "Imported", "comment": ""},
            }
            step = StepScrapingModel.import_from_data_json(data)

        assert step.step_type is StepTypeEnum.E_SECTION_STEPS
        assert step.step_id == "abc1"
        assert step.is_active is True
        assert step.params is params
        mock_build.assert_called_once()

    def test_import_invalid_step_type_raises(self) -> None:
        """Unknown step_type value causes ValueError."""
        data = {
            "step_type": "TOTALLY_UNKNOWN",
            "step_id": "x",
            "is_active": True,
            "params": {},
        }
        with pytest.raises(ValueError):
            StepScrapingModel.import_from_data_json(data)

    def test_import_missing_modified_date_uses_now(self) -> None:
        """When modified_date is absent, datetime.now() is used."""
        params = SectionParams(title="X", comment="")
        before = datetime.now()

        with patch("shared.step_registry.build_params", return_value=params):
            data = {
                "step_type": StepTypeEnum.E_SECTION_STEPS.value,
                "step_id": "s1",
                "is_active": False,
                "params": {},
            }
            step = StepScrapingModel.import_from_data_json(data)

        after = datetime.now()
        assert before <= step.modified_date <= after

    def test_export_then_import_round_trip(self) -> None:
        """export_to_data_json → import_from_data_json round-trip via mock."""
        params = SectionParams(title="Round Trip", comment="note")
        original = StepScrapingModel(
            step_type=StepTypeEnum.E_SECTION_STEPS,
            step_id="rt42",
            params=params,
            is_active=True,
            modified_date=datetime(2024, 6, 1),
        )
        exported = original.export_to_data_json()

        with patch("shared.step_registry.build_params", return_value=params):
            reconstructed = StepScrapingModel.import_from_data_json(exported)

        assert reconstructed.step_id == "rt42"
        assert reconstructed.step_type is StepTypeEnum.E_SECTION_STEPS
