"""IStepExecutor for SCROLL_DOWN."""

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.scroll_down_params import ScrollDownParams
from services.steps.step_executor_base import StepExecutorBase
from shared.constants import C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT, C_MAXIMUM_RETRY_EVALUATE_SCRIPT
from shared.enums import StepTypeEnum
from shared.exception_util import ScriptExecutionFailedError
from shared.step_registry import register_step_executor


class ScrollDownExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(ScrollDownParams, context.step_scraping_data.params)

        is_success, _ = browser.evaluate_script_with_safe_retry(
            f"window.scrollBy(0, {p.pixels})", C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )
        if not is_success:
            raise ScriptExecutionFailedError("scroll_down")


register_step_executor(ScrollDownExecutor())
