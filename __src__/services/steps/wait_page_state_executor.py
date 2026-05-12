"""IStepExecutor for WAIT_PAGE_STATE."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_page_state_params import WaitPageStateParams
from services.steps._helpers import resolve_timeout_ms
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL


class WaitPageStateExecutor(IStepExecutor):
    """Executor for the wait page state scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_PAGE_STATE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitPageStateParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitPageStateParams.from_dict(params)
        page = browser.get_current_page()

        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        page.wait_for_load_state(p.wait_state, timeout=timeout_ms)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitPageStateParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if p.timeout_duration <= 0:
            errors.append(f"Dans l'étape {index_display}. : timeout_duration doit être >= 1.")
        if p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : L'unité de timeout est invalide.")
        return errors


register_step_executor(WaitPageStateExecutor())
