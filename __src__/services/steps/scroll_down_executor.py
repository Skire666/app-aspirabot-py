"""IStepExecutor for SCROLL_DOWN."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.scroll_down_params import ScrollDownParams
from shared.step_registry import register_executor
from services.steps._helpers import evaluate_script_with_safe_retry


class ScrollDownExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.SCROLL_DOWN

    def default_params_dict(self) -> dict[str, Any]:
        return ScrollDownParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        p = ScrollDownParams.from_dict(params)
        evaluate_script_with_safe_retry(page, f"window.scrollBy(0, {p.pixels})", 5)

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        return []


register_executor(ScrollDownExecutor())
