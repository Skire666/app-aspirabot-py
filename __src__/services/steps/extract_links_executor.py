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
from shared.constants import C_STR_ERROR_EXTRACT_LINKS
from shared.enums import ExtractTargetEnum, ProcessResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor
from shared.url_util import transformer_url


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
    ) -> ProcessResultEnum:
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
            links: list[str] = []
            if not elements:
                event_bus.log_step(context, f"Excp : Aucun élément trouvé pour le sélecteur '{p.selector}'")
                return ProcessResultEnum.E_ERROR
            selected = self._select_elements(elements, p.target)
            parsed = urlparse(page.url)
            base_url = f"{parsed.scheme}://{parsed.netloc}"
            links = self._get_all_links_from_elements(selected, base_url, p, context)

            # push
            context.push_links_extracted(links)

            # debug log
            preview_one_item = links[0] if links and links[0] else C_STR_ERROR_EXTRACT_LINKS
            event_bus.log_step(context, f"x{len(links)} lien(s) | str[:25] ='{preview_one_item[:25]}'")
        except Exception as exc:  # ruff: ignore[blind-except]
            event_bus.log_step(context, f"Excp : {exc}")
            return ProcessResultEnum.E_ERROR
        else:
            return ProcessResultEnum.E_SUCCESS

    @staticmethod
    def _select_elements(elements: list[ElementHandle], target: ExtractTargetEnum) -> list[ElementHandle]:
        """Return the subset of elements based on the target filter.

        Args:
            elements: Full list of matching elements.
            target: Which element(s) to keep (first, last, or all).

        Returns:
            A list containing the selected element(s).
        """
        if target is ExtractTargetEnum.E_FIRST:
            return [elements[0]]
        if target is ExtractTargetEnum.E_LAST:
            return [elements[-1]]
        return elements

    @staticmethod
    def _get_all_links_from_elements(
        elements: list[ElementHandle], base_url: str, p: ExtractLinksParams, context: ScrapingContextModel
    ) -> list[str]:
        """Extract href attributes from a list of elements.

        Args:
            elements: List of ElementHandle objects to extract links from.
            base_url: The base URL to resolve relative links against.
            p: ExtractLinksParams instance containing extraction parameters.
            context: The scraping context.

        Returns:
            List of fully qualified URLs extracted from the elements.
        """
        links: list[str] = []

        for el in elements:
            href = (el.get_attribute("href") or "").strip()
            if href:
                full_url = urljoin(base_url, href)
                full_url = ExtractLinksExecutor._cut_row(full_url, context)
                links.append(full_url)
        return links

    @staticmethod
    def _cut_row(full_url: str, context: ScrapingContextModel) -> str:
        """Apply the URL cleanup options to a single extracted link.

        Args:
            full_url: Absolute URL extracted from the page.
            context: The scraping context holding the transformer options.
        """
        if context and context.transformer_url_regexp and context.transformer_url_base:
            full_url = transformer_url(
                full_url,
                context.transformer_url_regexp,
                context.transformer_url_base,
                context.transformer_url_trailing_slash,
            )
        return full_url


register_step_executor(ExtractLinksExecutor())


# EOF
