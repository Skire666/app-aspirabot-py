"""IStepExecutor for COUNT_HTML_IMAGES."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.count_html_images_params import CountHtmlImagesParams
from services.steps._helpers import evaluate_count_condition, get_filtered_images
from services.workflow_service import register_step_executor
from shared.enums import StepTypeEnum
from shared.exception_util import CountHtmlImagesConditionNotMetError
from shared.i18n_fra import ERROR_TEMPLATES


class CountHtmlImagesExecutor(IStepExecutor):
    """Executor for the count HTML images step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_IMAGES

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = CountHtmlImagesParams.from_dict(context.step_params)
        all_images = get_filtered_images(browser, context.step_params)
        condition_met = evaluate_count_condition(len(all_images), p.operator, p.value)
        step_success = condition_met if p.success_if == "success" else not condition_met
        if not step_success:
            val_desc = str(p.value)
            raise CountHtmlImagesConditionNotMetError(len(all_images), p.operator, val_desc)

        context.last_message_step = f"Trouvé {len(all_images)} image(s), condition vérifiée."

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model parameters."""
        p = CountHtmlImagesParams.from_dict(model.params)
        step_label = str(step_index + 1).zfill(2)
        bounds, errors = self._parse_bounds(model.params, step_label)
        errors.extend(self._validate_ranges(bounds, step_label))

        # Validate count comparison parameters.
        allowed_operators = {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }
        if p.value < 0:
            errors.append(ERROR_TEMPLATES["count_html_images_value_negative"].format(step=step_label))
        if p.success_if not in {"success", "failure"}:
            errors.append(
                ERROR_TEMPLATES["count_html_images_success_if_invalid"].format(step=step_label, value=p.success_if),
            )
        if p.operator not in allowed_operators:
            errors.append(
                ERROR_TEMPLATES["count_html_images_operator_invalid"].format(step=step_label, value=p.operator),
            )
        return errors

    @staticmethod
    def _parse_bounds(params: dict[str, Any], step_label: str) -> tuple[dict[str, int], list[str]]:
        """Parse dimension params as integers; return (bounds, errors)."""
        errors: list[str] = []
        bounds: dict[str, int] = {}

        # Attempt integer conversion for each dimension key.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                bounds[key] = int(params.get(key, -1))
            except ValueError, TypeError:
                errors.append(ERROR_TEMPLATES["image_dim_not_int"].format(step=step_label, key=key))
        return bounds, errors

    @staticmethod
    def _validate_ranges(bounds: dict[str, int], step_label: str) -> list[str]:
        """Validate non-negativity, max >= 1, and min <= max constraints."""
        errors: list[str] = []

        # Check non-negativity for all bounds.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            if bounds.get(key, 0) < 0:
                errors.append(ERROR_TEMPLATES["image_dim_negative"].format(step=step_label, key=key))

        # Check max bounds are at least 1.
        for key in ("height_max", "width_max"):
            if bounds.get(key, 1) < 1:
                errors.append(ERROR_TEMPLATES["image_dim_max_below_one"].format(step=step_label, key=key))

        # Check min <= max for each dimension.
        for min_k, max_k in (("height_min", "height_max"), ("width_min", "width_max")):
            if min_k in bounds and max_k in bounds and bounds[min_k] > bounds[max_k]:
                errors.append(
                    ERROR_TEMPLATES["image_dim_range_invalid"].format(step=step_label, min_key=min_k, max_key=max_k),
                )
        return errors


register_step_executor(CountHtmlImagesExecutor())
