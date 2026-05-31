"""IStepExecutor for SECTION_STEPS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import cast, override

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.section_params import SectionParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor

_logger = logging.getLogger(__name__)


class SectionExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the section step — logs the title and always returns success."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SECTION_STEPS

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Execute the step."""
        p = cast(SectionParams, context.step_scraping_data.params)

        context.last_message_step = f"Section : {p.title}"


register_step_executor(SectionExecutor())


# EOF
