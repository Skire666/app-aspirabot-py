"""IStepExecutor for CLICK_ON_ELEMENT."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.click_on_element_params import ClickOnElementParams
from playwright.sync_api import ElementHandle
from playwright.sync_api import Error as PlaywrightError
from services.workflow_service import register_step_executor
from shared.enums import StepTypeEnum
from shared.exception_util import ElementNotFoundForClickError
from shared.i18n_fra import ERROR_TEMPLATES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# TODO PCO est en dur, pas bien.
# Faudrait le rendre flexible
C_LIMIT_TIMEOUT_CLICK_MS = 10000

# ---------------------------------------------------------------------------
# Class
# ---------------------------------------------------------------------------


class ClickOnElementExecutor(IStepExecutor):
    """Executor for the click element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLICK_ON_ELEMENT

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = ClickOnElementParams.from_dict(context.step_params)

        page = browser.get_current_page()  # can throw if page is closed
        if page.locator(p.selector).count() <= 0:
            raise ElementNotFoundForClickError(p.selector, p.mode)

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
        page = browser.get_current_page()
        elements = page.query_selector_all(selector)
        if not elements:
            raise ElementNotFoundForClickError(selector, mode_click)
        element = elements[index_clicked]

        # NOTE PCO : Aucune idée de si ça plante.... (pas moyen de vérifier, pas de timeout)
        element.evaluate("element => element.click()", timeout=C_LIMIT_TIMEOUT_CLICK_MS)
        return "JS Direct"

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ClickOnElementParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        if p.index_clicked <= -1:
            return [ERROR_TEMPLATES["click_element_index_invalid"].format(step=index_display)]
        # if selecteur est vide ou ne contient que des espaces
        if not p.selector.strip():
            return [ERROR_TEMPLATES["click_element_selector_required"].format(step=index_display)]
        return []


register_step_executor(ClickOnElementExecutor())
