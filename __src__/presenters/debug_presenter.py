"""Presenter for the Debug sidebar module.

Owns the entire debug browser session lifecycle: launches a persistent
BrowserPlaywrightService worker thread, routes all Playwright calls through
a task queue so they stay in the same thread, and updates DebugViewModel
Vars via after(0, callback).

All page-inspection callbacks (refresh, analyze, close) are bound once at
construction time; no per-session ViewModel is created.

Example:
    >>> presenter = DebugPresenter(vm=debug_vm, debug_service=svc)
"""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import contextlib
import logging
import queue
import threading
from collections.abc import Callable

from models.app_configuration_model import AppConfigurationModel
from playwright.sync_api import Page
from services.browser_playwright_service import BrowserPlaywrightService
from services.debug_browser_service import DebugBrowserService
from shared.enums import ExtractTextHtmlEnum
from shared.exception_util import AspirabotBaseError
from shared.i18n_fra import C_DEBUG_DNS_DELAY_INVALID, C_DEBUG_TIMEOUT_INVALID, C_DEBUG_URL_EMPTY
from view_models.debug_view_model import DebugViewModel

# -----------------------------------------------------------------------------
# Module-level helpers
# -----------------------------------------------------------------------------

_DEBUG_SPIN_MIN: int = 1
_DEBUG_SPIN_MAX: int = 30


def _is_valid_spin_int(value: str) -> bool:
    """Return True when *value* parses as an integer within the spinbox range.

    Args:
        value: Raw string from a debug-session spinbox widget.

    Returns:
        True if the value is a valid bounded integer, False otherwise.
    """
    try:
        n = int(value)
        return _DEBUG_SPIN_MIN <= n <= _DEBUG_SPIN_MAX
    except ValueError:
        return False


# -----------------------------------------------------------------------------
# Classes
# -----------------------------------------------------------------------------


