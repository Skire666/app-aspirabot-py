"""IStepExecutor for WAIT_HTML_IMAGES."""

from __future__ import annotations

import time
from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.wait_html_images_params import WaitHtmlImagesParams
from services.steps._helpers import evaluate_count_condition
from services.workflow_service import register_step_executor
from shared.constants import (
    C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT,
    C_MAXIMUM_RETRY_EVALUATE_SCRIPT,
    C_UNITS_TIME_ALLOWED_FOR_MODEL,
)
from shared.enums import StepTypeEnum
from shared.exception_util import CountHtmlImagesConditionNotMetError
from shared.time_util import convert_to_sec


class WaitHtmlImagesExecutor(IStepExecutor):
    """Executor for the wait html images step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_HTML_IMAGES

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return WaitHtmlImagesParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = WaitHtmlImagesParams.from_dict(context.step_params)
        nbr_delay_in_sec = convert_to_sec(p.retry_delay, p.retry_unit)
        count: int = -1

        for i in range(p.retry_max):
            all_images = self._get_filtered_images(browser, p)
            count = len(all_images)
            condition_met = evaluate_count_condition(count, p.operator, p.quantity)
            if condition_met:
                break
            if i == p.retry_max - 1:  # i=5 -> max=6
                raise CountHtmlImagesConditionNotMetError(count, p.operator, str(p.quantity))
            time.sleep(nbr_delay_in_sec)

        context.last_message_step = f"Trouvé {count} image(s), condition vérifiée."

    @staticmethod
    def _get_filtered_images(browser: IWebBrowserService, params: dict[str, int]) -> list[dict[str, Any]]:
        script = """
            () => Array.from(document.querySelectorAll('img'))
                .filter(img => img.naturalWidth > 0)
                .map(img => ({src: img.src, width: img.naturalWidth, height: img.naturalHeight, complete: img.complete}))
        """
        all_imgs: list[dict[str, Any]] = browser.evaluate_script_with_safe_retry(
            script, C_MAXIMUM_RETRY_EVALUATE_SCRIPT, C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT
        )
        # return an empty list if the script evaluation failed after all retries
        if all_imgs is None:
            return []
        # filter images that do not match the dimension criteria
        h_min, h_max = params["height_min"], params["height_max"]
        w_min, w_max = params["width_min"], params["width_max"]
        return [img for img in all_imgs if w_min <= img["width"] <= w_max and h_min <= img["height"] <= h_max]

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = WaitHtmlImagesParams.from_dict(model.params)
        errors: list[str] = []
        index_display = str(step_index + 1).zfill(2)
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                int(model.params.get(key, 0))
            except ValueError, TypeError:
                errors.append(f"Dans l'étape {index_display}. : {key} doit être un entier.")
        if p.operator not in {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }:
            errors.append(
                f"Dans l'étape {index_display}. : l'opérateur doit être l'un des suivants : equal, not_equal, greater_than, less_than, greater_or_equal, less_or_equal."
            )
        if p.quantity < 0:
            errors.append(f"Dans l'étape {index_display}. : la quantité doit être >= 0")
        if p.retry_delay <= 0:
            errors.append(f"Dans l'étape {index_display}. : le délai de retry doit être >= 1")
        if p.retry_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(
                f"Dans l'étape {index_display}. : l'unité de retry doit être l'une des suivantes : {', '.join(C_UNITS_TIME_ALLOWED_FOR_MODEL)}."
            )
        if p.retry_max <= 0:
            errors.append(f"Dans l'étape {index_display}. : le nombre maximum de retry doit être >= 1")
        return errors


register_step_executor(WaitHtmlImagesExecutor())
