"""Unit tests for WorkflowView."""

from __future__ import annotations

import tkinter as tk
from typing import Any
from unittest.mock import patch

import pytest
import views.steps  # noqa: F401  — registers all step form defs
from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from views.workflow_view import WorkflowView


def _make_step(step_id: str) -> StepScrapingModel:
    """Return a minimal step for test setup."""
    return StepScrapingModel(step_type=StepTypeEnum.E_OPEN_URL, step_id=step_id)


@pytest.fixture()
def view(tk_root: tk.Tk) -> WorkflowView:
    """Return a WorkflowView embedded in the session root."""
    frame = tk.Frame(tk_root)
    v = WorkflowView(frame)
    v.pack()
    tk_root.update_idletasks()
    yield v
    frame.destroy()


# ---------------------------------------------------------------------------
# load_data / get_data / clear_data
# ---------------------------------------------------------------------------


def test_load_data_populates_all_fields(view: WorkflowView) -> None:
    """load_data() must populate every form field from the given dict."""
    data: dict[str, Any] = {
        "id_file": "file123",
        "provider_name": "My Provider",
        "url": "https://example.com",
        "version": "1.0.0",
    }
    view.load_data(data)
    result = view.get_data()
    assert result["id_file"] == "file123"
    assert result["provider_name"] == "My Provider"
    assert result["url"] == "https://example.com"
    assert result["version"] == "1.0.0"


def test_get_data_returns_current_field_values(view: WorkflowView) -> None:
    """get_data() must reflect all current entry values."""
    view._var_name.set("Test Name")
    view._var_url.set("https://test.com")
    view._var_version.set("2.0")
    result = view.get_data()
    assert result["provider_name"] == "Test Name"
    assert result["url"] == "https://test.com"
    assert result["version"] == "2.0"


def test_clear_data_empties_all_fields(view: WorkflowView) -> None:
    """clear_data() must reset every field to an empty string."""
    view.load_data({"id_file": "x", "provider_name": "n", "url": "u", "version": "v"})
    view.clear_data()
    result = view.get_data()
    assert result["provider_name"] == ""
    assert result["url"] == ""
    assert result["version"] == ""


def test_load_data_missing_keys_use_empty_string(view: WorkflowView) -> None:
    """load_data() with a partial dict must leave missing fields empty."""
    view.load_data({})
    result = view.get_data()
    assert result["id_file"] == ""
    assert result["provider_name"] == ""


# ---------------------------------------------------------------------------
# set_workflow_validation_message
# ---------------------------------------------------------------------------


def test_set_workflow_validation_message_ok_state(view: WorkflowView) -> None:
    """Success state must update the label text."""
    view.set_workflow_validation_message("All good", False)
    assert view._lbl_workflow_status.cget("text") == "All good"


def test_set_workflow_validation_message_error_state(view: WorkflowView) -> None:
    """Error state must update the label text."""
    view.set_workflow_validation_message("Bad step", True)
    assert view._lbl_workflow_status.cget("text") == "Bad step"


# ---------------------------------------------------------------------------
# set_callbacks — save/cancel wiring
# ---------------------------------------------------------------------------


def test_set_callbacks_wires_save(view: WorkflowView) -> None:
    """Pressing save must invoke the registered on_save callback."""
    received: list[dict[str, Any]] = []
    view.set_callbacks(on_save=lambda d: received.append(d), on_cancel=lambda: None)
    view._notify_save()
    assert len(received) == 1


def test_set_callbacks_wires_cancel(view: WorkflowView) -> None:
    """Pressing cancel must invoke the registered on_cancel callback."""
    called: list[bool] = []
    view.set_callbacks(on_save=lambda d: None, on_cancel=lambda: called.append(True))
    view._notify_cancel()
    assert called == [True]


# ---------------------------------------------------------------------------
# workflow_builder_view property
# ---------------------------------------------------------------------------


def test_workflow_builder_view_property_returns_inner_widget(view: WorkflowView) -> None:
    """workflow_builder_view must return the embedded WorkflowListCrudView."""
    from views.workflow_list_crud_view import WorkflowListCrudView

    assert isinstance(view.workflow_builder_view, WorkflowListCrudView)


# ---------------------------------------------------------------------------
# set_available_steps
# ---------------------------------------------------------------------------


