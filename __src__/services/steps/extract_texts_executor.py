"""IStepExecutor for EXTRACT_TEXTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_texts_params import ExtractTextsParams
from playwright.sync_api import ElementHandle
from services.steps._helpers import extract_from_element
from shared.enums import ExtractTargetEnum, StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor


class ExtractTextsExecutor(IStepExecutor):
    """Executor for the extract text scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type handled by this executor.

        Returns:
            StepTypeEnum.E_EXTRACT_TEXTS — used by the registry to dispatch to this executor.
        """
        return StepTypeEnum.E_EXTRACT_TEXTS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Query the selector, apply the target filter, and extract text into the context.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context; step params is read.
            event_bus: Event bus for intermediate log entries.
        """
        assert context.step_scraping_data is not None
        p = cast(ExtractTextsParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            elements: list[ElementHandle] = page.query_selector_all(p.selector)
            if not elements:
                raise ValueError(f"Aucun élément pour le sélecteur '{p.selector}'")
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
            event_bus.log_step(context, f"x{len(texts)} texte(s) | str[:35] ='{debug_one_item[:35]}'")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(ExtractTextsExecutor())


# EOF
