"""IStepExecutor for COUNT_HTML_ELEMENTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.count_html_elements_params import CountHtmlElementsParams
from services.steps._helpers import evaluate_count_condition
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import CountHtmlElementsConditionNotMetError
from shared.step_registry import register_step_executor

_logger = logging.getLogger(__name__)


class CountHtmlElementsExecutor(IStepExecutor):
    """Executor for the count element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_ELEMENTS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(CountHtmlElementsParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            count = page.locator(p.selector).count()
            condition_met = evaluate_count_condition(count, p.operator, p.value)
            step_success = condition_met if p.success_if == "success" else not condition_met
            if not step_success:
                raise CountHtmlElementsConditionNotMetError(count, p.operator, str(p.value))  # noqa: TRY301
            msg = f"Trouvé x{count} élément(s) pour le sélecteur '{p.selector}', condition vérifiée."
            event_bus.log_step(context, msg)
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(CountHtmlElementsExecutor())


# EOF
