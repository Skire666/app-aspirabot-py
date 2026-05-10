"""IStepExecutor for REFRESH_PAGE."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.refresh_page_params import RefreshPageParams
from services.workflow_service import register_step_executor


class RefreshPageExecutor(IStepExecutor):
    """Executor for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.REFRESH_PAGE

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return RefreshPageParams.default().to_dict()

    @override
    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = RefreshPageParams.from_dict(params)
        if p.clear_cache:
            page.context.clear_cookies()
        page.reload()

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        # always valid as there are no parameters with constraints
        return []


register_step_executor(RefreshPageExecutor())
