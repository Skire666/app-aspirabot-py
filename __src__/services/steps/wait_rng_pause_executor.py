"""IStepExecutor for RANDOM_PAUSE."""

from __future__ import annotations

import random
import time
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps_context_model import StepsContext
from models.steps.wait_rng_pause_params import WaitRngPauseParams
from shared.step_registry import register_step_executor
from shared.enums import StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_sec


class WaitRngPauseExecutor(IStepExecutor):
    """Executor for the random pause scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_WAIT_RANDOM_PAUSE

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(WaitRngPauseParams, context.step_scraping_data.params)
        delay = random.uniform(float(p.min_val), float(p.max_val))
        time_sec = convert_to_sec(delay, p.unit)
        if time_sec > 0:
            time.sleep(time_sec)

        context.last_message_step = f"Pause aléatoire de {time_sec:.3f} secondes effectuée."

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int, steps_context: StepsContext) -> list[str]:
        """Validate the step model."""
        p = cast(WaitRngPauseParams, model.params)
        index_display = str(step_index + 1).zfill(2)
        if p.min_val <= 0:
            return [ERROR_TEMPLATES["wait_rng_pause_min_invalid"].format(step=index_display)]
        if p.max_val <= 0:
            return [ERROR_TEMPLATES["wait_rng_pause_max_invalid"].format(step=index_display)]
        if p.min_val > p.max_val:
            return [ERROR_TEMPLATES["wait_rng_pause_range_invalid"].format(step=index_display)]
        return []


register_step_executor(WaitRngPauseExecutor())
