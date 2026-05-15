"""IStepExecutor for WAIT_PAGE_STATE."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_page_state_params import WaitPageStateParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_ms


class WaitPageStateExecutor(IStepExecutor):
    """Executor for the wait page state scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_PAGE_STATE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitPageStateParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = WaitPageStateParams.from_dict(context.step_params)
        page = browser.get_current_page()

        timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
        page.wait_for_load_state(p.wait_state, timeout=timeout_ms)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitPageStateParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if p.timeout_duration <= 0:
            errors.append(ERROR_TEMPLATES["wait_page_state_timeout_invalid"].format(step=index_display))
        if p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(ERROR_TEMPLATES["wait_page_state_timeout_unit_invalid"].format(step=index_display))
        return errors


register_step_executor(WaitPageStateExecutor())
