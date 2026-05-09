"""IStepExecutor for WAIT_IMAGE_SIZE."""

from __future__ import annotations

import time
from typing import Any

from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepScrapingModel, StepType
from models.steps.wait_image_size_params import WaitImageSizeParams
from services.steps._helpers import evaluate_script_with_safe_retry, resolve_timeout_ms
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL


def _get_filtered_images(page: Any, p: WaitImageSizeParams) -> list[dict]:
    script = """
        () => Array.from(document.querySelectorAll('img'))
            .filter(img => img.naturalWidth > 0)
            .map(img => ({src: img.src, width: img.naturalWidth, height: img.naturalHeight}))
    """
    all_imgs = evaluate_script_with_safe_retry(page, script, 5)
    return [
        img
        for img in all_imgs
        if p.width_min <= img["width"] <= p.width_max and p.height_min <= img["height"] <= p.height_max
    ]


class WaitImageSizeExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        """Return the step type."""
        return StepType.WAIT_IMAGE_SIZE

    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitImageSizeParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        """Execute the step."""
        p = WaitImageSizeParams.from_dict(params)
        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        wait_seconds = timeout_ms / 1000 if timeout_ms is not None else 15
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if _get_filtered_images(page, p):
                return
            time.sleep(0.4)
        raise TimeoutError(f"No image matching size constraints appeared within {wait_seconds}s.")

    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitImageSizeParams.from_dict(model.params)
        errors: list[str] = []
        index_display = str(step_index + 1).zfill(2)
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(model.params.get(key, 0))
            except (ValueError, TypeError):
                errors.append(f"Dans l'étape {index_display}. : {key} doit être un entier.")
        if p.timeout_duration < 0:
            errors.append(f"Dans l'étape {index_display}. : timeout_duration doit être >= 0.")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"Dans l'étape {index_display}. : timeout_unit invalide — {p.timeout_unit!r}.")
        return errors


register_step_executor(WaitImageSizeExecutor())
