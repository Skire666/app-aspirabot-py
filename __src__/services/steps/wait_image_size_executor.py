"""IStepExecutor for WAIT_IMAGE_SIZE."""
from __future__ import annotations
import time
from typing import Any
from interfaces.i_step_executor import IStepExecutor
from models.step_scraping_model import StepType
from models.steps.wait_image_size_params import WaitImageSizeParams
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.step_registry import register_executor
from services.steps._helpers import evaluate_script_with_safe_retry, resolve_timeout_ms


def _get_filtered_images(page: Any, p: WaitImageSizeParams) -> list[dict]:
    script = """
        () => Array.from(document.querySelectorAll('img'))
            .filter(img => img.naturalWidth > 0)
            .map(img => ({src: img.src, width: img.naturalWidth, height: img.naturalHeight}))
    """
    all_imgs = evaluate_script_with_safe_retry(page, script, 5)
    return [
        img for img in all_imgs
        if p.width_min <= img["width"] <= p.width_max and p.height_min <= img["height"] <= p.height_max
    ]


class WaitImageSizeExecutor(IStepExecutor):
    @classmethod
    def step_type(cls) -> StepType:
        return StepType.WAIT_IMAGE_SIZE

    def default_params_dict(self) -> dict[str, Any]:
        return WaitImageSizeParams.default().to_dict()

    def execute(self, page: Any, params: dict[str, Any]) -> None:
        p = WaitImageSizeParams.from_dict(params)
        timeout_ms = resolve_timeout_ms(p.timeout_duration, p.timeout_unit)
        wait_seconds = timeout_ms / 1000 if timeout_ms is not None else 15
        deadline = time.time() + wait_seconds
        while time.time() < deadline:
            if _get_filtered_images(page, p):
                return
            time.sleep(0.4)
        raise TimeoutError(f"No image matching size constraints appeared within {wait_seconds}s.")

    def validate(self, params: dict[str, Any], step_index: int) -> list[str]:
        p = WaitImageSizeParams.from_dict(params)
        errors: list[str] = []
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(params.get(key, 0))
            except (ValueError, TypeError):
                errors.append(f"WAIT_IMAGE_SIZE : {key} doit être un entier.")
        if p.timeout_duration < 0:
            errors.append("WAIT_IMAGE_SIZE : timeout_duration doit être >= 0.")
        if p.timeout_duration > 0 and p.timeout_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(f"WAIT_IMAGE_SIZE : timeout_unit invalide — {p.timeout_unit!r}.")
        return errors


register_executor(WaitImageSizeExecutor())
