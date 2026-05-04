"""IStepExecutor for RANDOM_PAUSE."""
from __future__ import annotations
import random
import time
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.random_pause_params import RandomPauseParams
from playwright.sync_api import Page
from shared.step_registry import register_executor

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class RandomPauseExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.RANDOM_PAUSE

    def default_params_dict(self) -> dict[str, Any]:
        return RandomPauseParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = RandomPauseParams.from_dict(params)
        delay = random.uniform(float(p.min_val), float(p.max_val))
        time.sleep(delay * _MULTIPLIERS.get(p.unit, 1.0))

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = RandomPauseParams.from_dict(params)
        if p.min_val >= p.max_val:
            return ["RANDOM_PAUSE : min doit être strictement inférieur à max."]
        return []


register_executor(RandomPauseExecutor())
