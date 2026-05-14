"""IStepExecutor for CLICK_ELEMENT."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.click_element_params import ClickElementParams
from presenters.messages import ERROR_TEMPLATES
from services.workflow_service import register_step_executor
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
)
from shared.enums import StepTypeEnum
from shared.exception_util import ElementNotFoundForClickError

C_LIMIT_TIMEOUT_CLICK_MS = 8000


class ClickElementExecutor(IStepExecutor):
    """Executor for the click element scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_CLICK_ELEMENT

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return ClickElementParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = ClickElementParams.from_dict(context.step_params)

        context.last_message_step = (
            f"Élément cliqué avec succès pour le sélecteur {p.selector!r} avec le mode {p.click_mode!r}."
        )

    def _do_click(browser: IWebBrowserService, mode_click: str, selector: str) -> str:
        page = browser.get_current_page()

        # Tentative 1 : click normal
        try:
            if mode_click == "Normal":
                page.click(selector, timeout=C_LIMIT_TIMEOUT_CLICK_MS)
                return "Normal"
        except Exception:
            pass
        if mode_click == "Normal":
            raise ElementNotFoundForClickError(selector, "Normal")

        # Tentative 2 : click forcé
        try:
            if mode_click == "Forced":
                page.click(selector, force=True, timeout=C_LIMIT_TIMEOUT_CLICK_MS)
                return "Forced"
        except Exception:
            pass
        if mode_click == "Forced":
            raise ElementNotFoundForClickError(selector, "Forced")

        # Tentative 3 : JS direct
        script = f"document.querySelector('{selector}')?.click();"
        browser.evaluate_script_with_safe_retry(
            script, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )  # can throw

        return "JS Direct"

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ClickElementParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        # if selecteur est vide ou ne contient que des espaces
        if not p.selector.strip():
            return [ERROR_TEMPLATES["click_element_selector_required"].format(step=index_display)]
        return []


register_step_executor(ClickElementExecutor())
