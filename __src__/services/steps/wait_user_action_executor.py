"""IStepExecutor for WAIT_USER_ACTION."""

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
from models.steps.wait_user_action_params import WaitUserActionParams
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_sec


class WaitUserActionExecutor(IStepExecutor):
    """Executor for the wait user action scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_USER_ACTION

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(WaitUserActionParams, context.step_scraping_data.params)
        try:
            if not self._should_pause(p, context):
                return ProcessResultEnum.E_SKIPPED
            self._do_pause(context, p, event_bus)
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

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
    def _do_pause(context: ScrapingContextModel, p: WaitUserActionParams, event_bus: IScrapingEventBus) -> None:
        """Block until the user resumes or the scraping is cancelled.

        Args:
            context: Current scraping context.
            p: Step parameters.
            event_bus: Event bus for emitting the resume/cancel log entry.
        """
        if callable(context.on_user_wait):
            context.on_user_wait()
        context.pause_event.clear()
        context.pause_event.wait()
        cancelled = context.cancel_event.is_set()
        if p.wait_duration >= 1 and not cancelled:
            time.sleep(convert_to_sec(p.wait_duration, p.wait_unit))
        msg = "Reprise utilisateur détectée" if not cancelled else "Attente annulée par l'utilisateur"
        event_bus.log_step(context, msg)


register_step_executor(WaitUserActionExecutor())


# EOF
