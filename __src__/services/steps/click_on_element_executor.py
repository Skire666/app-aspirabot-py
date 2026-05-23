"""IStepExecutor for CLICK_ON_ELEMENT."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.click_on_element_params import ClickOnElementParams
from playwright.sync_api import Error as PlaywrightError
from services.workflow_service import register_step_executor
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
)
from shared.enums import StepTypeEnum
from shared.exception_util import ElementNotFoundForClickError
from shared.i18n_fra import ERROR_TEMPLATES

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

C_LIMIT_TIMEOUT_CLICK_MS = 8000

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

        result = self._do_click(browser, p.click_mode, p.selector)  # can throw

        context.last_message_step = f"Clique OK avec sélecteur {p.selector!r} avec le mode {result!r}."

    @staticmethod
    def _do_click(browser: IWebBrowserService, mode_click: str, selector: str) -> str:
        page = browser.get_current_page()

        # Tentative 1 : click normal
        try:
            if mode_click == "Normal":
                page.click(selector, timeout=C_LIMIT_TIMEOUT_CLICK_MS)
                return "Normal"
        except PlaywrightError:
            pass
        if mode_click == "Normal":
            raise ElementNotFoundForClickError(selector, "Normal")

        # Tentative 2 : click forcé
        try:
            if mode_click == "Forced":
                page.click(selector, force=True, timeout=C_LIMIT_TIMEOUT_CLICK_MS)
                return "Forced"
        except PlaywrightError:
            pass
        if mode_click == "Forced":
            raise ElementNotFoundForClickError(selector, "Forced")

        # Tentative 3 : JS direct
        script = f"document.querySelector('{selector}')?.click();"
        is_success, _ = browser.evaluate_script_with_safe_retry(
            script, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )  # can throw

        if not is_success:
            raise ElementNotFoundForClickError(selector, "JS Direct")

        return "JS Direct"

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ClickOnElementParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        # if selecteur est vide ou ne contient que des espaces
        if not p.selector.strip():
            return [ERROR_TEMPLATES["click_element_selector_required"].format(step=index_display)]
        return []


register_step_executor(ClickOnElementExecutor())
