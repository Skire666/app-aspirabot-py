"""IStepExecutor for WAIT_HTML_ELEMENTS."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_html_elements_params import WaitHtmlElementsParams
from services.steps._helpers import resolve_timeout_ms
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL


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

        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        if timeout_ms is not None:
            page.wait_for_selector(p.selector, timeout=timeout_ms)
        else:
            page.wait_for_selector(p.selector)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        errors: list[str] = []
        p = WaitHtmlElementsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        if not p.selector.strip():
            errors.append(f"Dans l'étape {index_display}. : le sélecteur CSS est obligatoire.")
        if p.timeout_duration < 0:
            errors.append(f"Dans l'étape {index_display}. : timeout_duration doit être >= 0.")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : timeout_unit invalide - {p.timeout_unit}.")
        return errors


register_step_executor(WaitHtmlElementsExecutor())
