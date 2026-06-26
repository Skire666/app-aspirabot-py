"""Shared helper functions for step executors."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any, cast

from interfaces.i_web_browser_service import IWebBrowserService
from playwright.sync_api import ElementHandle
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
    C_STR_ERROR_JS_EVALUATION,
)

from __src__.shared.enums import ExtractTextHtmlEnum

_logger = logging.getLogger(__name__)

_ELEMENT_EXTRACTORS: dict[ExtractTextHtmlEnum, Callable[[ElementHandle], str]] = {
    ExtractTextHtmlEnum.E_TEXT_CONTENT: lambda el: (el.text_content() or "").strip(),
    ExtractTextHtmlEnum.E_OUTER_HTML: lambda el: str(el.evaluate("el => el.outerHTML") or "").strip(),
    ExtractTextHtmlEnum.E_INNER_HTML: lambda el: el.inner_html().strip(),
    ExtractTextHtmlEnum.E_INPUT_VALUE: lambda el: el.input_value().strip(),
}


def extract_from_element(element: ElementHandle, mode: ExtractTextHtmlEnum) -> str:
    """Reads a property from a Playwright ElementHandle.

    Args:
        element: The Playwright element to extract from.
        mode: One of 'textContent', 'outerHTML', 'innerHTML', 'value'; defaults to inner_text.

    Returns:
        The extracted string value.
    """
    extractor = _ELEMENT_EXTRACTORS.get(mode)
    if extractor is not None:
        return extractor(element)
    return element.inner_text().strip()


def evaluate_count_condition(count: int, operator: str, value: int) -> bool:
    """Evaluates a COUNT_ELEMENT condition."""
    conditions: dict[str, bool] = {
        "equal": count == value,
        "not_equal": count != value,
        "greater_than": count > value,
        "less_than": count < value,
        "greater_or_equal": count >= value,
        "less_or_equal": count <= value,
    }
    return conditions.get(operator, False)


def get_script_js_image() -> str:
    """Return the JavaScript function for extracting image info."""
    return """
        () => Array.from(document.querySelectorAll('img'))
            .filter(img => img.naturalWidth > 0)
            .map(img => ({src: img.src, width: img.naturalWidth, height: img.naturalHeight, complete: img.complete}))
        """


def get_filtered_images(browser: IWebBrowserService, bounds: dict[str, int]) -> list[dict[str, Any]]:
    script = get_script_js_image()
    is_success, all_imgs = browser.evaluate_script_with_safe_retry(
        script, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
    )
    # return an empty list if the script evaluation failed after all retries
    if not is_success or all_imgs is None or str(all_imgs) == C_STR_ERROR_JS_EVALUATION:
        return []
    # filter images that do not match the dimension criteria
    h_min, h_max = bounds["height_min"], bounds["height_max"]
    w_min, w_max = bounds["width_min"], bounds["width_max"]
    imgs = cast(list[dict[str, Any]], all_imgs)
    return [img for img in imgs if w_min <= img["width"] <= w_max and h_min <= img["height"] <= h_max]


# EOF
