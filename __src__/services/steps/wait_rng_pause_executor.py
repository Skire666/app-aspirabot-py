"""IStepExecutor for RANDOM_PAUSE."""

from __future__ import annotations

import random
import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_rng_pause_params import WaitRngPauseParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_CONVERSION_TO_SEC


class WaitRngPauseExecutor(IStepExecutor):
    """Executor for the random pause scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_RANDOM_PAUSE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitRngPauseParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitRngPauseParams.from_dict(params)
        delay = random.uniform(float(p.min_val), float(p.max_val))
        time.sleep(delay * C_UNITS_TIME_CONVERSION_TO_SEC.get(p.unit, 1.0))

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitRngPauseParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.min_val <= 0:
            return [f"Dans l'étape {index_display}. : min doit être >= 1"]
        if p.max_val <= 0:
            return [f"Dans l'étape {index_display}. : max doit être >= 1"]
        if p.min_val > p.max_val:
            return [f"Dans l'étape {index_display}. : min doit être inférieur ou égale à max."]
        return []


register_step_executor(WaitRngPauseExecutor())
