"""IStepExecutor for SECTION_STEPS."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import logging
from typing import override

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor

_logger = logging.getLogger(__name__)


class SectionExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the section step — logs the title and always returns success."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_SECTION_STEPS

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Execute the step."""
        assert context.step_scraping_data is not None

        return StepExecutionResultEnum.E_SUCCESS


register_step_executor(SectionExecutor())


# EOF
