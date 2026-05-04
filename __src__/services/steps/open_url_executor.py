"""IStepExecutor for OPEN_URL."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.open_url_params import OpenUrlParams
from playwright.sync_api import Page
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.step_registry import register_executor
from services.steps._helpers import resolve_timeout_ms


class OpenUrlExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.OPEN_URL

    def default_params_dict(self) -> dict[str, Any]:
        return OpenUrlParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = OpenUrlParams.from_dict(params)
        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        if timeout_ms is not None:
            page.goto(p.url, wait_until=p.wait_state, timeout=timeout_ms)
        else:
            page.goto(p.url, wait_until=p.wait_state)

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = OpenUrlParams.from_dict(params)
        errors: list[str] = []
        if not p.url.strip():
            errors.append("OPEN_URL : l'URL est obligatoire.")
        if p.timeout_duration < 0:
            errors.append("OPEN_URL : timeout_duration doit être >= 0.")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"OPEN_URL : timeout_unit invalide — {p.timeout_unit!r}.")
        return errors


register_executor(OpenUrlExecutor())