def test_set_available_steps_forwards_to_inline_form(view: WorkflowView) -> None:
    """set_available_steps() must propagate the list to the inline form panel."""
    steps = [_make_step("aa"), _make_step("bb")]
    view.set_available_steps(steps)
    assert view._inline_form._available_steps == steps


# ---------------------------------------------------------------------------
# show_inline_form
# ---------------------------------------------------------------------------


def test_show_inline_form_none_triggers_creation_mode(view: WorkflowView) -> None:
    """show_inline_form(None) must switch the inline form to creation mode."""
    view.show_inline_form(None)
    assert not view._is_edit_mode


def test_show_inline_form_step_triggers_edit_mode(view: WorkflowView) -> None:
    """show_inline_form(step) must switch the inline form to edit mode."""
    step = _make_step("abcd")
    step.params = {"url": "https://example.com"}
    view.show_inline_form(step)
    assert view._is_edit_mode


# ---------------------------------------------------------------------------
# _on_inline_confirm / _on_inline_cancel
# ---------------------------------------------------------------------------


def test_on_inline_confirm_forwards_to_builder_view(view: WorkflowView) -> None:
    """_on_inline_confirm must call on_confirm_inline_step on the builder view."""
    received: list[StepScrapingModel] = []
    view.workflow_builder_view.on_confirm_inline_step = lambda s: received.append(s)
    step = _make_step("aa")
    view._is_edit_mode = False
    view._on_inline_confirm(step)
    assert received == [step]


def test_on_inline_confirm_resets_edit_mode(view: WorkflowView) -> None:
    """_on_inline_confirm must clear _is_edit_mode to False."""
    view.workflow_builder_view.on_confirm_inline_step = lambda s: None
    view._is_edit_mode = True
    view._on_inline_confirm(_make_step("aa"))
    assert not view._is_edit_mode


def test_on_inline_cancel_forwards_to_builder_view(view: WorkflowView) -> None:
    """_on_inline_cancel must call on_cancel_inline_step on the builder view."""
    cancelled: list[bool] = []
    view.workflow_builder_view.on_cancel_inline_step = lambda: cancelled.append(True)
    view._on_inline_cancel()
    assert cancelled == [True]


def test_on_inline_cancel_resets_edit_mode(view: WorkflowView) -> None:
    """_on_inline_cancel must clear _is_edit_mode to False."""
    view.workflow_builder_view.on_cancel_inline_step = lambda: None
    view._is_edit_mode = True
    view._on_inline_cancel()
    assert not view._is_edit_mode


# ---------------------------------------------------------------------------
# ask_overwrite_confirmation / show_error (static methods)
# ---------------------------------------------------------------------------


def test_ask_overwrite_confirmation_returns_true_on_yes(view: WorkflowView) -> None:
    """ask_overwrite_confirmation() must return True when user clicks Yes."""
    with patch("views.workflow_view.messagebox.askyesno", return_value=True):
        assert WorkflowView.ask_overwrite_confirmation() is True


def test_ask_overwrite_confirmation_returns_false_on_no(view: WorkflowView) -> None:
    """ask_overwrite_confirmation() must return False when user clicks No."""
    with patch("views.workflow_view.messagebox.askyesno", return_value=False):
        assert WorkflowView.ask_overwrite_confirmation() is False


def test_show_error_calls_messagebox(view: WorkflowView) -> None:
    """show_error() must delegate to messagebox.showerror."""
    with patch("views.workflow_view.messagebox.showerror") as mock_err:
        WorkflowView.show_error("Something went wrong")
    mock_err.assert_called_once()


# ---------------------------------------------------------------------------
# _on_type_list_select
# ---------------------------------------------------------------------------


def test_on_type_list_select_rebuilds_form_for_new_type(view: WorkflowView) -> None:
    """Selecting a different type in the listbox must trigger a form rebuild."""
    from shared.i18n_fra import C_STEP_TYPE_TO_LABELS

    labels = list(C_STEP_TYPE_TO_LABELS.values())
    # Force the inline form to show a different type than the listbox selection.
    view._inline_form._type_var.set(labels[1] if len(labels) > 1 else labels[0])
    # Select the first label programmatically.
    view._type_listbox.selection_clear(0, tk.END)
    view._type_listbox.selection_set(0)
    event = tk.Event()  # type: ignore[attr-defined]
    view._on_type_list_select(event)
    # After selection, the type var must match the listbox item.
    assert view._inline_form._type_var.get() == labels[0]
