"""IStepExecutor for WAIT_USER_ACTION."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_user_action_params import WaitUserActionParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL, C_UNITS_TIME_CONVERSION_TO_SEC


class WaitUserActionExecutor(IStepExecutor):
    """Executor for the wait user action scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_USER_ACTION

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitUserActionParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = WaitUserActionParams.from_dict(context.step_params)
        should_pause = (
            p.condition == "always"
            or (p.condition == "success" and context.prev_success)
            or (p.condition == "failure" and not context.prev_success)
        )
        if not should_pause:
            return
        if callable(context.on_user_wait):
            context.on_user_wait()
        context.pause_event.clear()
        context.pause_event.wait()
        cancelled = context.cancel_event.is_set()
        if p.wait_duration >= 1 and not cancelled:
            time.sleep(float(p.wait_duration) * C_UNITS_TIME_CONVERSION_TO_SEC.get(p.wait_unit, 1.0))

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitUserActionParams.from_dict(model.params)
        errors: list[str] = []
        index_display = str(step_index + 1).zfill(2)
        if p.condition not in {"always", "success", "failure"}:
            errors.append(f"Dans l'étape {index_display}. : condition invalide — {p.condition!r}.")
        if p.wait_duration <= 0:
            errors.append(f"Dans l'étape {index_display}. : wait_duration doit être >= 1.")
        if p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : unité de temps invalide — {p.wait_unit!r}.")
        return errors


register_step_executor(WaitUserActionExecutor())
