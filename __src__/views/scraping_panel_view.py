"""Tkinter panel for monitoring and reporting a live scraping workflow execution.

This ttk.Frame is placed inside the main content area by the application shell,
exactly like ProviderEditView is placed under the 'Modification' tab.
All UI mutations triggered from a background thread are scheduled via
self.after(0, ...) so Tkinter's event loop applies them on the main thread.

Example:
    >>> panel = ScrapingPanelView(content_area)
    >>> panel.set_on_launch(lambda: print("launch"))
    >>> panel.reset()
"""

## ---------------------------------------------------------------------------
## Imports
## ---------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable
from tkinter import messagebox, ttk

## ---------------------------------------------------------------------------
## Classes
## ---------------------------------------------------------------------------


class ScrapingView(ttk.Frame):
    """Display-only frame for monitoring and reporting a scraping workflow.

    Layout (top to bottom):
      - Action bar: [Lancer] [Annuler] buttons.
      - Provider info section: Nom, URL, ID Fichier, Version.
      - Progress section: current step label and progress bar.
      - Log section: scrollable history of step results.
      - Report section: final summary shown after completion.

    All business logic and service calls must remain in the presenter.

    Example:
        >>> panel = ScrapingPanelView(parent)
        >>> panel.set_on_launch(lambda: None)
        >>> panel.reset()
    """

    def __init__(self, parent: tk.Widget) -> None:
        """Initializes the scraping panel and builds all widgets.

        Args:
            parent: The parent Tkinter widget (e.g. main_view.content_area).
        """
        super().__init__(parent)

        # Callback slots — populated once by the presenter via set_on_*.
        self._on_launch: Callable[[], None] | None = None
        self._on_cancel: Callable[[], None] | None = None
        self._on_pause: Callable[[], None] | None = None
        self._on_resume: Callable[[], None] | None = None

        self._create_widgets()

    def _create_widgets(self) -> None:
        """Builds all UI sections: action bar, provider info, progress, log, and report."""
        self._create_action_bar()
        self._create_provider_info_section()

    def _create_action_bar(self) -> None:
        """Creates the top action bar with Lancer, Annuler, Pause, and Reprendre buttons."""
        bar = ttk.Frame(self, padding=(5, 5))
        bar.pack(side=tk.TOP, fill=tk.X)

        self._btn_launch = ttk.Button(bar, text="Lancer le scraping", command=self._notify_launch)
        self._btn_launch.pack(side=tk.LEFT, padx=5)

        # Annuler is disabled until a workflow is running.
        self._btn_cancel = ttk.Button(bar, text="Annuler", command=self._notify_cancel, state=tk.DISABLED)
        self._btn_cancel.pack(side=tk.LEFT, padx=5)

        # Pause is disabled until a workflow is running.
        self._btn_pause = ttk.Button(bar, text="Pause", command=self._notify_pause, state=tk.DISABLED)
        self._btn_pause.pack(side=tk.LEFT, padx=5)

        # Reprendre is disabled until the workflow is paused.
        self._btn_resume = ttk.Button(bar, text="Reprendre", command=self._notify_resume, state=tk.DISABLED)
        self._btn_resume.pack(side=tk.LEFT, padx=5)

    def _create_provider_info_section(self) -> None:
        """Creates the provider summary block displayed below the action bar."""
        section = ttk.LabelFrame(self, text="Fournisseur sélectionné", padding=(5, 5))
        section.pack(side=tk.TOP, fill=tk.X, padx=5, pady=(0, 5))

        # Each field is a (label, var) pair packed left to right in a single row.
        fields = [
            ("Nom :", "_var_provider_name"),
            ("ID Fichier :", "_var_provider_id"),
            ("Version :", "_var_provider_version"),
            ("URL :", "_var_provider_url"),
        ]
        for label_text, var_attr in fields:
            var = tk.StringVar(value="—")
            setattr(self, var_attr, var)
            ttk.Label(section, text=label_text).pack(side=tk.LEFT, padx=(8, 2))
            ttk.Label(section, textvariable=var).pack(side=tk.LEFT, padx=(0, 8))

    # ------------------------------------------------------------------
    # Callback registration (called once by the presenter)
    # ------------------------------------------------------------------

    def set_on_launch(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Lancer.

        Args:
            callback: Zero-argument callable that starts the workflow.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_launch = callback

    def set_on_cancel(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Annuler.

        Args:
            callback: Zero-argument callable that signals cancellation.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_cancel = callback

    def set_on_pause(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Pause.

        Args:
            callback: Zero-argument callable that pauses the workflow.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_pause = callback

    def set_on_resume(self, callback: Callable[[], None]) -> None:
        """Registers the callback fired when the user clicks Reprendre.

        Args:
            callback: Zero-argument callable that resumes the workflow.

        Returns:
            None.

        Raises:
            None.
        """
        self._on_resume = callback

    def set_provider_info(
        self,
        name: str,
        url: str,
        id_file: str,
        version: str,
    ) -> None:
        """Populates the provider summary section with the given values.

        Must be called from the main thread (invoked by load_provider before
        the workflow starts, not from a background thread).

        Args:
            name: Provider display name.
            url: Provider root URL.
            id_file: Provider unique file identifier.
            version: Provider version string.

        Returns:
            None.

        Raises:
            None.
        """
        self._var_provider_name.set(name)
        self._var_provider_url.set(url)
        self._var_provider_id.set(id_file)
        self._var_provider_version.set(version)

    # ------------------------------------------------------------------
    # Public state management (called by the presenter from main thread)
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Resets all UI elements to their initial idle state for a new run.

        Must be called from the main thread. Used by the presenter each time
        a new provider is loaded via load_provider().

        Returns:
            None.

        Raises:
            None.

        Example:
            >>> panel.reset()
        """
        # Clear the provider summary fields.
        for var in (
            self._var_provider_name,
            self._var_provider_url,
            self._var_provider_id,
            self._var_provider_version,
        ):
            var.set("—")

        # Restore all buttons to idle state.
        self._btn_launch.config(state=tk.NORMAL)
        self._btn_cancel.config(state=tk.DISABLED)
        self._btn_pause.config(state=tk.DISABLED)
        self._btn_resume.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Public render interface (called by the presenter, thread-safe)
    # ------------------------------------------------------------------

    def set_paused_state(self, paused: bool) -> None:
        """Toggles Pause/Reprendre buttons to match whether the workflow is paused.

        Safe to call from a background thread — the update is deferred to the
        main thread via self.after(0, ...).

        Args:
            paused: True while the workflow is paused; False when running.

        Returns:
            None.

        Raises:
            None.
        """
        self.after(0, lambda: self._apply_paused_state(paused))

    def _apply_paused_state(self, paused: bool) -> None:
        """Applies Pause/Reprendre button states on the main thread.

        Args:
            paused: True to show paused state; False to restore running state.
        """
        pause_state = tk.DISABLED if paused else tk.NORMAL
        resume_state = tk.NORMAL if paused else tk.DISABLED

        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=resume_state)

    def set_running_state(self, running: bool) -> None:
        """Toggles button states to match whether a workflow is in progress.

        Safe to call from a background thread — the state change is deferred to
        the main thread via self.after(0, ...).

        Args:
            running: True while the workflow is running; False when idle.

        Returns:
            None.

        Raises:
            None.
        """
        self.after(0, lambda: self._apply_running_state(running))

    def _apply_running_state(self, running: bool) -> None:
        """Applies button enable/disable state on the main thread.

        Args:
            running: True to show running state; False to restore idle state.
        """
        launch_state = tk.DISABLED if running else tk.NORMAL
        cancel_state = tk.NORMAL if running else tk.DISABLED
        pause_state = tk.NORMAL if running else tk.DISABLED

        self._btn_launch.config(state=launch_state)
        self._btn_cancel.config(state=cancel_state)
        # Pause activates when running starts; Reprendre always resets to DISABLED.
        self._btn_pause.config(state=pause_state)
        self._btn_resume.config(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Internal notification helpers
    # ------------------------------------------------------------------

    def _notify_launch(self) -> None:
        """Fires the on_launch callback when the Lancer button is clicked."""
        if self._on_launch:
            self._on_launch()

    def _notify_cancel(self) -> None:
        """Fires the on_cancel callback when the Annuler button is clicked."""
        if self._on_cancel:
            self._on_cancel()

    def _notify_pause(self) -> None:
        """Fires the on_pause callback when the Pause button is clicked."""
        if self._on_pause:
            self._on_pause()

    def _notify_resume(self) -> None:
        """Fires the on_resume callback when the Reprendre button is clicked."""
        if self._on_resume:
            self._on_resume()

    def show_warning(self, message: str) -> None:
        """Shows a warning message box.

        Args:
            message: The message to be displayed.
        """
        messagebox.showwarning("Avertissement", message)
