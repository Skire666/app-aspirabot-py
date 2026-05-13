"""IStepExecutor for REFRESH_PAGE."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.refresh_page_params import RefreshPageParams
from services.steps._helpers import resolve_timeout_ms
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL


class RefreshPageExecutor(IStepExecutor):
    """Executor for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.REFRESH_PAGE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return RefreshPageParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = RefreshPageParams.from_dict(context.step_params)
        page = browser.get_current_page()

        # Clear session cookies before reload when requested.
        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        if p.clear_cache:
            page.context.clear_cookies()
        page.reload()
        page.wait_for_load_state(p.wait_state, timeout=timeout_ms)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = RefreshPageParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if p.timeout_duration <= 0:
            errors.append(f"Dans l'étape {index_display}. : Timeout doit être >= 1")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : timeout_unit invalide - {p.timeout_unit}.")
        return errors


register_step_executor(RefreshPageExecutor())
