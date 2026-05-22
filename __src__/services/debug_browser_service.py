"""DOM inspection service for a live Playwright-controlled page.

Provides stateless utilities to extract HTML content, text metrics, and
image metadata from a caller-supplied Page object, without coupling to
the scraping workflow lifecycle.

Example:
    >>> svc = DebugBrowserService()
    >>> html = svc.get_html_content(page)
    >>> result = svc.analyze_texts(page, "h1")
"""

# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------

from __future__ import annotations

import logging
from urllib.parse import urlparse

from playwright.sync_api import Page

# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------


class DebugBrowserService:
    """DOM inspection utilities for a live Playwright page.

    All methods are stateless — they operate on a caller-supplied Page
    object and are safe to call from any thread that owns the sync context.

    Example:
        >>> svc = DebugBrowserService()
        >>> html = svc.get_html_content(page)
    """

    def __init__(self) -> None:
        """Initializes the service."""
        self._logger = logging.getLogger(__name__)

    @staticmethod
    def get_html_content(page: Page) -> str:
        """Returns the current full HTML content of the page.

        Args:
            page: Live Playwright Page object.

        Returns:
            Raw HTML string of the page's current DOM state.
        """
        return page.content()

    @staticmethod
    def analyze_texts(page: Page, selector: str) -> dict[str, object]:
        """Extracts text metrics for the first element matching the selector.

        Args:
            page: Live Playwright Page object.
            selector: CSS selector to query.

        Returns:
            Dict with keys: count, innerHTML, textContent, innerText, outerText.
            Only ``count`` is present (value 0) when no elements are found.
        """
        elements = page.query_selector_all(selector)
        count = len(elements)
        if count == 0:
            return {"count": 0}

        # Evaluate DOM properties via JS on the first matched element.
        first = elements[0]
        return {
            "count": count,
            "innerHTML": first.evaluate("el => el.innerHTML") or "",
            "textContent": first.evaluate("el => el.textContent") or "",
            "innerText": first.evaluate("el => el.innerText") or "",
            "outerText": first.evaluate("el => el.outerText") or "",
        }

    def analyze_images(self, page: Page, selector: str) -> list[dict[str, object]]:
        """Extracts metadata for each image element matching the selector.

        Args:
            page: Live Playwright Page object.
            selector: CSS selector targeting image elements.

        Returns:
            List of dicts (one per image) with keys: src, alt, naturalWidth,
            naturalHeight, clientWidth, clientHeight, ext.
        """
        elements = page.query_selector_all(selector)
        results: list[dict[str, object]] = []

        # Evaluate all image properties in a single JS call per element.
        for el in elements:
            data: dict[str, object] = el.evaluate(
                "el => ({"
                "    src: el.src || el.getAttribute('data-src')"
                "        || el.getAttribute('data-lazy') || '',"
                "    alt: el.alt || '',"
                "    naturalWidth: el.naturalWidth || 0,"
                "    naturalHeight: el.naturalHeight || 0,"
                "    clientWidth: el.clientWidth || 0,"
                "    clientHeight: el.clientHeight || 0,"
                "})"
            )
            data["ext"] = self._extract_extension(str(data.get("src", "")))
            results.append(data)

        return results

    @staticmethod
    def _extract_extension(url: str) -> str:
        """Extracts the file extension from an image URL.

        Args:
            url: Image source URL string.

        Returns:
            Lowercase extension without leading dot, or empty string if absent.
        """
        if not url:
            return ""
        # Strip query parameters before extracting the extension.
        path = urlparse(url).path
        if "." in path:
            return path.rsplit(".", 1)[-1].lower()
        return ""


# EOF
