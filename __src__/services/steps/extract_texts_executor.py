"""IStepExecutor for EXTRACT_TEXTS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_texts_params import ExtractTextsParams
from playwright.sync_api import ElementHandle
from services.steps._helpers import extract_from_element
from shared.constants import C_STR_ERROR_EXTRACT_TEXTS
from shared.enums import ExtractTargetEnum, ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor

_logger = logging.getLogger(__name__)


class ExtractTextsExecutor(IStepExecutor):
    """Executor for the extract text scraping step."""

    @classmethod
    def _select_elements(cls, elements: list[ElementHandle], target: ExtractTargetEnum) -> list[ElementHandle]:
        """Return the elements matching the extraction target."""
        if target is ExtractTargetEnum.E_FIRST:
            return [elements[0]]
        if target is ExtractTargetEnum.E_LAST:
            return [elements[-1]]
        return elements  # all

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
    ) -> ProcessResultEnum:
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
                event_bus.log_step(context, f"Excp : Aucun élément trouvé pour le sélecteur '{p.selector}'")
                return ProcessResultEnum.E_ERROR

            selected: list[ElementHandle] = self._select_elements(elements, p.target)
            if not selected:
                event_bus.log_step(context, f"Excp : Aucune sélection trouvée pour le sélecteur '{p.selector}'")
                return ProcessResultEnum.E_ERROR

            texts: list[str] = [extract_from_element(el, p.extract_mode) for el in selected]
            if not texts:
                event_bus.log_step(context, f"Excp : Aucun texte extrait pour le sélecteur '{p.selector}'")
                return ProcessResultEnum.E_ERROR

            # push
            context.push_texts_extracted(p.mapping, texts, p.target)

            # infos
            preview_one_item = texts[0] if texts and texts[0] else C_STR_ERROR_EXTRACT_TEXTS
            event_bus.log_step(context, f"x{len(texts)} texte(s) | str[:25] ='{preview_one_item[:25]}'")
        except Exception as exc:
            _logger.exception("An error occurred while extracting texts.")
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS


register_step_executor(ExtractTextsExecutor())


# EOF
