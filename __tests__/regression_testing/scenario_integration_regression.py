"""Regression tests — ScenarioModel / StepScrapingModel integration.

Freezes the multi-module integration behaviour that unit tests do not cover:
- Full scenario round-trip (export → import) with real embedded step params.
- StepsContext built from real step lists.
- JumpToStepParams cross-step validation with a live StepsContext.
- ScenarioModel.copy_business() contract.
- StepScrapingModel.copy_business() contract.

Bootstrap: importing `presenters.steps` registers all params builders in the
step registry so StepScrapingModel.import_from_data_json() works end-to-end.
"""

from __future__ import annotations

import pytest

import presenters.steps  # noqa: F401 — registers all params builders

from datetime import datetime

from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from models.steps.jump_to_step_params import JumpToStepParams
from models.steps.scroll_down_params import ScrollDownParams
from models.steps.section_params import SectionParams
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from models.steps_collections_model import StepsCollections as StepsContext
from shared.enums import StepTypeEnum
from pydantic import ValidationError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_step(step_type: StepTypeEnum, params_obj, step_id: str = "id01") -> StepScrapingModel:
    return StepScrapingModel(
        step_type=step_type,
        step_id=step_id,
        params=params_obj,
        is_active=True,
        modified_date=datetime(2024, 6, 1, 12, 0, 0),
    )


def _make_scenario_with_steps(steps: list[StepScrapingModel]) -> ScenarioModel:
    s = ScenarioModel.get_default_data()
    s.steps = steps
    return s


# ---------------------------------------------------------------------------
# StepScrapingModel serialisation round-trip
# ---------------------------------------------------------------------------


class TestStepScrapingModelRoundTrip:
    def test_section_step_round_trip(self) -> None:
        original = _make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="Intro", comment=""), step_id="aaa1")
        exported = original.export_to_data_json()
        restored = StepScrapingModel.import_from_data_json(exported)

        assert restored.step_type is StepTypeEnum.E_SECTION_STEPS, "step_type must survive round-trip"
        assert restored.step_id == "aaa1", "step_id must survive round-trip"
        assert restored.params.to_dict()["title"] == "Intro", "params content must survive round-trip"

    def test_scroll_down_step_round_trip(self) -> None:
        original = _make_step(StepTypeEnum.E_SCROLL_DOWN, ScrollDownParams(pixels=500, comment=""), step_id="bb22")
        exported = original.export_to_data_json()
        restored = StepScrapingModel.import_from_data_json(exported)

        assert restored.step_type is StepTypeEnum.E_SCROLL_DOWN
        assert restored.params.to_dict()["pixels"] == 500

    def test_wait_fixed_time_step_round_trip(self) -> None:
        original = _make_step(StepTypeEnum.E_WAIT_FIXED_TIME, WaitFixedTimeParams(duration=3, unit="s", comment=""), step_id="cc33")
        exported = original.export_to_data_json()
        restored = StepScrapingModel.import_from_data_json(exported)

        assert restored.step_type is StepTypeEnum.E_WAIT_FIXED_TIME
        assert restored.params.to_dict()["duration"] == 3
        assert restored.params.to_dict()["unit"] == "s"

    def test_is_active_false_preserved(self) -> None:
        step = StepScrapingModel(
            step_type=StepTypeEnum.E_SECTION_STEPS,
            step_id="d001",
            params=SectionParams(title="Disabled", comment=""),
            is_active=False,
            modified_date=datetime(2024, 1, 1),
        )
        exported = step.export_to_data_json()
        restored = StepScrapingModel.import_from_data_json(exported)

        assert restored.is_active is False, "is_active=False must survive round-trip"

    def test_export_contains_expected_keys(self) -> None:
        step = _make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="X", comment=""), step_id="e001")
        d = step.export_to_data_json()
        assert set(d.keys()) == {"step_type", "step_id", "is_active", "modified_date", "params"}


# ---------------------------------------------------------------------------
# ScenarioModel serialisation round-trip with real steps
# ---------------------------------------------------------------------------


