"""IStepExecutor for COUNT_HTML_IMAGES."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

from typing import cast, override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.count_html_images_params import CountHtmlImagesParams
from services.steps._helpers import evaluate_count_condition, get_filtered_images
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.exception_util import CountHtmlImagesConditionNotMetError
from shared.step_registry import register_step_executor


class CountHtmlImagesExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the count HTML images step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_COUNT_HTML_IMAGES

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None
        p = cast(CountHtmlImagesParams, context.step_scraping_data.params)
        try:
            all_images = get_filtered_images(browser, p.to_dict())
            condition_met = evaluate_count_condition(len(all_images), p.operator, p.value)
            step_success = condition_met if p.success_if == "success" else not condition_met
            if not step_success:
                raise CountHtmlImagesConditionNotMetError(len(all_images), p.operator, str(p.value))  # noqa: TRY301
            event_bus.log_step(context, f"Trouvé {len(all_images)} image(s), condition vérifiée.")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(CountHtmlImagesExecutor())


# EOF
