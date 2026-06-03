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
        assert context.step_scraping_data is not None
        p = cast(WaitUserActionParams, context.step_scraping_data.params)
        if not self._should_pause(p, context):
            return
        self._do_pause(context, p)

    @staticmethod
    def _should_pause(p: WaitUserActionParams, context: ScrapingContextModel) -> bool:
        """Determine whether this step must pause execution.

        Args:
            p: Step parameters.
            context: Current scraping context.

        Returns:
            True if the step must pause.
        """
        if p.condition == "always":
            return True
        if p.condition == "success":
            return bool(context.last_result_step)
        if p.condition == "failure":
            return not context.last_result_step
        return False

    @staticmethod
    def _do_pause(context: ScrapingContextModel, p: WaitUserActionParams) -> None:
        """Block until the user resumes or the scraping is cancelled.

        Args:
            context: Current scraping context.
            p: Step parameters.
        """
        if callable(context.on_user_wait):
            context.on_user_wait()
        context.pause_event.clear()
        context.pause_event.wait()
        cancelled = context.cancel_event.is_set()
        if p.wait_duration >= 1 and not cancelled:
            time.sleep(convert_to_sec(p.wait_duration, p.wait_unit))
        context.last_message_step = (
            "Reprise utilisateur détectée" if not cancelled else "Attente annulée par l'utilisateur"
        )


register_step_executor(WaitUserActionExecutor())


# EOF
