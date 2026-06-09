"""IStepExecutor for EXTRACT_LINKS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override
from urllib.parse import urljoin, urlparse

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_links_params import ExtractLinksParams
from playwright.sync_api import ElementHandle
from shared.enums import ExtractTargetEnum, StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor


class ExtractLinksExecutor(IStepExecutor):
    """Executor for the extract links scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type handled by this executor.

        Returns:
            StepTypeEnum.E_EXTRACT_LINKS — used by the registry to dispatch to this executor.
        """
        return StepTypeEnum.E_EXTRACT_LINKS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Query the selector, apply the target filter, and extract links into the context.

        Args:
            browser: Live browser service providing the current Playwright page.
            context: Scraping context.
            event_bus: Event bus for intermediate log entries.
        """
        assert context.step_scraping_data is not None
        p = cast(ExtractLinksParams, context.step_scraping_data.params)
        try:
            page = browser.get_workflow_page()
            elements: list[ElementHandle] = page.query_selector_all(p.selector)
            if not elements:
                return StepExecutionResultEnum.E_SUCCESS
            selected: list[ElementHandle] = (
                [elements[0]]
                if p.target == ExtractTargetEnum.E_FIRST
                else [elements[-1]]
                if p.target == ExtractTargetEnum.E_LAST
                else elements  # all
            )
            parsed = urlparse(page.url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            links: list[str] = self._get_all_links_from_elements(selected, base_url, p.cutted_ampersand)
            context.push_extracted_values(p.mapping, p.selector, p.comment, links)
            debug_one_item = links[0] if links and links[0] else "<no link>"
            event_bus.log_step(context, f"Extrait x{len(links)} lien(s) | Debug='{debug_one_item}'.")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS

    @staticmethod
    def _get_all_links_from_elements(elements: list[ElementHandle], base_url: str, cutted_ampersand: bool) -> list[str]:
        """Extract href attributes from a list of elements.

        Args:
            elements: List of ElementHandle objects to extract links from.
            base_url: The base URL to resolve relative links against.
            cutted_ampersand: Whether to cut the ampersand from the links.

        Returns:
            List of fully qualified URLs extracted from the elements.
        """
        links: list[str] = []

        for el in elements:
            href = (el.get_attribute("href") or "").strip()
            if href:
                full_url = urljoin(base_url, href)
                if cutted_ampersand:
                    # anti-youtube and random extra query params
                    links.append(full_url.split("&")[0])
                else:
                    links.append(full_url)
        return links


register_step_executor(ExtractLinksExecutor())


# EOF
