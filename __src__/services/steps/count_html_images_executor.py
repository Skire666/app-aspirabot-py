"""IStepExecutor for COUNT_HTML_IMAGES."""

from __future__ import annotations

from typing import Any, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.count_html_images_params import CountHtmlImagesParams
from services.steps._helpers import evaluate_count_condition
from services.workflow_service import register_step_executor
from shared.constants import C_DELAY_BETWEEN_RETRY_EVALUATE_SCRIPT, C_MAXIMUM_RETRY_EVALUATE_SCRIPT
from shared.enums import StepTypeEnum
from shared.exception_util import CountHtmlImagesConditionNotMetError


class CountHtmlImagesExecutor(IStepExecutor):
    """Executor for the count HTML images step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_IMAGES

    @override
    def default_params_dict(self) -> dict[str, Any]:
        """Return default parameters as dict."""
        return CountHtmlImagesParams.default().to_dict()

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = CountHtmlImagesParams.from_dict(context.step_params)
        all_images = self._get_filtered_images(browser, context.step_params)
        condition_met = evaluate_count_condition(len(all_images), p.operator, p.value)
        step_success = condition_met if p.success_if == "success" else not condition_met
        if not step_success:
            val_desc = str(p.value)
            raise CountHtmlImagesConditionNotMetError(len(all_images), p.operator, val_desc)

        context.last_message_step = f"Trouvé {len(all_images)} image(s), condition vérifiée."

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
        errors: list[str] = []
        p = CountHtmlImagesParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)

        # Validate that width and height parameters are integers.
        for key in ("height_min", "height_max", "width_min", "width_max"):
            try:
                result = int(model.params.get(key, -1))
                if result < 0:
                    errors.append(f"Erreur dans l'étape {index_display}. : {key} doit être un entier positif.")
            except ValueError, TypeError:
                errors.append(f"Erreur dans l'étape {index_display}. : {key} doit être un nombre.")

        # condition validations
        allowed_operators = {
            "equal",
            "not_equal",
            "greater_than",
            "less_than",
            "greater_or_equal",
            "less_or_equal",
        }
        if p.success_if not in {"success", "failure"}:
            errors.append(f"Erreur dans l'étape {index_display}. : success_if invalide — {p.success_if!r}.")
        if p.operator not in allowed_operators:
            errors.append(f"Erreur dans l'étape {index_display}. : operator invalide — {p.operator!r}.")
        return errors


register_step_executor(CountHtmlImagesExecutor())
