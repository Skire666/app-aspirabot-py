"""Unit tests for WorkflowListPresenter."""

from __future__ import annotations

from typing import Any

import pytest

from models.provider_model import ProviderModel
from models.step_scraping_model import StepScrapingModel, StepType
from presenters.workflow_list_presenter import WorkflowListPresenter


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------


class _StubListView:
    """Stub for WorkflowListCrudView — captures render calls and exposes callbacks."""

    def __init__(self) -> None:
        self.rendered_steps: list[StepScrapingModel] = []
        self.selection_cleared: int = 0
        # Callback slots mirroring WorkflowListCrudView
        self.on_edit_step = None
        self.on_delete_step = None
        self.on_move_step = None
        self.on_toggle_active_step = None
        self.on_reorder_steps = None
        self.on_confirm_inline_step = None
        self.on_cancel_inline_step = None
        self.on_clear_all_steps = None
        self.on_duplicate_step = None

    def render_steps(self, steps: list[StepScrapingModel]) -> None:
        self.rendered_steps = list(steps)

    def clear_selection(self) -> None:
        self.selection_cleared += 1


class _StubGestionView:
    """Stub for WorkflowView (gestion_view) — tracks calls from the presenter."""

    def __init__(self) -> None:
        self.available_steps: list[StepScrapingModel] = []
        self.inline_form_loaded: StepScrapingModel | None = None
        self.inline_form_loaded_calls: int = 0

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        self.available_steps = list(steps)

    def show_inline_form(self, step: StepScrapingModel | None) -> None:
        self.inline_form_loaded = step
        self.inline_form_loaded_calls += 1


class _StubProviderService:
    """Stub for ProviderService — returns a configurable ProviderModel."""

    def __init__(self, provider: ProviderModel) -> None:
        self._provider = provider

    def read_provider(self, id_file: str) -> ProviderModel:
        return self._provider


class _StubWorkflowService:
    """Stub for WorkflowService — returns a configurable error list."""

    def __init__(self, errors: list[str] | None = None) -> None:
        self._errors = errors or []

    def validate_step(
        self,
        step_index: int,
        step: StepScrapingModel,
        steps: list[StepScrapingModel] | None = None,
    ) -> list[str]:
        return list(self._errors)


def _make_step(step_id: str, step_type: StepType = StepType.OPEN_URL) -> StepScrapingModel:
    """Return a minimal StepScrapingModel for test setup."""
    return StepScrapingModel(step_type=step_type, step_id=step_id)


def _make_provider(steps: list[StepScrapingModel] | None = None) -> ProviderModel:
    """Return a minimal ProviderModel for test setup."""
    return ProviderModel(
        id_file="test-file",
        provider_name="Test",
        url="https://example.com",
        created_date="2024-01-01 00:00:00",
        modified_date="2024-01-01 00:00:00",
        version="1.0.0",
        steps=steps or [],
    )


def _make_presenter(
    steps: list[StepScrapingModel] | None = None,
    workflow_errors: list[str] | None = None,
) -> tuple[WorkflowListPresenter, _StubListView, _StubGestionView]:
    """Build a WorkflowListPresenter with stub dependencies."""
    list_view = _StubListView()
    gestion_view = _StubGestionView()
    provider = _make_provider(steps)
    service = _StubProviderService(provider)
    workflow_service = _StubWorkflowService(workflow_errors)
    presenter = WorkflowListPresenter(
        view=list_view,  # type: ignore[arg-type]
        service_provider=service,  # type: ignore[arg-type]
        workflow_service=workflow_service,  # type: ignore[arg-type]
        gestion_view=gestion_view,  # type: ignore[arg-type]
    )
    return presenter, list_view, gestion_view


# ---------------------------------------------------------------------------
# init_new
# ---------------------------------------------------------------------------


def test_init_new_clears_steps_and_renders(  # noqa: ANN201
) -> None:
    """init_new() must start with an empty step list and call render_steps."""
    presenter, list_view, _ = _make_presenter()
    presenter.init_new("new-id")
    assert list_view.rendered_steps == []
    assert presenter.get_steps() == []


# ---------------------------------------------------------------------------
# load
# ---------------------------------------------------------------------------


def test_load_populates_steps_from_provider() -> None:
    """load() must fill _steps from the provider returned by the service."""
    step = _make_step("aa")
    presenter, list_view, _ = _make_presenter(steps=[step])
    presenter.load("test-file")
    assert len(presenter.get_steps()) == 1
    assert list_view.rendered_steps[0].step_id == "aa"


