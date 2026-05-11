"""IStepExecutor for RANDOM_PAUSE."""

from __future__ import annotations

import random
import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.random_pause_params import RandomPauseParams
from services.workflow_service import register_step_executor

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class RandomPauseExecutor(IStepExecutor):
    """Executor for the random pause scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_RANDOM_PAUSE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return RandomPauseParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = RandomPauseParams.from_dict(params)
        delay = random.uniform(float(p.min_val), float(p.max_val))
        time.sleep(delay * _MULTIPLIERS.get(p.unit, 1.0))

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = RandomPauseParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.min_val >= p.max_val:
            return [f"Dans l'étape {index_display}. : min doit être strictement inférieur à max."]
        return []


register_step_executor(RandomPauseExecutor())
