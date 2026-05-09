"""IStepExecutor for OPEN_URL."""

from __future__ import annotations

from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.open_url_params import OpenUrlParams
from services.steps._helpers import resolve_timeout_ms
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL


class OpenUrlExecutor(IStepExecutor):
    """Executor for the open URL scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.OPEN_URL

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return OpenUrlParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = OpenUrlParams.from_dict(params)
        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        if timeout_ms is not None:
            page.goto(p.url, wait_until=p.wait_state, timeout=timeout_ms)
        else:
            page.goto(p.url, wait_until=p.wait_state)

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = OpenUrlParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        errors: list[str] = []
        if not p.url.strip():
            errors.append(f"Dans l'étape {index_display}. : l'URL est obligatoire.")
        if p.timeout_duration < 0:
            errors.append(f"Dans l'étape {index_display}. : timeout_duration doit être >= 0.")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : timeout_unit invalide - {p.timeout_unit}.")
        return errors


register_step_executor(OpenUrlExecutor())
