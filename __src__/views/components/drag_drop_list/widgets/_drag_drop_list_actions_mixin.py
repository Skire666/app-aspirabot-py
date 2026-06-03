"""Action-dispatch mixin for DragDropList.

Provides the button-dispatch and item-mutation methods that are called when
the user clicks an action button (move up/down, duplicate, delete, toggle).
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import Any, cast

# -----------------------------------------------------------------------------
# Mixin
# -----------------------------------------------------------------------------


class _DragDropListActionsMixin:
    """Provides action-dispatch and item-mutation methods for DragDropList.

    All methods reference attributes that live on the concrete DragDropList
    class (``items``, ``_cbs``, ``canvas``, etc.). Python resolves these
    correctly at runtime through the combined class's MRO.
    """

    # ─── Button dispatch ──────────────────────────────────────────────────────

    def _dispatch_btn(self, idx: int, key: str) -> None:
        """Call the user callback for *key* and apply the resulting mutation.

        Args:
            idx: Zero-based item index.
            key: Button action key.
        """
        cb = cast(Any, self)._cbs.get(key)
        if cb is None:
            return
        result = cb(cast(Any, self).items[idx], idx)
        self._apply_action(key, idx, result)

    def _apply_action(self, key: str, idx: int, result: object) -> None:
        """Route *key* to the correct mutation helper.

        Args:
            key: Button action key.
            idx: Zero-based item index.
            result: Return value from the user callback.
        """
        if self._apply_result_action(key, idx, result):
            return
        self._apply_reorder_action(key, idx, cast(Any, self).items)

    def _apply_result_action(self, key: str, idx: int, result: object) -> bool:
        """Apply duplicate/delete actions that depend on the callback result.

        Args:
            key: Button action key.
            idx: Zero-based item index.
            result: Return value from the user callback.

        Returns:
            True if an action was applied, False otherwise.
        """
        if key == "duplicate" and result is not None:
            self._apply_duplicate(idx, result)
            return True
        if key == "delete" and result:
            self._apply_delete(idx)
            return True
        return False

    def _apply_reorder_action(self, key: str, idx: int, items: list[Any]) -> None:
        """Apply move/toggle actions.

        Args:
            key: Button action key.
            idx: Zero-based item index.
            items: Current item list.
        """
        if key == "move_up" and idx > 0:
            self._apply_move_up(idx)
        elif key == "move_down" and idx < len(items) - 1:
            self._apply_move_down(idx)
        elif key == "toggle_active":
            self._apply_toggle(idx)

    def _apply_delete(self, idx: int) -> None:
        """Remove item at *idx* and refresh the canvas.

        Args:
            idx: Zero-based item index.
        """
        s = cast(Any, self)
        s.items.pop(idx)
        self._notify_reorder()
        s._hovered_btn = None
        s._update_canvas_height()
        s.redraw_visible(force=True) if s._virtualize else s.redraw()

    def _apply_duplicate(self, idx: int, result: object) -> None:
        """Insert a clone after *idx* and refresh the canvas.

        Args:
            idx: Zero-based item index.
            result: Clone returned by the on_duplicate callback.
        """
        s = cast(Any, self)
        s.items.insert(idx + 1, result)
        self._notify_reorder()
        s._hovered_btn = None
        s._update_canvas_height()
        s.redraw_visible(force=True) if s._virtualize else s.redraw()

    def _apply_move_down(self, idx: int) -> None:
        """Move item at *idx* down one position and redraw affected rows.

        Args:
            idx: Zero-based item index.
        """
        s = cast(Any, self)
        s.items.insert(idx + 1, s.items.pop(idx))
        self._notify_reorder()
        s._hovered_btn = None
        s._redraw_item(idx)
        s._redraw_item(idx + 1)

    def _apply_move_up(self, idx: int) -> None:
        """Move item at *idx* up one position and redraw affected rows.

        Args:
            idx: Zero-based item index.
        """
        s = cast(Any, self)
        s.items.insert(idx - 1, s.items.pop(idx))
        self._notify_reorder()
        s._hovered_btn = None
        s._redraw_item(idx)
        s._redraw_item(idx - 1)

    def _apply_toggle(self, idx: int) -> None:
        """Refresh item at *idx* after a toggle-active action.

        The callback is responsible for mutating item.is_active.
        Attempts a zero-allocation color update via update_colors; falls back
        to a full clear-region redraw when the hook is absent or misses cache.

        Args:
            idx: Zero-based item index.
        """
        s = cast(Any, self)
        s._hovered_btn = None
        if not self._try_update_item_colors(idx):
            s._redraw_item(idx)

    def _try_update_item_colors(self, idx: int) -> bool:
        """Attempt a color-only update via the renderer's update_colors hook.

        When the renderer exposes update_colors, reconfigures the item's canvas
        primitives in-place (no delete/create), then redraws only the buttons.

        Args:
            idx: Zero-based item index.

        Returns:
            True when the renderer handled the update; False on cache miss.
        """
        s = cast(Any, self)
        renderer = s._render_item
        if not hasattr(renderer, "update_colors"):
            return False
        updated: bool = bool(renderer.update_colors(s.canvas, s.items[idx], idx, "normal"))
        if updated:
            s.canvas.delete(f"_btns{idx}")
            s._draw_buttons_for(idx)
        return updated

    def _notify_reorder(self) -> None:
        """Fire the on_reorder callback with the current item list."""
        s = cast(Any, self)
        if s._on_reorder:
            s._on_reorder(s.items)


# EOF
