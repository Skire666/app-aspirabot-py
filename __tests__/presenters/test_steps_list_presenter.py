"""Tests for presenters/steps_list_presenter.py."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from unittest.mock import MagicMock, call

import pytest

from models.scenario_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from models.steps.section_params import SectionParams
from models.steps.scroll_down_params import ScrollDownParams
from presenters.steps_list_presenter import StepsListPresenter
from shared.enums import StepTypeEnum
from shared.step_view_item import StepViewItem


# ---------------------------------------------------------------------------
# Helpers / Fixtures
# ---------------------------------------------------------------------------


def _make_step(
    step_type: StepTypeEnum = StepTypeEnum.E_SECTION_STEPS,
    step_id: str = "step-001",
    is_active: bool = True,
) -> StepScrapingModel:
    params = SectionParams(title="T", comment="") if step_type == StepTypeEnum.E_SECTION_STEPS else ScrollDownParams(enabled=True)
    return StepScrapingModel(
        step_type=step_type,
        step_id=step_id,
        params=params,
        is_active=is_active,
        modified_date=datetime(2024, 1, 1),
    )


@pytest.fixture()
def presenter() -> StepsListPresenter:
    view = MagicMock()
    gestion_view = MagicMock()
    svc_scenario = MagicMock()
    workflow_service = MagicMock()
    workflow_service.validate_step.return_value = []

    p = StepsListPresenter(
        view=view,
        service_scenario=svc_scenario,
        workflow_service=workflow_service,
        gestion_view=gestion_view,
    )
    p.init_new("scenario-test")
    return p


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------


class TestLoad:
    def test_load_reads_scenario_from_service(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        scenario = ScenarioModel.get_default_data()
        scenario.steps = [step]
        presenter._service_scenario.read_scenario.return_value = scenario

        presenter.load("scenario-abc")

        presenter._service_scenario.read_scenario.assert_called_once_with("scenario-abc")
        assert presenter._scenario_id_file == "scenario-abc"

    def test_load_populates_steps(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        scenario = ScenarioModel.get_default_data()
        scenario.steps = [step]
        presenter._service_scenario.read_scenario.return_value = scenario

        presenter.load("sc001")
        assert len(presenter._steps) == 1

    def test_load_sets_is_new_scenario_false(self, presenter: StepsListPresenter) -> None:
        scenario = ScenarioModel.get_default_data()
        presenter._service_scenario.read_scenario.return_value = scenario
        presenter.load("sc001")
        assert presenter._is_new_scenario is False

    def test_load_calls_set_validation_status(self, presenter: StepsListPresenter) -> None:
        scenario = ScenarioModel.get_default_data()
        presenter._service_scenario.read_scenario.return_value = scenario
        presenter.load("sc001")
        presenter._view.set_validation_status.assert_called()


# ---------------------------------------------------------------------------
# init_new
# ---------------------------------------------------------------------------


class TestInitNew:
    def test_init_new_clears_steps(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter.init_new("new-scenario")
        assert presenter._steps == []

    def test_init_new_sets_is_new_scenario_true(self, presenter: StepsListPresenter) -> None:
        presenter.init_new("new-scenario")
        assert presenter._is_new_scenario is True


# ---------------------------------------------------------------------------
# get_steps
# ---------------------------------------------------------------------------


class TestGetSteps:
    def test_returns_copy_of_steps(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        presenter._steps = [step]
        result = presenter.get_steps()
        assert result == [step]
        assert result is not presenter._steps


# ---------------------------------------------------------------------------
# validate_steps
# ---------------------------------------------------------------------------


class TestValidateSteps:
    def test_returns_empty_list_when_all_valid(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._workflow_service.validate_step.return_value = []
        errors = presenter.validate_steps()
        assert errors == []

    def test_returns_errors_from_service(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._workflow_service.validate_step.return_value = ["Field required"]
        errors = presenter.validate_steps()
        assert "Field required" in errors

    def test_calls_validate_for_each_step(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(step_id="s1"), _make_step(step_id="s2")]
        presenter._workflow_service.validate_step.return_value = []
        presenter.validate_steps()
        assert presenter._workflow_service.validate_step.call_count == 2


# ---------------------------------------------------------------------------
# clear_steps
# ---------------------------------------------------------------------------


class TestClearSteps:
    def test_clears_steps_list(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter.clear_steps()
        assert presenter._steps == []

    def test_resets_edit_index(self, presenter: StepsListPresenter) -> None:
        presenter._edit_index = 2
        presenter.clear_steps()
        assert presenter._edit_index is None

    def test_calls_render_steps(self, presenter: StepsListPresenter) -> None:
        presenter.clear_steps()
        presenter._view.render_steps.assert_called()


# ---------------------------------------------------------------------------
# _on_edit_step
# ---------------------------------------------------------------------------


class TestOnEditStep:
    def test_shows_inline_form_for_valid_index(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._on_edit_step(0)
        presenter._gestion_view.show_inline_form.assert_called_once()

    def test_ignores_negative_index(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._on_edit_step(-1)
        presenter._gestion_view.show_inline_form.assert_not_called()

    def test_ignores_out_of_bounds_index(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._on_edit_step(5)
        presenter._gestion_view.show_inline_form.assert_not_called()

    def test_sets_edit_index(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(), _make_step(step_id="s2")]
        presenter._on_edit_step(1)
        assert presenter._edit_index == 1


# ---------------------------------------------------------------------------
# _on_confirm_create_step
# ---------------------------------------------------------------------------


class TestOnConfirmCreateStep:
    def test_appends_step_on_success(self, presenter: StepsListPresenter) -> None:
        presenter._workflow_service.validate_step.return_value = []
        result = presenter._on_confirm_create_step(StepTypeEnum.E_SECTION_STEPS, {"title": "X", "comment": ""})
        assert result is True
        assert len(presenter._steps) == 1

    def test_returns_false_when_validation_fails(self, presenter: StepsListPresenter) -> None:
        presenter._workflow_service.validate_step.return_value = ["Error"]
        result = presenter._on_confirm_create_step(StepTypeEnum.E_SECTION_STEPS, {"title": "", "comment": ""})
        assert result is False
        assert len(presenter._steps) == 0

    def test_shows_form_errors_when_validation_fails(self, presenter: StepsListPresenter) -> None:
        presenter._workflow_service.validate_step.return_value = ["Required field"]
        presenter._on_confirm_create_step(StepTypeEnum.E_SECTION_STEPS, {"title": "", "comment": ""})
        presenter._gestion_view.show_inline_form_errors.assert_called_once()

    def test_resets_edit_index_on_success(self, presenter: StepsListPresenter) -> None:
        presenter._edit_index = 3
        presenter._workflow_service.validate_step.return_value = []
        presenter._on_confirm_create_step(StepTypeEnum.E_SECTION_STEPS, {"title": "T", "comment": ""})
        assert presenter._edit_index is None


# ---------------------------------------------------------------------------
# _on_confirm_update_step
# ---------------------------------------------------------------------------


class TestOnConfirmUpdateStep:
    def test_returns_true_when_edit_index_is_none(self, presenter: StepsListPresenter) -> None:
        presenter._edit_index = None
        result = presenter._on_confirm_update_step(StepTypeEnum.E_SECTION_STEPS, {"title": "X", "comment": ""})
        assert result is True

    def test_shows_warning_when_edit_index_is_none(self, presenter: StepsListPresenter) -> None:
        presenter._edit_index = None
        presenter._on_confirm_update_step(StepTypeEnum.E_SECTION_STEPS, {"title": "X", "comment": ""})
        presenter._gestion_view.show_warning.assert_called_once()

    def test_updates_step_on_success(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        presenter._steps = [step]
        presenter._edit_index = 0
        presenter._workflow_service.validate_step.return_value = []
        result = presenter._on_confirm_update_step(StepTypeEnum.E_SECTION_STEPS, {"title": "New", "comment": ""})
        assert result is True
        assert presenter._steps[0].params.title == "New"  # type: ignore[union-attr]

    def test_returns_false_when_validation_fails(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        presenter._steps = [step]
        presenter._edit_index = 0
        presenter._workflow_service.validate_step.return_value = ["Error"]
        result = presenter._on_confirm_update_step(StepTypeEnum.E_SECTION_STEPS, {"title": "", "comment": ""})
        assert result is False

    def test_shows_form_errors_when_validation_fails(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        presenter._steps = [step]
        presenter._edit_index = 0
        presenter._workflow_service.validate_step.return_value = ["Bad field"]
        presenter._on_confirm_update_step(StepTypeEnum.E_SECTION_STEPS, {})
        presenter._gestion_view.show_inline_form_errors.assert_called_once()

    def test_edit_index_out_of_bounds_returns_true(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._edit_index = 99
        result = presenter._on_confirm_update_step(StepTypeEnum.E_SECTION_STEPS, {})
        assert result is True


# ---------------------------------------------------------------------------
# find_step_index_by_id
# ---------------------------------------------------------------------------


class TestFindStepIndexById:
    def test_returns_index_when_found(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(step_id="s1"), _make_step(step_id="s2")]
        assert presenter.find_step_index_by_id("s2") == 1

    def test_returns_none_when_not_found(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(step_id="s1")]
        assert presenter.find_step_index_by_id("missing") is None

    def test_returns_zero_for_first_step(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(step_id="first")]
        assert presenter.find_step_index_by_id("first") == 0


# ---------------------------------------------------------------------------
# _on_cancel_inline_step
# ---------------------------------------------------------------------------


class TestOnCancelInlineStep:
    def test_resets_edit_index(self, presenter: StepsListPresenter) -> None:
        presenter._edit_index = 2
        presenter._on_cancel_inline_step()
        assert presenter._edit_index is None

    def test_calls_clear_selection(self, presenter: StepsListPresenter) -> None:
        presenter._on_cancel_inline_step()
        presenter._view.clear_selection.assert_called_once()


# ---------------------------------------------------------------------------
# _on_delete_step
# ---------------------------------------------------------------------------


class TestOnDeleteStep:
    def test_removes_step_at_index(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(step_id="s1"), _make_step(step_id="s2")]
        presenter._on_delete_step(0)
        assert len(presenter._steps) == 1
        assert presenter._steps[0].step_id == "s2"

    def test_ignores_out_of_bounds(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._on_delete_step(99)
        assert len(presenter._steps) == 1

    def test_ignores_negative_index(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._on_delete_step(-1)
        assert len(presenter._steps) == 1

    def test_calls_render_steps(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step()]
        presenter._view.render_steps.reset_mock()
        presenter._on_delete_step(0)
        presenter._view.render_steps.assert_called()


# ---------------------------------------------------------------------------
# _on_clear_all_steps
# ---------------------------------------------------------------------------


class TestOnClearAllSteps:
    def test_clears_all_steps(self, presenter: StepsListPresenter) -> None:
        presenter._steps = [_make_step(), _make_step(step_id="s2")]
        presenter._on_clear_all_steps()
        assert presenter._steps == []

    def test_resets_edit_index(self, presenter: StepsListPresenter) -> None:
        presenter._edit_index = 1
        presenter._on_clear_all_steps()
        assert presenter._edit_index is None


# ---------------------------------------------------------------------------
# _on_reorder_steps
# ---------------------------------------------------------------------------


class TestOnReorderSteps:
    def test_reorders_steps_by_id(self, presenter: StepsListPresenter) -> None:
        s1 = _make_step(step_id="s1")
        s2 = _make_step(step_id="s2")
        presenter._steps = [s1, s2]
        presenter._on_reorder_steps(["s2", "s1"])
        assert presenter._steps[0].step_id == "s2"
        assert presenter._steps[1].step_id == "s1"

    def test_ignores_unknown_ids(self, presenter: StepsListPresenter) -> None:
        s1 = _make_step(step_id="s1")
        presenter._steps = [s1]
        presenter._on_reorder_steps(["s1", "unknown"])
        assert len(presenter._steps) == 1


# ---------------------------------------------------------------------------
# _on_move_step
# ---------------------------------------------------------------------------


class TestOnMoveStep:
    def test_moves_step_down(self, presenter: StepsListPresenter) -> None:
        s1 = _make_step(step_id="s1")
        s2 = _make_step(step_id="s2")
        presenter._steps = [s1, s2]
        presenter._on_move_step(0, 1)
        assert presenter._steps[0].step_id == "s2"
        assert presenter._steps[1].step_id == "s1"

    def test_moves_step_up(self, presenter: StepsListPresenter) -> None:
        s1 = _make_step(step_id="s1")
        s2 = _make_step(step_id="s2")
        presenter._steps = [s1, s2]
        presenter._on_move_step(1, -1)
        assert presenter._steps[0].step_id == "s2"

    def test_ignores_move_out_of_bounds(self, presenter: StepsListPresenter) -> None:
        s1 = _make_step(step_id="s1")
        presenter._steps = [s1]
        presenter._on_move_step(0, 1)  # can't move down — only 1 step
        assert presenter._steps[0].step_id == "s1"


# ---------------------------------------------------------------------------
# _on_duplicate_step
# ---------------------------------------------------------------------------


class TestOnDuplicateStep:
    def test_inserts_copy_after_original(self, presenter: StepsListPresenter) -> None:
        step = _make_step(step_id="orig")
        presenter._steps = [step]
        view_item = StepViewItem(
            step_id="orig",
            step_type=step.step_type,
            is_active=True,
            modified_date=datetime.now(),
            params_dict={},
            label="",
        )
        presenter._on_duplicate_step(view_item, 0)
        assert len(presenter._steps) == 2
        assert presenter._steps[0].step_id == "orig"
        assert presenter._steps[1].step_id != "orig"

    def test_returns_item_when_step_not_found(self, presenter: StepsListPresenter) -> None:
        presenter._steps = []
        view_item = StepViewItem(
            step_id="missing",
            step_type=StepTypeEnum.E_SECTION_STEPS,
            is_active=True,
            modified_date=datetime.now(),
            params_dict={},
            label="",
        )
        result = presenter._on_duplicate_step(view_item, 0)
        assert result is view_item


# ---------------------------------------------------------------------------
# _notify_validation_feedback
# ---------------------------------------------------------------------------


class TestNotifyValidationFeedback:
    def test_sets_error_status_when_error_present(self, presenter: StepsListPresenter) -> None:
        presenter._notify_validation_feedback("Some error")
        presenter._view.set_validation_status.assert_called_with("Some error", True)

    def test_sets_valid_status_when_no_error(self, presenter: StepsListPresenter) -> None:
        presenter._notify_validation_feedback(None)
        presenter._view.set_validation_status.assert_called_with("Workflow valide.", False)


# ---------------------------------------------------------------------------
# _validate_solo_step
# ---------------------------------------------------------------------------


class TestValidateSoloStep:
    def test_delegates_to_workflow_service(self, presenter: StepsListPresenter) -> None:
        step = _make_step()
        presenter._workflow_service.validate_step.return_value = []
        result = presenter._validate_solo_step([step], 0)
        assert result == []
        presenter._workflow_service.validate_step.assert_called_with(0, step, [step])
