"""IStepExecutor for SCROLL_DOWN."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import time
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.scroll_down_params import ScrollDownParams
from services.steps.step_executor_base import StepExecutorBase
from shared.constants import C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT, C_MAXIMUM_RETRY_EVALUATE_SCRIPT
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import ScriptExecutionFailedError
from shared.step_registry import register_step_executor


class ScrollDownExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(ScrollDownParams, context.step_scraping_data.params)
        try:
            consecutive_no_growth, previous_height = 0, self._get_page_height(browser)
            for idx in range(p.nbr_loops):
                if idx >= 1 and p.delay_pause > 0:
                    time.sleep(p.delay_pause)
                self._do_scroll(browser, p)
                event_bus.log_step(context, f"Défilement de {p.pixels}px effectué.")
                previous_height, consecutive_no_growth = self._is_page_growing(
                    browser, previous_height, consecutive_no_growth
                )
                if consecutive_no_growth >= 5:
                    event_bus.log_step(context, "Page stabilisée, arrêt du défilement.")
                    return False
            return True
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS

    def _get_page_height(self, browser) -> int:
        return browser.evaluate_script("document.documentElement.scrollHeight")

    def _is_page_growing(self, browser, previous_height: int, consecutive_no_growth: int) -> tuple[int, int]:
        new_height = self._get_page_height(browser)
        growing = new_height > previous_height
        return new_height if growing else previous_height, 0 if growing else consecutive_no_growth + 1

    def _do_scroll(self, browser, p) -> None:
        is_success, _ = browser.evaluate_script_with_safe_retry(
            f"window.scrollBy(0, {p.pixels})", C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )
        if not is_success:
            raise ScriptExecutionFailedError("scroll_down")


register_step_executor(ScrollDownExecutor())


# EOF