class TestScenarioModelRoundTrip:
    def _build_scenario(self) -> ScenarioModel:
        steps = [
            _make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="Phase 1", comment=""), step_id="s001"),
            _make_step(StepTypeEnum.E_SCROLL_DOWN, ScrollDownParams(pixels=300, comment=""), step_id="s002"),
            _make_step(StepTypeEnum.E_WAIT_FIXED_TIME, WaitFixedTimeParams(duration=2, unit="s", comment=""), step_id="s003"),
        ]
        return _make_scenario_with_steps(steps)

    def test_step_count_preserved(self) -> None:
        scenario = self._build_scenario()
        exported = scenario.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(exported)

        assert len(restored.steps) == 3, "All steps must survive scenario serialisation"

    def test_step_types_preserved(self) -> None:
        scenario = self._build_scenario()
        exported = scenario.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(exported)

        assert restored.steps[0].step_type is StepTypeEnum.E_SECTION_STEPS
        assert restored.steps[1].step_type is StepTypeEnum.E_SCROLL_DOWN
        assert restored.steps[2].step_type is StepTypeEnum.E_WAIT_FIXED_TIME

    def test_step_ids_preserved(self) -> None:
        scenario = self._build_scenario()
        exported = scenario.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(exported)

        assert restored.steps[0].step_id == "s001"
        assert restored.steps[1].step_id == "s002"

    def test_step_params_content_preserved(self) -> None:
        scenario = self._build_scenario()
        exported = scenario.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(exported)

        assert restored.steps[0].params.to_dict()["title"] == "Phase 1"
        assert restored.steps[1].params.to_dict()["pixels"] == 300

    def test_scenario_metadata_preserved(self) -> None:
        scenario = self._build_scenario()
        scenario.scenario_name = "My Test Scenario"
        scenario.scenario_desc = "Description here"
        exported = scenario.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(exported)

        assert restored.scenario_name == "My Test Scenario"
        assert restored.scenario_desc == "Description here"

    def test_empty_steps_round_trip(self) -> None:
        scenario = ScenarioModel.get_default_data()
        exported = scenario.export_to_data_json()
        restored = ScenarioModel.import_from_data_json(exported)

        assert restored.steps == [], "Empty step list must survive round-trip"

    def test_invalid_step_in_json_is_skipped(self) -> None:
        scenario = ScenarioModel.get_default_data()
        exported = scenario.export_to_data_json()
        # Inject a malformed step (unknown step_type)
        exported["steps"] = [
            {"step_type": "TOTALLY_UNKNOWN", "step_id": "bad1", "is_active": True, "params": {}},
            {"step_type": StepTypeEnum.E_SECTION_STEPS.value, "step_id": "good1", "is_active": True, "params": {"title": "OK", "comment": ""}},
        ]
        restored = ScenarioModel.import_from_data_json(exported)
        # The invalid step is silently skipped; only the valid one is kept
        assert len(restored.steps) == 1, "Invalid step entries must be silently skipped during import"
        assert restored.steps[0].step_id == "good1"


# ---------------------------------------------------------------------------
# ScenarioModel.copy_business() contract
# ---------------------------------------------------------------------------


class TestScenarioModelCopyBusiness:
    def test_new_id_generated(self) -> None:
        source = ScenarioModel.get_default_data()
        copy = ScenarioModel.copy_business(source)

        assert copy.id_file != source.id_file, "copy_business must produce a fresh ID"

    def test_name_prefixed(self) -> None:
        source = ScenarioModel.get_default_data()
        source.scenario_name = "My Workflow"
        copy = ScenarioModel.copy_business(source)

        assert copy.scenario_name == "Copie de My Workflow", "copy_business must prefix name with 'Copie de '"

    def test_steps_deep_copied(self) -> None:
        steps = [_make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="X", comment=""), step_id="orig1")]
        source = _make_scenario_with_steps(steps)
        copy = ScenarioModel.copy_business(source)

        assert len(copy.steps) == 1, "Copied scenario must have the same step count"
        # Deep copy: mutating the copy must not affect the source
        copy.steps.append(_make_step(StepTypeEnum.E_SCROLL_DOWN, ScrollDownParams(pixels=100, comment=""), step_id="new1"))
        assert len(source.steps) == 1, "Deep copy: modifying the copy must not affect the source"


# ---------------------------------------------------------------------------
# StepScrapingModel.copy_business() contract
# ---------------------------------------------------------------------------


class TestStepScrapingModelCopyBusiness:
    def test_new_id_generated(self) -> None:
        original = _make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="T", comment=""), step_id="orig-id")
        copy = original.copy_business()

        assert copy.step_id != "orig-id", "copy_business must give the copy a new step_id"

    def test_step_type_preserved(self) -> None:
        original = _make_step(StepTypeEnum.E_SCROLL_DOWN, ScrollDownParams(pixels=1000, comment=""), step_id="s1")
        copy = original.copy_business()

        assert copy.step_type is StepTypeEnum.E_SCROLL_DOWN

    def test_params_shared(self) -> None:
        params = SectionParams(title="Same", comment="")
        original = _make_step(StepTypeEnum.E_SECTION_STEPS, params, step_id="s1")
        copy = original.copy_business()

        # Params are the same object (frozen immutable, sharing is safe)
        assert copy.params is original.params, "copy_business should share the frozen params instance"


