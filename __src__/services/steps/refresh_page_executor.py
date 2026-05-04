"""IStepExecutor for REFRESH_PAGE."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.refresh_page_params import RefreshPageParams
from playwright.sync_api import Page
from shared.step_registry import register_executor


class RefreshPageExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.REFRESH_PAGE

    def default_params_dict(self) -> dict[str, Any]:
        return RefreshPageParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = RefreshPageParams.from_dict(params)
        if p.clear_cache:
            page.context.clear_cookies()
        page.reload()

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        return []


register_executor(RefreshPageExecutor())
