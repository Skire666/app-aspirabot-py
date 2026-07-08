"""IStepExecutor for WAIT_HTML_ELEMENTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from services.steps._helpers import evaluate_count_condition
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.exception_util import CountHtmlElementsConditionNotMetError
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class WaitHtmlElementsExecutor(IStepExecutor):
    """Executor for the wait element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_HTML_ELEMENTS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(WaitHtmlElementsParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            nbr_delay_in_sec = convert_to_sec(p.retry_delay, p.retry_unit)
            count: int = -1
            for i in range(p.retry_max):
                count = page.locator(p.selector).count()
                condition_met = evaluate_count_condition(count, p.operator, p.quantity)
                if condition_met:
                    break
                if i == p.retry_max - 1:  # i=5 -> max=6
                    raise CountHtmlElementsConditionNotMetError(count, p.operator, str(p.quantity))  # noqa: TRY301
                time.sleep(nbr_delay_in_sec)
            msg = f"Trouvé x{count} élément(s) | Sélecteur '{p.selector}' | Condition OK."
            event_bus.log_step(context, msg)
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(WaitHtmlElementsExecutor())


# EOF
