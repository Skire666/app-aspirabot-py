"""ViewModel for the debug browser module — launcher panel and inspection Toplevel.

Holds launcher state (user inputs, validation errors) and page inspection state
(HTML content, text/image analysis results, session lifecycle).

The Presenter binds all callbacks once at composition time.  ``reset_page()``
clears page Vars and marks the session alive before each new browser session.
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import tkinter as tk
from collections.abc import Callable

from shared.enums import ExtractTextHtmlEnum
from shared.exception_util import CallbackNotDefinedError

from view_models.view_model_base import ViewModelBase

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class DebugViewModel(ViewModelBase):
    """Merged ViewModel for the Debug tab panel and the inspection Toplevel.

    Launcher Vars (``error_message_var``) are persistent for the app lifetime.
    Page Vars (``html_content_var``, ``text_results_var``, ``image_results_var``,
    ``is_alive_var``, ``url_var``) are reset by ``reset_page()`` at the start
    of each new session.
    """

    def __init__(self, master: tk.Misc) -> None:
        """Initialise all Vars and register bind slots.

        Args:
            master: Tkinter parent used to scope all Var lifetimes.
        """
        super().__init__(master)

        # Launcher Var — Presenter writes on invalid input, View binds via textvariable=
        self.error_message_var = tk.StringVar(master=master, value="")

        # Page Vars — reset by reset_page() before every new browser session
        self.url_var = tk.StringVar(master=master, value="")
        self.html_content_var = tk.StringVar(master=master, value="")
        self.text_results_var = tk.StringVar(master=master, value="")
        self.image_results_var = tk.StringVar(master=master, value="")

        # Lifecycle Var — True while a session Toplevel is open; View traces to auto-destroy
        self.is_alive_var = tk.BooleanVar(master=master, value=False)

        # Presenter callback slots
        self._on_start: Callable[[str, str, str, str], None] | None = None
        self._on_open_debug_page: Callable[[], None] | None = None
        self._on_refresh: Callable[[], None] | None = None
        self._on_analyze_texts: Callable[[str], None] | None = None
        self._on_analyze_images: Callable[[str], None] | None = None
        self._on_close: Callable[[], None] | None = None

    # ------------------------------------------------------------------
    # Read-only accessors
    # ------------------------------------------------------------------

    @property
    def master(self) -> tk.Misc:
        """Tkinter master widget, usable as parent for child Toplevels."""
        return self._master

    @property
    def url(self) -> str:
        """URL of the active session (for the Toplevel title)."""
        return self.url_var.get()

    # ------------------------------------------------------------------
    # Session reset
    # ------------------------------------------------------------------

    def reset_page(self, url: str) -> None:
        """Prepare the VM for a new session by resetting all page Vars.

        Call this before ``open_debug_page()`` to clear stale content and mark
        the session as alive so the Toplevel's lifecycle trace fires correctly.

        Args:
            url: URL being opened in the new browser session.
        """
        self.url_var.set(url)
        self.html_content_var.set("")
        self.text_results_var.set("")
        self.image_results_var.set("")
        self.is_alive_var.set(True)

    # ------------------------------------------------------------------
    # Presenter binding hooks
    # ------------------------------------------------------------------

    def bind_start(self, cb: Callable[[str, str, str, str], None]) -> None:
        """Register the handler invoked when the user clicks Lancer.

        Args:
            cb: Called with (url, timeout_raw, dns_delay_raw, wait_until_raw) as raw widget strings.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_start is not None:
            raise CallbackNotDefinedError()
        self._on_start = cb

    def bind_open_debug_page(self, cb: Callable[[], None]) -> None:
        """Register the View factory that opens the inspection Toplevel.

        The View registers this so it can instantiate DebugPageView bound to
        this VM without the Presenter ever importing a View class.

        Args:
            cb: Zero-argument callable that creates and shows the Toplevel.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_open_debug_page is not None:
            raise CallbackNotDefinedError()
        self._on_open_debug_page = cb

    def bind_refresh(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user clicks Rafraîchir.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_refresh is not None:
            raise CallbackNotDefinedError()
        self._on_refresh = cb

    def bind_analyze_texts(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user requests text analysis.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_analyze_texts is not None:
            raise CallbackNotDefinedError()
        self._on_analyze_texts = cb

    def bind_analyze_images(self, cb: Callable[[str], None]) -> None:
        """Register the handler invoked when the user requests image analysis.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_analyze_images is not None:
            raise CallbackNotDefinedError()
        self._on_analyze_images = cb

    def bind_close(self, cb: Callable[[], None]) -> None:
        """Register the handler invoked when the user closes the inspection window.

        Raises:
            AspirabotBaseError: If the hook is already bound.
        """
        if self._on_close is not None:
            raise CallbackNotDefinedError()
        self._on_close = cb

    # ------------------------------------------------------------------
    # Action methods — called by the View
    # ------------------------------------------------------------------

    def start(self, url: str, timeout_raw: str, dns_delay_raw: str, wait_until_raw: str) -> None:
        """Dispatch a start-session request with raw widget values for the Presenter.

        Args:
            url: The URL string from the entry widget.
            timeout_raw: Raw spinbox string for the navigation timeout.
            dns_delay_raw: Raw spinbox string for the DNS-resolution wait.
            wait_until_raw: Raw combobox string for the page-state condition.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_start is None:
            raise CallbackNotDefinedError()
        self._on_start(url, timeout_raw, dns_delay_raw, wait_until_raw)

    def open_debug_page(self) -> None:
        """Ask the View to open the inspection Toplevel bound to this VM.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_open_debug_page is None:
            raise CallbackNotDefinedError()
        self._on_open_debug_page()

    def refresh(self) -> None:
        """Dispatch a page-refresh request to the Presenter.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_refresh is None:
            raise CallbackNotDefinedError()
        self._on_refresh()

    def analyze_texts(self, selector: str) -> None:
        """Dispatch a text-analysis request with the given CSS selector.

        Args:
            selector: CSS selector entered by the user.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_analyze_texts is None:
            raise CallbackNotDefinedError()
        self._on_analyze_texts(selector)

    def analyze_images(self, selector: str) -> None:
        """Dispatch an image-analysis request with the given CSS selector.

        Args:
            selector: CSS selector targeting image elements.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_analyze_images is None:
            raise CallbackNotDefinedError()
        self._on_analyze_images(selector)

    def close(self) -> None:
        """Dispatch a user-initiated window-close request to the Presenter.

        Raises:
            AspirabotBaseError: If the hook is not bound.
        """
        if self._on_close is None:
            raise CallbackNotDefinedError()
        self._on_close()

    # ------------------------------------------------------------------
    # Result formatters (pure, no Playwright or UI calls)
    # ------------------------------------------------------------------

    @staticmethod
    def format_text_results(selector: str, results: list[dict[str, object]]) -> str:
        """Format text analysis results into a human-readable string.

        Args:
            selector: The CSS selector that was queried.
            results: List of dicts from DebugBrowserService.analyze_texts().

        Returns:
            Multi-line formatted string ready for display.
        """
        if not results:
            return f"Sélecteur : {selector!r}\nAucun élément trouvé."

        lines: list[str] = [f"Sélecteur : {selector!r}", f"Nombre total : {len(results)}", ""]
        for i, el in enumerate(results, 1):
            str_inner_txt = str(el.get(ExtractTextHtmlEnum.E_INNER_TEXT.value, "")).strip()
            str_txt_content = str(el.get(ExtractTextHtmlEnum.E_TEXT_CONTENT.value, "")).strip()
            str_inner_html = str(el.get(ExtractTextHtmlEnum.E_INNER_HTML.value, "")).strip()
            str_outer_html = str(el.get(ExtractTextHtmlEnum.E_OUTER_HTML.value, "")).strip()
            str_input_val = str(el.get(ExtractTextHtmlEnum.E_INPUT_VALUE.value, "")).strip()
            lines += [
                f"[{i}]",
                f"   innerText x{len(str_inner_txt)} \t : {str_inner_txt}",
                f"   textContent x{len(str_txt_content)} \t : {str_txt_content}",
                f"   innerHTML x{len(str_inner_html)} \t : {str_inner_html}",
                f"   outerHTML x{len(str_outer_html)} \t : {str_outer_html}",
                f"   value x{len(str_input_val)} \t : {str_input_val}",
                "",
            ]
        return "\n".join(lines)

    @staticmethod
    def format_image_results(selector: str, results: list[dict[str, object]]) -> str:
        """Format image analysis results into a human-readable string.

        Args:
            selector: The CSS selector used for the query.
            results: List of dicts from DebugBrowserService.analyze_images().

        Returns:
            Multi-line formatted string ready for display.
        """
        if not results:
            return f"Sélecteur : {selector!r}\nAucune image trouvée."

        lines: list[str] = [f"Sélecteur : {selector!r}", f"Nombre total : {len(results)}", ""]
        for i, img in enumerate(results, 1):
            lines += [
                f"[{i}]",
                f"  src             : {img.get('src', '')}",
                f"  alt             : {img.get('alt', '')}",
                f"  Taille réelle   : {img.get('naturalWidth', 0)} x {img.get('naturalHeight', 0)} px",
                f"  Taille affichée : {img.get('clientWidth', 0)} x {img.get('clientHeight', 0)} px",
                f"  Extension       : {img.get('ext', '')}",
                "",
            ]
        return "\n".join(lines)


# EOF
