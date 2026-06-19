"""Sidebar navigation panel with canvas-based module buttons."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk

from PIL.ImageTk import PhotoImage
from shared.constants import C_COLOR_BLACK_FONT, C_COLOR_BLUE_HIGHLIGHT_DARK, C_COLOR_GRAY_BACKGROUND
from shared.i18n_fra import C_LISTING_MODULES, TitleModuleEnum
from shared.resources_icons_util import get_resource_icon_32px, get_resource_icon_32px_disabled

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# Main view sidebar width in pixels
C_VIEW_SIDEBAR_LEFT_WIDTH = 70

# Canvas geometry: height, icon vertical center, text vertical center
_C_CANVAS_HEIGHT = 70
_C_CANVAS_ICON_OFFSET_TO_TOP = 26
_C_CANVAS_TEXT_OFFSET_TO_TOP = 54

# Canvas-button color constants per state
C_COLOR_SIDEBAR_ACTIVE_BG = C_COLOR_BLUE_HIGHLIGHT_DARK
C_COLOR_SIDEBAR_ACTIVE_FG = "#ffffff"
C_COLOR_SIDEBAR_NORMAL_BG = C_COLOR_GRAY_BACKGROUND
C_COLOR_SIDEBAR_NORMAL_FG = C_COLOR_BLACK_FONT
C_COLOR_SIDEBAR_HOVER_BG = "#d0d0d0"
C_COLOR_SIDEBAR_HOVER_FG = C_COLOR_BLACK_FONT
C_COLOR_SIDEBAR_DISABLED_FG = "#8e8e8e"


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class SideBarView(ttk.Frame):
    """Sidebar navigation panel with canvas-based module buttons.

    Each button is a tk.Canvas drawing a background rect, a 32px icon, and a
    text label. State priority for rendering: disabled > active > hover > normal.
    Notifies the caller via on_select when a non-disabled button is clicked.
    """

    def __init__(self, parent: tk.Widget, on_select: Callable[[TitleModuleEnum], None]) -> None:
        """Initializes the sidebar and builds all canvas navigation buttons.

        Args:
            parent: Parent widget (typically the MainView frame).
            on_select: Callback invoked with the selected module on click.
        """
        super().__init__(parent, width=C_VIEW_SIDEBAR_LEFT_WIDTH)
        self.pack_propagate(False)
        self._on_select = on_select
        self._canvases: dict[TitleModuleEnum, tk.Canvas] = {}
        self._button_states: dict[TitleModuleEnum, str] = {}
        self._image_refs: dict[TitleModuleEnum, tuple[PhotoImage, PhotoImage, PhotoImage]] = {}
        self._active_module: TitleModuleEnum | None = None
        self._hover_module: TitleModuleEnum | None = None
        self._build_canvas_buttons()

    def _build_canvas_buttons(self) -> None:
        """Creates one canvas button per module defined in C_LISTING_MODULES."""
        for module, (display, icon_b, icon_w) in C_LISTING_MODULES.items():
            self._button_states[module] = tk.NORMAL
            self._create_canvas_button(module, display, icon_b, icon_w)

    def _create_canvas_button(self, module: TitleModuleEnum, display: str, icon_b: str, icon_w: str) -> None:
        """Builds one canvas button and registers it for a module.

        Keeps hard references to both icon variants to prevent Tkinter's
        garbage collection from erasing the images after construction.

        Args:
            module: The module this button navigates to.
            display: French label rendered below the icon.
            icon_b: Resource key for the black (inactive) icon variant.
            icon_w: Resource key for the white (active) icon variant.
        """
        imgs = self._load_button_images(icon_b, icon_w)
        self._image_refs[module] = imgs
        canvas = self._make_sidebar_canvas()
        self._draw_sidebar_items(canvas, display, imgs[0])
        self._canvases[module] = canvas
        self._bind_canvas_events(canvas, module)

    @staticmethod
    def _load_button_images(icon_b: str, icon_w: str) -> tuple[PhotoImage, PhotoImage, PhotoImage]:
        """Load the three icon variants (normal, active, disabled) for a button."""
        return (get_resource_icon_32px(icon_b), get_resource_icon_32px(icon_w), get_resource_icon_32px_disabled(icon_b))

    def _make_sidebar_canvas(self) -> tk.Canvas:
        """Create and pack a blank canvas sized for a sidebar button."""
        canvas = tk.Canvas(
            self,
            width=C_VIEW_SIDEBAR_LEFT_WIDTH,
            height=_C_CANVAS_HEIGHT,
            highlightthickness=0,
            bd=0,
            bg=C_COLOR_SIDEBAR_NORMAL_BG,
        )
        canvas.pack(fill=tk.X)
        return canvas

    @staticmethod
    def _draw_sidebar_items(canvas: tk.Canvas, display: str, img_black: object) -> None:
        """Draw the background rect, icon image, and label on a sidebar canvas."""
        # Three tagged items allow itemconfig() to repaint without deleting
        cx = C_VIEW_SIDEBAR_LEFT_WIDTH // 2
        canvas.create_rectangle(
            0,
            0,
            C_VIEW_SIDEBAR_LEFT_WIDTH,
            _C_CANVAS_HEIGHT,
            fill=C_COLOR_SIDEBAR_NORMAL_BG,
            outline="",
            tags="bg_rect",
        )
        canvas.create_image(cx, _C_CANVAS_ICON_OFFSET_TO_TOP, image=img_black, tags="icon")  # type: ignore[reportUnknownMemberType]
        canvas.create_text(
            cx,
            _C_CANVAS_TEXT_OFFSET_TO_TOP,
            text=display,
            fill=C_COLOR_SIDEBAR_NORMAL_FG,
            font=("Segoe UI", 9),
            tags="label",
        )

    def _bind_canvas_events(self, canvas: tk.Canvas, module: TitleModuleEnum) -> None:
        """Attaches click and hover bindings to a canvas button.

        Args:
            canvas: The canvas widget to bind events on.
            module: The module associated with this canvas.
        """
        canvas.bind("<Button-1>", lambda _, m=module: self._on_canvas_click(m))
        canvas.bind("<Enter>", lambda _, m=module: self._on_canvas_enter(m))
        canvas.bind("<Leave>", lambda _, m=module: self._on_canvas_leave(m))

    def _redraw(self, module: TitleModuleEnum) -> None:
        """Repaints a canvas button according to its current state.

        Priority: disabled > active > hover > normal.
        Uses itemconfig() on stable tags — never destroys and recreates items.

        Args:
            module: The module whose canvas should be repainted.
        """
        canvas = self._canvases[module]
        state = self._button_states[module]
        img_black, img_white, img_disabled = self._image_refs[module]

        if state == tk.DISABLED:
            bg, fg, icon = C_COLOR_SIDEBAR_NORMAL_BG, C_COLOR_SIDEBAR_DISABLED_FG, img_disabled
        elif module == self._active_module:
            bg, fg, icon = C_COLOR_SIDEBAR_ACTIVE_BG, C_COLOR_SIDEBAR_ACTIVE_FG, img_white
        elif module == self._hover_module:
            bg, fg, icon = C_COLOR_SIDEBAR_HOVER_BG, C_COLOR_SIDEBAR_HOVER_FG, img_black
        else:
            bg, fg, icon = C_COLOR_SIDEBAR_NORMAL_BG, C_COLOR_SIDEBAR_NORMAL_FG, img_black

        canvas.config(bg=bg)
        canvas.itemconfig("bg_rect", fill=bg)
        canvas.itemconfig("icon", image=icon)
        canvas.itemconfig("label", fill=fg)

    def _on_canvas_click(self, module: TitleModuleEnum) -> None:
        """Fires on_select for the clicked module, skipping disabled buttons.

        Args:
            module: The module that received the click.
        """
        if self._button_states[module] == tk.DISABLED:
            return
        self._on_select(module)

    def _on_canvas_enter(self, module: TitleModuleEnum) -> None:
        """Applies hover highlight when the cursor enters a canvas button.

        Args:
            module: The module being hovered.
        """
        if self._button_states[module] == tk.DISABLED:
            return
        self._hover_module = module
        self._redraw(module)

    def _on_canvas_leave(self, module: TitleModuleEnum) -> None:
        """Restores the resting color when the cursor leaves a canvas button.

        Args:
            module: The module being left.
        """
        if self._button_states[module] == tk.DISABLED:
            return
        self._hover_module = None
        self._redraw(module)

    def set_active(self, module: TitleModuleEnum) -> None:
        """Marks a button as active and resets the previously active one.

        Args:
            module: The module to highlight as active.
        """
        previous = self._active_module
        self._active_module = module

        # Repaint previous button back to normal before highlighting the new one
        if previous is not None and previous != module:
            self._redraw(previous)
        self._redraw(module)

    def set_button_state(self, module: TitleModuleEnum, state: str) -> None:
        """Sets the enabled or disabled state of a sidebar button and repaints it.

        Args:
            module: The module button to update.
            state: tk.NORMAL or tk.DISABLED.
        """
        if module in self._button_states:
            self._button_states[module] = state
            self._redraw(module)

    def get_button_state(self, module: TitleModuleEnum) -> str:
        """Returns the current enabled/disabled state of a sidebar button.

        Args:
            module: The module button to query.

        Returns:
            tk.NORMAL or tk.DISABLED. Falls back to tk.DISABLED for unknown modules.
        """
        return self._button_states.get(module, tk.DISABLED)


# EOF
