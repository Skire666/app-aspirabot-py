"""IStepExecutor for CLOSE_TABS."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.close_tabs_params import CloseTabsParams
from services.workflow_service import register_step_executor
from shared.enums import StepTypeEnum
from shared.exception_util import CurrentPageClosedUnexpectedlyError
from shared.i18n_fra import ERROR_TEMPLATES
from views.steps.close_tabs_form_def import C_INPUT_IS_FILTER_CUSTOM


class CloseTabsExecutor(IStepExecutor):
    """Executor for the close tabs scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLOSE_TABS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = CloseTabsParams.from_dict(context.step_params)
        filter_used = p.filter_custom if p.filter_mode == C_INPUT_IS_FILTER_CUSTOM else context.last_url_opened
        filter_used = filter_used.strip().lower()

        if not filter_used:
            raise ValueError("Aucun filtre URL disponible (configurez un mode ou ouvrez une page avant.")

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

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = CloseTabsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        if p.filter_mode == C_INPUT_IS_FILTER_CUSTOM and not p.filter_custom.strip():
            return [ERROR_TEMPLATES["close_tabs_filter_required"].format(step=index_display)]
        if p.max_tabs <= 0:
            return [ERROR_TEMPLATES["close_tabs_max_tabs_invalid"].format(step=index_display)]
        return []


register_step_executor(CloseTabsExecutor())
