"""IStepExecutor for WAIT_FIXED_TIME."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_fixed_time_params import WaitFixedTimeParams
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class WaitFixedTimeExecutor(IStepExecutor):
    """Executor for the wait fixed time scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_FIXED_TIME

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(WaitFixedTimeParams, context.step_scraping_data.params)
        try:
            time_sec = convert_to_sec(p.duration, p.unit)
            if time_sec > 0:
                time.sleep(time_sec)
            event_bus.log_step(context, f"Pause durant '{time_sec:.3f}' sec.")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(WaitFixedTimeExecutor())


# EOF
