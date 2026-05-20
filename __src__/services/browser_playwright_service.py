"""Playwright-based implementation of IWebBrowserService.

Uses Playwright Chromium with custom args. Tracks all open pages internally —
including those opened by JavaScript — via context-level events. When a page
is closed (by an executor or by the browser), it is removed automatically from
the internal list.

Example:
    >>> svc = BrowserService(folder)
    >>> svc.launch(provider)
    >>> svc.append_new_page()
    >>> page = svc.get_current_page()
    >>> svc.close_browser()
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

import logging
import time

from interfaces.i_web_browser_service import IWebBrowserService
from playwright.sync_api import Browser, BrowserContext, Page, Playwright, sync_playwright
from shared.constants import C_STR_ERROR_JS_EVALUATION
from shared.exception_util import (
    BrowserAlreadyLaunchedError,
    BrowserNotLaunchedError,
    PageNotAvailableOrClosedError,
)

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class BrowserPlaywrightService(IWebBrowserService):
    """Playwright + stealth browser service for scraping workflows.

    Handles Chromium launch with anti-detection hardening and manages all
    open pages in an internal list. Pages opened programmatically via
    ``append_new_page()`` and pages opened by JavaScript (target="_blank")
    are both tracked. Closed pages are removed automatically via Playwright
    page-close events.

    Example:
        >>> svc = BrowserPlaywrightService(Path("."))
        >>> svc.launch(provider)
        >>> svc.append_new_page()
        >>> page = svc.get_current_page()
        >>> svc.close_browser()
    """

    def __init__(self) -> None:
        """Initialise the service without launching the browser yet."""
        self._logger = logging.getLogger(__name__)

        # Lifecycle state — populated by launch(), cleared by close_browser().
        self._pw: Playwright | None = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None

    # ------------------------------------------------------------------
    # IWebBrowserService — public API
    # ------------------------------------------------------------------

    def launch(self) -> None:
        """Initialize and launch Chromium with provider configuration.

        Args:
            provider: Provider model carrying browser configuration.

        Returns:
            None.

        Raises:
            RuntimeError: If the browser is already launched.
        """
        if self._pw is not None:
            raise BrowserAlreadyLaunchedError()

        # Obfuscated mode uses custom args; standard mode uses a plain context.
        args = ["--disable-blink-features=AutomationControlled"]

        # Start Playwright and create the browser + context.
        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(headless=False, args=args)
        self._context = self._browser.new_context(no_viewport=True)

        # pour le no_viewport=True, à garder
        # en gros, si je l'ai pas à True, il va pertuber les événéments clavier,
        # ou bien pertuber le focus des champsd e formulaire
        # ou alors bloque le refresh d'une page si 2 onglets d'ouvert
        # ou alors ignorer la touche "entrée" sur google.com, du coup la recherche ne se lance pas
        # les symptomes sont assez étrange, car les pages tournes en boucle, comme en attente de réponse

        # NOTE PCO : Ne plus faire un dossier au démarrage, dans l'optique de préserver la session.
        # Les détections de bot n'aiment pas du tout ça. Surtout CloudFlare.
        # Les trucs de 'stealth', avec headless false, ils ne servent à rien (utile que si mode 'caché').
        # Donc autant ne pas le mettre, surtout qu'avec cloudflare, le stealth ne suffit pas.

    def _launch_todo_pco_with_extension(self) -> None:
        # code pour lancer un chrome, avec ublock origine lite déjà chargé
        # attention, lance dans un dossier temporaire en live (cf. tempfile)

        import tempfile
        from pathlib import Path

        args = ["--disable-blink-features=AutomationControlled"]
        self._pw = sync_playwright().start()

        path_folder = r"E:/app-aspirabot-py/extensions/uBlock0_chromium"
        # le manifeste doit être dedans.
        # ne pas faire "./" car il part du dossier temporaire de chrome, pas du projet python.

        if Path(path_folder).is_dir():
            args.append(f"--load-extension={path_folder}")
            args.append(f"--disable-extensions-except={path_folder}")
        else:
            self._logger.warning("Le dossier d'extension uBlock Origin Lite n'existe pas : %s", path_folder)

        self._context = self._pw.chromium.launch_persistent_context(
            user_data_dir=tempfile.mkdtemp(), headless=False, args=args, no_viewport=True
        )
        self._context.on("page", self._on_context_new_page)  # Track every page opened

    def _launch_todo_pco_with_remote_port(self) -> None:
        # TODO PCO lance mon chrome, mais dans un dossier à part, il persiste le contenu de la session.
        # au début vide, mais on peut installer un ublock lite par exemple

        # command powershel (à lancer en 1 commande, j'ai juste mis un retour à la ligne)
        # & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
        # --user-data-dir="C:\temp\chrome-debug" --no-first-run --no-default-browser-check

        # Pour debug et voir si ça marche bien :
        # & "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222
        # --user-data-dir="C:\temp\chrome-debug" --no-first-run --no-default-browser-check
        # --remote-debugging-address=0.0.0.0

        # netstat -ano | findstr 9222
        # REPONSE :  TCP    127.0.0.1:9222         0.0.0.0:0              LISTENING       5464

        self._pw = sync_playwright().start()

        # Connexion au Chrome existant via CDP
        self._browser = self._pw.chromium.connect_over_cdp("http://localhost:9222")

        # Récupère le contexte existant (avec tout l'historique/session en cours)
        self._context = self._browser.contexts[0]

    def append_new_page(self) -> None:
        """Open a new browser page and register it via the context page event.

        The page is not returned — use ``get_current_page()`` or
        ``get_all_pages()`` to access it after this call.

        Returns:
            None.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """
        if self._context is None:
            raise BrowserNotLaunchedError()

        # The context "page" event fires for all new pages, including this one.
        # _on_context_new_page handles registration — do not append here.
        self._context.new_page()
        # DO NOT append to self._pages here; the context event will handle it.

    def close_all_tabs(self) -> None:
        """Close all open pages/tabs in the browser.

        Returns:
            None.

        Raises:
            RuntimeError: If ``launch()`` has not been called yet.
        """
        if self._context is None:
            raise BrowserNotLaunchedError()

        # Close each page; the context event will handle de-registration.
        for page in self._context.pages:
            page.close()

    def get_current_page(self) -> Page:
        """Return the primary browser page (the first one opened).

        Returns:
            The main workflow Page object.

        Raises:
            PageNotAvailableOrClosedError: If no page is available or the current page is closed.
        """
        if not self._context.pages or len(self._context.pages) == 0 or self._context.pages[0].is_closed():
            raise PageNotAvailableOrClosedError()

        # First page in the list is always the primary workflow page.
        return self._context.pages[0]

    def get_all_pages(self) -> list[Page]:
        """Return all currently open pages tracked by this service.

        Returns:
            A snapshot list of all open Page objects.
        """
        return list(self._context.pages) if self._context is not None else []

    def close_browser(self) -> None:
        """Close all pages, the context, the browser, and Playwright runtime.

        Returns:
            None.
        """
        try:
            # Clear page registry before closing so stale references are gone.
            self.close_all_tabs()

            # Close in reverse-creation order: context → browser → playwright.
            if self._context is not None:
                self._context.close()
                self._context = None

            if self._browser is not None:
                self._browser.close()
                self._browser = None

            if self._pw is not None:
                self._pw.stop()
                self._pw = None

            self._logger.info("Browser closed successfully. is_launched=%s", self.is_launched)

        except Exception:
            self._logger.error("Une erreur s'est produite lors de la fermeture du navigateur", exc_info=True)
            # Don't re-raise; ensure all resources are attempted to be cleaned up.

    @property
    def is_launched(self) -> bool:
        """True if the browser has been launched and not yet closed.

        Returns:
            bool: current launch state.
        """
        return self._pw is not None

    def evaluate_script_with_safe_retry(self, script: str, retries: int, delay: float) -> tuple[bool, object]:
        """Evaluate a JS snippet on the current page with retries on failure.

        Args:
            script: JavaScript expression or function to evaluate.
            retries: Maximum number of attempts.
            delay: Seconds to wait between attempts.

        Returns:
            A tuple of (is_success, result) where is_success indicates if the evaluation was successful and result is the value returned by the JS expression.

        Raises:
            Exception: The last exception raised if all retries are exhausted.
        """
        page = self.get_current_page()

        # Retry loop — re-raises on the final failed attempt.
        for attempt in range(1, retries + 1):
            try:
                result = page.evaluate(script)
                return True, result
            except Exception as exc:
                self._logger.warning("Script eval failed attempt %d/%d: %s", attempt, retries, exc)
                if attempt == retries:
                    # if this was the last attempt, re-raise the exception to signal failure
                    raise
                time.sleep(delay)

        # This line should never be reached due to the re-raise in the except block
        # but is required for type checking.
        return False, C_STR_ERROR_JS_EVALUATION
