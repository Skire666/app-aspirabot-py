"""IStepExecutor for SLEEP_X_TIME."""
from __future__ import annotations
import time
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.sleep_x_time_params import SleepXTimeParams
from playwright.sync_api import Page
from shared.step_registry import register_executor

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class SleepXTimeExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.SLEEP_X_TIME

    def default_params_dict(self) -> dict[str, Any]:
        return SleepXTimeParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = SleepXTimeParams.from_dict(params)
        time.sleep(p.duration * _MULTIPLIERS.get(p.unit, 1.0))

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = SleepXTimeParams.from_dict(params)
        if p.duration < 0:
            return ["SLEEP_X_TIME : duration doit être >= 0."]
        return []


register_executor(SleepXTimeExecutor())
