"""IStepExecutor for WAIT_HTML_ELEMENTS."""

from __future__ import annotations

import time
from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from services.steps._helpers import evaluate_count_condition
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import StepTypeEnum
from shared.exception_util import CountHtmlElementsConditionNotMetError
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_sec


class WaitHtmlElementsExecutor(IStepExecutor):
    """Executor for the wait element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_HTML_ELEMENTS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = WaitHtmlElementsParams.from_dict(context.step_params)
        page = browser.get_current_page()
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

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        errors: list[str] = []
        p = WaitHtmlElementsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        if not p.selector.strip():
            errors.append(ERROR_TEMPLATES["wait_html_elements_selector_required"].format(step=index_display))
        if p.operator not in {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }:
            errors.append(ERROR_TEMPLATES["wait_html_elements_operator_invalid"].format(step=index_display))
        if p.quantity < 0:
            errors.append(ERROR_TEMPLATES["wait_html_elements_quantity_negative"].format(step=index_display))
        if p.retry_delay <= 0:
            errors.append(ERROR_TEMPLATES["wait_html_elements_retry_delay_invalid"].format(step=index_display))
        if p.retry_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(ERROR_TEMPLATES["wait_html_elements_retry_unit_invalid"].format(step=index_display))
        if p.retry_max <= 0:
            errors.append(ERROR_TEMPLATES["wait_html_elements_retry_max_invalid"].format(step=index_display))
        return errors


register_step_executor(WaitHtmlElementsExecutor())
