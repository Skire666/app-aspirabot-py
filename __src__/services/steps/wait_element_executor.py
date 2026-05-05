"""IStepExecutor for WAIT_ELEMENT."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.wait_element_params import WaitElementParams
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.step_registry import register_executor
from services.steps._helpers import resolve_timeout_ms


class WaitElementExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.WAIT_ELEMENT

    def default_params_dict(self) -> dict[str, Any]:
        return WaitElementParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        p = WaitElementParams.from_dict(params)
        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        if timeout_ms is not None:
            page.wait_for_selector(p.selector, timeout=timeout_ms)
        else:
            page.wait_for_selector(p.selector)

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = WaitElementParams.from_dict(params)
        errors: list[str] = []
        if not p.selector.strip():
            errors.append("WAIT_ELEMENT : le sélecteur CSS est obligatoire.")
        if p.timeout_duration < 0:
            errors.append("WAIT_ELEMENT : timeout_duration doit être >= 0.")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"WAIT_ELEMENT : timeout_unit invalide — {p.timeout_unit!r}.")
        return errors


register_executor(WaitElementExecutor())
