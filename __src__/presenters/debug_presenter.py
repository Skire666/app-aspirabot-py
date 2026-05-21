"""Presenter for the Debug sidebar module.

Owns the entire debug browser session lifecycle: launches a persistent
BrowserPlaywrightService worker thread, routes all Playwright calls through
a task queue so they stay in the same thread, and updates the DebugPageView
window via after(0, callback).

Example:
    >>> presenter = DebugPresenter(view=debug_view)
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import contextlib
import logging
import queue
import threading
from collections.abc import Callable

from playwright.sync_api import Page
from services.browser_playwright_service import BrowserPlaywrightService
from services.debug_browser_service import DebugBrowserService
from views.debug_view import DebugView
from views.workflow.debug_page_view import DebugPageView

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class DebugPresenter:
    """Orchestrates the debug browser session from the Debug sidebar module.

    Responsibilities:
    - Binds the DebugView launch callback.
    - Manages a single persistent browser worker thread per session.
    - Routes all Playwright API calls through a queue to that thread.
    - Updates DebugView status and DebugPageView content via Tkinter after().

    Attributes:
        _view: The Debug sidebar module view.
    """

    def __init__(self, view: DebugView) -> None:
        """Initialises the presenter and binds the view callback.

        Args:
            view: The DebugView module widget.
        """
        self._logger = logging.getLogger(__name__)
        self._view = view

        # Debug session state — one active session at a time.
        self._debug_browser: BrowserPlaywrightService | None = None
        self._debug_window: DebugPageView | None = None
        self._debug_service: DebugBrowserService = DebugBrowserService()
        self._debug_queue: queue.Queue[Callable[[Page], None] | None] = queue.Queue()
        self._debug_thread: threading.Thread | None = None

        self._view.on_start = self._on_debug_start

    # -----------------------------------------------------------------------
    # Debug session — public entry point
    # -----------------------------------------------------------------------

    def _on_debug_start(self, url: str, timeout: int, dns_delay: int) -> None:
        """Opens a debug browser session for the given URL.

        Closes any prior session, creates a fresh queue, and starts the
        single persistent browser worker thread with the supplied timing
        parameters.

        Args:
            url: The URL to open in the debug browser.
            timeout: Navigation timeout in seconds (1-30).
            dns_delay: DNS resolution wait in seconds (1-30).
        """
        self._close_debug_session()
        # Fresh queue — old worker reads None from its own (now unreferenced) queue.
        self._debug_queue = queue.Queue()
        self._debug_browser = BrowserPlaywrightService()
        self._debug_window = DebugPageView(self._view, url)
        self._debug_window.on_refresh = self._on_debug_refresh
        self._debug_window.on_analyze_texts = self._on_debug_analyze_texts
        self._debug_window.on_analyze_images = self._on_debug_analyze_images
        self._debug_window.on_close = self._on_debug_close
        self._debug_window.set_html_content("Chargement en cours…")
        self._view.set_status_active(url)
        self._debug_thread = threading.Thread(
            target=self._browser_worker, args=(url, timeout, dns_delay), daemon=True
        )
        self._debug_thread.start()

    def _close_debug_session(self) -> None:
        """Destroys the debug window and sends a stop signal to the worker."""
        if self._debug_window is not None:
            with contextlib.suppress(Exception):
                self._debug_window.destroy()
            self._debug_window = None
        # Sentinel None causes the worker loop to exit and close the browser.
        self._debug_queue.put(None)
        self._view.set_status_idle()

    # -----------------------------------------------------------------------
    # Browser worker (long-lived thread)
    # -----------------------------------------------------------------------

    def _browser_worker(self, url: str, timeout: int, dns_delay: int) -> None:
        """Long-lived browser thread — the only thread that calls Playwright.

        Launches the browser, navigates to url using the supplied timing
        parameters, pushes the initial HTML, then processes Callable tasks
        from _debug_queue until a None sentinel arrives. The browser is
        always closed in the finally block.

        Args:
            url: The URL to navigate to on startup.
            timeout: Navigation timeout in seconds (converted to ms internally).
            dns_delay: DNS resolution wait passed to safe_goto_url.
        """
        try:
            self._debug_browser.launch()
            self._debug_browser.append_new_page()
            self._debug_browser.safe_goto_url(
                url,
                wait_state="networkidle",
                timeout_ms=timeout * 1000,
                wait_dns_solver_sec=dns_delay,
            )

            page = self._debug_browser.get_current_page()

            # Push initial HTML to the view after successful navigation.
            html = self._debug_service.get_html_content(page)
            win = self._debug_window
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_html_content(html))

            # Process tasks — all Playwright calls stay in this thread.
            while True:
                task = self._debug_queue.get()
                if task is None:
                    break
                task(page)
        except Exception as exc:
            self._logger.exception("Browser worker startup failed")
            win = self._debug_window
            msg = f"Erreur lors du chargement :\n{exc}"
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_html_content(msg))
        finally:
            with contextlib.suppress(Exception):
                self._debug_browser.close_browser()

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
        """Stops the browser worker when the DebugPageView window is closed."""
        self._debug_window = None
        self._debug_queue.put(None)
        self._view.set_status_idle()

    # -----------------------------------------------------------------------
    # Task implementations (run inside the browser worker thread)
    # -----------------------------------------------------------------------

    def _task_refresh(self, page: Page) -> None:
        """Fetches current page HTML and pushes it to the debug window.

        Args:
            page: The live Playwright Page owned by the worker thread.
        """
        try:
            html = self._debug_service.get_html_content(page)
            win = self._debug_window
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_html_content(html))
        except Exception as exc:
            self._logger.exception("Debug refresh failed")
            win = self._debug_window
            msg = f"Erreur lors du rafraîchissement : {exc}"
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_html_content(msg))

    def _task_analyze_texts(self, page: Page, selector: str) -> None:
        """Runs text analysis and pushes formatted results to the debug window.

        Args:
            page: The live Playwright Page owned by the worker thread.
            selector: CSS selector to query.
        """
        try:
            result = self._debug_service.analyze_texts(page, selector)
            text = self._format_text_results(selector, result)
            win = self._debug_window
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_text_results(text))
        except Exception as exc:
            self._logger.exception("Debug analyze texts failed")
            win = self._debug_window
            msg = f"Erreur : {exc}"
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_text_results(msg))

    def _task_analyze_images(self, page: Page, selector: str) -> None:
        """Runs image analysis and pushes formatted results to the debug window.

        Args:
            page: The live Playwright Page owned by the worker thread.
            selector: CSS selector targeting image elements.
        """
        try:
            results = self._debug_service.analyze_images(page, selector)
            text = self._format_image_results(selector, results)
            win = self._debug_window
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_image_results(text))
        except Exception as exc:
            self._logger.exception("Debug analyze images failed")
            win = self._debug_window
            msg = f"Erreur : {exc}"
            if win and win.winfo_exists():
                win.after(0, lambda: win.set_image_results(msg))

    # -----------------------------------------------------------------------
    # Formatters (pure functions — no Playwright or UI calls)
    # -----------------------------------------------------------------------

    @staticmethod
    def _format_text_results(selector: str, result: dict[str, object]) -> str:
        """Formats a text analysis result dict into a human-readable string.

        Args:
            selector: The CSS selector that was queried.
            result: Dict from DebugBrowserService.analyze_texts().

        Returns:
            Multi-line formatted string ready for display.
        """
        count = int(result.get("count", 0))
        if count == 0:
            return f"Sélecteur : {selector!r}\nAucun élément trouvé."

        str_inner_html = result.get("innerHTML", "").strip()
        str_txt_content = result.get("textContent", "").strip()
        str_inner_txt = result.get("innerText", "").strip()
        str_outer_txt = result.get("outerText", "").strip()

        lines = [
            f"Sélecteur : {selector!r}",
            f"count       : {count}",
            "",
            "--------- Premier élément ---------",
            f"--- innerHTML x{len(str_inner_html)}  :\n{str_inner_html}",
            "",
            f"--- textContent x{len(str_txt_content)}  :\n{str_txt_content}",
            "",
            f"--- innerText x{len(str_inner_txt)}  :\n{str_inner_txt}",
            "",
            f"--- outerText x{len(str_outer_txt)}  :\n{str_outer_txt}",
            "",
        ]
        if count > 1:
            lines.insert(3, f"(Affichage du 1er élément sur {count} trouvés)")
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
