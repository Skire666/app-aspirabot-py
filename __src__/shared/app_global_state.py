"""Application-wide singleton with navigation helpers, dialogs, and widget extensions."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import contextlib
import logging
import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, simpledialog, ttk
from typing import Any

from models.app_configuration_model import AppConfigurationModel
from repositories.app_configuration_repository import AppConfigurationRepository
from shared.enums import TitleModuleEnum

_logger = logging.getLogger(__name__)
_C_GEO_SPLIT_PARTS = 3  # "WxH+X+Y".split("+") must yield exactly 3 parts

# ---------------------------------------------------------------------------
# tk.Widget pack helpers
# ---------------------------------------------------------------------------


class PackMixin:
    """Mixin that adds pack_left() and pack_right() convenience methods to any tk.Widget subclass."""

    def pack_left(self: tk.Widget, **kwargs: Any) -> None:  # pyright: ignore[reportGeneralTypeIssues]
        """Pack this widget to the left with standard horizontal padding."""
        self.pack(side=tk.LEFT, padx=(0, 6), pady=4, **kwargs)

    def pack_right(self: tk.Widget, **kwargs: Any) -> None:  # pyright: ignore[reportGeneralTypeIssues]
        """Pack this widget to the right with standard horizontal padding."""
        self.pack(side=tk.RIGHT, padx=(0, 6), pady=4, **kwargs)


class MyButton(ttk.Button):
    """ttk.Button with pack_left() and pack_right() helpers."""

    def pack_left(self: tk.Widget, **kwargs: Any) -> None:
        """Pack this button to the left with reduced vertical padding."""
        self.pack(side=tk.LEFT, padx=(0, 6), pady=2, **kwargs)

    def pack_right(self: tk.Widget, **kwargs: Any) -> None:
        """Pack this button to the right with reduced vertical padding."""
        self.pack(side=tk.RIGHT, padx=(0, 6), pady=2, **kwargs)


class MyLabel(PackMixin, ttk.Label):
    """ttk.Label with pack_left() and pack_right() helpers."""


class MyEntry(PackMixin, ttk.Entry):
    """ttk.Entry with pack_left() and pack_right() helpers."""


class MyCombobox(PackMixin, ttk.Combobox):
    """ttk.Combobox with pack_left() and pack_right() helpers."""


class MyListbox(PackMixin, tk.Listbox):
    """tk.Listbox with pack_left() and pack_right() helpers."""


class MyRadioButton(PackMixin, ttk.Radiobutton):
    """ttk.Radiobutton with pack_left() and pack_right() helpers."""


# ---------------------------------------------------------------------------
# AppGlobalState
# ---------------------------------------------------------------------------


_ShowViewFn = Callable[[TitleModuleEnum], None]
_SetTabStateFn = Callable[[TitleModuleEnum, str], None]


class AppGlobalState:
    """Singleton holding the root window and the navigation shell.

    Usage:
        # In main.py, after MainView is built:
        app_state.setup(root, main_view.show_view, main_view.set_tab_state)

        # Anywhere else:
        from shared.app_global_state import app_state
        app_state.show_module(TitleModuleEnum.E_EXECUTOR)
        answer = app_state.ask("Titre", "Entrez une valeur :")
    """

    _instance: AppGlobalState | None = None

    def __new__(cls) -> AppGlobalState:
        """Return the unique instance, creating it on first call."""
        if cls._instance is None:
            inst = super().__new__(cls)
            inst._root = None
            inst._show_view_fn = None
            inst._set_tab_state_fn = None
            cls._instance = inst
        return cls._instance

    # ------------------------------------------------------------------
    # Bootstrap (called once from main.py after MainView is built)
    # ------------------------------------------------------------------

    def setup(self, root: tk.Tk, show_view: _ShowViewFn, set_tab_state: _SetTabStateFn) -> None:
        """Wire the singleton to the live root window and navigation shell."""
        self._root = root
        self._show_view_fn = show_view
        self._set_tab_state_fn = set_tab_state

    # ------------------------------------------------------------------
    # Startup helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_global_styles() -> None:
        """Configure global ttk widget styles."""
        ttk.Style().configure("TButton", padding=(4, 4))

    def override_gui_and_style(self) -> None:
        """Apply window title, geometry, fullscreen state, and global widget style."""
        root = self._root
        config_model = AppConfigurationModel.get_instance()
        root.title("Aspirabot")
        position = config_model.gui_booting_position
        if position:
            try:
                x, y = position.split(",", 1)
                root.geometry(f"{config_model.gui_booting_size}+{int(x)}+{int(y)}")
            except Exception:  # noqa: BLE001
                root.geometry(config_model.gui_booting_size)
        else:
            root.geometry(config_model.gui_booting_size)
        if config_model.gui_booting_fullscreen:
            root.after(15, lambda: root.state("zoomed"))

        # apply global widget styles
        self._apply_global_styles()

    @staticmethod
    def _persist_geometry(root: tk.Tk, config_repo: AppConfigurationRepository) -> None:
        """Write current window geometry to config, ignoring errors gracefully."""
        try:
            state_rt = root.state()
            if state_rt in {"iconic", "withdrawn"}:
                return
            parts = root.geometry().split("+")  # "WxH+X+Y" → ["WxH", "X", "Y"]
            if len(parts) != _C_GEO_SPLIT_PARTS:
                return
            config_repo.read_configuration()
            config = AppConfigurationModel.get_instance()
            config.gui_booting_size = parts[0]
            config.gui_booting_position = f"{parts[1]},{parts[2]}"
            config.gui_booting_fullscreen = state_rt == "zoomed"
            config_repo.write_configuration()
        except tk.TclError:
            pass
        except Exception:
            _logger.exception("Erreur lors de la sauvegarde de la géométrie")

    def wire_geometry_persistence(self, config_repo: AppConfigurationRepository) -> None:
        """Poll window geometry every 200 ms and persist it debounced (500 ms).

        Uses polling rather than <Configure> binding, which is unreliable for
        move events on Windows multi-monitor setups.
        """
        root = self._root
        pending: list[str | None] = [None]
        last_geo: list[str] = [""]

        def _save() -> None:
            pending[0] = None
            self._persist_geometry(root, config_repo)

        def _poll() -> None:
            try:
                if root.state() not in {"iconic", "withdrawn"}:
                    geo = root.geometry()
                    if geo != last_geo[0]:
                        last_geo[0] = geo
                        if pending[0] is not None:
                            with contextlib.suppress(tk.TclError):
                                root.after_cancel(pending[0])
                        pending[0] = root.after(400, _save)
            except tk.TclError:
                return  # fenêtre en cours de destruction — arrêt du poll
            root.after(200, _poll)

        root.after(200, _poll)
        root._force_save_geometry = _save  # type: ignore[attr-defined]

    # ------------------------------------------------------------------
    # Module navigation
    # ------------------------------------------------------------------

    def show_module(self, module: TitleModuleEnum) -> None:
        """Reveal *module* in the main content area."""
        if self._show_view_fn is not None:
            self._show_view_fn(module)

    def set_module_state(self, module: TitleModuleEnum, state: str) -> None:
        """Enable (tk.NORMAL) or disable (tk.DISABLED) a sidebar tab."""
        if self._set_tab_state_fn is not None:
            self._set_tab_state_fn(module, state)

    def select_module(
        self,
        module: TitleModuleEnum,
        *,
        enable: tuple[TitleModuleEnum, ...] = (),
        disable: tuple[TitleModuleEnum, ...] = (),
    ) -> None:
        """Show *module* and batch-update sibling tab states in one call.

        Example — open the workflow tab while locking everything else::

            app_state.select_module(
                TitleModuleEnum.E_WORKFLOW,
                disable=(E_SCENARIOS, E_PROFILES, E_EXECUTOR, E_SCRAPING),
            )
        """
        for mod in enable:
            self.set_module_state(mod, tk.NORMAL)
        for mod in disable:
            self.set_module_state(mod, tk.DISABLED)
        self.show_module(module)

    def open_workflow_tab(self) -> None:
        """Enable the workflow tab and disable all sibling tabs."""
        self.set_module_state(TitleModuleEnum.E_WORKFLOW, tk.NORMAL)
        for mod in (
            TitleModuleEnum.E_SCENARIOS,
            TitleModuleEnum.E_PROFILES,
            TitleModuleEnum.E_EXECUTOR,
            TitleModuleEnum.E_SCRAPING,
        ):
            self.set_module_state(mod, tk.DISABLED)
        self.show_module(TitleModuleEnum.E_WORKFLOW)

    def close_workflow_tab(self) -> None:
        """Disable the workflow tab and re-enable sibling tabs."""
        self.set_module_state(TitleModuleEnum.E_WORKFLOW, tk.DISABLED)
        for mod in (
            TitleModuleEnum.E_SCENARIOS,
            TitleModuleEnum.E_PROFILES,
            TitleModuleEnum.E_EXECUTOR,
            TitleModuleEnum.E_SCRAPING,
        ):
            self.set_module_state(mod, tk.NORMAL)
        self.show_module(TitleModuleEnum.E_SCENARIOS)

    # ------------------------------------------------------------------
    # User dialogs
    # ------------------------------------------------------------------

    def ask(self, title: str, prompt: str, **kwargs: Any) -> str | None:
        """Open a text-input dialog; returns the entered string or None on cancel."""
        return simpledialog.askstring(title, prompt, parent=self._root, **kwargs)

    def ask_integer(self, title: str, prompt: str, **kwargs: Any) -> int | None:
        """Open an integer-input dialog."""
        return simpledialog.askinteger(title, prompt, parent=self._root, **kwargs)

    def ask_yes_no(self, title: str, message: str) -> bool:
        """Open a yes/no confirmation dialog."""
        return messagebox.askyesno(title, message, parent=self._root)

    def ask_ok_cancel(self, title: str, message: str) -> bool:
        """Open an ok/cancel confirmation dialog."""
        return messagebox.askokcancel(title, message, parent=self._root)

    # ------------------------------------------------------------------
    # Accessor
    # ------------------------------------------------------------------

    @property
    def root(self) -> tk.Tk | None:
        """The root Tk window."""
        return self._root


# Module-level singleton — importez directement `app_state` dans le reste du code.
app_state = AppGlobalState()


# EOF
