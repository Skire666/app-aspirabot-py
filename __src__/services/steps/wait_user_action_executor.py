"""IStepExecutor for WAIT_USER_ACTION."""
from __future__ import annotations
import time
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.wait_user_action_params import WaitUserActionParams
from playwright.sync_api import Page
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.step_registry import register_executor

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class WaitUserActionExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.WAIT_USER_ACTION

    def default_params_dict(self) -> dict[str, Any]:
        return WaitUserActionParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
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

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = WaitUserActionParams.from_dict(params)
        errors: list[str] = []
        if p.condition not in {"always", "success", "failure"}:
            errors.append(f"WAIT_USER_ACTION : condition invalide — {p.condition!r}.")
        if p.wait_duration < 0:
            errors.append("WAIT_USER_ACTION : wait_duration doit être >= 0.")
        if p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"WAIT_USER_ACTION : unité de temps invalide — {p.wait_unit!r}.")
        return errors


register_executor(WaitUserActionExecutor())
