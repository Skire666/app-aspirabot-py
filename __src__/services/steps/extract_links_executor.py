"""IStepExecutor for EXTRACT_LINKS."""

from __future__ import annotations

from typing import override
from urllib.parse import urljoin, urlparse

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.extract_links_params import ExtractLinksParams
from playwright.sync_api import ElementHandle
from services.workflow_service import register_step_executor
from shared.enums import ExtractTargetEnum, StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES


class ExtractLinksExecutor(IStepExecutor):
    """Executor for the extract text scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type handled by this executor.

        Returns:
            StepTypeEnum.E_EXTRACT_LINKS — used by the registry to dispatch to this executor.
        """
        return StepTypeEnum.E_EXTRACT_LINKS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Query the selector, apply the target filter, and extract links into the context.

        Reads ExtractTextParams from context.step_params, queries all matching DOM
        elements, filters to first, last, or all per the target param, then extracts
        links using the configured mode. Writes a summary to context.last_message_step.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context; step_params is read and last_message_step is written.
        """
        p = ExtractLinksParams.from_dict(context.step_params)
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

        parsed = urlparse(page.url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        links: list[str] = self._get_all_links_from_elements(selected, base_url)

        debug_one_item = links[0] if links and links[0] else "<no link>"
        context.last_message_step = f"Extrait x{len(links)} lien(s) | Debug='{debug_one_item}'."
        context.push_extracted_values(p.mapping, links)

    @staticmethod
    def _get_all_links_from_elements(elements: list[ElementHandle], base_url: str) -> list[str]:
        """Extract href attributes from a list of elements.

        Args:
            elements: List of ElementHandle objects to extract links from.
            base_url: The base URL to resolve relative links against.

        Returns:
            List of fully qualified URLs extracted from the elements.
        """
        links: list[str] = []

        for el in elements:
            href = el.get_attribute("href")
            if href.strip():
                full_url = urljoin(base_url, href.strip())
                links.append(full_url)
        return links

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Check that selector, extract_mode, and target are all valid.

        Args:
            model: The step model whose params dict is inspected.
            step_index: Zero-based index used to format error messages.

        Returns:
            List of user-facing error strings; empty when the model is valid.
        """
        p = ExtractLinksParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        allowed_targets = {
            ExtractTargetEnum.E_FIRST.value,
            ExtractTargetEnum.E_LAST.value,
            ExtractTargetEnum.E_ALL.value,
        }
        errors: list[str] = []

        if not p.selector.strip():
            errors.append(ERROR_TEMPLATES["extract_links_selector_required"].format(step=index_display))
        if p.target not in allowed_targets:
            errors.append(ERROR_TEMPLATES["extract_links_target_invalid"].format(step=index_display, value=p.target))
        if not p.mapping.strip():
            errors.append(ERROR_TEMPLATES["extract_links_mapping_required"].format(step=index_display))
        return errors


register_step_executor(ExtractLinksExecutor())
