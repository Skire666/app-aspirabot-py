"""IStepExecutor for CLICK_ELEMENT."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.click_element_params import ClickElementParams
from services.steps._helpers import evaluate_script_with_safe_retry
from services.workflow_service import register_step_executor


class ClickElementExecutor(IStepExecutor):
    """Executor for the click element scraping step."""

    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.CLICK_ELEMENT

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return ClickElementParams.default().to_dict()

    @override
    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = ClickElementParams.from_dict(params)
        # Tentative 1 : click normal
        try:
            if p.click_mode == "Normal":
                page.click(p.selector, timeout=1000)
                return
        except Exception:
            pass
        if p.click_mode == "Normal":
            raise ValueError(f"Element {p.selector!r} not found for normal click.")
        # Tentative 2 : click forcé
        try:
            if p.click_mode == "Forced":
                page.click(p.selector, force=True, timeout=1000)
                return
        except Exception:
            pass
        if p.click_mode == "Forced":
            raise ValueError(f"Element {p.selector!r} not found for forced click.")
        # Tentative 3 : JS direct
        if p.click_mode == "JS Direct":
            script = f"document.querySelector('{p.selector}')?.click();"
            evaluate_script_with_safe_retry(page, script, 5)
        else:
            raise ValueError(f"Unsupported click mode: {p.click_mode}")

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ClickElementParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        # if selecteur est vide ou ne contient que des espaces
        if not p.selector.strip():
            return [f"Erreur dans l'étape {index_display}. : le sélecteur CSS est obligatoire."]
        return []


register_step_executor(ClickElementExecutor())
