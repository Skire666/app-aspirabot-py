"""Shared helper functions for step executors."""

from __future__ import annotations

import logging
from typing import Any

from shared.constants import C_UNITS_TIME_CONVERSION_TO_MS

_logger = logging.getLogger(__name__)


def resolve_timeout_ms(timeout_duration: int, timeout_unit: str) -> int | None:
    """Returns timeout in ms or None when duration is 0."""
    if timeout_duration <= -1 or timeout_unit not in C_UNITS_TIME_CONVERSION_TO_MS:
        _logger.warning("Invalid timeout parameters: duration=%d, unit=%r", timeout_duration, timeout_unit)
        return None
    return int(timeout_duration * C_UNITS_TIME_CONVERSION_TO_MS.get(timeout_unit, 1_000))


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


def evaluate_count_condition(count: int, operator: str, value: int, value_min: int, value_max: int) -> bool:
    """Evaluates a COUNT_ELEMENT condition."""
    conditions: dict[str, bool] = {
        "between": value_min <= count <= value_max,
        "equal": count == value,
        "not_equal": count != value,
        "greater_than": count > value,
        "less_than": count < value,
        "greater_or_equal": count >= value,
        "less_or_equal": count <= value,
    }
    return conditions.get(operator, False)
