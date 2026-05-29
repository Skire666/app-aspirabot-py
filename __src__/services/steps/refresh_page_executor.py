"""IStepExecutor for REFRESH_PAGE."""

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.refresh_page_params import RefreshPageParams
from services.steps.step_executor_base import StepExecutorBase
from shared.step_registry import register_step_executor
from shared.enums import StepTypeEnum
from shared.time_util import convert_to_ms


class RefreshPageExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_REFRESH_PAGE

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(RefreshPageParams, context.step_scraping_data.params)
        page = browser.get_current_page()
        timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)

        # Clear session cookies before reload when requested.
        if p.clear_cache:
            page.context.clear_cookies()
        page.reload()
        page.wait_for_load_state(p.wait_state, timeout=timeout_ms)
        context.last_message_step = "Page rafraîchie avec succès, attente de chargement"


register_step_executor(RefreshPageExecutor())
