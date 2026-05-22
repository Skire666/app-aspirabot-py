"""IStepExecutor for EXTRACT_TEXT."""

from __future__ import annotations

from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.extract_text_params import ExtractTextParams
from playwright.sync_api import ElementHandle
from services.steps._helpers import extract_from_element
from services.workflow_service import register_step_executor
from shared.enums import ExtractTargetEnum, ExtractTextHtmlEnum, StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES


class ExtractTextExecutor(IStepExecutor):
    """Executor for the extract text scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXTRACT_TEXT

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = ExtractTextParams.from_dict(context.step_params)
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
        texts = [extract_from_element(el, p.extract_mode) for el in selected]

        context.last_message_step = (
            f"Texte extrait : {len(texts)} élément(s). Sél. : {p.selector!r}. Mode : {p.extract_mode!r}."
        )

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ExtractTextParams.from_dict(model.params)
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
            errors.append(ERROR_TEMPLATES["extract_text_selector_required"].format(step=index_display))
        if p.extract_mode not in allowed_modes:
            errors.append(ERROR_TEMPLATES["extract_text_mode_invalid"].format(step=index_display, value=p.extract_mode))
        if p.target not in allowed_targets:
            errors.append(ERROR_TEMPLATES["extract_text_target_invalid"].format(step=index_display, value=p.target))
        return errors


register_step_executor(ExtractTextExecutor())
