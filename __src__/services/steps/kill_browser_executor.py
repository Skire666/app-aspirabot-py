"""IStepExecutor for END_PROCESS."""

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
from models.steps.kill_browser_params import KillBrowserParams
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class KillBrowserExecutor(IStepExecutor):
    """Executor for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_KILL_BROWSER

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(KillBrowserParams, context.step_scraping_data.params)
        try:
            delay = convert_to_sec(p.wait_duration, p.wait_unit)
            if delay > 0:
                time.sleep(delay)
            browser.close_all_tabs()
            context.end_process = True
            event_bus.log_step(context, "Arrêt du processus demandé.")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(KillBrowserExecutor())


# EOF
