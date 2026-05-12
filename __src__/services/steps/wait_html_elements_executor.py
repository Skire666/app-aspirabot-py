"""IStepExecutor for WAIT_HTML_ELEMENTS."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from services.steps._helpers import evaluate_count_condition
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL, C_UNITS_TIME_CONVERSION_TO_SEC
from shared.exception_util import CountHtmlElementsConditionNotMetError


class WaitHtmlElementsExecutor(IStepExecutor):
    """Executor for the wait element scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_HTML_ELEMENTS

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitHtmlElementsParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitHtmlElementsParams.from_dict(params)
        page = browser.get_current_page()
        nbr_delay_in_sec = p.retry_delay * C_UNITS_TIME_CONVERSION_TO_SEC.get(p.retry_unit, 1.0)
        count: int = -1

        for i in range(p.retry_max):
            count = page.locator(p.selector).count()
            condition_met = evaluate_count_condition(count, p.operator, p.quantity)
            step_success = condition_met if p.success_if == "success" else not condition_met
            if step_success:
                break
            if i == p.retry_max - 1:  # i=5 -> max=6
                raise CountHtmlElementsConditionNotMetError(count, p.operator, str(p.quantity))
            time.sleep(nbr_delay_in_sec)

        # success case: store a message in the mutable params dict to be used by potential next steps (e.g. for logging or user feedback).
        params["_last_message_step"] = (
            f"Trouvé {count} élément(s) pour le sélecteur {p.selector!r}, condition vérifiée."
        )

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        errors: list[str] = []
        p = WaitHtmlElementsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        if not p.selector.strip():
            errors.append(f"Dans l'étape {index_display}. : le sélecteur CSS est obligatoire.")
        if p.operator not in {"equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"}:
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