def test_load_updates_gestion_view_available_steps() -> None:
    """load() must forward the step list to gestion_view via set_available_steps."""
    step = _make_step("aa")
    presenter, _, gestion_view = _make_presenter(steps=[step])
    presenter.load("test-file")
    assert len(gestion_view.available_steps) == 1


# ---------------------------------------------------------------------------
# get_steps
# ---------------------------------------------------------------------------


def test_get_steps_returns_independent_copy() -> None:
    """get_steps() must return a copy; mutating it must not affect the internal list."""
    presenter, _, _ = _make_presenter()
    presenter.init_new("x")
    copy = presenter.get_steps()
    copy.append(_make_step("zz"))
    assert presenter.get_steps() == []


# ---------------------------------------------------------------------------
# validate_steps
# ---------------------------------------------------------------------------


def test_validate_steps_returns_empty_for_empty_workflow() -> None:
    """validate_steps() on an empty list must return no errors."""
    presenter, _, _ = _make_presenter()
    presenter.init_new("x")
    assert presenter.validate_steps() == []


def test_validate_steps_forwards_service_errors() -> None:
    """validate_steps() must accumulate errors from WorkflowService."""
    step = _make_step("aa")
    presenter, _, _ = _make_presenter(steps=[step], workflow_errors=["Erreur test"])
    presenter.load("test-file")
    errors = presenter.validate_steps()
    assert errors == ["Erreur test"]


# ---------------------------------------------------------------------------
# clear_steps
# ---------------------------------------------------------------------------


def test_clear_steps_empties_the_list_and_renders() -> None:
    """clear_steps() must empty _steps and call render_steps([])."""
    step = _make_step("aa")
    presenter, list_view, _ = _make_presenter(steps=[step])
    presenter.load("test-file")
    presenter.clear_steps()
    assert presenter.get_steps() == []
    assert list_view.rendered_steps == []


# ---------------------------------------------------------------------------
# _on_confirm_inline_step
# ---------------------------------------------------------------------------


def test_confirm_inline_step_appends_in_add_mode() -> None:
    """Confirming a step in add mode must append it to _steps."""
    presenter, _, _ = _make_presenter()
    presenter.init_new("x")
    step = _make_step("aa")
    # Simulate confirmation with no errors.
    list_view = presenter._view
    list_view.on_confirm_inline_step(step)
    assert len(presenter.get_steps()) == 1


def test_confirm_inline_step_replaces_in_edit_mode() -> None:
    """Confirming a step in edit mode must replace the existing entry."""
    step_a = _make_step("aa")
    step_b = _make_step("bb")
    presenter, _, _ = _make_presenter(steps=[step_a])
    presenter.load("test-file")
    presenter._edit_index = 0
    presenter._view.on_confirm_inline_step(step_b)
    steps = presenter.get_steps()
    assert len(steps) == 1
    assert steps[0].step_id == "bb"


def test_confirm_inline_step_keeps_form_open_on_error() -> None:
    """If validation fails, the step must not be added."""
    presenter, _, _ = _make_presenter(workflow_errors=["Erreur"])
    presenter.init_new("x")
    step = _make_step("aa")
    presenter._view.on_confirm_inline_step(step)
    # Error step must not be appended.
    assert presenter.get_steps() == []


# ---------------------------------------------------------------------------
# _on_delete_step
# ---------------------------------------------------------------------------


def test_delete_step_removes_by_index() -> None:
    """Deleting step at index 0 must leave only the second step."""
    step_a = _make_step("aa")
    step_b = _make_step("bb")
    presenter, _, _ = _make_presenter(steps=[step_a, step_b])
    presenter.load("test-file")
    presenter._view.on_delete_step(0)
    steps = presenter.get_steps()
    assert len(steps) == 1
    assert steps[0].step_id == "bb"


def test_delete_step_out_of_range_is_ignored() -> None:
    """Deleting an out-of-range index must not change the step list."""
    step = _make_step("aa")
    presenter, _, _ = _make_presenter(steps=[step])
    presenter.load("test-file")
    presenter._view.on_delete_step(99)
    assert len(presenter.get_steps()) == 1


# ---------------------------------------------------------------------------
# _on_move_step
# ---------------------------------------------------------------------------


