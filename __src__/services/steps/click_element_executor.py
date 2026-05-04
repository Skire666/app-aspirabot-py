"""IStepExecutor for CLICK_ELEMENT."""
from __future__ import annotations
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.click_element_params import ClickElementParams
from playwright.sync_api import Page
from playwright.sync_api import Error as PlaywrightError
from shared.step_registry import register_executor
from services.steps._helpers import evaluate_script_with_safe_retry


class ClickElementExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.CLICK_ELEMENT

    def default_params_dict(self) -> dict[str, Any]:
        return ClickElementParams.default().to_dict()

    def execute(self, page: Page, params: dict[str, Any]) -> None:
        p = ClickElementParams.from_dict(params)
        # Tentative 1 : click normal
        try:
            if p.click_mode == "Normal":
                page.click(p.selector, timeout=1000)
                return
        except Exception:
            pass
        if p.click_mode == "Normal":
            raise PlaywrightError(f"Element {p.selector!r} not found for normal click.")
        # Tentative 2 : click forcé
        try:
            if p.click_mode == "Forced":
                page.click(p.selector, force=True, timeout=1000)
                return
        except Exception:
            pass
        if p.click_mode == "Forced":
            raise PlaywrightError(f"Element {p.selector!r} not found for forced click.")
        # Tentative 3 : JS direct
        if p.click_mode == "JS Direct":
            script = f"document.querySelector('{p.selector}')?.click();"
            evaluate_script_with_safe_retry(page, script, 5)
        else:
            raise ValueError(f"Unsupported click mode: {p.click_mode}")

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = ClickElementParams.from_dict(params)
        if not p.selector.strip():
            return ["CLICK_ELEMENT : le sélecteur CSS est obligatoire."]
        return []


register_executor(ClickElementExecutor())
