"""IStepExecutor for COUNT_HTML_ELEMENTS."""

from __future__ import annotations

import logging
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.count_html_elements_params import CountHtmlElementsParams
from services.steps._helpers import evaluate_count_condition
from services.workflow_service import register_step_executor
from shared.exception_util import CountHtmlElementsConditionNotMetError

_logger = logging.getLogger(__name__)


class CountHtmlElementsExecutor(IStepExecutor):
    """Executor for the count element scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.COUNT_HTML_ELEMENTS

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return CountHtmlElementsParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = CountHtmlElementsParams.from_dict(params)
        page = browser.get_current_page()

        count = page.locator(p.selector).count()
        condition_met = evaluate_count_condition(count, p.operator, p.value)
        step_success = condition_met if p.success_if == "success" else not condition_met
        if not step_success:
            val_desc = str(p.value)
            raise CountHtmlElementsConditionNotMetError(count, p.operator, val_desc)

        params["_last_message_step"] = (
            f"Trouvé {count} élément(s) pour le sélecteur {p.selector!r}, condition vérifiée."
        )

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = CountHtmlElementsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        allowed_operators = {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }
        errors: list[str] = []
        if not p.selector.strip():
            errors.append(f"Erreur dans l'étape {index_display}. : le sélecteur CSS est obligatoire.")
        if p.success_if not in {"success", "failure"}:
            errors.append(f"Erreur dans l'étape {index_display}. : success_if invalide — {p.success_if!r}.")
        if p.operator not in allowed_operators:
            errors.append(f"Erreur dans l'étape {index_display}. : operator invalide — {p.operator!r}.")
        return errors


register_step_executor(CountHtmlElementsExecutor())
