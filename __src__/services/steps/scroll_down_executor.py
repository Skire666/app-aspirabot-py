"""IStepExecutor for SCROLL_DOWN."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.scroll_down_params import ScrollDownParams
from services.steps._helpers import evaluate_script_with_safe_retry
from services.workflow_service import register_step_executor


class ScrollDownExecutor(IStepExecutor):
    """Executor for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.SCROLL_DOWN

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return ScrollDownParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = ScrollDownParams.from_dict(params)
        page = browser.get_current_page()

        evaluate_script_with_safe_retry(page, f"window.scrollBy(0, {p.pixels})", 5)

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        # always valid as there are no parameters with constraints
        return []


register_step_executor(ScrollDownExecutor())
