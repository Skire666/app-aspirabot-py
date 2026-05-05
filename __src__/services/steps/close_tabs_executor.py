"""IStepExecutor for CLOSE_TABS."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.close_tabs_params import CloseTabsParams
from shared.step_registry import register_executor


class CloseTabsExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.CLOSE_TABS

    def default_params_dict(self) -> dict[str, Any]:
        return CloseTabsParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        p = CloseTabsParams.from_dict(params)
        for p_tab in list(page.context.pages):
            if p.url_filter and p_tab.url.find(p.url_filter) == -1:
                p_tab.close()
        if page.context.pages.count(page) == 0:
            raise ValueError("Current page was closed unexpectedly.")
        if p.max_tabs > 0:
            others = [t for t in page.context.pages if t is not page]
            for t in others[p.max_tabs - 1:]:
                t.close()

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = CloseTabsParams.from_dict(params)
        if p.max_tabs < 0:
            return ["CLOSE_TABS : max_tabs doit être >= 0."]
        return []


register_executor(CloseTabsExecutor())
