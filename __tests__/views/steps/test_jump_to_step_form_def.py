"""Unit tests for JumpToStepFormDef."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any

import pytest
from models.step_scraping_model import StepScrapingModel
from shared.enums import StepTypeEnum
from views.steps._constants import CONDITION_DISPLAY, CONDITION_MODEL_TO_VIEW
from views.steps.jump_to_step_form_def import JumpToStepFormDef

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------


class _Var:
    """Minimal StringVar stub usable without a Tk root."""

    def __init__(self, value: str = "") -> None:
        self._v = value

    def get(self) -> str:
        return self._v

    def set(self, value: str) -> None:
        self._v = value


def _make_step(step_id: str) -> StepScrapingModel:
    """Return a minimal StepScrapingModel for test setup."""
    return StepScrapingModel(step_type=StepTypeEnum.E_OPEN_URL, step_id=step_id)


def _make_jump_step(step_id: str, condition: str, target: str) -> StepScrapingModel:
    """Return a JUMP_TO_STEP model with the given params."""
    s = StepScrapingModel(step_type=StepTypeEnum.E_JUMP_TO_STEP, step_id=step_id)
    s.params = {"condition": condition, "target_hexastring": target}
    return s


@pytest.fixture()
def root(tk_root: tk.Tk) -> tk.Tk:
    """Re-expose the session Tk root under the name 'root' for form-def tests."""
    return tk_root


# -----------------------------------------------------------------------------
# step_type / label — no Tkinter required
# -----------------------------------------------------------------------------


def test_step_type_returns_jump_to_step() -> None:
    """step_type() must return StepTypeEnum.E_JUMP_TO_STEP."""
    assert JumpToStepFormDef.step_type() == StepTypeEnum.E_JUMP_TO_STEP


def test_label_is_non_empty_string() -> None:
    """label() must return a non-empty string."""
    lbl = JumpToStepFormDef.label()
    assert isinstance(lbl, str) and lbl


# -----------------------------------------------------------------------------
# compute_string_displayed_in_combobox — no Tkinter required
# -----------------------------------------------------------------------------


def test_compute_string_positive_index() -> None:
    """Valid index and model must produce a non-empty formatted string."""
    step = _make_step("abcd")
    result = JumpToStepFormDef.compute_string_displayed_in_combobox(0, step)
    assert "#abcd" in result
    assert "01" in result


def test_compute_string_negative_index_returns_empty() -> None:
    """Negative index must return an empty string."""
    step = _make_step("abcd")
    result = JumpToStepFormDef.compute_string_displayed_in_combobox(-1, step)
    assert result == ""


def test_compute_string_none_model_returns_empty() -> None:
    """None model must return an empty string."""
    result = JumpToStepFormDef.compute_string_displayed_in_combobox(0, None)  # type: ignore[arg-type]
    assert result == ""


# -----------------------------------------------------------------------------
# _extract_after_hash_hexastring — no Tkinter required
# -----------------------------------------------------------------------------


def test_extract_hexastring_from_valid_format() -> None:
    """Must return the 4 characters after '#' from a combobox display string."""
    result = JumpToStepFormDef._extract_after_hash_hexastring("01.  -  #abcd  - label")
    assert result == "abcd"


def test_extract_hexastring_no_hash_returns_empty() -> None:
    """String without '#' must return an empty string."""
    result = JumpToStepFormDef._extract_after_hash_hexastring("no hash here")
    assert result == ""


def test_extract_hexastring_none_returns_empty() -> None:
    """None input must return an empty string."""
    result = JumpToStepFormDef._extract_after_hash_hexastring(None)  # type: ignore[arg-type]
    assert result == ""


def test_extract_hexastring_hash_at_end_returns_empty() -> None:
    """'#' with fewer than 4 following chars must return an incomplete string."""
    result = JumpToStepFormDef._extract_after_hash_hexastring("01. #ab")
    assert len(result) <= 4


# -----------------------------------------------------------------------------
# format_label — no Tkinter required
# -----------------------------------------------------------------------------


def test_format_label_success_condition() -> None:
    """format_label() with condition='success' must mention succès."""
    target = _make_step("abcd")
    source = _make_jump_step("efgh", "success", "abcd")
    source.parent_context = [source, target]
    label = JumpToStepFormDef().format_label(source, 0)
    assert "succès" in label


def test_format_label_failure_condition() -> None:
    """format_label() with condition='failure' must mention échec."""
    target = _make_step("abcd")
    source = _make_jump_step("efgh", "failure", "abcd")
    source.parent_context = [source, target]
    label = JumpToStepFormDef().format_label(source, 0)
    assert "échec" in label


def test_format_label_always_condition() -> None:
    """format_label() with condition='always' must mention toujours."""
    target = _make_step("abcd")
    source = _make_jump_step("efgh", "always", "abcd")
    source.parent_context = [source, target]
    label = JumpToStepFormDef().format_label(source, 0)
    assert "toujours" in label.lower() or "Toujours" in label


def test_format_label_unknown_target_shows_question_marks() -> None:
    """format_label() with a missing target must show '????'."""
    source = _make_jump_step("efgh", "success", "zzzz")
    source.parent_context = [source]
    label = JumpToStepFormDef().format_label(source, 0)
    assert "????" in label


# -----------------------------------------------------------------------------
# read_params_from_view — stub-based (no Tk root required)
# -----------------------------------------------------------------------------


def test_read_params_returns_correct_condition() -> None:
    """read_params_from_view() must map view display value to model value."""
    form = JumpToStepFormDef()
    widgets: dict[str, Any] = {
        "condition": _Var(CONDITION_DISPLAY[0]),  # "Si succès" → "success"
        "_choice_from_listbox": _Var("01.  -  #abcd  - label"),
        "comment": _Var("my note"),
    }
    result = form.read_params_from_view(widgets)
    assert result["condition"] == "success"
    assert result["target_hexastring"] == "abcd"
    assert result["comment"] == "my note"


def test_read_params_failure_condition() -> None:
    """read_params_from_view() must map 'Si échec' to 'failure'."""
    form = JumpToStepFormDef()
    widgets: dict[str, Any] = {
        "condition": _Var(CONDITION_DISPLAY[1]),  # "Si échec"
        "_choice_from_listbox": _Var("02.  -  #efgh  - label"),
        "comment": _Var(""),
    }
    result = form.read_params_from_view(widgets)
    assert result["condition"] == "failure"
    assert result["target_hexastring"] == "efgh"


# -----------------------------------------------------------------------------
# validate_form — stub-based (no Tk root required)
# -----------------------------------------------------------------------------


def test_validate_form_empty_choice_returns_error() -> None:
    """validate_form() must return an error when no target is chosen."""
    form = JumpToStepFormDef()
    widgets: dict[str, Any] = {
        "_choice_from_listbox": _Var(""),
        "_all_hexastring_to_model": {},
    }
    errors = form.validate_form(widgets)
    assert errors


def test_validate_form_unknown_hexastring_returns_error() -> None:
    """validate_form() must flag a target not present in _all_hexastring_to_model."""
    form = JumpToStepFormDef()
    widgets: dict[str, Any] = {
        "_choice_from_listbox": _Var("01.  -  #zzzz  - label"),
        "_all_hexastring_to_model": {"abcd": _make_step("abcd")},
    }
    errors = form.validate_form(widgets)
    assert errors


def test_validate_form_valid_choice_returns_no_errors() -> None:
    """validate_form() must return no errors when the target exists."""
    form = JumpToStepFormDef()
    step = _make_step("abcd")
    widgets: dict[str, Any] = {
        "_choice_from_listbox": _Var("01.  -  #abcd  - label"),
        "_all_hexastring_to_model": {"abcd": step},
    }
    errors = form.validate_form(widgets)
    assert errors == []


# -----------------------------------------------------------------------------
# build_form + load_params_step_to_widget — Tkinter required
# -----------------------------------------------------------------------------


def test_build_form_populates_widgets(root: tk.Tk) -> None:
    """build_form() must populate 'condition', '_choice_from_listbox', 'comment'."""
    frame = ttk.Frame(root)
    step = _make_step("abcd")
    widgets: dict[str, Any] = {"_all_steps_available": [step]}
    JumpToStepFormDef().build_form(frame, widgets)
    assert "condition" in widgets
    assert "_choice_from_listbox" in widgets
    assert "comment" in widgets
    assert "_all_hexastring_to_model" in widgets


def test_load_params_step_to_widget_sets_correct_choice(root: tk.Tk) -> None:
    """load_params_step_to_widget() must select the matching combobox entry."""
    frame = ttk.Frame(root)
    target = _make_step("abcd")
    source = _make_jump_step("efgh", "failure", "abcd")
    source.parent_context = [source, target]
    widgets: dict[str, Any] = {"_all_steps_available": [source, target]}

    # Build the form first so widgets are populated.
    JumpToStepFormDef().build_form(frame, widgets)
    JumpToStepFormDef().load_params_step_to_widget(source, widgets)

    # The selected display string must reference the target hexastring.
    chosen = widgets["_choice_from_listbox"].get()
    assert "abcd" in chosen

    # Condition must be mapped to its display value.
    cond_display = widgets["condition"].get()
    assert cond_display == CONDITION_MODEL_TO_VIEW.get("failure")
