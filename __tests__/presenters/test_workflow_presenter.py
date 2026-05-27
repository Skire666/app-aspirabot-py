"""Unit tests for WorkflowPresenter."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from models.provider_model import ScenarioModel
from models.step_scraping_model import StepScrapingModel
from presenters.workflow_presenter import WorkflowPresenter

# -----------------------------------------------------------------------------
# Stubs
# -----------------------------------------------------------------------------


class _StubListCrudView:
    """Stub for WorkflowListCrudView — minimal surface used by WorkflowListPresenter."""

    def __init__(self) -> None:
        self.rendered_steps: list[StepScrapingModel] = []
        # Callback slots matched to WorkflowListCrudView attributes.
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
        pass


class _StubWorkflowView:
    """Stub for WorkflowView — captures all presenter interactions."""

    def __init__(self) -> None:
        self._list_crud_view = _StubListCrudView()
        self.on_save: Callable[[dict[str, Any]], None] | None = None
        self.on_cancel: Callable[[], None] | None = None
        self.data_loaded: dict[str, Any] | None = None
        self.data_cleared: bool = False
        self.validation_messages: list[tuple[str, bool]] = []
        self.errors_shown: list[str] = []
        self.inline_forms_loaded: list[StepScrapingModel | None] = []
        self.available_steps_set: list[list[StepScrapingModel]] = []

    @property
    def workflow_builder_view(self) -> _StubListCrudView:
        return self._list_crud_view

    def set_callbacks(
        self,
        on_save: Callable[[dict[str, Any]], None],
        on_cancel: Callable[[], None],
    ) -> None:
        self.on_save = on_save
        self.on_cancel = on_cancel

    def set_workflow_validation_message(self, message: str, is_error: bool) -> None:
        self.validation_messages.append((message, is_error))

    def load_data(self, data: dict[str, Any]) -> None:
        self.data_loaded = dict(data)

    def clear_data(self) -> None:
        self.data_cleared = True

    def show_error(self, message: str) -> None:
        self.errors_shown.append(message)

    def show_inline_form(self, step: StepScrapingModel | None = None) -> None:
        self.inline_forms_loaded.append(step)

    def set_available_steps(self, steps: list[StepScrapingModel]) -> None:
        self.available_steps_set.append(list(steps))

    def ask_overwrite_confirmation(self) -> bool:
        return True


class _StubProviderService:
    """Stub for ProviderService — returns configurable provider data."""

    def __init__(self, provider: ScenarioModel | None = None) -> None:
        self._provider = provider or _default_provider()
        self.created: list[ScenarioModel] = []
        self.updated: list[ScenarioModel] = []

    def read_provider(self, id_file: str) -> ScenarioModel:
        return self._provider

    def exists_provider(self, id_file: str) -> bool:
        return False

    def create_provider(self, provider: ScenarioModel) -> None:
        self.created.append(provider)

    def update_provider(self, provider: ScenarioModel) -> None:
        self.updated.append(provider)


def _default_provider(steps: list[StepScrapingModel] | None = None) -> ScenarioModel:
    """Return a minimal ScenarioModel for test setup."""
    return ScenarioModel(
        id_file="prov-id",
        provider_name="Test Provider",
        provider_desc="https://example.com",
        created_date="2024-01-01 00:00:00",
        modified_date="2024-01-01 00:00:00",
        version="1.0.0",
        steps=steps or [],
    )


def _make_presenter(
    provider: ScenarioModel | None = None,
) -> tuple[WorkflowPresenter, _StubWorkflowView, _StubProviderService]:
    """Build a WorkflowPresenter with stub dependencies."""
    view = _StubWorkflowView()
    service = _StubProviderService(provider)
    presenter = WorkflowPresenter(
        view=view,  # type: ignore[arg-type]
        provider_service=service,  # type: ignore[arg-type]
    )
    return presenter, view, service


# -----------------------------------------------------------------------------
# create_new
# -----------------------------------------------------------------------------


def test_create_new_loads_default_data() -> None:
    """create_new() must call load_data() with a provider dict."""
    presenter, view, _ = _make_presenter()
    presenter.create_new()
    assert view.data_loaded is not None
    assert "id_file" in view.data_loaded


def test_create_new_shows_inline_form_with_none() -> None:
    """create_new() must open the inline form in creation mode (step=None)."""
    presenter, view, _ = _make_presenter()
    presenter.create_new()
    # show_inline_form(None) must have been called at least once.
    assert None in view.inline_forms_loaded


def test_create_new_sets_creation_mode_flag() -> None:
    """create_new() must set _is_creation_mode to True."""
    presenter, _, _ = _make_presenter()
    presenter.create_new()
    assert presenter._is_creation_mode is True


# -----------------------------------------------------------------------------
# load_provider
# -----------------------------------------------------------------------------


def test_load_provider_populates_form_fields() -> None:
    """load_provider() must push provider data into the view."""
    provider = _default_provider()
    presenter, view, _ = _make_presenter(provider)
    presenter.load_provider("prov-id")
    assert view.data_loaded is not None
    assert view.data_loaded.get("provider_name") == "Test Provider"


def test_load_provider_sets_edit_mode_flag() -> None:
    """load_provider() must set _is_creation_mode to False."""
    presenter, _, _ = _make_presenter()
    presenter.load_provider("prov-id")
    assert presenter._is_creation_mode is False


def test_load_provider_shows_inline_form() -> None:
    """load_provider() must open the inline form (None for creation-ready state)."""
    presenter, view, _ = _make_presenter()
    presenter.load_provider("prov-id")
    assert None in view.inline_forms_loaded


# -----------------------------------------------------------------------------
# _on_save — creation mode
# -----------------------------------------------------------------------------


def test_on_save_creates_provider_in_creation_mode() -> None:
    """Save in creation mode must call service.create_provider()."""
    presenter, view, service = _make_presenter()
    presenter.create_new()
    assert view.on_save is not None
    view.on_save({"provider_name": "New", "provider_desc": "https://x.com", "version": "1.0"})
    assert len(service.created) == 1


def test_on_save_clears_view_after_success() -> None:
    """Save must call view.clear_data() on success."""
    presenter, view, _ = _make_presenter()
    presenter.create_new()
    assert view.on_save is not None
    view.on_save({"provider_name": "N", "provider_desc": "https://x.com", "version": "1"})
    assert view.data_cleared is True


def test_on_save_calls_done_callback() -> None:
    """Save must invoke the on_done callback after persisting."""
    done_calls: list[bool] = []
    presenter, view, _ = _make_presenter()
    presenter.set_on_done_callback(lambda: done_calls.append(True))
    presenter.create_new()
    assert view.on_save is not None
    view.on_save({"provider_name": "N", "provider_desc": "https://x.com", "version": "1"})
    assert done_calls == [True]


# -----------------------------------------------------------------------------
# _on_cancel
# -----------------------------------------------------------------------------


def test_on_cancel_clears_view_data() -> None:
    """Cancel must call view.clear_data() to reset the form."""
    presenter, view, _ = _make_presenter()
    presenter.create_new()
    assert view.on_cancel is not None
    view.on_cancel()
    assert view.data_cleared is True


def test_on_cancel_calls_done_callback() -> None:
    """Cancel must invoke the on_done callback."""
    done_calls: list[bool] = []
    presenter, view, _ = _make_presenter()
    presenter.set_on_done_callback(lambda: done_calls.append(True))
    presenter.create_new()
    assert view.on_cancel is not None
    view.on_cancel()
    assert done_calls == [True]


def test_on_cancel_resets_current_provider() -> None:
    """Cancel must nullify _current_provider."""
    presenter, view, _ = _make_presenter()
    presenter.create_new()
    assert view.on_cancel is not None
    view.on_cancel()
    assert presenter._current_provider is None


# -----------------------------------------------------------------------------
# set_on_done_callback
# -----------------------------------------------------------------------------


def test_set_on_done_callback_replaces_previous() -> None:
    """set_on_done_callback() must replace any previous callback."""
    calls_a: list[int] = []
    calls_b: list[int] = []
    presenter, view, _ = _make_presenter()
    presenter.set_on_done_callback(lambda: calls_a.append(1))
    presenter.set_on_done_callback(lambda: calls_b.append(1))
    presenter.create_new()
    assert view.on_cancel is not None
    view.on_cancel()
    assert calls_a == []
    assert calls_b == [1]
