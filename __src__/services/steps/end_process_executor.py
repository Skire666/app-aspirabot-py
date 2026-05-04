"""IStepExecutor for END_PROCESS."""
from __future__ import annotations
import time
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.end_process_params import EndProcessParams
from playwright.sync_api import Page
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.step_registry import register_executor

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class EndProcessExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.END_PROCESS

    def default_params_dict(self) -> dict[str, Any]:
        return EndProcessParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = EndProcessParams.from_dict(params)
        delay = float(p.wait_duration) * _MULTIPLIERS.get(p.wait_unit, 1.0)
        if delay > 0:
            time.sleep(delay)
        # Signal end-process to the service via the mutable params dict.
        params["_end_process"] = True

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = EndProcessParams.from_dict(params)
        errors: list[str] = []
        if p.wait_duration < 0:
            errors.append("END_PROCESS : wait_duration doit être >= 0.")
        if p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"END_PROCESS : unité de temps invalide — {p.wait_unit!r}.")
        return errors


register_executor(EndProcessExecutor())