def test_move_step_up_swaps_with_predecessor() -> None:
    """Moving step at index 1 up must swap it with index 0."""
    step_a = _make_step("aa")
    step_b = _make_step("bb")
    presenter, _, _ = _make_presenter(steps=[step_a, step_b])
    presenter.load("test-file")
    presenter._view.on_move_step(1, -1)
    steps = presenter.get_steps()
    assert steps[0].step_id == "bb"
    assert steps[1].step_id == "aa"


def test_move_step_down_swaps_with_successor() -> None:
    """Moving step at index 0 down must swap it with index 1."""
    step_a = _make_step("aa")
    step_b = _make_step("bb")
    presenter, _, _ = _make_presenter(steps=[step_a, step_b])
    presenter.load("test-file")
    presenter._view.on_move_step(0, 1)
    steps = presenter.get_steps()
    assert steps[0].step_id == "bb"
    assert steps[1].step_id == "aa"


def test_move_step_first_up_is_ignored() -> None:
    """Moving the first step further up must be a no-op."""
    step_a = _make_step("aa")
    step_b = _make_step("bb")
    presenter, _, _ = _make_presenter(steps=[step_a, step_b])
    presenter.load("test-file")
    presenter._view.on_move_step(0, -1)
    steps = presenter.get_steps()
    assert steps[0].step_id == "aa"


# ---------------------------------------------------------------------------
# _on_toggle_active_step
# ---------------------------------------------------------------------------


def test_toggle_active_flips_is_active() -> None:
    """Toggling a step must invert its is_active flag."""
    step = _make_step("aa")
    assert step.is_active is True
    presenter, _, _ = _make_presenter(steps=[step])
    presenter.load("test-file")
    presenter._view.on_toggle_active_step(0)
    assert presenter.get_steps()[0].is_active is False


# ---------------------------------------------------------------------------
# _on_clear_all_steps
# ---------------------------------------------------------------------------


def test_clear_all_steps_empties_the_list() -> None:
    """on_clear_all_steps must remove all steps."""
    presenter, _, _ = _make_presenter(steps=[_make_step("aa"), _make_step("bb")])
    presenter.load("test-file")
    presenter._view.on_clear_all_steps()
    assert presenter.get_steps() == []


# ---------------------------------------------------------------------------
# _on_reorder_steps
# ---------------------------------------------------------------------------


def test_reorder_steps_syncs_internal_list() -> None:
    """on_reorder_steps must replace _steps with the provided list."""
    step_a = _make_step("aa")
    step_b = _make_step("bb")
    presenter, _, _ = _make_presenter(steps=[step_a, step_b])
    presenter.load("test-file")
    presenter._view.on_reorder_steps([step_b, step_a])
    steps = presenter.get_steps()
    assert steps[0].step_id == "bb"
    assert steps[1].step_id == "aa"


# ---------------------------------------------------------------------------
# _on_duplicate_step
# ---------------------------------------------------------------------------


def test_duplicate_step_returns_copy_with_new_id() -> None:
    """on_duplicate_step must return a step with a different step_id."""
    step = _make_step("aa")
    presenter, _, _ = _make_presenter()
    presenter.init_new("x")
    duplicate = presenter._view.on_duplicate_step(step, 0)
    assert duplicate.step_type == step.step_type
    assert duplicate.step_id != step.step_id


# ---------------------------------------------------------------------------
# _on_cancel_inline_step
# ---------------------------------------------------------------------------


def test_cancel_inline_step_clears_edit_index() -> None:
    """Cancelling edit mode must reset _edit_index to None."""
    presenter, _, _ = _make_presenter(steps=[_make_step("aa")])
    presenter.load("test-file")
    presenter._edit_index = 0
    presenter._view.on_cancel_inline_step()
    assert presenter._edit_index is None


# ---------------------------------------------------------------------------
# set_validation_feedback_handler
# ---------------------------------------------------------------------------


def test_validation_feedback_handler_called_on_confirm() -> None:
    """A registered feedback handler must receive the validation result on confirm."""
    messages: list[tuple[str, bool]] = []
    presenter, _, _ = _make_presenter()
    presenter.init_new("x")
    presenter.set_validation_feedback_handler(lambda msg, err: messages.append((msg, err)))
    presenter._view.on_confirm_inline_step(_make_step("aa"))
    # A valid step must produce a success feedback.
    assert messages and messages[-1][1] is False
