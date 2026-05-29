"""ViewModel for the debug browser inspection popup window."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DebugPageViewModel:
    """UI state and action hooks for the debug-page inspection Toplevel.

    Holds the three display Vars (raw HTML, text results, image results) and an
    ``is_alive_var`` that the View traces to destroy itself when set to False.
    The ``after`` method proxies Tkinter scheduling so the Presenter never
    needs to import ``tkinter``.
    """

    def __init__(self, master: tk.Misc, url: str) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope Var lifetimes and ``after()`` calls.
            url: URL currently loaded in the browser (display only — window title).
        """
        self._master = master
        self._url = url

        # Content Vars — Presenter writes, View traces and renders.
        self.html_content_var = tk.StringVar(master=master, value="")
        self.text_results_var = tk.StringVar(master=master, value="")
        self.image_results_var = tk.StringVar(master=master, value="")

        # Lifecycle Var — set to False by the Presenter to force-close the window.
        self.is_alive_var = tk.BooleanVar(master=master, value=True)

        # Registered Presenter callbacks
        self._on_refresh: Callable[[], None] | None = None
        self._on_analyze_texts: Callable[[str], None] | None = None
        self._on_analyze_images: Callable[[str], None] | None = None
        self._on_close: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Read-only accessor
    # ------------------------------------------------------------------

    @property
    def url(self) -> str:
        """URL currently shown in the debug window (for the Toplevel title)."""
        return self._url

    # ------------------------------------------------------------------
    # Threading proxy
    # ------------------------------------------------------------------

    def after(self, delay_ms: int, callback: Callable[[], None]) -> None:
        """Schedule a callback on the main Tkinter thread.

        Args:
            delay_ms: Delay in milliseconds before the callback fires.
            callback: Zero-argument callable to schedule.
        """
        self._master.after(delay_ms, callback)

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_refresh(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Rafraîchir."""
        self._on_refresh = cb

    def bind_analyze_texts(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user requests text analysis."""
        self._on_analyze_texts = cb

    def bind_analyze_images(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user requests image analysis."""
        self._on_analyze_images = cb

    def bind_close(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user closes the window."""
        self._on_close = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def refresh(self) -> None:
        """Dispatch a refresh request to the Presenter."""
        if self._on_refresh is not None:
            self._on_refresh()

    def analyze_texts(self, selector: str) -> None:
        """Dispatch a text-analysis request with the CSS selector.

        Args:
            selector: CSS selector entered by the user.
        """
        if self._on_analyze_texts is not None:
            self._on_analyze_texts(selector)

    def analyze_images(self, selector: str) -> None:
        """Dispatch an image-analysis request with the CSS selector.

        Args:
            selector: CSS selector entered by the user.
        """
        if self._on_analyze_images is not None:
            self._on_analyze_images(selector)

    def close(self) -> None:
        """Dispatch a user-initiated close request to the Presenter."""
        if self._on_close is not None:
            self._on_close()


# EOF
