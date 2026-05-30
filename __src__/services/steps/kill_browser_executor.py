"""IStepExecutor for END_PROCESS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.kill_browser_params import KillBrowserParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class KillBrowserExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_KILL_BROWSER

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(KillBrowserParams, context.step_scraping_data.params)
        delay = convert_to_sec(p.wait_duration, p.wait_unit)
        if delay > 0:
            time.sleep(delay)

        browser.close_all_tabs()  # ensure all tabs are closed before signaling end-process
        context.end_process = True


register_step_executor(KillBrowserExecutor())


# EOF
