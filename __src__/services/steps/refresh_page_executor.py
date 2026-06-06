"""IStepExecutor for REFRESH_PAGE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.refresh_page_params import RefreshPageParams
from services.steps.step_executor_base import StepExecutorBase
from shared.converter_util import convert_wait_until_to_literals
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.time_util import convert_to_ms


class RefreshPageExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the refresh page scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_REFRESH_PAGE

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(RefreshPageParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            timeout_ms = convert_to_ms(p.timeout_duration, p.timeout_unit)
            cast_wait_time = convert_wait_until_to_literals(p.wait_until)
            if p.clear_cache:
                page.context.clear_cookies()
            page.reload()
            page.wait_for_load_state(cast_wait_time, timeout=timeout_ms)
            event_bus.log_step(context, "Page rafraîchie avec succès, attente de chargement")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Erreur : {exc}")
            return StepExecutionResultEnum.ERROR
        else:
            return StepExecutionResultEnum.SUCCESS


register_step_executor(RefreshPageExecutor())


# EOF
