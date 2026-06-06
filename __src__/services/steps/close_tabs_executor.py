"""IStepExecutor for CLOSE_TABS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.close_tabs_params import CloseTabsParams
from playwright.sync_api import Page
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import OpenUrlModeEnum, StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import CurrentPageClosedUnexpectedlyError, MissingUrlFilterError
from shared.step_registry import register_step_executor


class CloseTabsExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLOSE_TABS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(CloseTabsParams, context.step_scraping_data.params)
        try:
            filter_used = self._resolve_url_filter(p, context)
            current_page = browser.get_workflow_page()
            counter_closed = self._close_non_matching_tabs(browser, filter_used)
            msg = f"Fermé {counter_closed} onglet(s) ne correspondant pas au filtre URL {filter_used!r}."
            event_bus.log_step(context, msg)
            if current_page not in browser.get_all_pages():
                raise CurrentPageClosedUnexpectedlyError()  # noqa: TRY301
            self._enforce_max_tabs(browser, current_page, p.max_tabs)
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Erreur : {exc}")
            return StepExecutionResultEnum.ERROR
        else:
            return StepExecutionResultEnum.SUCCESS

    @staticmethod
    def _resolve_url_filter(p: CloseTabsParams, context: ScrapingContextModel) -> str:
        """Resolve and validate the URL filter from params or context.

        Args:
            p: Step parameters carrying the filter mode and optional custom filter.
            context: Scraping context providing the last opened URL as fallback.

        Returns:
            The lowercased, stripped filter string.

        Raises:
            MissingUrlFilterError: When the resolved filter is empty.
        """
        raw = p.filter_custom if p.filter_mode == OpenUrlModeEnum.E_CUSTOM.value else context.last_url_opened
        filter_used = raw.strip().lower()
        if not filter_used:
            raise MissingUrlFilterError()
        return filter_used

    @staticmethod
    def _close_non_matching_tabs(browser: IWebBrowserService, filter_used: str) -> int:
        """Close tabs whose URL does not contain filter_used.

        Args:
            browser: Browser service exposing the page list.
            filter_used: Lowercased URL substring that tabs must contain to survive.

        Returns:
            Number of tabs closed.
        """
        counter = 0
        for tab in list(browser.get_all_pages()):
            if tab.url.lower().find(filter_used) == -1:
                tab.close()
                counter += 1
        return counter

    @staticmethod
    def _enforce_max_tabs(browser: IWebBrowserService, current_page: Page, max_tabs: int) -> None:
        """Close excess non-primary tabs to respect the max_tabs limit.

        Args:
            browser: Browser service exposing the page list.
            current_page: Primary workflow page that must not be closed.
            max_tabs: Maximum number of tabs allowed (0 or negative means no limit).
        """
        if max_tabs < 1:
            return
        others = [t for t in browser.get_all_pages() if t is not current_page]
        for t in others[max_tabs - 1 :]:
            t.close()


register_step_executor(CloseTabsExecutor())


# EOF
