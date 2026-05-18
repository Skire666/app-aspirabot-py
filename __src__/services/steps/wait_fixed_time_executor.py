"""IStepExecutor for WAIT_FIXED_TIME."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from services.workflow_service import register_step_executor
from shared.enums import StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_sec


class WaitFixedTimeExecutor(IStepExecutor):
    """Executor for the wait fixed time scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_FIXED_TIME

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitFixedTimeParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = WaitFixedTimeParams.from_dict(context.step_params)
        time_sec = convert_to_sec(p.duration, p.unit)
        if time_sec > 0:
            time.sleep(time_sec)

        context.last_message_step = f"Pause durant {time_sec:.3f} sec."

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitFixedTimeParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.duration < 0:
            return [ERROR_TEMPLATES["wait_fixed_time_duration_invalid"].format(step=index_display)]
        return []


register_step_executor(WaitFixedTimeExecutor())
