"""ViewModel for the application configuration panel."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from shared.exception_util import CallbackNotDefinedError

from view_models.view_model_base import ViewModelBase

# -----------------------------------------------------------------------------
# Snapshot
# -----------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class AppConfigViewState:
    """Immutable read-only snapshot of the configuration form scalar state.

    Attributes:
        log_level_enum: Currently selected log-level string.
        folder_logs: Path to the logs folder.
        folder_scenarios: Path to the scenarios folder.
        folder_scraping: Path to the scraping output folder.
        gui_booting_size: Window geometry string (e.g. ``"1400x900"``).
        gui_booting_fullscreen: True when the app should start in fullscreen mode.
        browser_engine: Selected browser engine identifier.
    """

    log_level_enum: str
    folder_logs: str
    folder_scenarios: str
    folder_scraping: str
    gui_booting_size: str
    gui_booting_fullscreen: bool
    browser_engine: str


# -----------------------------------------------------------------------------
# ViewModel
# -----------------------------------------------------------------------------


class AppConfigurationViewModel(ViewModelBase):
    """UI state and action hooks for the configuration panel.

    All form fields are held as ``tk.*Var`` instances so the View can bind
    entries and comboboxes directly.  Combo-option lists are paired with
    version IntVars that increment when the options change.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        super().__init__(master)

        # Form field Vars — bound to widgets in the View
        self.log_level_var = tk.StringVar(master=master, value="")
        self.folder_logs_var = tk.StringVar(master=master, value="")
        self.folder_scenarios_var = tk.StringVar(master=master, value="")
        self.folder_scraping_var = tk.StringVar(master=master, value="")
        self.gui_booting_size_var = tk.StringVar(master=master, value="")
        self.gui_booting_fullscreen_var = tk.BooleanVar(master=master, value=False)
        self.browser_engine_var = tk.StringVar(master=master, value="")

        # Combo option lists with version triggers
        self._log_level_options: list[str] = []
        self.log_level_options_version_var = tk.IntVar(master=master, value=0)
        self._browser_engine_options: list[str] = []
        self.browser_engine_options_version_var = tk.IntVar(master=master, value=0)

        # Status Vars — Presenter writes, View traces for button enable/disable
        self.is_cancel_enabled_var = tk.BooleanVar(master=master, value=False)
        self.last_write_time_var = tk.StringVar(master=master, value="Dernière écriture : --")

        # Presenter callback slots
        self._on_save: Callable[[], None] | None = None
        self._on_reset: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_form_changed: Callable[[], None] | None = None
        self._on_ask_reset: Callable[[], bool] | None = None
        self._on_show_error: Callable[[str], None] | None = None

    # ------------------------------------------------------------------
    # Option list accessors
    # ------------------------------------------------------------------

    def get_log_level_options(self) -> list[str]:
        """Return the current list of valid log level values.

        Returns:
            A copy of the internal option list.
        """
        return list(self._log_level_options)

    def set_log_level_options(self, options: list[str]) -> None:
        """Replace the log-level option list and increment the version trigger.

        Args:
            options: New ordered list of log-level choice strings.
        """
        self._log_level_options = list(options)
        self.log_level_options_version_var.set(self.log_level_options_version_var.get() + 1)

    def get_browser_engine_options(self) -> list[str]:
        """Return the current list of valid browser engine values.

        Returns:
            A copy of the internal option list.
        """
        return list(self._browser_engine_options)

    def set_browser_engine_options(self, options: list[str]) -> None:
        """Replace the browser-engine option list and increment the version trigger.

        Args:
            options: New ordered list of browser engine choice strings.
        """
        self._browser_engine_options = list(options)
        self.browser_engine_options_version_var.set(self.browser_engine_options_version_var.get() + 1)

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> AppConfigViewState:
        """Return an immutable copy of the current form scalar state.

        Returns:
            Frozen ``AppConfigViewState`` reflecting current Var values.
        """
        return AppConfigViewState(
            log_level_enum=self.log_level_var.get(),
            folder_logs=self.folder_logs_var.get(),
            folder_scenarios=self.folder_scenarios_var.get(),
            folder_scraping=self.folder_scraping_var.get(),
            gui_booting_size=self.gui_booting_size_var.get(),
            gui_booting_fullscreen=self.gui_booting_fullscreen_var.get(),
            browser_engine=self.browser_engine_var.get(),
        )

    # ------------------------------------------------------------------
    # Form data helpers
    # ------------------------------------------------------------------

    def set_data(self, data: dict[str, Any]) -> None:
        """Write a configuration dict into all form Vars (used by the Presenter on load).

        Args:
            data: Dict with keys matching ``AppConfigurationModel`` fields.
        """

        def _str(key: str) -> str:
            v = data.get(key)
            return "" if v is None else str(v)

        with self.batch_update():
            self.log_level_var.set(_str("log_level_enum"))
            self.folder_logs_var.set(_str("folder_logs"))
            self.folder_scenarios_var.set(_str("folder_scenarios"))
            self.folder_scraping_var.set(_str("folder_scraping"))
            self.gui_booting_size_var.set(_str("gui_booting_size"))
            self.gui_booting_fullscreen_var.set(bool(data.get("gui_booting_fullscreen")))
            self.browser_engine_var.set(_str("browser_engine"))

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_save(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Sauvegarder.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_save is not None:
            raise CallbackNotDefinedError()
        self._on_save = cb

    def bind_reset(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Réinitialiser.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_reset is not None:
            raise CallbackNotDefinedError()
        self._on_reset = cb

    def bind_cancel(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Annuler.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_cancel is not None:
            raise CallbackNotDefinedError()
        self._on_cancel = cb

    def bind_form_changed(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when any form field value changes.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_form_changed is not None:
            raise CallbackNotDefinedError()
        self._on_form_changed = cb

    def bind_ask_reset(self, cb: Callable[[], bool]) -> None:
        """Register the handler that shows a reset-confirmation dialog.

        Args:
            cb: Synchronous callable that returns True when the user confirms.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_ask_reset is not None:
            raise CallbackNotDefinedError()
        self._on_ask_reset = cb

    def bind_show_error(self, cb: Callable[[str], None]) -> None:
        """Register the handler that shows a modal error dialog.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_show_error is not None:
            raise CallbackNotDefinedError()
        self._on_show_error = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Dispatch a save request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_save is None:
            raise CallbackNotDefinedError()
        self._on_save()

    def reset(self) -> None:
        """Dispatch a reset request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_reset is None:
            raise CallbackNotDefinedError()
        self._on_reset()

    def cancel(self) -> None:
        """Dispatch a cancel request.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_cancel is None:
            raise CallbackNotDefinedError()
        self._on_cancel()

    def form_changed(self) -> None:
        """Dispatch a form-changed notification.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_form_changed is None:
            raise CallbackNotDefinedError()
        self._on_form_changed()

    # ------------------------------------------------------------------
    # Presenter-facing helpers (lenient — optional to bind)
    # ------------------------------------------------------------------

    def ask_reset(self) -> bool:
        """Show the reset-confirmation dialog synchronously.

        Returns:
            True when the user confirmed; False otherwise.
        """
        if self._on_ask_reset is not None:
            return self._on_ask_reset()
        return False

    def show_error(self, message: str) -> None:
        """Dispatch an error dialog request.

        Args:
            message: Error message to display.
        """
        if self._on_show_error is not None:
            self._on_show_error(message)


# EOF
