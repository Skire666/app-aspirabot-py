"""IStepExecutor for RANDOM_PAUSE."""

from __future__ import annotations

import random
import time
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.wait_rng_pause_params import WaitRngPauseParams
from services.steps.step_executor_base import StepExecutorBase
from shared.step_registry import register_step_executor
from shared.enums import StepTypeEnum
from shared.time_util import convert_to_sec


class WaitRngPauseExecutor(StepExecutorBase, IStepExecutor):
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


register_step_executor(WaitRngPauseExecutor())
