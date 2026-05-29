"""IStepExecutor for CLOSE_TABS."""

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.close_tabs_params import CloseTabsParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import OpenUrlModeEnum, StepTypeEnum
from shared.exception_util import CurrentPageClosedUnexpectedlyError, MissingUrlFilterError
from shared.step_registry import register_step_executor


class CloseTabsExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLOSE_TABS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(CloseTabsParams, context.step_scraping_data.params)
        filter_used = p.filter_custom if p.filter_mode == OpenUrlModeEnum.E_CUSTOM.value else context.last_url_opened
        filter_used = filter_used.strip().lower()

        if not filter_used:
            raise MissingUrlFilterError()

        current_page = browser.get_current_page()
        counter_closed = 0
        # Close tabs that do not match the URL filter.
        for p_tab in list(browser.get_all_pages()):
            lowercase = p_tab.url.lower()
            if filter_used and lowercase.find(filter_used) == -1:
                # not in filters... will be closed
                p_tab.close()
                counter_closed += 1

        context.last_message_step = (
            f"Fermé {counter_closed} onglet(s) ne correspondant pas au filtre URL {filter_used!r}."
            if filter_used
            else ""
        )

        # Ensure the primary workflow page was not accidentally closed.
        if current_page not in browser.get_all_pages():
            raise CurrentPageClosedUnexpectedlyError()

        # Enforce the max-tabs limit on the remaining non-primary pages.
        if p.max_tabs >= 1:
            others = [t for t in browser.get_all_pages() if t is not current_page]
            for t in others[p.max_tabs - 1 :]:
                t.close()


register_step_executor(CloseTabsExecutor())
