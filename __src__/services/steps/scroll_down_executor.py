"""IStepExecutor for SCROLL_DOWN."""

from __future__ import annotations

from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.scroll_down_params import ScrollDownParams
from services.steps._helpers import evaluate_script_with_safe_retry
from services.workflow_service import register_step_executor


class ScrollDownExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.SCROLL_DOWN

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return ScrollDownParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = ScrollDownParams.from_dict(params)
        evaluate_script_with_safe_retry(page, f"window.scrollBy(0, {p.pixels})", 5)

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        # always valid as there are no parameters with constraints
        return []


register_step_executor(ScrollDownExecutor())
