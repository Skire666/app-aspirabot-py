"""IStepExecutor for END_PROCESS."""

from __future__ import annotations

import time
from typing import override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.step_scraping_model import StepScrapingModel
from models.steps.kill_browser_params import KillBrowserParams
from services.workflow_service import register_step_executor
from shared.constants import C_UNITS_TIME_ALLOWED_FOR_MODEL
from shared.enums import StepTypeEnum
from shared.i18n_fra import ERROR_TEMPLATES
from shared.time_util import convert_to_sec


class KillBrowserExecutor(IStepExecutor):
    """Executor for the end process scraping step."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_KILL_BROWSER

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = KillBrowserParams.from_dict(context.step_params)
        delay = convert_to_sec(p.wait_duration, p.wait_unit)
        if delay > 0:
            time.sleep(delay)

        browser.close_all_tabs()  # ensure all tabs are closed before signaling end-process
        context.end_process = True

    @override
    def validate_model(self, model: StepScrapingModel, step_index: int) -> list[str]:
        """Validate the step model."""
        p = KillBrowserParams.from_dict(model.params)
        index_display = str(step_index + 1).zfill(2)
        errors: list[str] = []
        if p.wait_duration < 0:
            errors.append(ERROR_TEMPLATES["end_process_wait_duration_invalid"].format(step=index_display))
        if p.wait_unit not in C_UNITS_TIME_ALLOWED_FOR_MODEL:
            errors.append(
                ERROR_TEMPLATES["end_process_wait_unit_invalid"].format(step=index_display, value=p.wait_unit),
            )
        return errors


register_step_executor(KillBrowserExecutor())
