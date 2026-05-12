"""IStepExecutor for WAIT_X_TIME."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_x_time_params import WaitXTimeParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_CONVERSION_TO_SEC


class WaitXTimeExecutor(IStepExecutor):
    """Executor for the wait X time scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_X_TIME

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitXTimeParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitXTimeParams.from_dict(params)
        time.sleep(p.duration * C_UNITS_TIME_CONVERSION_TO_SEC.get(p.unit, 1.0))

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitXTimeParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.duration < 0:
            return [f"Dans l'étape {index_display}. : La durée d'attente doit être égale ou supérieure à 0."]
        return []


register_step_executor(WaitXTimeExecutor())
