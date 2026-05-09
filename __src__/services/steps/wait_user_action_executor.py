"""IStepExecutor for WAIT_USER_ACTION."""

from __future__ import annotations

import time
from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_user_action_params import WaitUserActionParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class WaitUserActionExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_USER_ACTION

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitUserActionParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitUserActionParams.from_dict(params)
        prev_success: bool = params.get("_prev_success", True)
        should_pause = (
            p.condition == "always"
            or (p.condition == "success" and prev_success)
            or (p.condition == "failure" and not prev_success)
        )
        if not should_pause:
            return
        on_user_wait = params.get("_on_user_wait")
        if callable(on_user_wait):
            on_user_wait()
        pause_event = params.get("_pause_event")
        if pause_event is not None:
            pause_event.clear()
            pause_event.wait()
        cancel_event = params.get("_cancel_event")
        cancelled = cancel_event is not None and cancel_event.is_set()
        if p.wait_duration > 0 and not cancelled:
            time.sleep(float(p.wait_duration) * _MULTIPLIERS.get(p.wait_unit, 1.0))

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitUserActionParams.from_dict(model.params)
        errors: list[str] = []
        index_display = str(step_index + 1).zfill(2)
        if p.condition not in {"always", "success", "failure"}:
            errors.append(f"Dans l'étape {index_display}. : condition invalide — {p.condition!r}.")
        if p.wait_duration < 0:
            errors.append(f"Dans l'étape {index_display}. : wait_duration doit être >= 0.")
        if p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : unité de temps invalide — {p.wait_unit!r}.")
        return errors


register_step_executor(WaitUserActionExecutor())
