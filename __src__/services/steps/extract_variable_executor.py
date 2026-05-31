"""IStepExecutor for EXPORT_VARIABLE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import datetime
from typing import cast, override
from urllib.parse import urlparse

from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_variable_params import ExtractVariableParams
from services.steps.step_executor_base import StepExecutorBase
from shared.enums import StepTypeEnum
from shared.step_registry import register_step_executor


def _resolve_variable(variable: str, context: ScrapingContextModel) -> str:
    """Return the current value for the requested context variable.

    Args:
        variable: One of 'date_time_now', 'last_url', or 'last_domain'.
        context: Live scraping context providing URL and timestamp data.

    Returns:
        The resolved string value for the variable.
    """
    if variable == "date_time_now":
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if variable == "last_url":
        return context.last_url_opened
    if variable == "last_domain":
        return urlparse(context.last_url_opened).netloc
    return ""


class ExtractVariableExecutor(StepExecutorBase, IStepExecutor):
    """Executor for the export variable step — reads from context and pushes to extracted data."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXPORT_VARIABLE

    @override
    def execute_logical(self, browser: IWebBrowserService, context: ScrapingContextModel) -> None:
        """Resolve the chosen variable from context and push it into extracted data.

        Args:
            browser: Unused — values are read from context, not the browser.
            context: Live scraping context; extracted_data is written with the resolved value.
        """
        p = cast(ExtractVariableParams, context.step_scraping_data.params)

        value = _resolve_variable(p.variable, context)
        context.push_extracted_values(p.mapping, p.variable, p.comment, [value])
        context.last_message_step = f"Variable extraite '{p.variable}' = '{value}'."


register_step_executor(ExtractVariableExecutor())


# EOF
