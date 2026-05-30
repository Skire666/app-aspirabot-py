"""IStepExecutor for WAIT_PAGE_STATE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_page_state_params import WaitPageStateParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_ms


class WaitPageStateExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the wait page state scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_PAGE_STATE

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(WaitPageStateParams, context.step_scraping_data.params)
        page = browser.get_current_page()

        timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
        page.wait_for_load_state(p.wait_state, timeout=timeout_ms)


register_step_executor(WaitPageStateExecutor())


# EOF
