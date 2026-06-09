"""IStepExecutor for EXTRACT_VARIABLE."""

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

from __future__ import annotations

import datetime
from typing import cast, override
from urllib.parse import urlparse

from interfaces.i_scraping_event_bus import IScrapingEventBus
from interfaces.i_step_executor import IStepExecutor
from interfaces.i_web_browser_service import IWebBrowserService
from models.scraping_context_model import ScrapingContextModel
from models.steps.extract_variable_params import ExtractVariableParams
from shared.datetime_util import C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS
from shared.enums import StepExecutionResultEnum, StepTypeEnum
from shared.step_registry import register_step_executor


def _resolve_variable(variable: str, context: ScrapingContextModel) -> str:
    """Return the current value for the requested context variable.

    Args:
        variable: One of 'datetime_now', 'last_url_full', 'last_url_domain', or 'last_url_cutted'.
        context: Live scraping context providing URL and timestamp data.

    Returns:
        The resolved string value for the variable.
    """
    if variable == "datetime_now":
        return datetime.datetime.now().strftime(C_DATETIME_FORMAT_YYYY_MM_DD_HH_MM_SS)
    if variable == "last_url_full":
        return context.last_url_opened
    if variable == "last_url_domain":
        # https://www.google.com/search?q=python&pp=654654 => www.google.com
        # https://api.example.com:443/v1/users   => api.example.com:443
        return urlparse(context.last_url_opened).netloc
    if variable == "last_url_cutted":
        # anti-youtube and random extra query params
        # https://www.google.com/search?q=python&pp=654654 => /search?q=python&pp=654654
        return context.last_url_opened.split("&")[0]
    return ""


class ExtractVariableExecutor(IStepExecutor):
    """Executor for the export variable step — reads from context and pushes to extracted data."""

    @classmethod
    def step_type(cls) -> StepTypeEnum:
        """Return the step type."""
        return StepTypeEnum.E_EXTRACT_VARIABLE

    @override
    def execute_logical(
        self, browser: IWebBrowserService, context: ScrapingContextModel, event_bus: IScrapingEventBus
    ) -> StepExecutionResultEnum:
        """Resolve the chosen variable from context and push it into extracted data.

        Args:
            browser: Unused — values are read from context, not the browser.
            context: Live scraping context; extracted_data is written with the resolved value.
            event_bus: Event bus for intermediate log entries.
        """
        assert context.step_scraping_data is not None
        p = cast(ExtractVariableParams, context.step_scraping_data.params)
        try:
            value = _resolve_variable(p.variable, context)
            context.push_extracted_values(p.mapping, p.variable, p.comment, [value])
            event_bus.log_step(context, f"Variable '{p.variable}' = '{value}'.")
        except Exception as exc:  # noqa: BLE001
            event_bus.log_step(context, f"Excp : {exc}")
            return StepExecutionResultEnum.E_ERROR
        else:
            return StepExecutionResultEnum.E_SUCCESS


register_step_executor(ExtractVariableExecutor())


# EOF
