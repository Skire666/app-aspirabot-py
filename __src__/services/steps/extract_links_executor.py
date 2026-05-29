"""IStepExecutor for EXTRACT_LINKS."""

from __future__ import annotations

from typing import cast, override
from urllib.parse import urljoin, urlparse

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_links_params import ExtractLinksParams
from playwright.sync_api import ElementHandle
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import ExtractTargetEnum, StepTypeEnum
from shared.step_registry import register_step_executor


class ExtractLinksExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the extract links scraping step."""

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

        Reads ExtractLinksParams from context step params, queries all matching DOM
        elements, filters to first, last, or all per the target param, then extracts
        links. Writes a summary to context.last_message_step.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context; step params is read and last_message_step is written.
        """
        p = cast(ExtractLinksParams, context.step_scraping_data.params)
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

        context.push_extracted_values(p.mapping, p.selector, p.comment, links)
        debug_one_item = links[0] if links and links[0] else "<no link>"
        context.last_message_step = f"Extrait x{len(links)} lien(s) | Debug='{debug_one_item}'."

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


register_step_executor(ExtractLinksExecutor())
