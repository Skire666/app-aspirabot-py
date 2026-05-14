"""Shared helper functions for step executors."""

from __future__ import annotations

import logging
from typing import Any

_logger = logging.getLogger(__name__)


def extract_from_element(element: Any, mode: str) -> str:
    """Reads a property from a Playwright ElementHandle."""
    if mode == "textContent":
        return element.text_content() or ""
    if mode == "outerHTML":
        return element.evaluate("el => el.outerHTML") or ""
    if mode == "innerHTML":
        return element.inner_html()
    if mode == "value":
        return element.input_value()
    return element.inner_text()


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
