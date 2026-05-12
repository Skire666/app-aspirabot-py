"""Unit tests for WorkflowListCrudView."""

from __future__ import annotations

import tkinter as tk
from unittest.mock import patch

import pytest

import views.steps  # noqa: F401  — registers all step form defs needed by StepItemRenderer
from models.step_scraping_model import StepScrapingModel, StepType
from views.workflow_list_crud_view import WorkflowListCrudView


def _make_step(step_id: str) -> StepScrapingModel:
    """Return a minimal step for test setup."""
    return StepScrapingModel(step_type=StepType.OPEN_URL, step_id=step_id)


@pytest.fixture()
def view(tk_root: tk.Tk) -> WorkflowListCrudView:
    """Return a WorkflowListCrudView embedded in the session root."""
    frame = tk.Frame(tk_root)
    v = WorkflowListCrudView(frame)
    v.pack()
    tk_root.update_idletasks()
    yield v
    frame.destroy()


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------


def test_all_callbacks_are_none_at_init(view: WorkflowListCrudView) -> None:
    """All public callback attributes must be None after construction."""
    assert view.on_edit_step is None
    assert view.on_delete_step is None
    assert view.on_move_step is None
    assert view.on_toggle_active_step is None
    assert view.on_reorder_steps is None
    assert view.on_confirm_inline_step is None
    assert view.on_cancel_inline_step is None
    assert view.on_clear_all_steps is None
    assert view.on_duplicate_step is None


# ---------------------------------------------------------------------------
# reset
# ---------------------------------------------------------------------------


def test_reset_clears_selected_index(view: WorkflowListCrudView) -> None:
    """reset() must set _selected_index to None."""
    view._selected_index = 2
    view.reset()
    assert view._selected_index is None


def test_reset_clears_last_steps(view: WorkflowListCrudView) -> None:
    """reset() must empty _last_steps."""
    view._last_steps = [_make_step("aa")]
    view.reset()
    assert view._last_steps == []


# ---------------------------------------------------------------------------
# render_steps
# ---------------------------------------------------------------------------


def test_render_steps_updates_last_steps(view: WorkflowListCrudView) -> None:
    """render_steps() must cache the provided list in _last_steps."""
    steps = [_make_step("aa"), _make_step("bb")]
    view.render_steps(steps)
    assert view._last_steps == steps


def test_render_steps_with_empty_list(view: WorkflowListCrudView) -> None:
    """render_steps([]) must store an empty list in _last_steps."""
    view.render_steps([])
    assert view._last_steps == []


def test_render_steps_stores_copy(view: WorkflowListCrudView) -> None:
    """render_steps() must store a copy — mutating the original must not affect cache."""
    steps = [_make_step("aa")]
    view.render_steps(steps)
    steps.append(_make_step("bb"))
    assert len(view._last_steps) == 1


def test_render_steps_skipped_during_dnd_busy(view: WorkflowListCrudView) -> None:
    """render_steps() must be a no-op when _dnd_busy is True."""
    initial = [_make_step("aa")]
    view.render_steps(initial)
    view._dnd_busy = True
    # A render_steps call while busy must NOT update _dnd_list.items.
    new_steps = [_make_step("bb"), _make_step("cc")]
    view.render_steps(new_steps)
    # _last_steps is always updated, but the DnD list must keep the old items.
    assert view._last_steps == new_steps
    assert view._dnd_list.items == initial
    view._dnd_busy = False


# ---------------------------------------------------------------------------
# clear_selection
# ---------------------------------------------------------------------------


def test_clear_selection_sets_index_to_none(view: WorkflowListCrudView) -> None:
    """clear_selection() must set _selected_index to None."""
    view._selected_index = 1
    view.render_steps([_make_step("aa"), _make_step("bb")])
    view.clear_selection()
    assert view._selected_index is None


# ---------------------------------------------------------------------------
# Callback wiring
# ---------------------------------------------------------------------------


def test_edit_step_callback_is_forwarded(view: WorkflowListCrudView) -> None:
    """on_edit_step callback must be invoked when _on_dnd_edit fires."""
    received: list[int] = []
    view.on_edit_step = lambda idx: received.append(idx)
    view.render_steps([_make_step("aa"), _make_step("bb")])
    step = view._last_steps[0]
    view._on_dnd_edit(step, 0)
    assert received == [0]


def test_toggle_active_callback_is_forwarded(view: WorkflowListCrudView) -> None:
    """on_toggle_active_step callback must be invoked when _on_dnd_toggle_active fires."""
    received: list[int] = []
    view.on_toggle_active_step = lambda idx: received.append(idx)
    step = _make_step("aa")
    view.render_steps([step])
    view._on_dnd_toggle_active(step, 0)
    assert received == [0]


