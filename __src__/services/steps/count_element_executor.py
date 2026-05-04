"""IStepExecutor for COUNT_ELEMENT."""
from __future__ import annotations
import logging
import time
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.count_element_params import CountElementParams
from playwright.sync_api import Page
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL, C_UNITS_TIME_CONVERSION_TO_MS, C_UNITS_TIME_DEFAULT_MODEL
from shared.step_registry import register_executor
from services.steps._helpers import evaluate_count_condition

_logger = logging.getLogger(__name__)


class CountElementExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.COUNT_ELEMENT

    def default_params_dict(self) -> dict[str, Any]:
        return CountElementParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = CountElementParams.from_dict(params)
        if p.wait_duration > 0:
            ms = p.wait_duration * C_UNITS_TIME_CONVERSION_TO_MS.get(p.wait_unit, 1_000)
            time.sleep(ms / 1_000.0)
        count = page.locator(p.selector).count()
        _logger.info("COUNT_ELEMENT: %d élément(s) pour %r", count, p.selector)
        condition_met = evaluate_count_condition(count, p.operator, p.value, p.value_min, p.value_max)
        step_success = condition_met if p.success_if == "success" else not condition_met
        if not step_success:
            val_desc = f"{p.value_min}-{p.value_max}" if p.operator in {"between", "not_between"} else str(p.value)
            raise ValueError(f"COUNT_ELEMENT : condition non satisfaite (COUNT={count}, {p.operator} {val_desc})")

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = CountElementParams.from_dict(params)
        allowed_operators = {"between", "not_between", "equal", "not_equal", "greater_than", "less_than", "greater_or_equal", "less_or_equal"}
        errors: list[str] = []
        if not p.selector.strip():
            errors.append("COUNT_ELEMENT : le sélecteur CSS est obligatoire.")
        if p.wait_duration < 0:
            errors.append("COUNT_ELEMENT : wait_duration doit être >= 0.")
        if p.wait_duration > 0 and p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"COUNT_ELEMENT : wait_unit invalide — {p.wait_unit!r}.")
        if p.success_if not in {"success", "failure"}:
            errors.append(f"COUNT_ELEMENT : success_if invalide — {p.success_if!r}.")
        if p.operator not in allowed_operators:
            errors.append(f"COUNT_ELEMENT : operator invalide — {p.operator!r}.")
        if p.operator in {"between", "not_between"} and p.value_min > p.value_max:
            errors.append("COUNT_ELEMENT : value_min doit être <= value_max.")
        return errors


register_executor(CountElementExecutor())
