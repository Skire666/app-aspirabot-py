"""IStepExecutor for EXTRACT_TEXTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_texts_params import ExtractTextsParams
from playwright.sync_api import ElementHandle
from services.steps._helpers import extract_from_element
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import ExtractTargetEnum, StepTypeEnum
from shared.step_registry import register_step_executor


class ExtractTextsExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the extract text scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type handled by this executor.

        Returns:
            StepTypeEnum.E_EXTRACT_TEXTS — used by the registry to dispatch to this executor.
        """
        return StepTypeEnum.E_EXTRACT_TEXTS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Query the selector, apply the target filter, and extract text into the context.

        Reads ExtractTextsParams from context step params, queries all matching DOM
        elements, filters to first, last, or all per the target param, then extracts
        text using the configured mode. Writes a summary to context.last_message_step.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context; step params is read and last_message_step is written.
        """
        p = cast(ExtractTextsParams, context.step_scraping_data.params)
        page = browser.get_workflow_page()

        elements: list[ElementHandle] = page.query_selector_all(p.selector)
        if not elements:
            return
        selected: list[ElementHandle] = (
            [elements[0]]
            if p.target == ExtractTargetEnum.E_FIRST
            else [elements[-1]]
            if p.target == ExtractTargetEnum.E_LAST
            else elements  # all
        )
        texts: list[str] = [extract_from_element(el, p.extract_mode) for el in selected]

        context.push_extracted_values(p.mapping, p.selector, p.comment, texts)
        debug_one_item = texts[0] if texts and texts[0] else "<no text>"
        context.last_message_step = f"Extrait x{len(texts)} texte(s) | Debug='{debug_one_item}'."


register_step_executor(ExtractTextsExecutor())


# EOF
