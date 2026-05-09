"""IStepExecutor for EXTRACT_TEXT."""

from __future__ import annotations

import logging
from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.extract_text_params import ExtractTextParams
from services.steps._helpers import extract_from_element
from services.workflow_service import register_step_executor

_logger = logging.getLogger(__name__)


class ExtractTextExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.EXTRACT_TEXT

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return ExtractTextParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = ExtractTextParams.from_dict(params)
        elements = page.query_selector_all(p.selector)
        if not elements:
            _logger.warning("EXTRACT_TEXT: no element matches %r", p.selector)
            return
        selected = [elements[0]] if p.target == "first" else [elements[-1]] if p.target == "last" else elements
        texts = [extract_from_element(el, p.extract_mode) for el in selected]
        _logger.info("EXTRACT_TEXT [%s]: %s", p.selector, "\n".join(texts)[:500])

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = ExtractTextParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        allowed_modes = {"innerText", "textContent", "outerHTML", "innerHTML", "value"}
        allowed_targets = {"first", "last", "all"}
        errors: list[str] = []
        if not p.selector.strip():
            errors.append(f"Erreur dans l'étape {index_display}. : le sélecteur CSS est obligatoire.")
        if p.extract_mode not in allowed_modes:
            errors.append(f"Erreur dans l'étape {index_display}. : mode d'extraction '{p.extract_mode}' invalide.")
        if p.target not in allowed_targets:
            errors.append(f"Erreur dans l'étape {index_display}. : cible '{p.target}' invalide.")
        return errors


register_step_executor(ExtractTextExecutor())
