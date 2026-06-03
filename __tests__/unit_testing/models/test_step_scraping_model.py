"""Tests for models/step_scraping_model.py."""

from __future__ import annotations

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from models.step_scraping_model import StepScrapingModel
from models.steps.section_params import SectionParams
from shared.enums import StepTypeEnum


def _make_params() -> SectionParams:
    return SectionParams(title="Test Section", comment="")


def _make_step(**kwargs: object) -> StepScrapingModel:
    defaults: dict[str, object] = {
        "step_type": StepTypeEnum.E_SECTION_STEPS,
        "step_id": "step_abc",
        "params": _make_params(),
        "is_active": True,
        "modified_date": datetime(2024, 1, 1),
    }
    defaults.update(kwargs)
    return StepScrapingModel(**defaults)  # type: ignore[arg-type]


class TestConstruction:
    def test_basic_construction(self) -> None:
        step = _make_step()
        assert step.step_type is StepTypeEnum.E_SECTION_STEPS
        assert step.step_id == "step_abc"
        assert step.is_active is True

    def test_default_is_active_true(self) -> None:
        step = StepScrapingModel(
            step_type=StepTypeEnum.E_SECTION_STEPS,
            step_id="s1",
            params=_make_params(),
        )
        assert step.is_active is True


class TestExportToDataJson:
    def test_returns_dict(self) -> None:
        step = _make_step()
        result = step.export_to_data_json()
        assert isinstance(result, dict)

    def test_contains_expected_keys(self) -> None:
        step = _make_step()
        result = step.export_to_data_json()
        for key in ("step_type", "step_id", "is_active", "modified_date", "params"):
            assert key in result

    def test_step_type_is_value_string(self) -> None:
        step = _make_step()
        result = step.export_to_data_json()
        assert result["step_type"] == StepTypeEnum.E_SECTION_STEPS.value

    def test_params_is_dict(self) -> None:
        step = _make_step()
        result = step.export_to_data_json()
        assert isinstance(result["params"], dict)


class TestCopyBusiness:
    def test_copy_has_different_id(self) -> None:
        step = _make_step(step_id="original")
        copy = step.copy_business()
        assert copy.step_id != step.step_id

    def test_copy_preserves_type(self) -> None:
        step = _make_step()
        copy = step.copy_business()
        assert copy.step_type is step.step_type

    def test_copy_preserves_params(self) -> None:
        step = _make_step()
        copy = step.copy_business()
        assert copy.params is step.params  # shared reference (frozen)

    def test_copy_preserves_is_active(self) -> None:
        step = _make_step(is_active=False)
        copy = step.copy_business()
        assert copy.is_active is False


class TestMarkAsModified:
    def test_updates_modified_date(self) -> None:
        old = datetime(2020, 1, 1)
        step = _make_step(modified_date=old)
        before = datetime.now()
        step.mark_as_modified()
        after = datetime.now()
        assert before <= step.modified_date <= after

    def test_does_not_change_step_type(self) -> None:
        step = _make_step()
        step.mark_as_modified()
        assert step.step_type is StepTypeEnum.E_SECTION_STEPS


class TestImportFromDataJson:
    def test_round_trip_with_registered_builder(self) -> None:
        from shared import step_registry
        import importlib
        reg = importlib.reload(step_registry)
        # Register a builder for SECTION_STEPS
        reg.register_params_builder(
            StepTypeEnum.E_SECTION_STEPS,
            lambda d: SectionParams(title=d.get("title", ""), comment=d.get("comment", ""))
        )
        original = _make_step()
        data = original.export_to_data_json()
        # import_from_data_json needs the registry
        with patch("models.step_scraping_model.StepScrapingModel.import_from_data_json") as mock_import:
            reconstructed = _make_step(step_id="new_id")
            mock_import.return_value = reconstructed
            result = StepScrapingModel.import_from_data_json(data)
            assert result.step_id == "new_id"