class DebugPresenter:
    """Orchestrates the debug browser session from the Debug sidebar module.

    Responsibilities:
    - Binds all DebugViewModel callbacks once at construction time.
    - Manages a single persistent browser worker thread per session.
    - Routes all Playwright API calls through a queue to that thread.
    - Updates DebugViewModel Vars on the main thread via after().
    """

    def __init__(
        self, vm: DebugViewModel, debug_service: DebugBrowserService, config_model: AppConfigurationModel
    ) -> None:
        """Initialises the presenter and binds all ViewModel callbacks.

        Args:
            vm: The merged DebugViewModel for the debug module.
            debug_service: Service providing DOM inspection utilities.
            config_model: Application configuration supplying Chromium paths.
        """
        self._logger = logging.getLogger(__name__)
        self._vm = vm
        self._config_model = config_model
        self._debug_browser: BrowserPlaywrightService | None = None
        self._debug_service: DebugBrowserService = debug_service
        self._debug_queue: queue.Queue[Callable[[Page], None] | None] = queue.Queue()
        self._debug_thread: threading.Thread | None = None

        # Bind all callbacks once — no per-session rebinding needed.
        vm.bind_start(self._on_debug_start)
        vm.bind_refresh(self._on_debug_refresh)
        vm.bind_analyze_texts(self._on_debug_analyze_texts)
        vm.bind_analyze_images(self._on_debug_analyze_images)
        vm.bind_close(self._on_debug_close)

    # -----------------------------------------------------------------------
    # Input validation
    # -----------------------------------------------------------------------

    def _validate_debug_inputs(self, url: str, timeout_raw: str, dns_delay_raw: str) -> list[str]:
        """Collect validation errors for the debug session inputs.

        Args:
            url: URL string entered by the user.
            timeout_raw: Raw spinbox string for the navigation timeout.
            dns_delay_raw: Raw spinbox string for the DNS-resolution wait.

        Returns:
            Ordered list of French error strings; empty when all inputs are valid.
        """
        errors: list[str] = []
        if not url or url == "https://":
            errors.append(C_DEBUG_URL_EMPTY)
        if not _is_valid_spin_int(timeout_raw):
            errors.append(C_DEBUG_TIMEOUT_INVALID)
        if not _is_valid_spin_int(dns_delay_raw):
            errors.append(C_DEBUG_DNS_DELAY_INVALID)
        return errors

    # -----------------------------------------------------------------------
    # Debug session — entry point
    # -----------------------------------------------------------------------

    def _on_debug_start(self, url: str, timeout_raw: str, dns_delay_raw: str) -> None:
        """Validates inputs then opens a debug browser session.

        Sets vm.error_message_var and returns early on invalid inputs.
        Resets page Vars, opens the inspection Toplevel, and starts the worker.

        Args:
            url: The URL to open in the debug browser.
            timeout_raw: Raw spinbox string for the navigation timeout (1-30 s).
            dns_delay_raw: Raw spinbox string for the DNS-resolution wait (1-30 s).
        """
        errors = self._validate_debug_inputs(url, timeout_raw, dns_delay_raw)
        if errors:
            self._vm.error_message_var.set("  |  ".join(errors))
            return
        self._vm.error_message_var.set("")
        timeout = int(timeout_raw)
        dns_delay = int(dns_delay_raw)

        self._close_debug_session()
        # Fresh queue — old worker reads None from its own (now unreferenced) queue.
        self._debug_queue = queue.Queue()
        self._debug_browser = BrowserPlaywrightService(
            chromium_persistant_dir=self._config_model.chromium_persistant_dir,
            chromium_extensions_dir=self._config_model.chromium_extensions_dir,
        )

        # Reset page Vars and open the inspection.
        self._vm.reset_page(url)
        self._vm.html_content_var.set("Chargement en cours…")
        self._vm.open_debug_page()

        self._debug_thread = threading.Thread(target=self._browser_worker, args=(url, timeout, dns_delay), daemon=True)
        self._debug_thread.start()

    def _close_debug_session(self) -> None:
        """Force-closes the inspection window and stops the browser worker."""
        # Setting is_alive_var to False triggers DebugPageView._sync_alive → destroy().
        with contextlib.suppress(Exception):
            self._vm.is_alive_var.set(False)
        # Sentinel None causes the worker loop to exit and close the browser.
        self._debug_queue.put(None)

    # -----------------------------------------------------------------------
    # Browser worker (long-lived thread)
    # -----------------------------------------------------------------------

    def _browser_worker(self, url: str, timeout: int, dns_delay: int) -> None:
        """Long-lived browser thread — the only thread that calls Playwright.

        Launches the browser, navigates to url, pushes the initial HTML, then
        processes Callable tasks from _debug_queue until a None sentinel arrives.
        The browser is always closed in the finally block.

        Args:
            url: The URL to navigate to on startup.
            timeout: Navigation timeout in seconds (converted to ms internally).
            dns_delay: DNS resolution wait passed to safe_goto_url.
        """
        try:
            self._debug_browser.launch()
            self._debug_browser.append_new_page()
            self._debug_browser.safe_goto_url(
                url, wait_state="networkidle", timeout_ms=timeout * 1000, wait_dns_solver_sec=dns_delay
            )
            page = self._debug_browser.get_current_page()
            html = self._debug_service.get_html_content(page)
            self._push_html(html)
            while True:
                task = self._debug_queue.get()
                if task is None:
                    break
                task(page)
        except AspirabotBaseError as exc:
            self._logger.exception("Échec du démarrage du worker navigateur")
            self._push_html(f"Erreur lors du chargement :\n{exc}")
        finally:
            with contextlib.suppress(Exception):
                self._debug_browser.close_browser()

    # -----------------------------------------------------------------------
    # Thread-safe ViewModel update helpers
    # -----------------------------------------------------------------------

    def _push_html(self, html: str) -> None:
        """Schedule an html_content_var update on the main thread.

        Args:
            html: Raw HTML string (or error message) to push to the ViewModel.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.html_content_var.set(html))

    def _push_text_results(self, text: str) -> None:
        """Schedule a text_results_var update on the main thread.

        Args:
            text: Formatted text-analysis result string.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.text_results_var.set(text))

    def _push_image_results(self, text: str) -> None:
        """Schedule an image_results_var update on the main thread.

        Args:
            text: Formatted image-analysis result string.
        """
        if self._vm.is_alive_var.get():
            self._vm.after(0, lambda: self._vm.image_results_var.set(text))

    # -----------------------------------------------------------------------
    # Queued task dispatchers (main thread → worker thread)
    # -----------------------------------------------------------------------

    def _on_debug_refresh(self) -> None:
        """Enqueues an HTML refresh task for the browser worker thread."""
        self._debug_queue.put(self._task_refresh)

    def _on_debug_analyze_texts(self, selector: str) -> None:
        """Enqueues a text analysis task for the given CSS selector.

        Args:
            selector: CSS selector to query.
        """
        self._debug_queue.put(lambda page: self._task_analyze_texts(page, selector))

    def _on_debug_analyze_images(self, selector: str) -> None:
        """Enqueues an image analysis task for the given CSS selector.

        Args:
            selector: CSS selector targeting image elements.
        """
        self._debug_queue.put(lambda page: self._task_analyze_images(page, selector))

    def _on_debug_close(self) -> None:
        """Handles a user-initiated window close: stops the browser worker."""
        self._debug_queue.put(None)
        with contextlib.suppress(Exception):
            self._vm.is_alive_var.set(False)

    # -----------------------------------------------------------------------
    # Task implementations (run inside the browser worker thread)
    # -----------------------------------------------------------------------

    def _task_refresh(self, page: Page) -> None:
        """Fetches current page HTML and pushes it to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
        """
        try:
            html = self._debug_service.get_html_content(page)
            self._push_html(html)
        except AspirabotBaseError as exc:
            self._logger.exception("Échec du rafraîchissement debug")
            self._push_html(f"Erreur lors du rafraîchissement : {exc}")

    def _task_analyze_texts(self, page: Page, selector: str) -> None:
        """Runs text analysis and pushes formatted results to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
            selector: CSS selector to query.
        """
        try:
            result = self._debug_service.analyze_texts(page, selector)
            self._push_text_results(self._format_text_results(selector, result))
        except AspirabotBaseError as exc:
            self._logger.exception("Échec de l'analyse des textes")
            self._push_text_results(f"Erreur : {exc}")

    def _task_analyze_images(self, page: Page, selector: str) -> None:
        """Runs image analysis and pushes formatted results to the ViewModel.

        Args:
            page: The live Playwright Page owned by the worker thread.
            selector: CSS selector targeting image elements.
        """
        try:
            results = self._debug_service.analyze_images(page, selector)
            self._push_image_results(self._format_image_results(selector, results))
        except AspirabotBaseError as exc:
            self._logger.exception("Échec de l'analyse des images")
            self._push_image_results(f"Erreur : {exc}")

    # -----------------------------------------------------------------------
    # Formatters (pure functions — no Playwright or UI calls)
    # -----------------------------------------------------------------------

    @staticmethod
    def _format_text_results(selector: str, results: list[dict[str, object]]) -> str:
        """Formats text analysis results into a human-readable string.

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
    def _format_image_results(selector: str, results: list[dict[str, object]]) -> str:
        """Formats image analysis results into a human-readable string.

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
