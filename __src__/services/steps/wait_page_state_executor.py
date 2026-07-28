"""IStepExecutor for WAIT_PAGE_STATE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_page_state_params import WaitPageStateParams
from shared.converter_util import convert_wait_until_to_literals
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_ms


class WaitPageStateExecutor(IStepExecutor):
    """Executor for the wait page state scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_PAGE_STATE

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(WaitPageStateParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
            cast_wait_time = convert_wait_until_to_literals(p.wait_until)
            page.wait_for_load_state(cast_wait_time, timeout=timeout_ms)
            event_bus.log_step(context, f"État '{p.wait_until.value}' atteint.")
        except Exception as exc:  # ruff: ignore[blind-except]
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(WaitPageStateExecutor())


# EOF
