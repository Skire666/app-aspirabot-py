"""IStepExecutor for CLICK_ON_ELEMENT."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.click_on_element_params import ClickOnElementParams
from playwright.sync_api import ElementHandle
from playwright.sync_api import Error as PlaywrightError
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.exception_util import ElementNotFoundForClickError
from shared.step_registry import register_step_executor

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------

# TODO PCO est en dur, pas bien.
# Faudrait le rendre flexible
C_LIMIT_TIMEOUT_CLICK_MS = 10000

# -----------------------------------------------------------------------------
# Class
# -----------------------------------------------------------------------------


class ClickOnElementExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the click element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLICK_ON_ELEMENT

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(ClickOnElementParams, context.step_scraping_data.params)

        page = browser.get_workflow_page()  # can throw if page is closed
        if page.locator(p.selector).count() <= 0:
            raise ElementNotFoundForClickError(p.selector, p.click_mode)

        result = self._do_click(browser, p.click_mode, p.selector, p.index_clicked)  # can throw

        context.last_message_step = f"Clique OK avec sélecteur {p.selector!r} avec le mode {result!r}."

    @staticmethod
    def _try_normal_click(element: ElementHandle) -> bool:
        try:
            element.click(timeout=C_LIMIT_TIMEOUT_CLICK_MS)
        except PlaywrightError:
            return False
        else:
            return True

    @staticmethod
    def _try_forced_click(element: ElementHandle) -> bool:
        try:
            element.click(force=True, timeout=C_LIMIT_TIMEOUT_CLICK_MS)
        except PlaywrightError:
            return False
        else:
            return True

    @staticmethod
    def _do_click(browser: IWebBrowserService, mode_click: str, selector: str, index_clicked: int) -> str:
        page = browser.get_workflow_page()
        elements = page.query_selector_all(selector)
        if not elements:
            raise ElementNotFoundForClickError(selector, mode_click)
        element = elements[index_clicked]

        # NOTE PCO : Aucune idée de si ça plante.... (pas moyen de vérifier, pas de timeout)
        element.evaluate("element => element.click()", timeout=C_LIMIT_TIMEOUT_CLICK_MS)
        return "JS Direct"


register_step_executor(ClickOnElementExecutor())


# EOF
