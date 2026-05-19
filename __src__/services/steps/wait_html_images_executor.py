"""IStepExecutor for WAIT_HTML_IMAGES."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from services.steps._helpers import evaluate_count_condition, get_filtered_images
from services.workflow_service import register_step_executor
from shared.constants import (
    C_UNITS_TIME_ALLOWED_FOR_MODEL,
)
from shared.enums import StepTypeEnum
from shared.exception_util import CountHtmlImagesConditionNotMetError
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_sec


class WaitHtmlImagesExecutor(IStepExecutor):
    """Executor for the wait html images step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_HTML_IMAGES

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = WaitHtmlImagesParams.from_dict(context.step_params)
        nbr_delay_in_sec = convert_to_sec(p.retry_delay, p.retry_unit)
        count: int = -1

        for i in range(p.retry_max):
            all_images = get_filtered_images(browser, p)
            count = len(all_images)
            condition_met = evaluate_count_condition(count, p.operator, p.quantity)
            if condition_met:
                break
            if i == p.retry_max - 1:  # i=5 -> max=6
                raise CountHtmlImagesConditionNotMetError(count, p.operator, str(p.quantity))
            time.sleep(nbr_delay_in_sec)

        context.last_message_step = f"Trouvé {count} image(s), condition vérifiée."

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model parameters."""
        p = WaitHtmlImagesParams.from_dict(model.params)
        errors: list[str] = []
        step_label = str(step_index + 1).zfill(2)

        # Validate dimension bounds.
        bounds = self._parse_dim_bounds(model.params, step_label, errors)
        errors.extend(self._validate_dim_ranges(bounds, step_label))

        # Validate count comparison and retry parameters.
        allowed_operators = {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }
        if p.operator not in allowed_operators:
            errors.append(ERROR_TEMPLATES["wait_html_images_operator_invalid"].format(step=step_label))
        if p.quantity < 0:
            errors.append(ERROR_TEMPLATES["wait_html_images_quantity_negative"].format(step=step_label))
        if p.retry_delay <= 0:
            errors.append(ERROR_TEMPLATES["wait_html_images_retry_delay_invalid"].format(step=step_label))
        if p.retry_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(ERROR_TEMPLATES["wait_html_images_retry_unit_invalid"].format(step=step_label))
        if p.retry_max <= 0:
            errors.append(ERROR_TEMPLATES["wait_html_images_retry_max_invalid"].format(step=step_label))
        return errors

    @staticmethod
    def _parse_dim_bounds(params: dict[str, Any], step_label: str, errors: list[str]) -> dict[str, int]:
        """Parse dimension params as integers; append parse errors in-place."""
        bounds: dict[str, int] = {}

        # Attempt integer conversion for each dimension key.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                bounds[key] = int(params.get(key, 0))
            except ValueError, TypeError:
                errors.append(ERROR_TEMPLATES["image_dim_not_int"].format(step=step_label, key=key))
        return bounds

    @staticmethod
    def _validate_dim_ranges(bounds: dict[str, int], step_label: str) -> list[str]:
        """Validate non-negativity and min <= max for dimension bounds."""
        errors: list[str] = []

        # Check non-negativity for all bounds (max only needs >= 0 here).
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if bounds.get(key, 0) < 0:
                errors.append(ERROR_TEMPLATES["image_dim_negative"].format(step=step_label, key=key))

        # Check min <= max for each dimension.
        for min_k, max_k in (("height_min", "height_max"), ("width_min", "width_max")):
            if min_k in bounds and max_k in bounds and bounds[min_k] > bounds[max_k]:
                errors.append(
                    ERROR_TEMPLATES["image_dim_range_invalid"].format(step=step_label, min_key=min_k, max_key=max_k)
                )
        return errors


register_step_executor(WaitHtmlImagesExecutor())
