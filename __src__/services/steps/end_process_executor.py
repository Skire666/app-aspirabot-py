"""IStepExecutor for END_PROCESS."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.end_process_params import EndProcessParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL, C_UNITS_TIME_CONVERSION_TO_SEC


class EndProcessExecutor(IStepExecutor):
    """Executor for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.END_PROCESS

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return EndProcessParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = EndProcessParams.from_dict(params)
        delay = float(p.wait_duration) * C_UNITS_TIME_CONVERSION_TO_SEC.get(p.wait_unit, 1.0)
        if delay > 0:
            time.sleep(delay)
        # Signal end-process to the service via the mutable params dict.
        params["_end_process"] = True

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = EndProcessParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        errors: list[str] = []
        if p.wait_duration < 0:
            errors.append(f"Erreur dans l'étape {index_display}. : wait_duration doit être >= 0.")
        if p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Erreur dans l'étape {index_display}. : unité de temps invalide — {p.wait_unit!r}.")
        return errors


register_step_executor(EndProcessExecutor())
