"""IStepExecutor for SCROLL_DOWN."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.scroll_down_params import ScrollDownParams
from services.workflow_service import register_step_executor
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
)
from shared.enums import StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES


class ScrollDownExecutor(IStepExecutor):
    """Executor for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return ScrollDownParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = ScrollDownParams.from_dict(context.step_params)

        browser.evaluate_script_with_safe_retry(
            f"window.scrollBy(0, {p.pixels})",
            C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
            C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
        )

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model parameters."""
        p = ScrollDownParams.from_dict(model.params)
        step_label = str(step_index + 1).zfill(2)
        if p.pixels < 1:
            return [ERROR_TEMPLATES["scroll_down_pixels_invalid"].format(step=step_label)]
        return []


register_step_executor(ScrollDownExecutor())
