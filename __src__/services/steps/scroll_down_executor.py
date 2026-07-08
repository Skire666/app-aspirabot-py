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
from shared.constants import C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT, C_MAXIMUM_RETRY_EVALUATE_SCRIPT
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.exception_util import ScriptExecutionFailedError
from shared.step_registry import register_step_executor

C_LIMIT_GIVE_UP_SCROLLING = 4  # number of consecutive no-growth iterations before giving up on scrolling


class ScrollDownExecutor(IStepExecutor):
    """Executor for the scroll down scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SCROLL_DOWN

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(ScrollDownParams, context.step_scraping_data.params)
        try:
            consecutive_same_value_count = 0
            height_previous = self._get_page_height(browser)
            for idx in range(p.nbr_loops):
                if idx >= 1 and p.delay_pause >= 1:
                    time.sleep(p.delay_pause)
                self._do_scroll(browser, p)
                event_bus.log_step(context, f"Défilement de '{p.pixels}px' effectué.")
                height_new = self._get_page_height(browser)
                if height_new == height_previous:
                    consecutive_same_value_count += 1
                else:
                    consecutive_same_value_count = 0
                height_previous = height_new

                if consecutive_same_value_count >= C_LIMIT_GIVE_UP_SCROLLING:
                    event_bus.log_step(context, "Page stabilisée, arrêt du défilement.")
                    break
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

    @staticmethod
    def _get_page_height(browser: IWebBrowserService) -> int:
        """Return the current page height by evaluating a script with retries."""
        success, values = browser.evaluate_script_with_safe_retry(
            "document.documentElement.scrollHeight",
            C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
            C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
        )
        if not success:
            return 0
        return int(str(values)) if values is not None else 0

    @staticmethod
    def _do_scroll(browser: IWebBrowserService, p: ScrollDownParams) -> None:
        """Execute the scrollBy script with retries."""
        is_success, _ = browser.evaluate_script_with_safe_retry(
            f"window.scrollBy(0, {p.pixels})", C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )
        if not is_success:
            raise ScriptExecutionFailedError("scroll_down")


register_step_executor(ScrollDownExecutor())


# EOF
