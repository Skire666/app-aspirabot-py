"""IStepExecutor for OPEN_URL."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.open_url_params import OpenUrlParams
from services.steps._helpers import resolve_timeout_ms
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL


class OpenUrlExecutor(IStepExecutor):
    """Executor for the open URL scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.OPEN_URL

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return OpenUrlParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = OpenUrlParams.from_dict(context.step_params)
        page = browser.get_current_page()

        # TODO PCO Url ou <<URL>> ou <<CUSTOM>>

        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        if timeout_ms is not None:
            page.goto(p.url_custom, wait_until=p.wait_state, timeout=timeout_ms)
        else:
            page.goto(p.url_custom, wait_until=p.wait_state)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = OpenUrlParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if p.url_mode is None or (p.url_mode == "<<CUSTOM>>" and not p.url_custom):
            errors.append(f"Dans l'étape {index_display}. : l'URL est obligatoire.")
        if p.timeout_duration <= 0:
            errors.append(f"Dans l'étape {index_display}. : Timeout doit être >= 1.")
        if p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : L'unité de timeout est invalide.")
        return errors


register_step_executor(OpenUrlExecutor())
