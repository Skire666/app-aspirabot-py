"""IStepExecutor for WAIT_HTML_ELEMENTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from services.steps._helpers import evaluate_count_condition
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.exception_util import CountHtmlElementsConditionNotMetError
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class WaitHtmlElementsExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the wait element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_HTML_ELEMENTS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(WaitHtmlElementsParams, context.step_scraping_data.params)
        page = browser.get_workflow_page()
        nbr_delay_in_sec = convert_to_sec(p.retry_delay, p.retry_unit)
        counted_items: int = -1

        for i in range(p.retry_max):
            counted_items = page.locator(p.selector).count()
            condition_met = evaluate_count_condition(counted_items, p.operator, p.quantity)
            if condition_met:
                break
            if i == p.retry_max - 1:  # i=5 -> max=6
                raise CountHtmlElementsConditionNotMetError(counted_items, p.operator, str(p.quantity))
            time.sleep(nbr_delay_in_sec)

        context.last_message_step = (
            f"Trouvé {counted_items} élément(s) pour le sélecteur {p.selector!r}, condition vérifiée."
        )


register_step_executor(WaitHtmlElementsExecutor())


# EOF
