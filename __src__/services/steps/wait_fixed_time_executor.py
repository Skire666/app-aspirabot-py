"""IStepExecutor for WAIT_FIXED_TIME."""

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class WaitFixedTimeExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the wait fixed time scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_FIXED_TIME

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(WaitFixedTimeParams, context.step_scraping_data.params)
        time_sec = convert_to_sec(p.duration, p.unit)
        if time_sec > 0:
            time.sleep(time_sec)

        context.last_message_step = f"Pause durant {time_sec:.3f} sec."


register_step_executor(WaitFixedTimeExecutor())