# ---------------------------------------------------------------------------
# StepsContext integration
# ---------------------------------------------------------------------------


class TestStepsContextIntegration:
    def _build_context(self) -> tuple[StepsContext, list[StepScrapingModel]]:
        steps = [
            _make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="T", comment=""), step_id="id_a"),
            _make_step(StepTypeEnum.E_SCROLL_DOWN, ScrollDownParams(pixels=100, comment=""), step_id="id_b"),
            _make_step(StepTypeEnum.E_WAIT_FIXED_TIME, WaitFixedTimeParams(duration=1, unit="s", comment=""), step_id="id_c"),
        ]
        return StepsContext.from_list(steps), steps

    def test_from_list_preserves_count(self) -> None:
        ctx, steps = self._build_context()
        assert len(ctx.steps) == 3

    def test_find_by_id_returns_correct_step(self) -> None:
        ctx, _ = self._build_context()
        found = ctx.find_by_id("id_b")
        assert found is not None
        assert found.step_type is StepTypeEnum.E_SCROLL_DOWN

    def test_find_by_id_returns_none_for_unknown(self) -> None:
        ctx, _ = self._build_context()
        assert ctx.find_by_id("nonexistent") is None

    def test_find_index_by_id_returns_correct_index(self) -> None:
        ctx, _ = self._build_context()
        assert ctx.find_index_by_id("id_a") == 0
        assert ctx.find_index_by_id("id_b") == 1
        assert ctx.find_index_by_id("id_c") == 2

    def test_find_index_by_id_returns_none_for_unknown(self) -> None:
        ctx, _ = self._build_context()
        assert ctx.find_index_by_id("ghost") is None


# ---------------------------------------------------------------------------
# JumpToStepParams cross-step validation with real StepsContext
# ---------------------------------------------------------------------------


class TestJumpToStepCrossStepValidation:
    """Integration: JumpToStepParams validators that query StepsContext."""

    def _make_steps_with_ids(self, step_id_a: str, step_id_jump: str) -> list[StepScrapingModel]:
        return [
            _make_step(StepTypeEnum.E_SECTION_STEPS, SectionParams(title="S", comment=""), step_id=step_id_a),
            _make_step(StepTypeEnum.E_SCROLL_DOWN, ScrollDownParams(pixels=100, comment=""), step_id=step_id_jump),
        ]

    def test_valid_target_passes(self) -> None:
        steps = self._make_steps_with_ids("aaa1", "bbb2")
        ctx_dict = {
            "step_index": 2,
            "step_id": "ccc3",
            "steps_context": StepsContext.from_list(steps),
        }
        params = JumpToStepParams.model_validate(
            {"condition": "always", "target_hexastring": "aaa1", "comment": ""},
            context=ctx_dict,
        )
        assert params.target_hexastring == "aaa1"

    def test_self_reference_raises(self) -> None:
        steps = self._make_steps_with_ids("aaa1", "bbb2")
        ctx_dict = {
            "step_index": 0,
            "step_id": "aaa1",
            "steps_context": StepsContext.from_list(steps),
        }
        with pytest.raises(ValidationError, match="elle-même|self"):
            JumpToStepParams.model_validate(
                {"condition": "always", "target_hexastring": "aaa1", "comment": ""},
                context=ctx_dict,
            )

    def test_target_not_in_context_raises(self) -> None:
        steps = self._make_steps_with_ids("aaa1", "bbb2")
        ctx_dict = {
            "step_index": 1,
            "step_id": "bbb2",
            "steps_context": StepsContext.from_list(steps),
        }
        with pytest.raises(ValidationError):
            JumpToStepParams.model_validate(
                {"condition": "success", "target_hexastring": "ghost99", "comment": ""},
                context=ctx_dict,
            )

    def test_no_context_accepts_self_reference(self) -> None:
        # Without context, no validator fires — construction must succeed
        params = JumpToStepParams(condition="always", target_hexastring="self_id", comment="")
        assert params.target_hexastring == "self_id", (
            "Without context, self-reference is accepted (safe deserialisation contract)"
        )
