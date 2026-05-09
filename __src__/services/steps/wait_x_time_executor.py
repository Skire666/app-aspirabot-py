"""IStepExecutor for WAIT_X_TIME."""

from __future__ import annotations

import time
from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_x_time_params import WaitXTimeParams
from services.workflow_service import register_step_executor

_MULTIPLIERS = {"m": 60.0, "s": 1.0, "ms": 0.001}


class WaitXTimeExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_X_TIME

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitXTimeParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitXTimeParams.from_dict(params)
        time.sleep(p.duration * _MULTIPLIERS.get(p.unit, 1.0))

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitXTimeParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.duration < 0:
            return [f"Dans l'étape {index_display}. : La durée d'attente doit être égale ou supérieure à 0."]
        return []


register_step_executor(WaitXTimeExecutor())
