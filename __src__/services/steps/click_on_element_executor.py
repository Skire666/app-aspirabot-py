"""IStepExecutor for CLICK_ON_ELEMENT."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.click_on_element_params import ClickOnElementParams
from shared.enums import ProcessResultEnum, StepTypeEnum
from shared.exception_util import ElementNotFoundForClickError
from shared.step_registry import register_step_executor

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# TODO PCO est en dur, pas bien. Faudrait le rendre flexible
C_LIMIT_TIMEOUT_CLICK_MS = 15000

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ClickOnElementExecutor(IStepExecutor):
    """Executor for the click element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLICK_ON_ELEMENT

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> ProcessResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(ClickOnElementParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            if page.locator(p.selector).count() <= 0:
                raise ElementNotFoundForClickError(p.selector, p.click_mode)  # ruff: ignore[raise-within-try]
            result = self._do_click(browser, p.click_mode, p.selector, p.index_clicked)
            event_bus.log_step(context, f"Clique OK avec sélecteur {p.selector!r} avec le mode {result!r}.")
        except Exception as exc:  # ruff: ignore[blind-except]
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

    @staticmethod
    def _do_click(browser: IWebBrowserService, mode_click: str, selector: str, index_clicked: int) -> str:
        page = browser.get_workflow_page()
        elements = page.query_selector_all(selector)
        if not elements:
            raise ElementNotFoundForClickError(selector, mode_click)
        element = elements[index_clicked]

        # NOTE PCO : Aucune idée de si ça plante.... (pas moyen de vérifier, pas de timeout)
        element.evaluate("element => element.click()")
        return "JS Direct"


register_step_executor(ClickOnElementExecutor())


# EOF
