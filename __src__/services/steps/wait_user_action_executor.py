"""IStepExecutor for WAIT_USER_ACTION."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_user_action_params import WaitUserActionParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class WaitUserActionExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the wait user action scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_USER_ACTION

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(WaitUserActionParams, context.step_scraping_data.params)
        should_pause = (
            p.condition == "always"
            or (p.condition == "success" and context.last_result_step)
            or (p.condition == "failure" and not context.last_result_step)
        )
        if not should_pause:
            return
        if callable(context.on_user_wait):
            context.on_user_wait()
        context.pause_event.clear()
        context.pause_event.wait()
        cancelled = context.cancel_event.is_set()
        if p.wait_duration >= 1 and not cancelled:
            time_sec = convert_to_sec(p.wait_duration, p.wait_unit)
            time.sleep(time_sec)

        context.last_message_step = (
            "Reprise utilisateur détectée" if not cancelled else "Attente annulée par l'utilisateur"
        )


register_step_executor(WaitUserActionExecutor())


# EOF
