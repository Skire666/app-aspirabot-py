"""IStepExecutor for CLOSE_TABS."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.close_tabs_params import CloseTabsParams
from services.workflow_service import register_step_executor
from shared.exception_util import CurrentPageClosedUnexpectedlyError


class CloseTabsExecutor(IStepExecutor):
    """Executor for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.CLOSE_TABS

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return CloseTabsParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = CloseTabsParams.from_dict(context.step_params)
        current_page = browser.get_current_page()

        counter_closed = 0
        # Close tabs that do not match the URL filter.
        for p_tab in list(browser.get_all_pages()):
            if p.url_filter and p_tab.url.find(p.url_filter) == -1:
                p_tab.close()
                counter_closed += 1

        context.last_message_step = (
            f"Fermé {counter_closed} onglet(s) ne correspondant pas au filtre URL {p.url_filter!r}."
            if p.url_filter
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

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = CloseTabsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        if p.url_filter is not None and not p.url_filter.strip():
            return [f"Erreur dans l'étape {index_display}. : Filtre URL ne peut pas être vide."]
        if p.max_tabs <= 0:
            return [f"Erreur dans l'étape {index_display}. : Max. onglets doit être >= 1."]
        return []


register_step_executor(CloseTabsExecutor())
