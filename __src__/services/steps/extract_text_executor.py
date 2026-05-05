"""IStepExecutor for EXTRACT_TEXT."""
from __future__ import annotations
import logging
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.extract_text_params import ExtractTextParams
from shared.step_registry import register_executor
from services.steps._helpers import extract_from_element

_logger = logging.getLogger(__name__)


class ExtractTextExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.EXTRACT_TEXT

    def default_params_dict(self) -> dict[str, Any]:
        return ExtractTextParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        p = ExtractTextParams.from_dict(params)
        elements = page.query_selector_all(p.selector)
        if not elements:
            _logger.warning("EXTRACT_TEXT: no element matches %r", p.selector)
            return
        selected = [elements[0]] if p.target == "first" else [elements[-1]] if p.target == "last" else elements
        texts = [extract_from_element(el, p.extract_mode) for el in selected]
        _logger.info("EXTRACT_TEXT [%s]: %s", p.selector, "\n".join(texts)[:500])

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = ExtractTextParams.from_dict(params)
        allowed_modes = {"innerText", "textContent", "outerHTML", "innerHTML", "value"}
        allowed_targets = {"first", "last", "all"}
        errors: list[str] = []
        if not p.selector.strip():
            errors.append("EXTRACT_TEXT : le sélecteur CSS est obligatoire.")
        if p.extract_mode not in allowed_modes:
            errors.append(f"EXTRACT_TEXT : mode d'extraction invalide — {p.extract_mode!r}.")
        if p.target not in allowed_targets:
            errors.append(f"EXTRACT_TEXT : cible invalide — {p.target!r}.")
        return errors


register_executor(ExtractTextExecutor())
