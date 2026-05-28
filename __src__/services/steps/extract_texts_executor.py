"""IStepExecutor for EXTRACT_TEXTS."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.extract_texts_params import ExtractTextsParams
from playwright.sync_api import ElementHandle
from services.steps._helpers import extract_from_element
from services.workflow_service import register_step_executor
from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum, StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES


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
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Query the selector, apply the target filter, and extract text into the context.

        Reads ExtractTextParams from context.step_params, queries all matching DOM
        elements, filters to first, last, or all per the target param, then extracts
        text using the configured mode. Writes a summary to context.last_message_step.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context; step_params is read and last_message_step is written.
        """
        p = ExtractTextsParams.from_dict(context.step_params)
        page = browser.get_current_page()

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

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Check that selector, extract_mode, and target are all valid.

        Args:
            model: The step model whose params dict is inspected.
            step_index: Zero-based index used to format error messages.

        Returns:
            List of user-facing error strings; empty when the model is valid.
        """
        p = ExtractTextsParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        allowed_modes = {
            ExtractTextHtmlEnum.E_INNER_TEXT.value,
            ExtractTextHtmlEnum.E_TEXT_CONTENT.value,
            ExtractTextHtmlEnum.E_OUTER_HTML.value,
            ExtractTextHtmlEnum.E_INNER_HTML.value,
            ExtractTextHtmlEnum.E_INPUT_VALUE.value,
        }
        allowed_targets = {
            ExtractTargetEnum.E_FIRST.value,
            ExtractTargetEnum.E_LAST.value,
            ExtractTargetEnum.E_ALL.value,
        }
        errors: list[str] = []

        if not p.selector.strip():
            errors.append(ERROR_TEMPLATES["extract_texts_selector_required"].format(step=index_display))
        if p.extract_mode not in allowed_modes:
            errors.append(
                ERROR_TEMPLATES["extract_texts_mode_invalid"].format(step=index_display, value=p.extract_mode),
            )
        if p.target not in allowed_targets:
            errors.append(ERROR_TEMPLATES["extract_texts_target_invalid"].format(step=index_display, value=p.target))
        if not p.mapping.strip():
            errors.append(ERROR_TEMPLATES["extract_texts_mapping_required"].format(step=index_display))
        return errors


register_step_executor(ExtractTextsExecutor())