def test_reorder_steps_callback_receives_list(view: WorkflowListCrudView) -> None:
    """on_reorder_steps must receive the full reordered step list."""
    captured: list[list[StepScrapingModel]] = []
    view.on_reorder_steps = lambda s: captured.append(s)
    steps = [_make_step("aa"), _make_step("bb")]
    view._on_dnd_reorder(steps)
    assert captured[0] == steps


# ---------------------------------------------------------------------------
# scroll_to_bottom
# ---------------------------------------------------------------------------


def test_scroll_to_bottom_does_not_raise(view: WorkflowListCrudView) -> None:
    """scroll_to_bottom() must schedule without raising."""
    view.scroll_to_bottom()  # schedules after_idle — just must not throw


# ---------------------------------------------------------------------------
# move-up / move-down callbacks
# ---------------------------------------------------------------------------


def test_move_up_callback_is_forwarded(view: WorkflowListCrudView) -> None:
    """_on_dnd_move_up must call on_move_step with direction -1."""
    moves: list[tuple[int, int]] = []
    view.on_move_step = lambda idx, d: moves.append((idx, d))
    view.render_steps([_make_step("aa"), _make_step("bb")])
    view._on_dnd_move_up(view._last_steps[1], 1)
    assert moves == [(1, -1)]


def test_move_up_adjusts_selected_index(view: WorkflowListCrudView) -> None:
    """_on_dnd_move_up must shift _selected_index when it matches the moved item."""
    view.render_steps([_make_step("aa"), _make_step("bb")])
    view._selected_index = 1
    view._on_dnd_move_up(view._last_steps[1], 1)
    assert view._selected_index == 0


def test_move_down_callback_is_forwarded(view: WorkflowListCrudView) -> None:
    """_on_dnd_move_down must call on_move_step with direction +1."""
    moves: list[tuple[int, int]] = []
    view.on_move_step = lambda idx, d: moves.append((idx, d))
    view.render_steps([_make_step("aa"), _make_step("bb")])
    view._on_dnd_move_down(view._last_steps[0], 0)
    assert moves == [(0, 1)]


def test_move_down_adjusts_selected_index(view: WorkflowListCrudView) -> None:
    """_on_dnd_move_down must shift _selected_index when it matches the moved item."""
    view.render_steps([_make_step("aa"), _make_step("bb")])
    view._selected_index = 0
    view._on_dnd_move_down(view._last_steps[0], 0)
    assert view._selected_index == 1


# ---------------------------------------------------------------------------
# delete callback
# ---------------------------------------------------------------------------


def test_delete_confirmed_calls_on_delete_step(view: WorkflowListCrudView) -> None:
    """_on_dnd_delete must call on_delete_step when the user confirms."""
    deleted: list[int] = []
    view.on_delete_step = lambda idx: deleted.append(idx)
    view.render_steps([_make_step("aa")])
    with patch("views.workflow_list_crud_view.messagebox.askyesno", return_value=True):
        result = view._on_dnd_delete(view._last_steps[0], 0)
    assert result is True
    assert deleted == [0]


def test_delete_cancelled_does_not_call_on_delete_step(view: WorkflowListCrudView) -> None:
    """_on_dnd_delete must return False and skip the callback when user cancels."""
    deleted: list[int] = []
    view.on_delete_step = lambda idx: deleted.append(idx)
    view.render_steps([_make_step("aa")])
    with patch("views.workflow_list_crud_view.messagebox.askyesno", return_value=False):
        result = view._on_dnd_delete(view._last_steps[0], 0)
    assert result is False
    assert deleted == []


# ---------------------------------------------------------------------------
# duplicate callback
# ---------------------------------------------------------------------------


def test_duplicate_callback_is_forwarded(view: WorkflowListCrudView) -> None:
    """_on_dnd_duplicate must delegate to on_duplicate_step and return its result."""
    step = _make_step("aa")
    clone = _make_step("bb")
    view.on_duplicate_step = lambda s, i: clone
    result = view._on_dnd_duplicate(step, 0)
    assert result is clone


# ---------------------------------------------------------------------------
# _fire_clear_all_steps
# ---------------------------------------------------------------------------


def test_fire_clear_all_steps_confirmed_calls_callback(view: WorkflowListCrudView) -> None:
    """Confirming clear must invoke on_clear_all_steps."""
    cleared: list[bool] = []
    view.on_clear_all_steps = lambda: cleared.append(True)
    with patch("views.workflow_list_crud_view.messagebox.askyesno", return_value=True):
        view._fire_clear_all_steps()
    assert cleared == [True]


def test_fire_clear_all_steps_cancelled_skips_callback(view: WorkflowListCrudView) -> None:
    """Cancelling clear must not invoke on_clear_all_steps."""
    cleared: list[bool] = []
    view.on_clear_all_steps = lambda: cleared.append(True)
    with patch("views.workflow_list_crud_view.messagebox.askyesno", return_value=False):
        view._fire_clear_all_steps()
    assert cleared == []
