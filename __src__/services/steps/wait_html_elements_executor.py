"""IStepExecutor for WAIT_HTML_ELEMENTS."""

from __future__ import annotations

import time
from typing import Any, override

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
from shared.time_util import convert_to_sec


class WaitHtmlElementsExecutor(IStepExecutor):
    """Executor for the wait element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_HTML_ELEMENTS

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitHtmlElementsParams.default().to_dict()

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
            errors.append(f"Dans l'étape {index_display}. : le sélecteur CSS est obligatoire.")
        if p.operator not in {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }:
            errors.append(
                f"Dans l'étape {index_display}. : l'opérateur doit être l'un des suivants : equal, not_equal, greater_than, less_than, greater_or_equal, less_or_equal."
            )
        if p.quantity < 0:
            errors.append(f"Dans l'étape {index_display}. : la quantité doit être >= 0")
        if p.retry_delay <= 0:
            errors.append(f"Dans l'étape {index_display}. : le délai de retry doit être >= 1")
        if p.retry_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(
                f"Dans l'étape {index_display}. : l'unité de retry doit être l'une des suivantes : {', '.join(C_UNITS_TIME_ALLOWED_FOR_MODEL)}."
            )
        if p.retry_max <= 0:
            errors.append(f"Dans l'étape {index_display}. : le nombre maximum de retry doit être >= 1")
        return errors


register_step_executor(WaitHtmlElementsExecutor())
